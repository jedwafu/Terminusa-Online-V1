#!/bin/bash

# Monitoring system upgrade script
echo "Upgrading monitoring system..."

# Configuration
MONITORING_DIR="/var/www/terminusa/monitoring"
LOG_DIR="/var/log/terminusa/monitoring"
BACKUP_DIR="/var/www/backups/monitoring"
VENV_DIR="/var/www/terminusa/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Error handling
set -e
trap 'echo -e "${RED}Upgrade failed${NC}"; exit 1' ERR

# Function to check current version
check_version() {
    echo -e "${YELLOW}Checking current version...${NC}"
    
    if [ -f "$MONITORING_DIR/version.txt" ]; then
        CURRENT_VERSION=$(cat "$MONITORING_DIR/version.txt")
    else
        CURRENT_VERSION="0.0.0"
    fi
    
    echo -e "Current version: ${GREEN}$CURRENT_VERSION${NC}"
}

# Function to backup before upgrade
backup_before_upgrade() {
    echo -e "${YELLOW}Creating backup before upgrade...${NC}"

    BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/pre_upgrade_$BACKUP_TIMESTAMP"

    # Create backup
    python manage.py backup_monitoring --type=full --destination="$BACKUP_PATH"

    echo -e "${GREEN}Backup created at: $BACKUP_PATH${NC}"
}

# Function to stop services
stop_services() {
    echo -e "${YELLOW}Stopping monitoring services...${NC}"

    systemctl stop terminusa-monitoring
    supervisorctl stop terminusa-monitoring

    echo -e "${GREEN}Services stopped${NC}"
}

# Function to upgrade dependencies
upgrade_dependencies() {
    echo -e "${YELLOW}Upgrading dependencies...${NC}"

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Upgrade pip
    pip install --upgrade pip setuptools wheel

    # Backup current requirements
    cp requirements-monitoring.txt requirements-monitoring.txt.bak

    # Install/upgrade requirements
    pip install -r requirements-monitoring.txt --upgrade

    echo -e "${GREEN}Dependencies upgraded${NC}"
}

# Function to upgrade database
upgrade_database() {
    echo -e "${YELLOW}Upgrading database...${NC}"

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Run migrations
    python manage.py migrate

    echo -e "${GREEN}Database upgraded${NC}"
}

# Function to upgrade configuration
upgrade_config() {
    echo -e "${YELLOW}Upgrading configuration...${NC}"

    # Backup current config
    cp "$MONITORING_DIR/config.py" "$MONITORING_DIR/config.py.bak"
    cp "$MONITORING_DIR/.env" "$MONITORING_DIR/.env.bak"

    # Update configuration files
    cp config/monitoring_config.py "$MONITORING_DIR/config.py"

    # Merge environment variables
    if [ -f "$MONITORING_DIR/.env.bak" ]; then
        while IFS='=' read -r key value; do
            if ! grep -q "^$key=" "$MONITORING_DIR/.env"; then
                echo "$key=$value" >> "$MONITORING_DIR/.env"
            fi
        done < "$MONITORING_DIR/.env.bak"
    fi

    echo -e "${GREEN}Configuration upgraded${NC}"
}

# Function to upgrade scripts
upgrade_scripts() {
    echo -e "${YELLOW}Upgrading scripts...${NC}"

    # Update monitoring scripts
    cp scripts/monitoring_*.sh /usr/local/bin/
    chmod +x /usr/local/bin/monitoring_*.sh

    echo -e "${GREEN}Scripts upgraded${NC}"
}

# Function to upgrade services
upgrade_services() {
    echo -e "${YELLOW}Upgrading services...${NC}"

    # Update service files
    cp terminusa-monitoring.service /etc/systemd/system/
    cp terminusa-monitoring.conf /etc/supervisor/conf.d/

    # Reload systemd
    systemctl daemon-reload

    # Update supervisor
    supervisorctl reread
    supervisorctl update

    echo -e "${GREEN}Services upgraded${NC}"
}

