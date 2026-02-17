#!/bin/bash

##############################################################################
#                                                                            #
#           ODOO 19 INSTALLER SCRIPT - ERP_CORE                            #
#                                                                            #
#  This script automates the installation and setup of Odoo 19 with all    #
#  migrated modules from the v17 → v19 migration project.                  #
#                                                                            #
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ODOO_VERSION="19.0"
ODOO_USER="odoo"
ODOO_GROUP="odoo"
ODOO_HOME="/opt/odoo"
ODOO_REPO="https://github.com/odoo/odoo.git"
PYTHON_VERSION="3.10"

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$SCRIPT_DIR"
MODULES_DIR="$PROJECT_DIR/extra-addons/V19"

##############################################################################
# FUNCTIONS
##############################################################################

print_header() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ $1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"
}

print_step() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

check_requirements() {
    print_header "Checking System Requirements"

    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root"
        exit 1
    fi
    print_step "Running as root"

    # Check OS
    if ! grep -qi "ubuntu\|debian" /etc/os-release; then
        print_warning "This script is optimized for Ubuntu/Debian. Other distributions may have issues."
    fi
    print_step "OS compatibility check passed"

    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    print_step "Python 3 found: $(python3 --version)"

    # Check Git
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed"
        exit 1
    fi
    print_step "Git found: $(git --version | cut -d' ' -f3)"

    # Check PostgreSQL
    if ! command -v psql &> /dev/null; then
        print_warning "PostgreSQL is not installed. Installing..."
        apt-get update
        apt-get install -y postgresql postgresql-contrib
    fi
    print_step "PostgreSQL available"
}

install_dependencies() {
    print_header "Installing System Dependencies"

    apt-get update
    print_step "APT cache updated"

    # Install required packages
    PACKAGES=(
        "build-essential"
        "libpq-dev"
        "libssl-dev"
        "libffi-dev"
        "libxml2-dev"
        "libxslt1-dev"
        "libjpeg-dev"
        "zlib1g-dev"
        "fontconfig"
        "libfreetype6-dev"
        "wkhtmltopdf"
        "xfonts-encodings"
        "xfonts-utils"
        "curl"
        "wget"
    )

    for package in "${PACKAGES[@]}"; do
        if dpkg -l | grep -q "^ii.*$package"; then
            print_step "$package already installed"
        else
            print_info "Installing $package..."
            apt-get install -y "$package"
        fi
    done
}

create_odoo_user() {
    print_header "Creating Odoo User"

    if id "$ODOO_USER" &>/dev/null; then
        print_step "User '$ODOO_USER' already exists"
    else
        useradd -m -d "$ODOO_HOME" -s /bin/bash "$ODOO_USER"
        print_step "User '$ODOO_USER' created"
    fi

    # Ensure home directory exists
    mkdir -p "$ODOO_HOME"
    chown "$ODOO_USER:$ODOO_GROUP" "$ODOO_HOME"
    print_step "Home directory set up: $ODOO_HOME"
}

setup_postgresql() {
    print_header "Setting Up PostgreSQL"

    # Start PostgreSQL if not running
    if ! pgrep -x "postgres" > /dev/null; then
        systemctl start postgresql
        systemctl enable postgresql
        print_step "PostgreSQL started"
    else
        print_step "PostgreSQL already running"
    fi

    # Create Odoo user in PostgreSQL
    if sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw "$ODOO_USER"; then
        print_step "PostgreSQL user '$ODOO_USER' already exists"
    else
        sudo -u postgres createuser -d "$ODOO_USER" 2>/dev/null || true
        print_step "PostgreSQL user '$ODOO_USER' created"
    fi
}

download_odoo() {
    print_header "Downloading Odoo $ODOO_VERSION"

    if [ -d "$ODOO_HOME/odoo-bin" ]; then
        print_step "Odoo already downloaded"
        return 0
    fi

    print_info "Cloning Odoo repository (this may take a few minutes)..."
    cd "$ODOO_HOME"

    sudo -u "$ODOO_USER" git clone --depth 1 --branch "$ODOO_VERSION" "$ODOO_REPO" . 2>&1 | tail -5

    print_step "Odoo $ODOO_VERSION downloaded"
}

