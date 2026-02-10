#!/bin/bash
# =============================================================================
# CONFIGURACIÓN DE CLOUDFLARE PARA PROVISIONING AUTOMÁTICO
# =============================================================================
# 
# Este archivo contiene las credenciales necesarias para crear subdominios
# automáticamente en Cloudflare cuando se provisiona un nuevo tenant.
#
# INSTRUCCIONES:
# 1. Obten un API Token en: https://dash.cloudflare.com/profile/api-tokens
#    - Permisos requeridos: Zone:DNS:Edit para sajet.us
# 2. Obten el Zone ID en: Dashboard de Cloudflare > sajet.us > Overview (lado derecho)
# 3. Completa las variables abajo
# 4. Ejecuta: source /opt/odoo/scripts/cloudflare_config.sh
#
# =============================================================================

# API Token de Cloudflare (NO uses la Global API Key, usa un Token específico)
export CF_API_TOKEN=""

# Zone ID de sajet.us (lo encuentras en el dashboard de Cloudflare)
export CF_ZONE_ID=""

# Tunnel ID (ya configurado)
export CF_TUNNEL_ID="da2bc763-a93b-41f5-9a22-1731403127e3"

# Dominio base
export DOMAIN="sajet.us"

# Master password de Odoo (para crear/eliminar BDs)
export ODOO_MASTER_PASSWORD="admin"

# URL de Odoo
export ODOO_URL="http://localhost:8069"

# =============================================================================
# NO MODIFIQUES DEBAJO DE ESTA LÍNEA
# =============================================================================

if [[ -z "$CF_API_TOKEN" ]] || [[ -z "$CF_ZONE_ID" ]]; then
    echo "⚠ ADVERTENCIA: CF_API_TOKEN o CF_ZONE_ID no están configurados"
    echo "  Los subdominios NO se crearán automáticamente en Cloudflare"
    echo "  Edita: /opt/odoo/scripts/cloudflare_config.sh"
fi
