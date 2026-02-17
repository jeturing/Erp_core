#!/bin/bash
################################################################################
# Odoo 19 Node Provisioning Script
# Sajet ERP - Multi-tenant LXC Container Setup
# Fecha: 2026-02-17
################################################################################

set -euo pipefail

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuración
CONTAINER_ID="${1:-106}"
NODE_NAME="${2:-node2}"
HOSTNAME="odoo19-${CONTAINER_ID}"
IP_SUBNET="10.0.3"
IP_ADDRESS="${IP_SUBNET}.${CONTAINER_ID}"
STORAGE_POOL="local"
CPU_CORES=4
RAM_MB=8192
DISK_GB=50
TIMEZONE="America/Bogota"

# Rutas
LXC_MOUNT_ODOO="/var/lib/lxc/odoo19-${CONTAINER_ID}/rootfs/opt/odoo"
ODOO_PORT=8069
LONGPOLL_PORT=8072

################################################################################
# FUNCIONES
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

check_prerequisites() {
    log_info "Verificando prerequisitos..."
    
    if ! command -v pct &> /dev/null; then
        log_error "pct command no encontrado. ¿Estás en Proxmox?"
        exit 1
    fi
    
    if [ "$(id -u)" != "0" ]; then
        log_error "Este script requiere ser ejecutado como root"
        exit 1
    fi
    
    # Verificar que el CONTAINER_ID no exista
    if pct list | grep -q "^${CONTAINER_ID}\s"; then
        log_error "Contenedor ${CONTAINER_ID} ya existe"
        exit 1
    fi
    
    log_success "Prerequisitos OK"
}

create_lxc_container() {
    log_info "Creando contenedor LXC ${CONTAINER_ID}..."
    
    pct create ${CONTAINER_ID} \
        local:vztmpl/debian-12-standard_12.3-1_amd64.tar.zst \
        -hostname ${HOSTNAME} \
        -memory ${RAM_MB} \
        -cores ${CPU_CORES} \
        -storage ${STORAGE_POOL} \
        -rootfs ${STORAGE_POOL}:${DISK_GB} \
        -net0 name=eth0,bridge=vmbr0,ip=${IP_ADDRESS}/24,gw=10.0.3.1 \
        -ostype debian \
        -features nesting=1,keyctl=1
    
    log_success "Contenedor LXC creado"
}

start_container() {
    log_info "Iniciando contenedor ${CONTAINER_ID}..."
    pct start ${CONTAINER_ID}
    sleep 3
    log_success "Contenedor iniciado"
}

setup_container_base() {
    log_info "Configurando sistema base..."
    
    pct exec ${CONTAINER_ID} -- apt-get update
    pct exec ${CONTAINER_ID} -- apt-get upgrade -y
    pct exec ${CONTAINER_ID} -- apt-get install -y \
        build-essential \
        git \
        curl \
        wget \
        nano \
        vim \
        htop \
        net-tools \
        telnet \
        python3 \
        python3-pip \
        python3-dev \
        python3-venv \
        postgresql \
        postgresql-contrib \
        postgresql-client \
        libpq-dev \
        libssl-dev \
        libffi-dev \
        libjpeg-dev \
        zlib1g-dev \
        libtiff-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libopenjp2-7-dev \
        npm \
        nodejs \
        wkhtmltopdf \
        xfonts-encodings \
        xfonts-utils \
        fonts-dejavu-core \
        fontconfig-config
    
    log_success "Sistema base configurado"
}

setup_postgresql() {
    log_info "Configurando PostgreSQL..."
    
    # Iniciar PostgreSQL
    pct exec ${CONTAINER_ID} -- systemctl enable postgresql
    pct exec ${CONTAINER_ID} -- systemctl start postgresql
    
    # Crear usuario y base de datos
    pct exec ${CONTAINER_ID} -- sudo -u postgres psql << EOF
CREATE USER odoo WITH PASSWORD 'odoo_secure_pwd_123!';
CREATE DATABASE odoo19 OWNER odoo;
GRANT ALL PRIVILEGES ON DATABASE odoo19 TO odoo;
ALTER ROLE odoo CREATEDB CREATEROLE;
EOF
    
    log_success "PostgreSQL configurado"
}

