"""
Routes package - API endpoints organizados por módulo

Routers disponibles:
- auth: Autenticación legacy (JWT básico)
- secure_auth: Autenticación segura (rate limiting, 2FA, refresh tokens)
- roles: Login unificado por roles
- dashboard: Panel de administración
- tenants: Gestión de tenants
- onboarding: Flujo de registro y checkout
- tenant_portal: Portal del cliente
- nodes: Multi-Proxmox management
- tunnels: Cloudflare Tunnel management
- provisioning: Auto-provisioning de tenants Odoo
- settings: Configuración administrable desde /admin
"""
