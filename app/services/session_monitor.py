"""
DSAM — Session Monitor Service
Escanea Redis (PCT 149) para capturar sesiones activas de Odoo,
geolocaliza IPs y sincroniza snapshots a la BD de ERP Core.
"""
import asyncio
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Any, Optional

import redis.asyncio as aioredis
from sqlalchemy import select, delete, and_
from sqlalchemy.orm import Session

from ..config import (
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB,
    GEOIP_DB_PATH, DSAM_POLL_INTERVAL_SECONDS,
)
from ..models.database import (
    ActiveSession, SessionGeoEvent, TenantSessionConfig,
)

logger = logging.getLogger(__name__)

# ── GeoIP2 lazy loader ──
_geoip_reader = None


def _get_geoip_reader():
    """Carga GeoIP2 bajo demanda. Si no existe el archivo MMDB, retorna None."""
    global _geoip_reader
    if _geoip_reader is not None:
        return _geoip_reader
    try:
        import geoip2.database
        _geoip_reader = geoip2.database.Reader(GEOIP_DB_PATH)
        logger.info("GeoIP2 database loaded: %s", GEOIP_DB_PATH)
    except Exception as e:
        logger.warning("GeoIP2 not available (%s), geolocation disabled", e)
        _geoip_reader = None
    return _geoip_reader


def geolocate_ip(ip: str) -> dict[str, Any]:
    """
    Geolocaliza una IP usando GeoIP2.
    Retorna dict con country, country_code, region, city, lat, lon.
    Si falla, retorna dict con valores None.
    """
    empty = {
        "country": None, "country_code": None,
        "region": None, "city": None,
        "lat": None, "lon": None,
    }
    # Skip private / localhost
    if ip.startswith(("10.", "192.168.", "172.", "127.", "::1")):
        return {**empty, "country": "Private", "country_code": "XX", "city": "LAN"}

    reader = _get_geoip_reader()
    if not reader:
        return empty
    try:
        resp = reader.city(ip)
        return {
            "country": resp.country.name,
            "country_code": resp.country.iso_code,
            "region": resp.subdivisions.most_specific.name if resp.subdivisions else None,
            "city": resp.city.name,
            "lat": resp.location.latitude,
            "lon": resp.location.longitude,
        }
    except Exception:
        return empty


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia Haversine entre dos coordenadas en kilómetros."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ═══════════════════════════════════════════════════════
# Redis Session Scanner
# ═══════════════════════════════════════════════════════

async def get_redis_pool() -> aioredis.Redis:
    """Crea pool async de Redis."""
    return aioredis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )


async def scan_redis_sessions(r: aioredis.Redis) -> list[dict[str, Any]]:
    """
    Escanea todas las claves session:* en Redis.
    Retorna lista de dicts con la data de cada sesión.
    Formato de clave: session:{subdomain}:{session_id}
    """
    sessions = []
    cursor = "0"
    while True:
        cursor, keys = await r.scan(cursor=cursor, match="session:*", count=200)
        for key in keys:
            try:
                raw = await r.get(key)
                if not raw:
                    continue
                data = json.loads(raw) if isinstance(raw, str) else raw
                parts = key.split(":", 2)
                tenant_db = parts[1] if len(parts) >= 3 else "unknown"
                sessions.append({
                    "redis_key": key,
                    "tenant_db": tenant_db,
                    "session_id": parts[2] if len(parts) >= 3 else key,
                    "data": data,
                })
            except Exception as e:
                logger.debug("Error parsing session key %s: %s", key, e)
        if cursor == 0 or cursor == "0":
            break
    return sessions


def parse_session_data(session: dict) -> dict[str, Any]:
    """Extrae campos relevantes del payload de sesión Odoo en Redis."""
    data = session.get("data", {})
    # Odoo almacena: db, login, uid, session_token, context, etc.
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}
    return {
        "redis_session_key": session["redis_key"],
        "tenant_db": session.get("tenant_db", data.get("db", "unknown")),
        "odoo_uid": data.get("uid"),
        "odoo_login": data.get("login"),
        "ip_address": data.get("ip", data.get("remote_addr", "0.0.0.0")),
        "user_agent": data.get("user_agent", ""),
        "session_start": data.get("created_at"),
        "last_activity": data.get("last_activity"),
    }