install_odoo19() {
    log_info "Instalando Odoo 19..."
    
    # Descargar Odoo 19
    pct exec ${CONTAINER_ID} -- mkdir -p /opt/odoo
    pct exec ${CONTAINER_ID} -- git clone --depth 1 \
        --branch 19.0 https://github.com/odoo/odoo.git /opt/odoo/odoo
    
    # Crear venv
    pct exec ${CONTAINER_ID} -- python3 -m venv /opt/odoo/venv
    
    # Instalar dependencias Python
    pct exec ${CONTAINER_ID} -- /opt/odoo/venv/bin/pip install --upgrade pip
    pct exec ${CONTAINER_ID} -- /opt/odoo/venv/bin/pip install -r /opt/odoo/odoo/requirements.txt
    
    # Crear carpeta de módulos custom
    pct exec ${CONTAINER_ID} -- mkdir -p /opt/odoo/custom-addons
    pct exec ${CONTAINER_ID} -- mkdir -p /opt/odoo/logs
    
    log_success "Odoo 19 instalado"
}

create_odoo_config() {
    log_info "Creando archivo de configuración Odoo..."
    
    pct exec ${CONTAINER_ID} -- tee /opt/odoo/odoo.conf > /dev/null << EOF
[options]
; Identificador de instancia
admin_passwd = admin_super_secret_change_me_123!

; Puertos
xmlrpc_port = ${ODOO_PORT}
longpolling_port = ${LONGPOLL_PORT}

; Base de datos
db_host = localhost
db_port = 5432
db_user = odoo
db_password = odoo_secure_pwd_123!
db_name = odoo19
db_maxconn = 64

; Rutas
addons_path = /opt/odoo/odoo/addons,/opt/odoo/custom-addons
logfile = /opt/odoo/logs/odoo.log
log_level = info

; Límites
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_time_cpu = 1200
limit_time_real = 1800

; Security
secure_cert_file = False
secure_key_file = False

; Email
email_from = noreply@sajet.us
smtp_server = smtp.sendgrid.net
smtp_port = 587
smtp_user = apikey
smtp_password = SG.your_sendgrid_key_here
smtp_ssl = False
smtp_tls = True

; Disable modules on load
auto_reload = False

; Workers
workers = 4
server_wide_modules = base,web,web_tour
EOF
    
    log_success "Configuración Odoo creada"
}

create_systemd_service() {
    log_info "Creando servicio systemd para Odoo..."
    
    pct exec ${CONTAINER_ID} -- tee /etc/systemd/system/odoo.service > /dev/null << EOF
[Unit]
Description=Odoo 19 Service
Documentation=https://www.odoo.com
Requires=postgresql.service
After=postgresql.service
ConditionPathExists=/opt/odoo/odoo.conf

[Service]
Type=simple
SyslogIdentifier=odoo
User=odoo
Group=odoo
WorkingDirectory=/opt/odoo/odoo
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/odoo/venv/bin/python -m odoo.cli.main -c /opt/odoo/odoo.conf

StandardOutput=journal
StandardError=journal

# Restart policy
Restart=on-failure
RestartSec=5

# Security
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF
    
    # Crear usuario odoo
    pct exec ${CONTAINER_ID} -- useradd -r -s /bin/bash odoo || true
    pct exec ${CONTAINER_ID} -- chown -R odoo:odoo /opt/odoo
    
    # Enable servicio
    pct exec ${CONTAINER_ID} -- systemctl daemon-reload
    pct exec ${CONTAINER_ID} -- systemctl enable odoo
    
    log_success "Servicio systemd creado"
}

setup_cloudflare_tunnel() {
    log_info "Configurando Cloudflare Tunnel..."
    
    # Instalar cloudflared en el contenedor
    pct exec ${CONTAINER_ID} -- curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    pct exec ${CONTAINER_ID} -- dpkg -i cloudflared.deb
    
    # Crear configuración (placeholder - requiere credenciales reales)
    pct exec ${CONTAINER_ID} -- tee /etc/cloudflared/config.yml > /dev/null << EOF
tunnel: odoo19-${CONTAINER_ID}
credentials-file: /etc/cloudflared/.cloudflared/cert.pem

ingress:
  - hostname: odoo19-${CONTAINER_ID}.sajet.us
    service: http://localhost:${ODOO_PORT}
  - service: http_status:404
EOF
    
    log_warn "IMPORTANTE: Configurar Cloudflare Tunnel credentials manualmente"
    log_warn "  $ pct exec ${CONTAINER_ID} -- cloudflared service install"
    log_warn "  $ pct exec ${CONTAINER_ID} -- systemctl start cloudflared"
    
    log_success "Cloudflare Tunnel config creada"
}

start_odoo_service() {
    log_info "Iniciando servicio Odoo..."
    
    pct exec ${CONTAINER_ID} -- systemctl start odoo
    sleep 3
    
    # Verificar estado
    if pct exec ${CONTAINER_ID} -- systemctl is-active --quiet odoo; then
        log_success "Servicio Odoo ejecutándose"
    else
        log_error "Odoo no inició. Verificar logs:"
        pct exec ${CONTAINER_ID} -- tail -50 /opt/odoo/logs/odoo.log
    fi
}

