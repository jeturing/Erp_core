#!/bin/bash
#===============================================================================
# Script: domain_sync.sh
# Descripción: Sincroniza dominios personalizados desde BD y configura Cloudflare
# Ubicación: PCT 105 (10.10.10.100) - /opt/scripts/domain_sync.sh
# Ejecución: Cron cada 2 minutos o llamado desde webhook ERP Core
#===============================================================================

set -euo pipefail

# === CONFIGURACIÓN ===
DB_HOST="10.10.10.20"
DB_PORT="5432"
DB_NAME="erp_core_db"
DB_USER="jeturing"
DB_PASS="321Abcd"

CF_API_TOKEN="${CF_API_TOKEN:-$(cat /root/.cf_credentials 2>/dev/null || echo '')}"
CF_ZONE_ID="4a83b88793ac3688486ace69b6ae80f9"  # sajet.us
CF_TUNNEL_NAME="tcs-sajet-tunnel"

CLOUDFLARED_CONFIG="/etc/cloudflared/config.yml"
LOG_FILE="/var/log/domain_sync.log"

# === FUNCIONES DE UTILIDAD ===

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_dependencies() {
    local deps=("psql" "cloudflared" "jq" "curl")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log "ERROR: $dep no está instalado"
            exit 1
        fi
    done
}

# === FUNCIONES DE BASE DE DATOS ===

get_pending_domains() {
    # Obtener dominios que necesitan configuración en Cloudflare
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -F'|' -c "
        SELECT 
            id,
            sajet_subdomain,
            external_domain,
            tenant_deployment_id
        FROM custom_domains 
        WHERE cloudflare_configured = false 
        AND verification_status = 'pending'
        ORDER BY created_at ASC
        LIMIT 10
    " 2>/dev/null || echo ""
}

get_verified_domains_for_tunnel() {
    # Obtener dominios verificados que necesitan configuración de tunnel ingress
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -A -F'|' -c "
        SELECT 
            cd.id,
            cd.sajet_subdomain,
            cd.external_domain,
            td.direct_url
        FROM custom_domains cd
        LEFT JOIN tenant_deployments td ON cd.tenant_deployment_id = td.id
        WHERE cd.cloudflare_configured = true 
        AND cd.tunnel_ingress_configured = false
        AND cd.verification_status IN ('pending', 'verified')
        ORDER BY cd.created_at ASC
    " 2>/dev/null || echo ""
}

update_domain_status() {
    local domain_id=$1
    local cf_configured=$2
    local tunnel_configured=$3
    local cf_record_id=$4
    
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        UPDATE custom_domains 
        SET 
            cloudflare_configured = $cf_configured,
            tunnel_ingress_configured = $tunnel_configured,
            cloudflare_dns_record_id = '$cf_record_id',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $domain_id
    " &>/dev/null
}

activate_domain() {
    local domain_id=$1
    
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
        UPDATE custom_domains 
        SET 
            is_active = true,
            verification_status = 'verified',
            verified_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = $domain_id
    " &>/dev/null
}

# === FUNCIONES DE CLOUDFLARE ===

create_dns_record() {
    local subdomain=$1
    local full_domain="${subdomain}.sajet.us"
    
    log "Creando DNS record: $full_domain"
    
    local response=$(curl -s -X POST \
        "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json" \
        --data "{
            \"type\": \"CNAME\",
            \"name\": \"${subdomain}\",
            \"content\": \"${CF_TUNNEL_NAME}.cfargotunnel.com\",
            \"proxied\": true,
            \"ttl\": 1
        }")
    
    local success=$(echo "$response" | jq -r '.success')
    
    if [ "$success" = "true" ]; then
        local record_id=$(echo "$response" | jq -r '.result.id')
        log "✅ DNS record creado: $record_id"
        echo "$record_id"
    else
        local error=$(echo "$response" | jq -r '.errors[0].message // "Unknown error"')
        log "❌ Error creando DNS: $error"
        echo ""
    fi
}

check_dns_record_exists() {
    local subdomain=$1
    
    local response=$(curl -s -X GET \
        "https://api.cloudflare.com/client/v4/zones/${CF_ZONE_ID}/dns_records?name=${subdomain}.sajet.us" \
        -H "Authorization: Bearer ${CF_API_TOKEN}" \
        -H "Content-Type: application/json")
    
    local count=$(echo "$response" | jq -r '.result | length')
    
    if [ "$count" -gt 0 ]; then
        echo $(echo "$response" | jq -r '.result[0].id')
    else
        echo ""
    fi
}

# === FUNCIONES DE CLOUDFLARED TUNNEL ===

