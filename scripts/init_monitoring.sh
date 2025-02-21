#!/bin/bash

# Monitoring system initialization script
echo "Initializing monitoring system..."

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
trap 'echo -e "${RED}Initialization failed${NC}"; exit 1' ERR

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"

    # Check Python version
    python3 --version || {
        echo -e "${RED}Python 3 is required${NC}"
        exit 1
    }

    # Check Redis
    redis-cli ping || {
        echo -e "${RED}Redis is required${NC}"
        exit 1
    }

    # Check PostgreSQL
    psql --version || {
        echo -e "${RED}PostgreSQL is required${NC}"
        exit 1
    }

    echo -e "${GREEN}Prerequisites check passed${NC}"
}

# Function to create directories
create_directories() {
    echo -e "${YELLOW}Creating directories...${NC}"

    # Create main directories
    mkdir -p $MONITORING_DIR/{data,cache,archive}
    mkdir -p $LOG_DIR/{metrics,alerts,system}
    mkdir -p $BACKUP_DIR/{daily,weekly,monthly}

    # Set permissions
    chown -R www-data:www-data $MONITORING_DIR $LOG_DIR $BACKUP_DIR
    chmod -R 755 $MONITORING_DIR $LOG_DIR $BACKUP_DIR

    echo -e "${GREEN}Directories created${NC}"
}

# Function to setup virtual environment
setup_venv() {
    echo -e "${YELLOW}Setting up virtual environment...${NC}"

    # Create virtual environment
    python3 -m venv $VENV_DIR

    # Activate virtual environment
    source $VENV_DIR/bin/activate

    # Install requirements
    pip install -r requirements.txt

    echo -e "${GREEN}Virtual environment setup complete${NC}"
}

# Function to setup database
setup_database() {
    echo -e "${YELLOW}Setting up database...${NC}"

    # Run migrations
    python manage.py migrate

    # Initialize monitoring tables
    python manage.py init_monitoring --create-db

    echo -e "${GREEN}Database setup complete${NC}"
}

# Function to setup monitoring service
setup_service() {
    echo -e "${YELLOW}Setting up monitoring service...${NC}"

    # Create service file
    cat > /etc/systemd/system/terminusa-monitoring.service << EOL
[Unit]
Description=Terminusa Monitoring Service
After=network.target redis-server.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/terminusa
Environment="PATH=/var/www/terminusa/venv/bin"
ExecStart=/var/www/terminusa/venv/bin/python -m game_systems.monitoring_init
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOL

    # Reload systemd
    systemctl daemon-reload

    # Enable and start service
    systemctl enable terminusa-monitoring
    systemctl start terminusa-monitoring

    echo -e "${GREEN}Service setup complete${NC}"
}

# Function to setup logging
setup_logging() {
    echo -e "${YELLOW}Setting up logging...${NC}"

    # Create log rotation config
    cat > /etc/logrotate.d/terminusa-monitoring << EOL
/var/log/terminusa/monitoring/*/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload terminusa-monitoring >/dev/null 2>&1 || true
    endscript
}
EOL

    echo -e "${GREEN}Logging setup complete${NC}"
}

# Function to setup monitoring configuration
setup_config() {
    echo -e "${YELLOW}Setting up monitoring configuration...${NC}"

    # Copy configuration files
    cp config/monitoring_config.py $MONITORING_DIR/config.py
    cp config/monitoring.py $MONITORING_DIR/settings.py

    # Create environment file
    cat > $MONITORING_DIR/.env << EOL
MONITORING_ENABLED=true
MONITORING_LOG_LEVEL=INFO
REDIS_HOST=localhost
REDIS_PORT=6379
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
EOL

    echo -e "${GREEN}Configuration setup complete${NC}"
}

# Function to setup cron jobs
setup_cron() {
    echo -e "${YELLOW}Setting up cron jobs...${NC}"

    # Create cron file
    cat > /etc/cron.d/terminusa-monitoring << EOL
# Metric collection
*/5 * * * * www-data /var/www/terminusa/venv/bin/python manage.py manage_monitoring collect-metrics
0 * * * * www-data /var/www/terminusa/venv/bin/python manage.py manage_monitoring aggregate-metrics

# Backups
0 1 * * * www-data /var/www/terminusa/venv/bin/python manage.py backup_monitoring --type=full
0 2 * * 0 www-data /var/www/terminusa/venv/bin/python manage.py backup_monitoring --type=full --destination=weekly
0 3 1 * * www-data /var/www/terminusa/venv/bin/python manage.py backup_monitoring --type=full --destination=monthly

# Maintenance
0 4 * * * www-data /var/www/terminusa/venv/bin/python manage.py manage_monitoring cleanup
0 5 * * * www-data /var/www/terminusa/venv/bin/python manage.py manage_monitoring optimize
EOL

    echo -e "${GREEN}Cron jobs setup complete${NC}"
}

# Function to verify setup
verify_setup() {
    echo -e "${YELLOW}Verifying setup...${NC}"

    # Check service status
    systemctl is-active --quiet terminusa-monitoring && \
        echo -e "${GREEN}Service is running${NC}" || \
        echo -e "${RED}Service is not running${NC}"

    # Check database
    python manage.py manage_monitoring check-db && \
        echo -e "${GREEN}Database check passed${NC}" || \
        echo -e "${RED}Database check failed${NC}"

    # Check Redis
    python manage.py manage_monitoring check-redis && \
        echo -e "${GREEN}Redis check passed${NC}" || \
        echo -e "${RED}Redis check failed${NC}"

    # Check metrics collection
    python manage.py manage_monitoring check-metrics && \
        echo -e "${GREEN}Metrics check passed${NC}" || \
        echo -e "${RED}Metrics check failed${NC}"

    echo -e "${GREEN}Setup verification complete${NC}"
}

# Main initialization process
main() {
    echo -e "${YELLOW}Starting monitoring system initialization...${NC}"

    # Run initialization steps
    check_prerequisites
    create_directories
    setup_venv
    setup_database
    setup_service
    setup_logging
    setup_config
    setup_cron
    verify_setup

    echo -e "${GREEN}Monitoring system initialization complete!${NC}"
    echo -e "\nNext steps:"
    echo "1. Review configuration in $MONITORING_DIR/config.py"
    echo "2. Update environment variables in $MONITORING_DIR/.env"
    echo "3. Access monitoring dashboard at: https://terminusa.online/admin/monitoring"
    echo "4. Check logs in: $LOG_DIR"
}

# Execute main function
main
