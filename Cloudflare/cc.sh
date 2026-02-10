
#!/bin/bash

# Manejo de errores
set -e
trap 'echo "❌ Error en la ejecución del script. Revisa los registros." && exit 1' ERR

# Variables globales
CLOUDFLARE_API="https://api.cloudflare.com/client/v4"
CERT_PATH="/root/.cloudflared/cert.pem"
DOMAINS_FILE="/root/Cloudflare/dominios.json"
CREDENTIALS_FILE="/root/Cloudflare/.cf_credentials"

# Cargar credenciales de Cloudflare si existen (evitar tokens hardcodeados)
if [ -f "$CREDENTIALS_FILE" ]; then
    # shellcheck disable=SC1090
    source "$CREDENTIALS_FILE"
fi
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "⚠️ CLOUDFLARE_API_TOKEN no está definido. Algunas validaciones de API se omitirán."
fi

# Determinar si hay sudo disponible
if command -v sudo &>/dev/null; then
    SUDO=sudo
else
    SUDO=""
fi

# Instalar dependencias si no están instaladas
install_dependencies() {
    for cmd in cloudflared jq curl nc lsb_release; do
        if ! command -v $cmd &>/dev/null; then
            echo "❌ $cmd no está instalado. Instalando..."
            if [[ "$cmd" == "cloudflared" ]]; then
                # Instalar cloudflared desde el repo oficial para actualizaciones automáticas
                $SUDO mkdir -p --mode=0755 /usr/share/keyrings
                curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | $SUDO tee /usr/share/keyrings/cloudflare-main.gpg > /dev/null
                export CLOUDFLARE_CODENAME=$(lsb_release -cs || echo "jammy")
                echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared ${CLOUDFLARE_CODENAME} main" | $SUDO tee /etc/apt/sources.list.d/cloudflared.list > /dev/null
                if [ -n "$SUDO" ]; then
                    sudo apt-get update && sudo apt-get install -y cloudflared
                else
                    apt-get update && apt-get install -y cloudflared
                fi
            else
                if [ -n "$SUDO" ]; then
                    sudo apt-get install -y $cmd
                else
                    apt-get update -y || true
                    apt-get install -y $cmd
                fi
            fi
        else
            echo "✅ $cmd ya está instalado."
        fi
    done
}

# Verificar y actualizar cloudflared si es necesario
get_installed_cloudflared_version() {
    cloudflared --version 2>/dev/null | head -n1 | awk '{print $3}'
}

# Instalar dependencias
install_dependencies

INSTALLED_VERSION=$(get_installed_cloudflared_version)
echo "✅ cloudflared versión instalada: ${INSTALLED_VERSION}"

# Selección de dominio desde dominios.json o ENTER para usar el 4to (sajet.us)
if [ ! -f "$DOMAINS_FILE" ]; then
        echo "❌ No se encontró $DOMAINS_FILE. Crea el archivo basado en el adjunto dominios.json."
        exit 1
fi

echo "🔹 Seleccione un dominio:" 
mapfile -t DOMAIN_LIST < <(jq -r '.[].name' "$DOMAINS_FILE")
for i in "${!DOMAIN_LIST[@]}"; do
        idx=$((i+1))
        label="${DOMAIN_LIST[$i]}"
        if [ "$idx" -eq 4 ]; then
                echo "   $idx) $label (default)"
        else
                echo "   $idx) $label"
        fi
done
read -p "Ingrese el número correspondiente o presione ENTER para usar 'sajet.us': " DOMAIN_OPTION
DOMAIN_OPTION=${DOMAIN_OPTION:-4}

DOMAIN="${DOMAIN_LIST[$((DOMAIN_OPTION-1))]}"
if [ -z "$DOMAIN" ]; then
        echo "❌ Opción no válida. Abortando."
        exit 1
fi
CLOUDFLARE_ZONE_ID=$(jq -r --arg name "$DOMAIN" '.[] | select(.name==$name) | .zone_id' "$DOMAINS_FILE")
echo "✅ Dominio seleccionado: $DOMAIN"
echo "✅ Zone ID configurado: $CLOUDFLARE_ZONE_ID"

# Verificar certificado
echo "🔐 Verificando el archivo cert.pem..."
if [ ! -f "$CERT_PATH" ]; then
    echo "⚠️ No se encontró el certificado en $CERT_PATH."
    read -p "🔹 ¿Deseas autenticar nuevamente con 'cloudflared login'? (s/n): " LOGIN_CONFIRM
    if [[ "$LOGIN_CONFIRM" == "s" ]]; then
        cloudflared login
    else
        echo "➡️ Continuando sin autenticación..."
    fi
else
    echo "✅ Certificado encontrado en $CERT_PATH."
fi

