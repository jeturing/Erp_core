"""
Tenant Credentials — Módulo compartido para generar credenciales bootstrap de tenants.

Usado por:
  - app/routes/tenants.py (panel admin)
  - app/routes/onboarding.py (webhook Stripe / provisioning automático)

Las credenciales bootstrap siguen la política SAJET:
  - Login: <subdomain>@sajet.us
  - Password: aleatoria robusta de 20 caracteres
"""
import secrets
import string
from typing import Tuple


def generate_bootstrap_password(length: int = 20) -> str:
    """Genera una contraseña robusta (sin comillas simples para evitar problemas SQL legacy)."""
    alphabet = string.ascii_letters + string.digits + "@#$%!-_"
    return "".join(secrets.choice(alphabet) for _ in range(max(12, length)))


def build_tenant_admin_credentials(
    subdomain: str,
    base_domain: str = "sajet.us",
) -> Tuple[str, str]:
    """
    Credenciales bootstrap del admin del tenant.

    Returns:
        (login, password) — ej: ("acme@sajet.us", "xK9!m@Rz...")
    """
    login = f"{subdomain}@{base_domain}"
    password = generate_bootstrap_password()
    return login, password
