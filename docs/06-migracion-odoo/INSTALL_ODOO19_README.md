# 🚀 Odoo 19 Installer - ERP_Core

Estado: vigente  
Validado: 2026-02-22  
Entorno objetivo: `/opt/Erp_core`


**Quick Installation Guide for Odoo 19 with All Migrated Modules**

---

## 📋 Overview

This installer script automates the complete setup of Odoo 19 with all 86 migrated modules from the v17 → v19 migration project.

**What the installer does:**
- ✅ Checks system requirements
- ✅ Installs system dependencies
- ✅ Creates Odoo user and PostgreSQL setup
- ✅ Downloads Odoo 19 from official repository
- ✅ Installs Python dependencies
- ✅ Configures Odoo with optimal settings
- ✅ Copies all 86 migrated modules
- ✅ Creates systemd service for automatic startup
- ✅ Starts Odoo service

---

## 🔧 System Requirements

### Minimum Requirements
- **OS**: Ubuntu 18.04+ or Debian 10+
- **CPU**: 2 cores
- **RAM**: 2 GB (4 GB recommended)
- **Disk**: 10 GB free space
- **Database**: PostgreSQL (will be installed if needed)

### Required Software
- `sudo` access (script must run as root)
- `git` (for cloning Odoo repository)
- `python3.10` or later

### Internet Connection
- Required for downloading Odoo repository and Python packages

---

## 📥 Installation

### Step 1: Download the Installer

```bash
# Navigate to the ERP_Core directory
cd /Users/owner/Desktop/jcore/Erp_core

# The installer is already executable
ls -la install_odoo19.sh
```

### Step 2: Run the Installer

```bash
# Run as root (will ask for sudo password)
sudo bash install_odoo19.sh

# Or if already root:
./install_odoo19.sh
```

### Step 3: Wait for Installation

The installation typically takes 10-20 minutes depending on internet speed and system performance.

**Installation stages:**
1. ✓ Checking requirements (1 min)
2. ✓ Installing dependencies (3-5 min)
3. ✓ Creating user and database (1 min)
4. ✓ Downloading Odoo 19 (3-5 min)
5. ✓ Installing Python packages (2-3 min)
6. ✓ Configuring Odoo (1 min)
7. ✓ Setting up modules (1 min)
8. ✓ Starting service (1 min)

---

## 🌐 Accessing Odoo

Once installation is complete:

1. **Open browser**: http://localhost:8069
2. **Default credentials**:
   - Username: `admin`
   - Password: `admin`

### Creating Your First Database

1. Click "Create a new database"
2. Enter database name
3. Set master password (different from admin password)
4. Select demo data (optional)
5. Click "Create database"

---

## 📦 Modules

### All 86 Migrated Modules Ready

After creating a database:

1. Go to **Apps** menu
2. Click **Update Apps List** (refreshes module cache)
3. Search for module names
4. Click **Install** on desired modules

### Key Module Categories

**Core ERP**
- Accounting (account_*)
- HR & Payroll (hr_*, ohrms_*)
- Sales & CRM
- Inventory & Warehouse
- Project Management

**Themes & UI**
- Backend themes (vista, clarity, spiffy)
- POS themes
- Web components (muk_web_*)

**Integrations**
- WhatsApp integration
- Google Analytics
- ChatGPT integration
- Stripe payments

**Advanced Features**
- Fleet rental
- Hotel management
- Document management
- Advanced dashboards

See: `FINAL_SUMMARY.md` for complete module list

---

## ⚙️ Configuration

### Configuration File

Location: `/etc/odoo/odoo.conf`

**Key settings:**
```ini
[options]
; Web interface port (default: 8069)
xmlrpc_port = 8069

; PostgreSQL configuration
db_host = localhost
db_port = 5432
db_user = odoo

; Number of worker processes (adjust based on CPU cores)
workers = 4

; Memory limits (adjust for your server)
limit_memory_hard = 2684354560
limit_memory_soft = 2147483648
```

### Editing Configuration

```bash
# Edit as root
sudo nano /etc/odoo/odoo.conf

# After editing, restart Odoo
sudo systemctl restart odoo
```

---

## 🔌 Service Management

### Useful Commands

```bash
# Start Odoo
sudo systemctl start odoo

# Stop Odoo
sudo systemctl stop odoo

# Restart Odoo
sudo systemctl restart odoo

# Check status
sudo systemctl status odoo

# Enable auto-start on boot
sudo systemctl enable odoo

# View logs (last 50 lines)
sudo journalctl -u odoo -n 50

# Follow logs in real-time
sudo journalctl -u odoo -f
```

---

## 🐛 Troubleshooting

### Odoo won't start

**Check logs:**
```bash
sudo journalctl -u odoo -n 100
```

**Common issues:**
- Port 8069 already in use: Edit `/etc/odoo/odoo.conf` and change `xmlrpc_port`
- PostgreSQL not running: `sudo systemctl start postgresql`
- Permission issues: `sudo chown -R odoo:odoo /opt/odoo`

### Can't connect to database

**Verify PostgreSQL is running:**
```bash
sudo systemctl status postgresql

# Or restart it:
sudo systemctl restart postgresql
```

**Check Odoo user can access database:**
```bash
sudo -u odoo psql -h localhost -U odoo -l
```

### Module installation fails

1. Check `validation_report.json` for module details
2. Review module-specific report: `migration_reports/[module_name]_migration.json`
3. Check Odoo logs for specific error

### Performance issues

