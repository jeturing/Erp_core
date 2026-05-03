"""
DSAM — Session Monitor Service
Escanea Redis (PCT 149) para capturar sesiones activas de Odoo,
geolocaliza IPs y sincroniza snapshots a la BD de ERP Core.
"""
import json
import logging
import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select, delete, and_
from sqlalchemy.orm import Session

try:
    import redis.asyncio as aioredis
except ModuleNotFoundError:  # pragma: no cover - depende del entorno local
    aioredis = None

from ..config import (
    REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_DB,
    GEOIP_DB_PATH, DSAM_POLL_INTERVAL_SECONDS, DSAM_REDIS_SESSION_SOURCES,
)
from ..models.database import (
    ActiveSession, SessionGeoEvent, TenantSessionConfig,
)

logger = logging.getLogger(__name__)

_PLACEHOLDER_IPS = {"0.0.0.0", "127.0.0.1", "::1", "localhost", "unknown"}


@dataclass(frozen=True)
class RedisSessionSource:
    """Origen Redis de sesiones Odoo para DSAM."""
    redis_db: int
    match_pattern: str
    app_name: str

# ── GeoIP2 lazy loader ──
_geoip_reader = None
_geoip_unavailable = False


def _get_geoip_reader():
    """Carga GeoIP2 bajo demanda. Si no existe el archivo MMDB, retorna None."""
    global _geoip_reader, _geoip_unavailable
    if _geoip_unavailable:
        return None
    if _geoip_reader is not None:
        return _geoip_reader
    try:
        import geoip2.database
        _geoip_reader = geoip2.database.Reader(GEOIP_DB_PATH)
        logger.info("GeoIP2 database loaded: %s", GEOIP_DB_PATH)
    except Exception as e:
        logger.warning("GeoIP2 not available (%s), geolocation disabled", e)
        _geoip_unavailable = True
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


def _parse_epoch_or_iso(value: Any) -> Optional[datetime]:
    """Convierte timestamps epoch/ISO a datetime UTC."""
    if value in (None, "", 0):
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        try:
            return datetime.utcfromtimestamp(value)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            try:
                return datetime.utcfromtimestamp(float(value))
            except (OverflowError, OSError, ValueError):
                return None
    return None


def _is_authenticated_session(data: dict[str, Any]) -> bool:
    """Filtra sesiones anónimas irrelevantes para DSAM."""
    return bool(data.get("uid") or data.get("login") or data.get("session_token"))


def _is_placeholder_ip(ip: Optional[str]) -> bool:
    """Detecta IPs vacías o internas que no sirven para visualización externa."""
    normalized = (ip or "").strip().lower()
    return not normalized or normalized in _PLACEHOLDER_IPS


def _extract_ip_from_trace(trace_data: Any) -> Optional[str]:
    """Busca una IP usable dentro del _trace de Odoo 19."""
    if not isinstance(trace_data, list):
        return None

    fallback: Optional[str] = None
    for item in trace_data:
        if not isinstance(item, dict):
            continue
        candidate = (item.get("ip_address") or item.get("ip") or "").strip()
        if not candidate:
            continue
        if fallback is None:
            fallback = candidate
        if not _is_placeholder_ip(candidate):
            return candidate
    return fallback


def _extract_ip_address(data: dict[str, Any]) -> str:
    """Extrae la mejor IP disponible desde distintas variantes del payload."""
    direct_candidates = [
        data.get("ip"),
        data.get("remote_addr"),
        data.get("ip_address"),
        data.get("client_ip"),
        data.get("forwarded_for"),
        data.get("x_forwarded_for"),
    ]
    for candidate in direct_candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.split(",")[0].strip()

    trace_ip = _extract_ip_from_trace(data.get("_trace"))
    if trace_ip:
        return trace_ip

    return "0.0.0.0"


def _extract_user_agent(data: dict[str, Any]) -> str:
    """Extrae un user agent o fallback descriptivo si existe."""
    if isinstance(data.get("user_agent"), str) and data.get("user_agent", "").strip():
        return data["user_agent"]

    trace_data = data.get("_trace")
    if isinstance(trace_data, list) and trace_data:
        first = trace_data[0]
        if isinstance(first, dict):
            browser = first.get("browser")
            platform = first.get("platform")
            if browser or platform:
                return " / ".join(part for part in [browser, platform] if part)

    return ""


def _get_session_sources() -> list[RedisSessionSource]:
    """Parses DSAM Redis session sources from env/config."""
    sources: list[RedisSessionSource] = []
    raw = (DSAM_REDIS_SESSION_SOURCES or "").strip()
    if raw:
        for chunk in raw.split(","):
            parts = [part.strip() for part in chunk.split("|")]
            if len(parts) < 2:
                continue
            try:
                redis_db = int(parts[0])
            except ValueError:
                logger.warning("Invalid DSAM Redis source db: %s", parts[0])
                continue
            pattern = parts[1] or "session:*"
            app_name = parts[2] if len(parts) >= 3 and parts[2] else f"redis-db-{redis_db}"
            sources.append(RedisSessionSource(redis_db=redis_db, match_pattern=pattern, app_name=app_name))

    if not sources:
        sources.append(RedisSessionSource(redis_db=REDIS_DB, match_pattern="session:*", app_name="legacy"))
    return sources