add_ingress_rule() {
    local subdomain=$1
    local backend_url=$2
    local full_domain="${subdomain}.sajet.us"
    
    log "Agregando ingress rule: $full_domain → $backend_url"
    
    # Verificar si ya existe la regla
    if grep -q "hostname: ${full_domain}" "$CLOUDFLARED_CONFIG" 2>/dev/null; then
        log "⚠️ Ingress rule ya existe para $full_domain"
        return 0
    fi
    
    # Backup del config actual
    cp "$CLOUDFLARED_CONFIG" "${CLOUDFLARED_CONFIG}.bak.$(date +%s)"
    
    # Leer config actual y agregar nueva regla antes del catch-all
    local temp_config=$(mktemp)
    
    # Usar Python para manipular YAML de forma segura
    python3 << PYTHON_EOF
import yaml

with open('$CLOUDFLARED_CONFIG', 'r') as f:
    config = yaml.safe_load(f)

# Nueva regla de ingress
new_rule = {
    'hostname': '${full_domain}',
    'service': 'http://${backend_url}'
}

# Insertar antes del catch-all (último elemento)
if 'ingress' in config:
    # Buscar si ya existe
    exists = any(r.get('hostname') == '${full_domain}' for r in config['ingress'])
    if not exists:
        # Insertar antes del último (catch-all)
        config['ingress'].insert(-1, new_rule)

with open('$temp_config', 'w') as f:
    yaml.dump(config, f, default_flow_style=False)
    
print("OK")
PYTHON_EOF

    if [ -f "$temp_config" ] && [ -s "$temp_config" ]; then
        # Validar config
        if cloudflared tunnel ingress validate --config "$temp_config" &>/dev/null; then
            mv "$temp_config" "$CLOUDFLARED_CONFIG"
            log "✅ Ingress rule agregada"
            return 0
        else
            log "❌ Config inválida, restaurando backup"
            rm -f "$temp_config"
            return 1
        fi
    else
        log "❌ Error generando config"
        return 1
    fi
}

reload_cloudflared() {
    log "Recargando cloudflared..."
    
    # Validar configuración primero
    if cloudflared tunnel ingress validate &>/dev/null; then
        systemctl restart cloudflared
        sleep 3
        
        if systemctl is-active --quiet cloudflared; then
            log "✅ cloudflared reiniciado correctamente"
            return 0
        else
            log "❌ cloudflared no inició correctamente"
            return 1
        fi
    else
        log "❌ Configuración inválida, no se reinicia"
        return 1
    fi
}

# === FUNCIÓN PRINCIPAL ===

process_pending_domains() {
    log "=== Procesando dominios pendientes de DNS ==="
    
    local domains=$(get_pending_domains)
    
    if [ -z "$domains" ]; then
        log "No hay dominios pendientes de DNS"
        return 0
    fi
    
    local count=0
    while IFS='|' read -r id subdomain external_domain tenant_id; do
        [ -z "$id" ] && continue
        
        log "Procesando: $subdomain ($external_domain)"
        
        # Verificar si ya existe el DNS record
        local existing_record=$(check_dns_record_exists "$subdomain")
        
        if [ -n "$existing_record" ]; then
            log "DNS record ya existe: $existing_record"
            update_domain_status "$id" "true" "false" "$existing_record"
        else
            # Crear nuevo DNS record
            local record_id=$(create_dns_record "$subdomain")
            
            if [ -n "$record_id" ]; then
                update_domain_status "$id" "true" "false" "$record_id"
                ((count++))
            fi
        fi
        
    done <<< "$domains"
    
    log "DNS records procesados: $count"
}

process_tunnel_ingress() {
    log "=== Procesando dominios para tunnel ingress ==="
    
    local domains=$(get_verified_domains_for_tunnel)
    
    if [ -z "$domains" ]; then
        log "No hay dominios pendientes de tunnel ingress"
        return 0
    fi
    
    local count=0
    local needs_reload=false
    
    while IFS='|' read -r id subdomain external_domain backend_url; do
        [ -z "$id" ] && continue
        
        # Si no hay backend URL, usar el default
        if [ -z "$backend_url" ]; then
            backend_url="localhost:8069"
        fi
        
        log "Configurando tunnel: $subdomain → $backend_url"
        
        if add_ingress_rule "$subdomain" "$backend_url"; then
            update_domain_status "$id" "true" "true" ""
            activate_domain "$id"
            needs_reload=true
            ((count++))
        fi
        
    done <<< "$domains"
    
    # Recargar cloudflared si hubo cambios
    if [ "$needs_reload" = true ]; then
        reload_cloudflared
    fi
    
    log "Ingress rules configuradas: $count"
}

# === EJECUCIÓN ===

main() {
    log "=========================================="
    log "Iniciando sincronización de dominios"
    log "=========================================="
    
    check_dependencies
    
    # Paso 1: Crear DNS records en Cloudflare
    process_pending_domains
    
    # Paso 2: Configurar tunnel ingress
    process_tunnel_ingress
    
    log "=========================================="
    log "Sincronización completada"
    log "=========================================="
}

# Ejecutar si no es sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
