"""
Dynamic CORS Middleware — origins from DB (custom_domains + tenant_deployments).

Caches allowed origins in-memory with TTL. Zero-latency on requests after first load.
Fallback to a static base set (localhost, sajet.us) if DB is unreachable.
"""
import time
import logging
import re
from typing import Set, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

# Base origins that are ALWAYS allowed (no DB needed)
_STATIC_ORIGINS: Set[str] = {
    "http://localhost:4443",
    "http://localhost:5173",
    "https://sajet.us",
    "https://www.sajet.us",
}

# Regex for *.sajet.us subdomains + devtunnels
_ALWAYS_REGEX = re.compile(
    r"^https://[a-z0-9-]+\.sajet\.us$"
    r"|^https://[a-z0-9-]+\.use\.devtunnels\.ms$"
)

# Cache
_cached_origins: Set[str] = set()
_cache_ts: float = 0.0
_CACHE_TTL: float = 60.0  # seconds


def _load_origins_from_db() -> Set[str]:
    """Load verified domains from DB. Returns set of full origin URLs."""
    origins: Set[str] = set()
    try:
        from app.models.database import CustomDomain, TenantDeployment, SessionLocal
        from app.models.database import DomainVerificationStatus

        db = SessionLocal()
        try:
            # Custom domains: external_domain where verified + active
            domains = db.query(CustomDomain).filter(
                CustomDomain.verification_status == DomainVerificationStatus.verified,
                CustomDomain.is_active == True,
            ).all()

            for d in domains:
                ext = d.external_domain.lower().strip()
                if not ext.startswith("http"):
                    origins.add(f"https://{ext}")
                    # Also add www variant if not present
                    if not ext.startswith("www."):
                        origins.add(f"https://www.{ext}")
                else:
                    origins.add(ext)

                # sajet subdomain
                if d.sajet_subdomain:
                    origins.add(f"https://{d.sajet_subdomain}.sajet.us")

            # Tenant deployments: subdomain
            deployments = db.query(TenantDeployment).all()
            for td in deployments:
                if td.subdomain:
                    origins.add(f"https://{td.subdomain}.sajet.us")

        finally:
            db.close()

    except Exception as e:
        logger.warning(f"CORS: failed to load origins from DB: {e}")

    return origins


def get_allowed_origins() -> Set[str]:
    """Get full set of allowed origins with caching."""
    global _cached_origins, _cache_ts

    now = time.time()
    if now - _cache_ts > _CACHE_TTL:
        db_origins = _load_origins_from_db()
        _cached_origins = _STATIC_ORIGINS | db_origins
        _cache_ts = now
        logger.info(f"CORS cache refreshed: {len(_cached_origins)} origins")

    return _cached_origins


def refresh_cors_cache():
    """Force cache refresh (called from admin endpoint)."""
    global _cache_ts
    _cache_ts = 0.0
    get_allowed_origins()


def is_origin_allowed(origin: str) -> bool:
    """Check if an origin is allowed — O(1) set lookup + regex fallback."""
    if not origin:
        return True  # Same-origin or server-to-server

    allowed = get_allowed_origins()
    if origin in allowed:
        return True

    # Regex fallback for *.sajet.us and devtunnels
    if _ALWAYS_REGEX.match(origin):
        return True

    return False


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    """
    Replaces FastAPI's static CORSMiddleware with dynamic origin validation.
    Origins are loaded from custom_domains + tenant_deployments tables.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        origin = request.headers.get("origin", "")

        # Preflight (OPTIONS)
        if request.method == "OPTIONS":
            if is_origin_allowed(origin):
                response = Response(status_code=204)
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
                response.headers["Access-Control-Max-Age"] = "600"
                return response
            else:
                return Response(status_code=403, content="CORS: origin not allowed")

        # Normal request
        response = await call_next(request)

        if origin and is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Vary"] = "Origin"

        return response
