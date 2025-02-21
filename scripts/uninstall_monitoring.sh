#!/bin/bash

# Monitoring system uninstallation script
echo "Uninstalling monitoring system..."

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
trap 'echo -e "${RED}Uninstallation failed${NC}"; exit 1' ERR

# Function to confirm uninstallation
confirm_uninstall() {
    echo -e "${RED}WARNING: This will completely remove the monitoring system and all its data${NC}"
    echo -e "${RED}This action cannot be undone!${NC}"
    read -p "Are you sure you want to proceed? (yes/no): " confirm
    
    if [[ "$confirm" != "yes" ]]; then
        echo -e "${YELLOW}Uninstallation cancelled${NC}"
        exit 0
    fi

    # Double confirmation for production
    if [[ "$FLASK_ENV" == "production" ]]; then
        read -p "This is a PRODUCTION environment. Type 'CONFIRM' to proceed: " confirm_prod
        if [[ "$confirm_prod" != "CONFIRM" ]]; then
            echo -e "${YELLOW}Uninstallation cancelled${NC}"
            exit 0
        fi
    fi
}

# Function to backup data before uninstall
backup_before_uninstall() {
    echo -e "${YELLOW}Creating backup before uninstallation...${NC}"

    BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/pre_uninstall_$BACKUP_TIMESTAMP"

    # Create backup directory
    mkdir -p "$BACKUP_PATH"

    # Backup configuration
    if [ -d "$MONITORING_DIR" ]; then
        cp -r "$MONITORING_DIR/config.py" "$BACKUP_PATH/"
        cp -r "$MONITORING_DIR/.env" "$BACKUP_PATH/"
    fi

    # Backup database
    if psql -lqt | cut -d \| -f 1 | grep -qw "terminusa_monitoring"; then
        pg_dump -U terminusa_monitor terminusa_monitoring > "$BACKUP_PATH/database_backup.sql"
    fi

    # Backup logs
    if [ -d "$LOG_DIR" ]; then
        cp -r "$LOG_DIR" "$BACKUP_PATH/logs"
    fi

    # Compress backup
    tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_PATH" .
    rm -rf "$BACKUP_PATH"

    echo -e "${GREEN}Backup created at: $BACKUP_PATH.tar.gz${NC}"
}

# Function to stop services
stop_services() {
    echo -e "${YELLOW}Stopping monitoring services...${NC}"

    # Stop systemd service
    if systemctl is-active --quiet terminusa-monitoring; then
        systemctl stop terminusa-monitoring
        systemctl disable terminusa-monitoring
    fi

    # Stop supervisor processes
    if [ -f "/etc/supervisor/conf.d/terminusa-monitoring.conf" ]; then
        supervisorctl stop terminusa-monitoring
    fi

    echo -e "${GREEN}Services stopped${NC}"
}

# Function to remove database
remove_database() {
    echo -e "${YELLOW}Removing database...${NC}"

    # Drop database and user
    sudo -u postgres psql << EOF
DROP DATABASE IF EXISTS terminusa_monitoring;
DROP USER IF EXISTS terminusa_monitor;
EOF

    echo -e "${GREEN}Database removed${NC}"
}

# Function to remove Redis data
remove_redis_data() {
    echo -e "${YELLOW}Removing Redis data...${NC}"

    # Clear monitoring-related keys
    redis-cli KEYS "monitoring:*" | xargs redis-cli DEL
    redis-cli KEYS "cache:monitoring:*" | xargs redis-cli DEL

    echo -e "${GREEN}Redis data removed${NC}"
}

# Function to remove files and directories
remove_files() {
    echo -e "${YELLOW}Removing files and directories...${NC}"

    # Remove monitoring directory
    if [ -d "$MONITORING_DIR" ]; then
        rm -rf "$MONITORING_DIR"
    fi

    # Remove log directory
    if [ -d "$LOG_DIR" ]; then
        rm -rf "$LOG_DIR"
    fi

    # Remove service files
    rm -f /etc/systemd/system/terminusa-monitoring.service
    rm -f /etc/supervisor/conf.d/terminusa-monitoring.conf
    rm -f /etc/cron.d/terminusa-monitoring

    # Remove configuration files
    rm -f /etc/nginx/conf.d/terminusa-monitoring.conf

    # Reload systemd
    systemctl daemon-reload

    # Reload supervisor
    supervisorctl reread
    supervisorctl update

    echo -e "${GREEN}Files removed${NC}"
}

# Function to remove Python packages
remove_packages() {
    echo -e "${YELLOW}Removing Python packages...${NC}"

    # Activate virtual environment
    source "$VENV_DIR/bin/activate"

    # Get list of monitoring packages
    packages=$(pip freeze | grep -i "monitoring\|metrics\|prometheus\|statsd")

    # Uninstall packages
    if [ ! -z "$packages" ]; then
        echo "$packages" | xargs pip uninstall -y
    fi

    echo -e "${GREEN}Packages removed${NC}"
}

# Function to clean up system
cleanup_system() {
    echo -e "${YELLOW}Cleaning up system...${NC}"

    # Remove log rotation config
    rm -f /etc/logrotate.d/terminusa-monitoring

    # Clean up temporary files
    find /tmp -name "monitoring_*" -delete

    # Clean up any remaining PID files
    rm -f /var/run/terminusa-monitoring.pid

    echo -e "${GREEN}System cleanup complete${NC}"
}

# Function to verify uninstallation
verify_uninstall() {
    echo -e "${YELLOW}Verifying uninstallation...${NC}"

    # Check directories
    if [ -d "$MONITORING_DIR" ] || [ -d "$LOG_DIR" ]; then
        echo -e "${RED}Monitoring directories still exist${NC}"
        return 1
    fi

    # Check database
    if psql -lqt | cut -d \| -f 1 | grep -qw "terminusa_monitoring"; then
        echo -e "${RED}Database still exists${NC}"
        return 1
    fi

    # Check services
    if systemctl is-active --quiet terminusa-monitoring; then
        echo -e "${RED}Service is still running${NC}"
        return 1
    fi

    # Check Redis keys
    if [ ! -z "$(redis-cli KEYS 'monitoring:*')" ]; then
        echo -e "${RED}Redis keys still exist${NC}"
        return 1
    fi

    echo -e "${GREEN}Uninstallation verified${NC}"
    return 0
}

# Main uninstallation process
main() {
    echo -e "${YELLOW}Starting monitoring system uninstallation...${NC}"

    # Run uninstallation steps
    confirm_uninstall
    backup_before_uninstall
    stop_services
    remove_database
    remove_redis_data
    remove_files
    remove_packages
    cleanup_system
    verify_uninstall

    echo -e "${GREEN}Monitoring system uninstallation complete!${NC}"
    echo -e "\nBackup of your data is available at: $BACKUP_PATH.tar.gz"
    echo "To completely remove all data, you can also delete:"
    echo "1. Backup directory: $BACKUP_DIR"
    echo "2. Virtual environment: $VENV_DIR"
}

# Execute main function
main