configure_firewall() {
    log_info "Configurando firewall en contenedor..."
    
    pct exec ${CONTAINER_ID} -- apt-get install -y ufw
    pct exec ${CONTAINER_ID} -- ufw default deny incoming
    pct exec ${CONTAINER_ID} -- ufw default allow outgoing
    pct exec ${CONTAINER_ID} -- ufw allow 22/tcp
    pct exec ${CONTAINER_ID} -- ufw allow ${ODOO_PORT}/tcp
    pct exec ${CONTAINER_ID} -- ufw allow ${LONGPOLL_PORT}/tcp
    pct exec ${CONTAINER_ID} -- ufw --force enable
    
    log_success "Firewall configurado"
}

show_summary() {
    log_info "═════════════════════════════════════════════════════════════════"
    log_success "✓ Provisioning Odoo 19 COMPLETADO"
    log_info "═════════════════════════════════════════════════════════════════"
    
    cat << EOF

📊 INFORMACIÓN DEL CONTENEDOR:

  Container ID:        ${CONTAINER_ID}
  Hostname:            ${HOSTNAME}
  IP Address:          ${IP_ADDRESS}/24
  CPU Cores:           ${CPU_CORES}
  RAM:                 ${RAM_MB}MB (${RAM_MB/1024}GB)
  Disk:                ${DISK_GB}GB
  Storage:             ${STORAGE_POOL}

🌐 ACCESO ODOO:

  URL:                 http://${IP_ADDRESS}:${ODOO_PORT}
  XML-RPC:             http://${IP_ADDRESS}:${ODOO_PORT}/xmlrpc
  Admin Password:      admin_super_secret_change_me_123! (⚠️ CAMBIAR)
  
  Tunnel URL:          odoo19-${CONTAINER_ID}.sajet.us (en Cloudflare)

🔧 CONFIGURACIÓN IMPORTANTE:

  1. Cambiar admin password inmediatamente
     Comando: pct exec ${CONTAINER_ID} -- odoo-bin --admin-passwd=nuevo_pwd

  2. Configurar credenciales Cloudflare Tunnel
     Archivo: /etc/cloudflared/config.yml
     
  3. Cambiar contraseña PostgreSQL
     Usuario: odoo
     BD: odoo19
     
  4. Configurar SMTP en Odoo (actualmente modo demo)
     Archivo: /opt/odoo/odoo.conf
     Servidor: smtp.sendgrid.net (u otro proveedor)

📁 RUTAS PRINCIPALES:

  Odoo Install:        /opt/odoo/odoo
  Custom Addons:       /opt/odoo/custom-addons
  Logs:                /opt/odoo/logs/odoo.log
  Config:              /opt/odoo/odoo.conf
  
  PostgreSQL:          localhost:5432
  DB User:             odoo
  DB Name:             odoo19

🔍 COMANDOS ÚTILES:

  Conectar a contenedor:
    $ pct exec ${CONTAINER_ID} -- bash
    
  Ver logs en vivo:
    $ pct exec ${CONTAINER_ID} -- tail -f /opt/odoo/logs/odoo.log
    
  Ver estado servicio:
    $ pct exec ${CONTAINER_ID} -- systemctl status odoo
    
  Reiniciar Odoo:
    $ pct exec ${CONTAINER_ID} -- systemctl restart odoo

✅ PRÓXIMOS PASOS:

  1. Validar acceso a http://${IP_ADDRESS}:${ODOO_PORT}
  2. Cambiar contraseña admin
  3. Instalar módulos custom en /opt/odoo/custom-addons
  4. Configurar Cloudflare Tunnel
  5. Realizar backup de BD

⏱️  INICIO TAREA: $(date '+%Y-%m-%d %H:%M:%S')

═════════════════════════════════════════════════════════════════

EOF
}

################################################################################
# MAIN
################################################################################

main() {
    log_info "╔════════════════════════════════════════════════════════════════╗"
    log_info "║      Odoo 19 Multi-tenant LXC Provisioning Script              ║"
    log_info "║      Sajet ERP - Container ID: ${CONTAINER_ID}                           ║"
    log_info "╚════════════════════════════════════════════════════════════════╝"
    log_info ""
    
    check_prerequisites
    create_lxc_container
    start_container
    setup_container_base
    setup_postgresql
    install_odoo19
    create_odoo_config
    create_systemd_service
    setup_cloudflare_tunnel
    configure_firewall
    start_odoo_service
    show_summary
}

# Ejecución
main "$@"
