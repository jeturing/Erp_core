"""
Security Middleware - HTTPS enforcement, Rate Limiting, WAF
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import time
import re
import os
import logging
import hashlib

logger = logging.getLogger(__name__)

# Environment config
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FORCE_HTTPS = os.getenv("FORCE_HTTPS", "false").lower() == "true"


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware principal de seguridad:
    - Fuerza HTTPS en producción
    - Agrega headers de seguridad
    """
    
    def __init__(self, app, force_https: bool = None):
        super().__init__(app)
        self.force_https = force_https if force_https is not None else FORCE_HTTPS
    
    async def dispatch(self, request: Request, call_next):
        # Forzar HTTPS en producción
        if self.force_https and request.url.scheme == "http":
            # Permitir health checks sin HTTPS
            if request.url.path not in ["/health", "/health/"]:
                https_url = str(request.url).replace("http://", "https://", 1)
                return RedirectResponse(url=https_url, status_code=301)
        
        response = await call_next(request)
        
        # Headers de seguridad
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS solo en producción con HTTPS
        if self.force_https:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # CSP - Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://js.stripe.com https://static.cloudflareinsights.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net https://r2cdn.perplexity.ai data:; "
            "img-src 'self' data: https:; "
            "frame-src https://js.stripe.com; "
            "connect-src 'self' https://api.stripe.com https://cloudflareinsights.com"
        )
        
        return response


