#!/bin/bash

# ==============================================================================
#   GESTOR AVANZADO DE CLOUDFLARE TUNNELS v2.2
#   - Estructura corregida para asegurar que las funciones se definan antes de ser llamadas.
# ==============================================================================

# --- Configuración y Variables Globales ---
set -eE
trap 'echo "❌ Error en la línea $LINENO: El comando falló. Revisa el log para más detalles."' ERR

LOG_FILE="/var/log/cf_manager.log"
CREDENTIALS_FILE="/root/.cf_credentials"
DOMAINS_FILE="./dominios.json"

# Variable global para la ruta de cloudflared
export CLOUDFLARED_PATH=""

# Redirigir toda la salida a un archivo de log y a la pantalla
exec &> >(tee -a "$LOG_FILE")

# --- Funciones de Utilidad (Colores) ---
COLOR_CYAN="\033[0;36m"
COLOR_GREEN="\033[0;32m"
COLOR_RED="\033[0;31m"
COLOR_YELLOW="\033[1;33m"
COLOR_RESET="\033[0m"

################################################################################
# DEFINICIÓN DE FUNCIONES
# Todas las funciones del script se definen en esta sección.
################################################################################

function load_config() {
    echo -e "${COLOR_CYAN}--- Cargando Configuración ---${COLOR_RESET}"
    if [ -f "$CREDENTIALS_FILE" ]; then
        source "$CREDENTIALS_FILE"
        echo -e "${COLOR_GREEN}✅ Credenciales cargadas.${COLOR_RESET}"
    else
        echo -e "${COLOR_RED}❌ No se encontró el archivo de credenciales en ${CREDENTIALS_FILE}.${COLOR_RESET}"
        echo "Crea el archivo con: CLOUDFLARE_API_TOKEN=\"tu_token\""
        exit 1
    fi

    if ! [ -f "$DOMAINS_FILE" ]; then
        echo -e "${COLOR_RED}❌ No se encontró el archivo de dominios en ${DOMAINS_FILE}.${COLOR_RESET}"
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        echo -e "${COLOR_RED}❌ La dependencia 'jq' no está instalada. Por favor, ejecuta 'sudo apt install jq'.${COLOR_RESET}"
        exit 1
    fi
    echo -e "${COLOR_GREEN}✅ Archivo de dominios encontrado.${COLOR_RESET}"
}

function install_or_update_cloudflared() {
    echo -e "${COLOR_CYAN}--- Verificando Instalación de cloudflared ---${COLOR_RESET}"
    if ! command -v cloudflared &> /dev/null; then
        echo "🔧 'cloudflared' no encontrado. Iniciando instalación..."
        if [ ! -f "/etc/apt/sources.list.d/cloudflared.list" ]; then
            echo "   Configurando el repositorio de Cloudflare..."
            sudo mkdir -p --mode=0755 /usr/share/keyrings
            curl -fsSL https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare-main.gpg > /dev/null
            export CLOUDFLARE_CODENAME=$(lsb_release -cs)
            echo "deb [signed-by=/usr/share/keyrings/cloudflare-main.gpg] https://pkg.cloudflare.com/cloudflared ${CLOUDFLARE_CODENAME} main" | sudo tee /etc/apt/sources.list.d/cloudflared.list > /dev/null
        fi
        echo "   Actualizando e instalando..."
        sudo apt-get update && sudo apt-get install -y cloudflared
    fi
    
    CLOUDFLARED_PATH=$(which cloudflared)
    echo -e "${COLOR_GREEN}✅ 'cloudflared' está disponible en: ${CLOUDFLARED_PATH}${COLOR_RESET}"
    echo -e "   Versión: $(${CLOUDFLARED_PATH} --version)"
}

function delete_tunnel() {
    echo -e "${COLOR_CYAN}--- Eliminar un Túnel de Cloudflare ---${COLOR_RESET}"
    ${CLOUDFLARED_PATH} tunnel list
    read -p "Ingresa el NOMBRE o ID del túnel que deseas eliminar: " TUNNEL_TO_DELETE

    if [ -z "$TUNNEL_TO_DELETE" ]; then
        echo -e "${COLOR_RED}No se ingresó ningún nombre. Abortando.${COLOR_RESET}"
        return
    fi

    TUNNEL_ID=$(${CLOUDFLARED_PATH} tunnel list | grep "$TUNNEL_TO_DELETE" | awk '{print $1}')
    TUNNEL_NAME=$(${CLOUDFLARED_PATH} tunnel list | grep "$TUNNEL_TO_DELETE" | awk '{print $2}')

    if [ -z "$TUNNEL_ID" ]; then
        echo -e "${COLOR_RED}No se encontró ningún túnel con ese nombre/ID. Abortando.${COLOR_RESET}"
        return
    fi
    
    echo -e "${COLOR_YELLOW}⚠️ Estás a punto de eliminar permanentemente el túnel '${TUNNEL_NAME}' (ID: ${TUNNEL_ID}).${COLOR_RESET}"
    read -p "Esta acción no se puede deshacer. Escribe 'eliminar' para confirmar: " confirmation
    if [ "$confirmation" != "eliminar" ]; then
        echo "Confirmación incorrecta. Abortando."
        return
    fi
    
    SERVICE_FILE="/etc/systemd/system/cloudflared-${TUNNEL_NAME}.service"

    echo "🧹 Deteniendo y deshabilitando el servicio..."
    sudo systemctl stop "cloudflared-${TUNNEL_NAME}.service" 2>/dev/null || true
    sudo systemctl disable "cloudflared-${TUNNEL_NAME}.service" 2>/dev/null || true
    
    echo "🗑️  Eliminando archivos locales..."
    [ -f "$SERVICE_FILE" ] && sudo rm "$SERVICE_FILE"
    
    echo "☁️  Eliminando el túnel de Cloudflare..."
    ${CLOUDFLARED_PATH} tunnel delete "$TUNNEL_ID"
    
    echo "🔄 Recargando systemd..."
    sudo systemctl daemon-reload
    
    echo -e "${COLOR_GREEN}✅ Túnel '${TUNNEL_NAME}' eliminado con éxito.${COLOR_RESET}"
}