# Function to upgrade cron jobs
upgrade_cron() {
    echo -e "${YELLOW}Upgrading cron jobs...${NC}"

    # Update cron file
    cp scripts/monitoring_cron.sh /etc/cron.d/terminusa-monitoring
    chmod 644 /etc/cron.d/terminusa-monitoring

    echo -e "${GREEN}Cron jobs upgraded${NC}"
}

# Function to start services
start_services() {
    echo -e "${YELLOW}Starting services...${NC}"

    systemctl start terminusa-monitoring
    supervisorctl start terminusa-monitoring

    echo -e "${GREEN}Services started${NC}"
}

# Function to verify upgrade
verify_upgrade() {
    echo -e "${YELLOW}Verifying upgrade...${NC}"

    # Check service status
    if ! systemctl is-active --quiet terminusa-monitoring; then
        echo -e "${RED}Service not running${NC}"
        return 1
    fi

    # Check database
    if ! python manage.py manage_monitoring check-db; then
        echo -e "${RED}Database check failed${NC}"
        return 1
    fi

    # Check monitoring
    if ! python manage.py manage_monitoring check; then
        echo -e "${RED}Monitoring check failed${NC}"
        return 1
    fi

    echo -e "${GREEN}Upgrade verified${NC}"
    return 0
}

# Function to cleanup
cleanup() {
    echo -e "${YELLOW}Cleaning up...${NC}"

    # Remove backup files older than 30 days
    find "$BACKUP_DIR" -name "pre_upgrade_*" -mtime +30 -delete

    # Remove old config backups
    find "$MONITORING_DIR" -name "*.bak" -mtime +7 -delete

    echo -e "${GREEN}Cleanup complete${NC}"
}

# Function to rollback
rollback() {
    echo -e "${RED}Rolling back upgrade...${NC}"

    # Stop services
    stop_services

    # Restore from backup
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR/pre_upgrade_"* | head -n1)
    if [ -n "$LATEST_BACKUP" ]; then
        python manage.py restore_monitoring --backup-dir="$LATEST_BACKUP" --force
    fi

    # Restore config files
    if [ -f "$MONITORING_DIR/config.py.bak" ]; then
        mv "$MONITORING_DIR/config.py.bak" "$MONITORING_DIR/config.py"
    fi
    if [ -f "$MONITORING_DIR/.env.bak" ]; then
        mv "$MONITORING_DIR/.env.bak" "$MONITORING_DIR/.env"
    fi

    # Start services
    start_services

    echo -e "${GREEN}Rollback complete${NC}"
}

# Function to update version
update_version() {
    echo -e "${YELLOW}Updating version...${NC}"

    NEW_VERSION="1.0.0"  # Update this with actual version
    echo "$NEW_VERSION" > "$MONITORING_DIR/version.txt"

    echo -e "${GREEN}Version updated to: $NEW_VERSION${NC}"
}

# Main upgrade process
main() {
    echo -e "${YELLOW}Starting monitoring system upgrade...${NC}"

    # Get confirmation
    read -p "Are you sure you want to upgrade? (yes/no): " confirm
    if [[ "$confirm" != "yes" ]]; then
        echo -e "${YELLOW}Upgrade cancelled${NC}"
        exit 0
    fi

    # Run upgrade steps
    check_version
    backup_before_upgrade
    stop_services
    
    # Try upgrade steps
    if upgrade_dependencies && \
       upgrade_database && \
       upgrade_config && \
       upgrade_scripts && \
       upgrade_services && \
       upgrade_cron && \
       start_services && \
       verify_upgrade; then
        
        update_version
        cleanup
        echo -e "${GREEN}Monitoring system upgrade completed successfully!${NC}"
        
    else
        echo -e "${RED}Upgrade failed, rolling back...${NC}"
        rollback
        exit 1
    fi

    echo -e "\nNext steps:"
    echo "1. Review configuration changes in $MONITORING_DIR/config.py"
    echo "2. Test monitoring functionality"
    echo "3. Check monitoring dashboard"
    echo "4. Review logs for any issues"
}

# Execute main function
main