# ═══════════════════════════════════════════════════════
# Redis Session Scanner
# ═══════════════════════════════════════════════════════

async def get_redis_pool(redis_db: Optional[int] = None) -> Any:
    """Crea pool async de Redis."""
    if aioredis is None:
        raise RuntimeError("redis package is not installed")

    return aioredis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        db=REDIS_DB if redis_db is None else redis_db,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5,
    )


async def scan_redis_sessions() -> list[dict[str, Any]]:
    """
    Escanea todas las claves configuradas de sesiones Odoo en Redis.
    Retorna lista de dicts con la data de cada sesión.
    Soporta múltiples DB/prefix por versión de Odoo.
    """
    sessions = []
    for source in _get_session_sources():
        try:
            r = await get_redis_pool(source.redis_db)
        except Exception as e:
            logger.error("Cannot connect to Redis source db=%s (%s): %s", source.redis_db, source.app_name, e)
            continue

        cursor = "0"
        source_count = 0
        try:
            while True:
                cursor, keys = await r.scan(cursor=cursor, match=source.match_pattern, count=200)
                for key in keys:
                    try:
                        raw = await r.get(key)
                        if not raw:
                            continue
                        data = json.loads(raw) if isinstance(raw, str) else raw
                        if not isinstance(data, dict) or not _is_authenticated_session(data):
                            continue
                        tenant_db = data.get("db") or "unknown"
                        session_id = key.rsplit(":", 1)[-1]
                        sessions.append({
                            "redis_key": key,
                            "tenant_db": tenant_db,
                            "session_id": session_id,
                            "source_db": source.redis_db,
                            "source_app": source.app_name,
                            "source_pattern": source.match_pattern,
                            "data": data,
                        })
                        source_count += 1
                    except Exception as e:
                        logger.debug("Error parsing session key %s from %s: %s", key, source.app_name, e)
                if cursor == 0 or cursor == "0":
                    break
            logger.info(
                "DSAM scanned Redis source db=%s app=%s pattern=%s sessions=%s",
                source.redis_db,
                source.app_name,
                source.match_pattern,
                source_count,
            )
        finally:
            await r.aclose()

    return sessions


def parse_session_data(session: dict) -> dict[str, Any]:
    """Extrae campos relevantes del payload de sesión Odoo en Redis."""
    data = session.get("data", {})
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}

    ip_address = _extract_ip_address(data)
    session_start = (
        _parse_epoch_or_iso(data.get("created_at"))
        or _parse_epoch_or_iso(data.get("create_time"))
    )
    last_activity = _parse_epoch_or_iso(data.get("last_activity")) or session_start

    return {
        "redis_session_key": session["redis_key"],
        "tenant_db": data.get("db") or session.get("tenant_db", "unknown"),
        "odoo_uid": data.get("uid"),
        "odoo_login": data.get("login"),
        "ip_address": ip_address,
        "user_agent": _extract_user_agent(data),
        "session_start": session_start,
        "last_activity": last_activity,
    }
async def sync_sessions_to_db(db: Session) -> dict[str, int]:
    """
    Escanea Redis → geolocaliza → upsert en active_sessions.
    Marca como inactivas las sesiones que ya no están en Redis.
    Registra eventos geo en session_geo_events.
    Retorna stats: {scanned, created, updated, removed}.
    """
    stats = {"scanned": 0, "created": 0, "updated": 0, "removed": 0}
    try:
        raw_sessions = await scan_redis_sessions()
        stats["scanned"] = len(raw_sessions)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
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
                existing.odoo_uid = parsed.get("odoo_uid")
                existing.odoo_login = parsed.get("odoo_login")
                if parsed.get("user_agent"):
                    existing.user_agent = parsed.get("user_agent")

                should_refresh_ip = not _is_placeholder_ip(parsed["ip_address"])
                should_backfill_geo = (
                    not _is_placeholder_ip(existing.ip_address)
                    and existing.geo_lat is None
                    and geo["lat"] is not None
                )

                # Actualizar geo si cambió la IP real o si faltaba geo previamente
                if should_refresh_ip and existing.ip_address != parsed["ip_address"]:
                    existing.ip_address = parsed["ip_address"]
                    existing.geo_country = geo["country"]
                    existing.geo_country_code = geo["country_code"]
                    existing.geo_region = geo["region"]
                    existing.geo_city = geo["city"]
                    existing.geo_lat = geo["lat"]
                    existing.geo_lon = geo["lon"]
                elif should_backfill_geo:
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
    cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
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