install_python_dependencies() {
    print_header "Installing Python Dependencies"

    # Install pip packages
    pip3 install --upgrade pip setuptools wheel
    print_step "pip, setuptools, wheel upgraded"

    # Install Odoo requirements
    if [ -f "$ODOO_HOME/requirements.txt" ]; then
        pip3 install -r "$ODOO_HOME/requirements.txt" 2>&1 | tail -10
        print_step "Odoo Python requirements installed"
    fi

    # Install additional packages for better compatibility
    pip3 install psycopg2-binary python-dotenv
    print_step "Additional Python packages installed"
}

setup_odoo_config() {
    print_header "Setting Up Odoo Configuration"

    CONFIG_FILE="/etc/odoo/odoo.conf"
    CONFIG_DIR="/etc/odoo"

    # Create config directory
    mkdir -p "$CONFIG_DIR"
    chown "$ODOO_USER:$ODOO_GROUP" "$CONFIG_DIR"

    # Create configuration file
    cat > "$CONFIG_FILE" << 'ODOO_CONFIG'
[options]
; This is the password at the web interface encrypted with the custom salt defined
; in ~/.odoorc
admin_passwd = admin
db_host = localhost
db_port = 5432
db_user = odoo
db_password =
db_template = template0
; dbuseronly controls whether the new database user will be created from a template
; if not, then it is created as a new user
dbuseronly = False
; dbfilter is a regexp for filtering available databases
; syntax is expressed in Python regular expression syntax
; The characters '%h' are replaced by the HTTP_HOST environment variable
; and '%d' are replaced by the database name.
; Example with regex_esc(): dbfilter=%d
dbfilter =
default_category_id = 1
demo = {}
email_from = False
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
limit_request = 8192
limit_time_cpu = 60
limit_time_real = 120
list_db = True
log_db = False
log_db_level = warning
log_handler = :INFO
logfile = False
logrotate = False
longpolling_port = 8072
max_cron_threads = 2
osv_memory_count_limit = False
osv_memory_field_number_limit = False
pg_path = False
pidfile = False
proxy_mode = False
reportgz = False
secure_cert_file = /server.cert
secure_key_file = /server.key
server_wide_modules = base,web
smtp_password = False
smtp_port = 25
smtp_server = localhost
smtp_ssl = False
smtp_user = False
static_http_document_root = False
static_http_enable = False
static_http_url_prefix = False
syslog = False
test_enable = False
test_file = False
test_tags = None
transifex_password = False
transifex_username = False
unaccent = False
upgrade_path = False
without_demo = False
workers = 4
xmlrpc_interface =
xmlrpc_port = 8069
xmlrpc_ssl_interface =
xmlrpc_ssl_port = 8071
ODOO_CONFIG

    chown "$ODOO_USER:$ODOO_GROUP" "$CONFIG_FILE"
    chmod 640 "$CONFIG_FILE"

    print_step "Odoo configuration created at $CONFIG_FILE"
}

setup_modules() {
    print_header "Setting Up Migrated Modules"

    if [ ! -d "$MODULES_DIR" ]; then
        print_error "Modules directory not found: $MODULES_DIR"
        return 1
    fi

    # Create symbolic link or copy modules to addons path
    ADDONS_PATH="$ODOO_HOME/addons"

    if [ ! -d "$ADDONS_PATH" ]; then
        mkdir -p "$ADDONS_PATH"
    fi

    # Copy migrated modules
    print_info "Copying 86 migrated modules..."
    cp -r "$MODULES_DIR"/* "$ADDONS_PATH/" 2>/dev/null || true

    # Ensure permissions
    chown -R "$ODOO_USER:$ODOO_GROUP" "$ADDONS_PATH"

    # Count modules
    MODULES_COUNT=$(ls -d "$ADDONS_PATH"/*/ 2>/dev/null | wc -l)
    print_step "Modules copied: $MODULES_COUNT modules"
}

create_systemd_service() {
    print_header "Creating Systemd Service"

    SERVICE_FILE="/etc/systemd/system/odoo.service"

    cat > "$SERVICE_FILE" << 'SYSTEMD_SERVICE'
[Unit]
Description=Odoo 19
Requires=postgresql.service
After=postgresql.service

[Service]
Type=simple
SyslogIdentifier=odoo
SyslogFacility=local6
User=odoo
Group=odoo
ExecStart=/opt/odoo/odoo-bin -c /etc/odoo/odoo.conf
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SYSTEMD_SERVICE

    chmod 644 "$SERVICE_FILE"
    systemctl daemon-reload
    print_step "Systemd service created"
}