class RateLimiter:
    """
    Rate limiter para endpoints sensibles como login.
    Almacena intentos en memoria (usar Redis en producción para escalabilidad).
    """
    
    def __init__(
        self,
        max_requests: int = 5,
        window_seconds: int = 300,  # 5 minutos
        block_duration_seconds: int = 900  # 15 minutos de bloqueo
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.block_duration_seconds = block_duration_seconds
        self.attempts = defaultdict(list)  # ip -> lista de timestamps
        self.blocked = {}  # ip -> timestamp de desbloqueo
    
    def _get_client_id(self, request: Request) -> str:
        """Obtiene identificador único del cliente (IP o hash)."""
        # Obtener IP real considerando proxies
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        # Hash para privacidad en logs
        return hashlib.sha256(ip.encode()).hexdigest()[:16]
    
    def _cleanup_old_attempts(self, client_id: str):
        """Limpia intentos antiguos fuera de la ventana."""
        cutoff = time.time() - self.window_seconds
        self.attempts[client_id] = [
            ts for ts in self.attempts[client_id] if ts > cutoff
        ]
    
    def is_blocked(self, request: Request) -> bool:
        """Verifica si el cliente está bloqueado."""
        client_id = self._get_client_id(request)
        
        if client_id in self.blocked:
            if time.time() < self.blocked[client_id]:
                return True
            else:
                # Desbloquear
                del self.blocked[client_id]
                self.attempts[client_id] = []
        
        return False
    
    def check_rate_limit(self, request: Request) -> tuple[bool, dict]:
        """
        Verifica rate limit. Retorna (allowed, info).
        info contiene remaining_attempts y retry_after si está bloqueado.
        """
        client_id = self._get_client_id(request)
        
        # Verificar bloqueo
        if client_id in self.blocked:
            if time.time() < self.blocked[client_id]:
                retry_after = int(self.blocked[client_id] - time.time())
                return False, {
                    "blocked": True,
                    "retry_after": retry_after,
                    "message": f"Demasiados intentos. Reintente en {retry_after // 60} minutos."
                }
            else:
                del self.blocked[client_id]
                self.attempts[client_id] = []
        
        # Limpiar intentos antiguos
        self._cleanup_old_attempts(client_id)
        
        # Registrar nuevo intento
        self.attempts[client_id].append(time.time())
        
        current_attempts = len(self.attempts[client_id])
        remaining = max(0, self.max_requests - current_attempts)
        
        # Verificar si excede límite
        if current_attempts > self.max_requests:
            # Bloquear cliente
            self.blocked[client_id] = time.time() + self.block_duration_seconds
            logger.warning(f"Rate limit exceeded for client {client_id}. Blocked for {self.block_duration_seconds}s")
            return False, {
                "blocked": True,
                "retry_after": self.block_duration_seconds,
                "message": f"Demasiados intentos. Cuenta bloqueada por {self.block_duration_seconds // 60} minutos."
            }
        
        return True, {
            "blocked": False,
            "remaining_attempts": remaining,
            "window_seconds": self.window_seconds
        }
    
    def reset(self, request: Request):
        """Resetea el contador para un cliente (llamar después de login exitoso)."""
        client_id = self._get_client_id(request)
        self.attempts[client_id] = []
        if client_id in self.blocked:
            del self.blocked[client_id]


class WAFMiddleware(BaseHTTPMiddleware):
    """
    Web Application Firewall básico.
    Detecta y bloquea patrones de ataque comunes.
    """
    
    # Patrones sospechosos
    SQL_INJECTION_PATTERNS = [
        r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
        r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))",
        r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))",
        r"((\%27)|(\'))union",
        r"exec(\s|\+)+(s|x)p\w+",
        r"UNION(\s+)SELECT",
        r"SELECT.*FROM",
        r"INSERT(\s+)INTO",
        r"DELETE(\s+)FROM",
        r"DROP(\s+)TABLE",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
        r"<link[^>]*href",
        r"expression\s*\(",
        r"vbscript:",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"%2e%2e%2f",
        r"%2e%2e/",
        r"\.%2e/",
        r"%2e\./",
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r";\s*cat\s+",
        r";\s*ls\s+",
        r"\|\s*cat\s+",
        r"\$\(",
        r"`.*`",
        r";\s*wget\s+",
        r";\s*curl\s+",
        r";\s*rm\s+",
    ]
    
    def __init__(self, app, enabled: bool = True):
        super().__init__(app)
        self.enabled = enabled
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> dict:
        """Compila patrones regex para mejor rendimiento."""
        return {
            "sql_injection": [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS],
            "xss": [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS],
            "path_traversal": [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS],
            "command_injection": [re.compile(p, re.IGNORECASE) for p in self.COMMAND_INJECTION_PATTERNS],
        }
    
    def _check_patterns(self, value: str, patterns: list) -> tuple[bool, str]:
        """Verifica si un valor coincide con patrones maliciosos."""
        for pattern in patterns:
            if pattern.search(value):
                return True, pattern.pattern
        return False, ""
    
    def _scan_value(self, value: str) -> tuple[bool, str, str]:
        """Escanea un valor por todos los tipos de ataques."""
        for attack_type, patterns in self.compiled_patterns.items():
            is_malicious, matched_pattern = self._check_patterns(value, patterns)
            if is_malicious:
                return True, attack_type, matched_pattern
        return False, "", ""
    
    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)
        
        # Verificar URL path
        is_malicious, attack_type, pattern = self._scan_value(str(request.url.path))
        if is_malicious:
            logger.warning(f"WAF blocked {attack_type} in path: {request.url.path}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Solicitud bloqueada por razones de seguridad"}
            )
        
        # Verificar query parameters
        for key, value in request.query_params.items():
            is_malicious, attack_type, pattern = self._scan_value(f"{key}={value}")
            if is_malicious:
                logger.warning(f"WAF blocked {attack_type} in query param: {key}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Solicitud bloqueada por razones de seguridad"}
                )
        
        # Verificar headers sospechosos
        suspicious_headers = ["User-Agent", "Referer", "Cookie"]
        for header in suspicious_headers:
            value = request.headers.get(header, "")
            if value:
                is_malicious, attack_type, pattern = self._scan_value(value)
                if is_malicious:
                    logger.warning(f"WAF blocked {attack_type} in header {header}")
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Solicitud bloqueada por razones de seguridad"}
                    )
        
        return await call_next(request)