# Validar Zone ID (si hay token disponible y no se solicita saltar)
if [ -n "$CLOUDFLARE_API_TOKEN" ] && [ -z "$SKIP_CF_VALIDATION" ]; then
        echo "🔍 Validando Zone ID para ${DOMAIN}..."
        ZONE_DOMAIN=$(curl -s -X GET "${CLOUDFLARE_API}/zones/${CLOUDFLARE_ZONE_ID}" \
            -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
            -H "Content-Type: application/json" | jq -r '.result.name')

        if [[ "$ZONE_DOMAIN" != "$DOMAIN" ]]; then
                echo "❌ El Zone ID no coincide con el dominio especificado."
                exit 1
        fi
        echo "✅ Zone ID validado para ${DOMAIN}."
else
    echo "ℹ️ Omitiendo validación de Zone ID (no hay token o se solicitó saltar)."
fi

# Subdominios en lote
read -p "🔹 Ingresa los subdominios separados por espacio (o deja en blanco para usar el dominio raíz): " -a SUBDOMAINS
if [[ ${#SUBDOMAINS[@]} -eq 0 ]]; then
    SUBDOMAINS=("")
fi

# Verificar si los subdominios ya existen
check_existing_subdomain() {
    local subdomain=$1
    local full_domain="${subdomain}.${DOMAIN}"
    echo "🔍 Verificando existencia de $full_domain en Cloudflare..."
    EXISTING_RECORD=$(curl -s -X GET "${CLOUDFLARE_API}/zones/${CLOUDFLARE_ZONE_ID}/dns_records?name=${full_domain}" \
        -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
        -H "Content-Type: application/json")
    RECORD_ID=$(echo "$EXISTING_RECORD" | jq -r '.result[0].id // empty')

    if [[ -n "$RECORD_ID" ]]; then
        echo "⚠️ El subdominio $full_domain ya existe en Cloudflare. Saltando..."
        return 1
    fi
    return 0
}

# Extraer el nombre del dominio sin su extensión (.com, .us, etc.)
DOMAIN_NAME=$(echo "$DOMAIN" | sed 's/\.[^.]*$//')

ensure_tunnel() {
    local name="$1"
    if cloudflared tunnel list | awk '{print $2}' | grep -qx "$name"; then
        echo "ℹ️ Túnel $name ya existe."
        return 0
    fi
    echo "🛠️ Creando túnel $name..."
    cloudflared tunnel create "$name"
}

create_service() {
    local name="$1"
    local port="$2"
    local cfg="/etc/cloudflared/${name}.yml"
    local svc="/etc/systemd/system/cloudflared-${name}.service"

    $SUDO mkdir -p /etc/cloudflared
    $SUDO bash -c "cat > $cfg" <<EOF
tunnel: $name
credentials-file: /root/.cloudflared/${name}.json

ingress:
  - hostname: ${FULL_DOMAIN}
    service: http://localhost:${port}
  - service: http_status:404
EOF

    $SUDO bash -c "cat > $svc" <<EOF
[Unit]
Description=Cloudflare Tunnel for ${FULL_DOMAIN}
After=network.target

[Service]
TimeoutStartSec=0
ExecStart=/usr/bin/cloudflared tunnel --no-autoupdate --config $cfg run $name
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

    echo "🔄 Habilitando e iniciando servicio cloudflared-${name}.service"
    $SUDO systemctl daemon-reload
    $SUDO systemctl enable "cloudflared-${name}.service"
    $SUDO systemctl start "cloudflared-${name}.service"
}

for SUB in "${SUBDOMAINS[@]}"; do
    if [[ "$SUB" == "" ]]; then
        FULL_DOMAIN="$DOMAIN"
        TUNNEL_NAME="${DOMAIN_NAME}-tunnel"
    elif [[ "$SUB" == "www" ]]; then
        FULL_DOMAIN="www.${DOMAIN}"
        TUNNEL_NAME="www-${DOMAIN_NAME}-tunnel"
    else
        FULL_DOMAIN="${SUB}.${DOMAIN}"
        TUNNEL_NAME="${SUB}-${DOMAIN_NAME}-tunnel"
    fi

    if ! check_existing_subdomain "$SUB"; then
        continue
    fi

    read -p "🔹 Puerto local para ${FULL_DOMAIN} (default 8069): " LOCAL_PORT
    LOCAL_PORT=${LOCAL_PORT:-8069}

    if ! nc -z localhost $LOCAL_PORT; then
        echo "❌ El puerto local $LOCAL_PORT no está activo en localhost. Saltando $FULL_DOMAIN..."
        continue
    fi
    echo "✅ Puerto $LOCAL_PORT válido para $FULL_DOMAIN."

    # Requerir login para operar túneles
    if [ ! -f "$CERT_PATH" ]; then
        echo "❌ Falta cert.pem en $CERT_PATH. Ejecuta 'cloudflared login' antes de crear túneles."
        exit 1
    fi

    ensure_tunnel "$TUNNEL_NAME"

    echo "🛣️ Enrutando DNS $FULL_DOMAIN al túnel $TUNNEL_NAME..."
    cloudflared tunnel route dns "$TUNNEL_NAME" "$FULL_DOMAIN"

    create_service "$TUNNEL_NAME" "$LOCAL_PORT"
    echo "✅ Túnel y servicio configurados para $FULL_DOMAIN."
done