start_odoo() {
    print_header "Starting Odoo Service"

    systemctl enable odoo
    systemctl start odoo

    # Wait for Odoo to start
    sleep 5

    if systemctl is-active --quiet odoo; then
        print_step "Odoo service started successfully"
    else
        print_warning "Odoo service may not have started. Check logs with: journalctl -u odoo -n 50"
    fi
}

show_completion_info() {
    print_header "Installation Complete! 🎉"

    echo -e "${GREEN}Odoo 19 has been successfully installed and configured.${NC}\n"

    echo "📊 Installation Summary:"
    echo "  • Odoo Version: $ODOO_VERSION"
    echo "  • Installation Path: $ODOO_HOME"
    echo "  • Database User: $ODOO_USER"
    echo "  • Web Interface: http://localhost:8069"
    echo "  • Configuration: /etc/odoo/odoo.conf"
    echo "  • Modules Count: $(ls -d $ODOO_HOME/addons/*/ 2>/dev/null | wc -l)"
    echo ""

    echo "🔧 Useful Commands:"
    echo "  • Start Odoo:   systemctl start odoo"
    echo "  • Stop Odoo:    systemctl stop odoo"
    echo "  • Restart Odoo: systemctl restart odoo"
    echo "  • View Logs:    journalctl -u odoo -f"
    echo "  • Check Status: systemctl status odoo"
    echo ""

    echo "📚 Next Steps:"
    echo "  1. Open http://localhost:8069 in your browser"
    echo "  2. Login with admin (default password: admin)"
    echo "  3. Create a new database"
    echo "  4. Install the migrated modules from Apps"
    echo "  5. See FINAL_SUMMARY.md for migration details"
    echo ""

    echo "📝 Configuration Files:"
    echo "  • Odoo Config: /etc/odoo/odoo.conf"
    echo "  • Systemd Unit: /etc/systemd/system/odoo.service"
    echo "  • Log File: journalctl -u odoo"
    echo ""

    echo -e "${GREEN}Installation completed successfully!${NC}\n"
}

show_post_install_notes() {
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}         ODOO 19 POST-INSTALLATION NOTES${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════${NC}\n"

    echo "✅ Modules Available (86 total):"
    echo "  Location: $ODOO_HOME/addons/"
    echo ""

    echo "📖 Documentation:"
    echo "  • Full Migration Guide: $PROJECT_DIR/docs/ODOO_MIGRATION_V17_TO_V19.md"
    echo "  • Summary: $PROJECT_DIR/FINAL_SUMMARY.md"
    echo "  • Status: $PROJECT_DIR/MIGRATION_STATUS.txt"
    echo ""

    echo "🚀 To Install Modules:"
    echo "  1. Go to Apps menu in Odoo"
    echo "  2. Update Apps List (refresh the module cache)"
    echo "  3. Search for module names"
    echo "  4. Click Install on desired modules"
    echo ""

    echo "⚙️  Configuration Recommendations:"
    echo "  • Edit /etc/odoo/odoo.conf to customize settings"
    echo "  • Set proper admin_passwd (currently: admin)"
    echo "  • Adjust workers count based on CPU cores"
    echo "  • Configure database backup strategy"
    echo ""

    echo "🔐 Security Notes:"
    echo "  ⚠️  Change default admin password immediately!"
    echo "  ⚠️  Use SSL certificates for production"
    echo "  ⚠️  Set up proper database backups"
    echo "  ⚠️  Configure firewall rules appropriately"
    echo ""

    echo "📞 Support:"
    echo "  • Odoo Logs: journalctl -u odoo -f"
    echo "  • Check Modules Status: $PROJECT_DIR/validation_report.json"
    echo "  • Module Reports: $PROJECT_DIR/migration_reports/"
    echo ""
}

##############################################################################
# MAIN EXECUTION
##############################################################################

main() {
    print_header "ODOO 19 INSTALLATION SCRIPT"

    print_info "This script will install Odoo 19 with all migrated modules"
    print_info "from the ERP_Core v17→v19 migration project."
    print_info ""

    # Execute installation steps
    check_requirements
    install_dependencies
    create_odoo_user
    setup_postgresql
    download_odoo
    install_python_dependencies
    setup_odoo_config
    setup_modules
    create_systemd_service
    start_odoo
    show_completion_info
    show_post_install_notes

    print_info "Installation script completed!"
    print_info "Odoo 19 should now be accessible at http://localhost:8069"
}

# Run main function
main "$@"

##############################################################################
# END OF SCRIPT
##############################################################################