# ═══════════════════════════════════════════════════════
# Sync to DB
# ═══════════════════════════════════════════════════════

async def sync_sessions_to_db(db: Session) -> dict[str, int]:
    """
    Escanea Redis → geolocaliza → upsert en active_sessions.
    Marca como inactivas las sesiones que ya no están en Redis.
    Registra eventos geo en session_geo_events.
    Retorna stats: {scanned, created, updated, removed}.
    """
    stats = {"scanned": 0, "created": 0, "updated": 0, "removed": 0}
    try:
        r = await get_redis_pool()
    except Exception as e:
        logger.error("Cannot connect to Redis: %s", e)
        return stats

    try:
        raw_sessions = await scan_redis_sessions(r)
        stats["scanned"] = len(raw_sessions)
        now = datetime.utcnow()
        active_keys: set[str] = set()

        for sess in raw_sessions:
            parsed = parse_session_data(sess)
            active_keys.add(parsed["redis_session_key"])
            geo = geolocate_ip(parsed["ip_address"])

            # Upsert active_sessions
            result = db.execute(
                select(ActiveSession).where(
                    ActiveSession.redis_session_key == parsed["redis_session_key"]
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.last_polled_at = now
                existing.last_activity = parsed.get("last_activity")
                existing.is_active = True
                # Actualizar geo si cambió IP
                if existing.ip_address != parsed["ip_address"]:
                    existing.ip_address = parsed["ip_address"]
                    existing.geo_country = geo["country"]
                    existing.geo_country_code = geo["country_code"]
                    existing.geo_region = geo["region"]
                    existing.geo_city = geo["city"]
                    existing.geo_lat = geo["lat"]
                    existing.geo_lon = geo["lon"]
                stats["updated"] += 1
            else:
                new_session = ActiveSession(
                    redis_session_key=parsed["redis_session_key"],
                    tenant_db=parsed["tenant_db"],
                    odoo_uid=parsed["odoo_uid"],
                    odoo_login=parsed["odoo_login"],
                    ip_address=parsed["ip_address"],
                    user_agent=parsed.get("user_agent"),
                    geo_country=geo["country"],
                    geo_country_code=geo["country_code"],
                    geo_region=geo["region"],
                    geo_city=geo["city"],
                    geo_lat=geo["lat"],
                    geo_lon=geo["lon"],
                    session_start=parsed.get("session_start"),
                    last_activity=parsed.get("last_activity"),
                    first_seen_at=now,
                    last_polled_at=now,
                    is_active=True,
                )
                db.add(new_session)
                stats["created"] += 1

                # Registrar evento geo
                geo_event = SessionGeoEvent(
                    tenant_db=parsed["tenant_db"],
                    odoo_login=parsed["odoo_login"] or "unknown",
                    ip_address=parsed["ip_address"],
                    geo_country=geo["country"],
                    geo_country_code=geo["country_code"],
                    geo_region=geo["region"],
                    geo_city=geo["city"],
                    geo_lat=geo["lat"],
                    geo_lon=geo["lon"],
                    event_at=now,
                )
                db.add(geo_event)

        # Marcar inactivas las sesiones que ya no están en Redis
        stale_result = db.execute(
            select(ActiveSession).where(
                and_(
                    ActiveSession.is_active == True,
                    ActiveSession.redis_session_key.notin_(active_keys) if active_keys else ActiveSession.is_active == True,
                )
            )
        )
        for stale in stale_result.scalars():
            if stale.redis_session_key not in active_keys:
                stale.is_active = False
                stats["removed"] += 1

        db.commit()
    except Exception as e:
        logger.error("Error syncing sessions: %s", e)
        db.rollback()
        raise
    finally:
        await r.aclose()

    return stats


async def terminate_redis_session(session_key: str) -> bool:
    """Elimina una sesión de Redis para forzar logout."""
    try:
        r = await get_redis_pool()
        deleted = await r.delete(session_key)
        await r.aclose()
        return deleted > 0
    except Exception as e:
        logger.error("Error terminating session %s: %s", session_key, e)
        return False


async def get_active_sessions_by_tenant(
    db: Session, tenant_db: str
) -> list[ActiveSession]:
    """Obtiene sesiones activas de un tenant desde la BD."""
    result = db.execute(
        select(ActiveSession).where(
            and_(ActiveSession.tenant_db == tenant_db, ActiveSession.is_active == True)
        ).order_by(ActiveSession.last_activity.desc())
    )
    return result.scalars().all()


async def get_active_sessions_by_user(
    db: Session, tenant_db: str, odoo_login: str
) -> list[ActiveSession]:
    """Obtiene sesiones activas de un usuario específico."""
    result = db.execute(
        select(ActiveSession).where(
            and_(
                ActiveSession.tenant_db == tenant_db,
                ActiveSession.odoo_login == odoo_login,
                ActiveSession.is_active == True,
            )
        ).order_by(ActiveSession.last_activity.desc())
    )
    return result.scalars().all()


async def get_session_stats(db: Session) -> dict[str, Any]:
    """Dashboard global stats."""
    from sqlalchemy import func
    total = db.execute(
        select(func.count(ActiveSession.id)).where(ActiveSession.is_active == True)
    )
    by_tenant = db.execute(
        select(
            ActiveSession.tenant_db,
            func.count(ActiveSession.id).label("count"),
        )
        .where(ActiveSession.is_active == True)
        .group_by(ActiveSession.tenant_db)
        .order_by(func.count(ActiveSession.id).desc())
    )
    by_country = db.execute(
        select(
            ActiveSession.geo_country_code,
            ActiveSession.geo_country,
            func.count(ActiveSession.id).label("count"),
        )
        .where(and_(ActiveSession.is_active == True, ActiveSession.geo_country_code.isnot(None)))
        .group_by(ActiveSession.geo_country_code, ActiveSession.geo_country)
        .order_by(func.count(ActiveSession.id).desc())
    )
    return {
        "total_active": total.scalar() or 0,
        "by_tenant": [
            {"tenant": t, "count": c} for t, c in by_tenant.fetchall()
        ],
        "by_country": [
            {"code": code, "country": name, "count": c}
            for code, name, c in by_country.fetchall()
        ],
    }


async def get_geo_heatmap_data(
    db: Session, days: int = 30
) -> list[dict[str, Any]]:
    """Datos para mapa de calor geográfico."""
    from sqlalchemy import func
    cutoff = datetime.utcnow() - timedelta(days=days)
    result = db.execute(
        select(
            SessionGeoEvent.geo_country_code,
            SessionGeoEvent.geo_country,
            SessionGeoEvent.geo_city,
            SessionGeoEvent.geo_lat,
            SessionGeoEvent.geo_lon,
            func.count(SessionGeoEvent.id).label("count"),
        )
        .where(
            and_(
                SessionGeoEvent.event_at >= cutoff,
                SessionGeoEvent.geo_lat.isnot(None),
            )
        )
        .group_by(
            SessionGeoEvent.geo_country_code,
            SessionGeoEvent.geo_country,
            SessionGeoEvent.geo_city,
            SessionGeoEvent.geo_lat,
            SessionGeoEvent.geo_lon,
        )
        .order_by(func.count(SessionGeoEvent.id).desc())
        .limit(500)
    )
    return [
        {
            "country_code": cc, "country": cn, "city": city,
            "lat": lat, "lon": lon, "count": cnt,
        }
        for cc, cn, city, lat, lon, cnt in result.fetchall()
    ]