function manage_tunnels() {
    select_domain() {
        echo -e "${COLOR_CYAN}🔹 Seleccione un dominio:${COLOR_RESET}"
        jq -r '.[] | .name' "$DOMAINS_FILE" | nl
        read -p "Ingrese el número correspondiente: " DOMAIN_OPTION
        
        DOMAIN=$(jq -r --argjson index "$((DOMAIN_OPTION-1))" '.[$index].name' "$DOMAINS_FILE")

        if [ -z "$DOMAIN" ] || [ "$DOMAIN" == "null" ]; then
            echo -e "${COLOR_RED}❌ Opción no válida. Abortando.${COLOR_RESET}"
            exit 1
        fi
        echo -e "${COLOR_GREEN}✅ Dominio seleccionado: $DOMAIN${COLOR_RESET}"
    }

    select_domain

    read -p "🔹 Ingresa los subdominios separados por espacio (deja en blanco para usar el dominio raíz): " -a SUBDOMAINS
    if [[ ${#SUBDOMAINS[@]} -eq 0 ]]; then SUBDOMAINS=(""); fi

    DOMAIN_NAME=$(echo "$DOMAIN" | sed 's/\.[^.]*$//')

    for SUB in "${SUBDOMAINS[@]}"; do
        if [[ "$SUB" == "" ]]; then
            FULL_DOMAIN="$DOMAIN"
            TUNNEL_NAME="${DOMAIN_NAME}-tunnel"
        else
            FULL_DOMAIN="${SUB}.${DOMAIN}"
            TUNNEL_NAME="${SUB}-${DOMAIN_NAME}-tunnel"
        fi

        read -p "🔹 Puerto local para ${FULL_DOMAIN} (default 80): " LOCAL_PORT
        LOCAL_PORT=${LOCAL_PORT:-80}

        echo "🛠️  Creando túnel: ${TUNNEL_NAME}"
        ${CLOUDFLARED_PATH} tunnel create "${TUNNEL_NAME}"

        echo "🛣️  Enrutando el DNS para el túnel..."
        ${CLOUDFLARED_PATH} tunnel route dns "$TUNNEL_NAME" "$FULL_DOMAIN"

        echo "📝 Creando archivo de servicio systemd..."
        SERVICE_FILE="/etc/systemd/system/cloudflared-${TUNNEL_NAME}.service"
        
        sudo bash -c "cat > ${SERVICE_FILE}" <<EOF
[Unit]
Description=Cloudflare Tunnel for ${FULL_DOMAIN}
After=network.target

[Service]
TimeoutStartSec=0
ExecStart=${CLOUDFLARED_PATH} tunnel --no-autoupdate run --url http://localhost:${LOCAL_PORT} ${TUNNEL_NAME}
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

        echo "✅ Servicio systemd creado en ${SERVICE_FILE}"
        echo "🔄 Habilitando e iniciando el servicio del túnel..."
        sudo systemctl daemon-reload
        sudo systemctl enable "cloudflared-${TUNNEL_NAME}.service"
        sudo systemctl start "cloudflared-${TUNNEL_NAME}.service"
        
        echo -e "${COLOR_GREEN}✅ Túnel '${TUNNEL_NAME}' para '${FULL_DOMAIN}' creado y activado con éxito.${COLOR_RESET}"
        echo "---"
    done
}


################################################################################
# EJECUCIÓN PRINCIPAL DEL SCRIPT
# Esta es la sección que se ejecuta. Llama a las funciones definidas arriba.
################################################################################

echo -e "${COLOR_CYAN}=============================================${COLOR_RESET}"
echo -e "${COLOR_YELLOW}    GESTOR DE CLOUDFLARE TUNNELS v2.2${COLOR_RESET}"
echo -e "${COLOR_CYAN}=============================================${COLOR_RESET}"

# 1. Cargar configuración y verificar dependencias
load_config
install_or_update_cloudflared

# 2. Mostrar el menú de opciones al usuario
PS3=$'\n'"▶️ Por favor, elige una opción: "
options=("Crear un nuevo Túnel" "Eliminar un Túnel existente" "Listar Túneles activos" "Salir")
select opt in "${options[@]}"
do
    case $opt in
        "Crear un nuevo Túnel")
            manage_tunnels
            break
            ;;
        "Eliminar un Túnel existente")
            delete_tunnel
            break
            ;;
        "Listar Túneles activos")
            echo -e "${COLOR_CYAN}--- Lista de Túneles Configurados ---${COLOR_RESET}"
            ${CLOUDFLARED_PATH} tunnel list
            break
            ;;
        "Salir")
            break
            ;;
        *) echo "Opción no válida $REPLY";;
    esac
done

echo -e "\n${COLOR_GREEN}👋 Script finalizado.${COLOR_RESET}"