**Optimize configuration:**
```bash
# Increase workers (for multi-core systems)
# Edit /etc/odoo/odoo.conf
workers = 8  # Adjust based on CPU cores

# Restart
sudo systemctl restart odoo
```

---

## 🔐 Security

### Important Post-Installation Steps

⚠️ **CHANGE DEFAULT ADMIN PASSWORD IMMEDIATELY**

```bash
# In Odoo web interface:
# 1. Log in with admin/admin
# 2. Go to Settings > Users > Administrator
# 3. Change password
```

### Additional Security

**Enable SSL/TLS:**
```bash
# Generate self-signed certificate
sudo openssl req -x509 -newkey rsa:4096 -nodes \
  -out /etc/odoo/server.crt \
  -keyout /etc/odoo/server.key -days 365

# Update /etc/odoo/odoo.conf
# secure_cert_file = /etc/odoo/server.crt
# secure_key_file = /etc/odoo/server.key

# Restart Odoo
sudo systemctl restart odoo
```

**Firewall Rules:**
```bash
# Allow Odoo port
sudo ufw allow 8069/tcp

# Allow only from specific IP
sudo ufw allow from 192.168.1.0/24 to any port 8069
```

### Database Backups

**Manual backup:**
```bash
sudo -u odoo pg_dump -h localhost odoo_database > backup.sql
```

**Automated daily backup:**
```bash
# Create backup script
sudo tee /usr/local/bin/backup-odoo.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/odoo"
mkdir -p $BACKUP_DIR
sudo -u odoo pg_dump -h localhost odoo_database > $BACKUP_DIR/backup_$DATE.sql
EOF

# Make executable
sudo chmod +x /usr/local/bin/backup-odoo.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup-odoo.sh
```

---

## 📊 Monitoring

### Check Server Status

```bash
# Overall status
sudo systemctl status odoo

# View resource usage
top
# Look for odoo process

# Check database connections
sudo -u odoo psql -h localhost -U odoo -c "SELECT count(*) FROM pg_stat_activity;"
```

### Common Metrics

```bash
# Number of active users
SELECT count(*) FROM ir_session WHERE active = true;

# Database size
SELECT pg_size_pretty(pg_database_size('odoo_database'));

# Number of installed modules
SELECT count(*) FROM ir_module_module WHERE state = 'installed';
```

---

## 🔄 Updating Modules

After installing new versions of migrated modules:

```bash
# 1. Copy updated modules
cp -r /path/to/updated/modules/* /opt/odoo/addons/

# 2. Restart Odoo
sudo systemctl restart odoo

# 3. Update module list in Odoo
# Go to Apps > Update Apps List

# 4. Upgrade module
# Go to Apps > Find module > Upgrade
```

---

## 📚 Documentation

**Installation-related:**
- This file: `INSTALL_ODOO19_README.md`

**Migration-related:**
- `FINAL_SUMMARY.md` - Complete migration overview
- `MIGRATION_STATUS.txt` - Quick reference
- `docs/ODOO_MIGRATION_V17_TO_V19.md` - Full migration guide

**Module information:**
- `migration_reports/MASTER_MIGRATION_REPORT.md` - All module details
- `validation_report.json` - Validation metrics
- `migration_reports/[module_name]_migration.json` - Per-module analysis

---

## 🆘 Getting Help

### Odoo Official Resources

- **Documentation**: https://www.odoo.com/documentation/19.0/
- **GitHub**: https://github.com/odoo/odoo
- **Community Forum**: https://github.com/OCA/server-tools

### Migration-Specific Help

1. **Check module report**: `migration_reports/[module_name]_migration.json`
2. **Review validation data**: `validation_report.json`
3. **See migration guide**: `docs/ODOO_MIGRATION_V17_TO_V19.md`
4. **Check migration summary**: `MIGRATION_COMPLETION_REPORT.md`

### Reporting Issues

When reporting installation issues, provide:
- OS and version: `lsb_release -a`
- Python version: `python3 --version`
- Odoo logs: `sudo journalctl -u odoo -n 100`
- Configuration file: `/etc/odoo/odoo.conf` (without passwords)

---

## ✅ Installation Verification

After successful installation, verify:

```bash
# 1. Service is running
sudo systemctl status odoo
# Should show: active (running)

# 2. Port is listening
sudo lsof -i :8069
# Should show odoo process

# 3. Database is created
sudo -u odoo psql -h localhost -U odoo -l
# Should list odoo database

# 4. Modules are present
ls /opt/odoo/addons | wc -l
# Should show 86+ directories

# 5. Web interface is accessible
curl http://localhost:8069
# Should return HTML content
```

---

## 🎯 Next Steps

After successful installation:

1. ✅ Access Odoo at http://localhost:8069
2. ✅ Change admin password
3. ✅ Create first database
4. ✅ Install required modules
5. ✅ Configure company information
6. ✅ Set up users and permissions
7. ✅ Begin using Odoo 19

See `FINAL_SUMMARY.md` for full post-deployment guide.

---

## 📞 Support

For help with:
- **General Odoo questions**: See Odoo documentation or community forums
- **Migration-specific issues**: Check migration reports and guides in this repository
- **Installation problems**: Review logs and troubleshooting section above

---

## 📝 License

This installer script is part of the ERP_Core Odoo v17→v19 migration project.

All migrated modules retain their original licenses (AGPL-3, LGPL-3, etc.)

---

**Last Updated**: 2026-02-17
**Odoo Version**: 19.0
**Modules**: 86 (all migrated and validated)
**Status**: ✅ Production Ready

