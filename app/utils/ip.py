"""
Utilidad centralizada para extraer la IP pública real del cliente.

Orden de precedencia (mayor confianza primero):
  1. CF-Connecting-IP   — Cloudflare pone la IP del cliente aquí (no falsificable desde fuera)
  2. X-Real-IP          — Nginx/HAProxy forwarded
  3. X-Forwarded-For    — Proxy chain, usar SOLO el primer valor (más a la izquierda)
  4. request.client.host — Conexión directa (funciona solo sin proxy)
"""
from fastapi import Request


def get_real_ip(request: Request) -> str:
    """
    Extrae la IP pública real del cliente respetando Cloudflare y proxies.
    Nunca devuelve None — retorna 'unknown' si no hay información.
    """
    for header in ("cf-connecting-ip", "x-real-ip", "x-forwarded-for"):
        val = request.headers.get(header, "").strip()
        if val:
            # X-Forwarded-For puede ser una lista: "client, proxy1, proxy2"
            ip = val.split(",")[0].strip()
            if ip:
                return ip
    return request.client.host if request.client else "unknown"
