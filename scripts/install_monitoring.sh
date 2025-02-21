#!/bin/bash

# Monitoring system installation script
echo "Installing monitoring system..."

# Configuration
VENV_DIR="/var/www/terminusa/venv"
MONITORING_DIR="/var/www/terminusa/monitoring"
LOG_DIR="/var/log/terminusa/monitoring"
BACKUP_DIR="/var/www/backups/monitoring"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Error handling
set -e
trap 'echo -e "${RED}Installation failed${NC}"; exit 1' ERR

# Function to check system requirements
check_requirements() {
    echo -e "${YELLOW}Checking system requirements...${NC}"

    # Check Python version
    python3 --version | grep "Python 3.[89]" || {
        echo -e "${RED}Python 3.8 or higher is required${NC}"
        exit 1
    }

    # Check pip
    python3 -m pip --version || {
        echo -e "${RED}pip is required${NC}"
        exit 1
    }

    # Check system packages
    for pkg in redis-server postgresql nginx; do
        dpkg -l | grep -q $pkg || {
            echo -e "${RED}$pkg is required${NC}"
            exit 1
        }
    }

    echo -e "${GREEN}System requirements check passed${NC}"
}

# Function to install system dependencies
install_system_deps() {
    echo -e "${YELLOW}Installing system dependencies...${NC}"

    # Update package list
    apt-get update

    # Install required packages
    apt-get install -y \
        python3-dev \
        python3-pip \
        python3-venv \
        redis-server \
        postgresql \
        postgresql-contrib \
        nginx \
        supervisor \
        build-essential \
        libpq-dev \
        git \
        curl \
        jq

    echo -e "${GREEN}System dependencies installed${NC}"
}

# Function to setup Python virtual environment
setup_venv() {
    echo -e "${YELLOW}Setting up virtual environment...${NC}"

    # Create virtual environment
    python3 -m venv $VENV_DIR

    # Activate virtual environment
    source $VENV_DIR/bin/activate

    # Upgrade pip
    pip install --upgrade pip setuptools wheel

    # Install monitoring requirements
    pip install -r requirements-monitoring.txt

    echo -e "${GREEN}Virtual environment setup complete${NC}"
}

# Function to setup monitoring directories
setup_directories() {
    echo -e "${YELLOW}Setting up monitoring directories...${NC}"

    # Create directories
    mkdir -p $MONITORING_DIR/{data,cache,archive}
    mkdir -p $LOG_DIR/{metrics,alerts,system}
    mkdir -p $BACKUP_DIR/{daily,weekly,monthly}

    # Set permissions
    chown -R www-data:www-data $MONITORING_DIR $LOG_DIR $BACKUP_DIR
    chmod -R 755 $MONITORING_DIR $LOG_DIR $BACKUP_DIR

    echo -e "${GREEN}Directories setup complete${NC}"
}

# Function to setup monitoring database
setup_database() {
    echo -e "${YELLOW}Setting up monitoring database...${NC}"

    # Create database and user
    sudo -u postgres psql << EOF
CREATE DATABASE terminusa_monitoring;
CREATE USER terminusa_monitor WITH PASSWORD '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE terminusa_monitoring TO terminusa_monitor;
\c terminusa_monitoring
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
EOF

    # Run migrations
    source $VENV_DIR/bin/activate
    python manage.py migrate

    echo -e "${GREEN}Database setup complete${NC}"
}

# Function to setup Redis
setup_redis() {
    echo -e "${YELLOW}Setting up Redis...${NC}"

    # Backup original Redis config
    cp /etc/redis/redis.conf /etc/redis/redis.conf.bak

    # Configure Redis
    cat > /etc/redis/redis.conf << EOF
bind 127.0.0.1
port 6379
maxmemory 1gb
maxmemory-policy allkeys-lru
appendonly yes
appendfsync everysec
save 900 1
save 300 10
save 60 10000
EOF

    # Restart Redis
    systemctl restart redis-server

    echo -e "${GREEN}Redis setup complete${NC}"
}

# Function to setup monitoring service
setup_service() {
    echo -e "${YELLOW}Setting up monitoring service...${NC}"

    # Create systemd service
    cat > /etc/systemd/system/terminusa-monitoring.service << EOF
[Unit]
Description=Terminusa Monitoring Service
After=network.target redis-server.service postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/terminusa
Environment="PATH=/var/www/terminusa/venv/bin"
Environment="PYTHONPATH=/var/www/terminusa"
ExecStart=/var/www/terminusa/venv/bin/python -m game_systems.monitoring_init
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

    # Create supervisor config
    cat > /etc/supervisor/conf.d/terminusa-monitoring.conf << EOF
[program:terminusa-monitoring]
command=/var/www/terminusa/venv/bin/python -m game_systems.monitoring_init
directory=/var/www/terminusa
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/terminusa/monitoring/supervisor.err.log
stdout_logfile=/var/log/terminusa/monitoring/supervisor.out.log
EOF

    # Reload systemd and supervisor
    systemctl daemon-reload
    supervisorctl reread
    supervisorctl update

    echo -e "${GREEN}Service setup complete${NC}"
}

# Function to setup monitoring configuration
setup_config() {
    echo -e "${YELLOW}Setting up monitoring configuration...${NC}"

    # Create monitoring config
    cp config/monitoring_config.py $MONITORING_DIR/config.py

    # Create environment file
    cat > $MONITORING_DIR/.env << EOF
MONITORING_ENABLED=true
MONITORING_LOG_LEVEL=INFO
REDIS_HOST=localhost
REDIS_PORT=6379
DB_NAME=terminusa_monitoring
DB_USER=terminusa_monitor
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST=${EMAIL_HOST}
EMAIL_PORT=${EMAIL_PORT}
EMAIL_USER=${EMAIL_USER}
EMAIL_PASSWORD=${EMAIL_PASSWORD}
SLACK_WEBHOOK_URL=${SLACK_WEBHOOK_URL}
EOF

    echo -e "${GREEN}Configuration setup complete${NC}"
}

# Function to setup monitoring cron jobs
setup_cron() {
    echo -e "${YELLOW}Setting up cron jobs...${NC}"

    # Create cron file
    cat > /etc/cron.d/terminusa-monitoring << EOF
# Metric collection
*/5 * * * * www-data /var/www/terminusa/venv/bin/python manage.py manage_monitoring collect-metrics
0 * * * * www-data /var/www/terminusa/venv/bin/python manage.py manage_monitoring aggregate-metrics

# Backups
0 1 * * * www-data /var/www/terminusa/venv/bin/python manage.py backup_monitoring --type=full
0 2 * * 0 www-data /var/www/terminusa/venv/bin/python manage.py backup_monitoring --type=full --destination=weekly
0 3 1 * * www-data /var/www/terminusa/venv/bin/python manage.py backup_monitoring --type=full --destination=monthly

# Maintenance
0 4 * * * www-data /var/www/terminusa/scripts/cleanup_monitoring.sh
0 5 * * * www-data /var/www/terminusa/venv/bin/python manage.py manage_monitoring optimize
EOF

    # Set permissions
    chmod 644 /etc/cron.d/terminusa-monitoring

    echo -e "${GREEN}Cron jobs setup complete${NC}"
}

# Function to verify installation
verify_installation() {
    echo -e "${YELLOW}Verifying installation...${NC}"

    # Check virtual environment
    test -d $VENV_DIR || {
        echo -e "${RED}Virtual environment not found${NC}"
        exit 1
    }

    # Check directories
    for dir in $MONITORING_DIR $LOG_DIR $BACKUP_DIR; do
        test -d $dir || {
            echo -e "${RED}Directory $dir not found${NC}"
            exit 1
        }
    }

    # Check database
    source $VENV_DIR/bin/activate
    python manage.py manage_monitoring check-db || {
        echo -e "${RED}Database check failed${NC}"
        exit 1
    }

    # Check Redis
    redis-cli ping | grep -q PONG || {
        echo -e "${RED}Redis check failed${NC}"
        exit 1
    }

    # Check service
    systemctl is-active --quiet terminusa-monitoring || {
        echo -e "${RED}Service check failed${NC}"
        exit 1
    }

    echo -e "${GREEN}Installation verification complete${NC}"
}

# Main installation process
main() {
    echo -e "${YELLOW}Starting monitoring system installation...${NC}"

    # Get configuration
    read -p "Enter database password: " DB_PASSWORD
    read -p "Enter email host: " EMAIL_HOST
    read -p "Enter email port: " EMAIL_PORT
    read -p "Enter email user: " EMAIL_USER
    read -p "Enter email password: " EMAIL_PASSWORD
    read -p "Enter Slack webhook URL: " SLACK_WEBHOOK_URL

    # Run installation steps
    check_requirements
    install_system_deps
    setup_venv
    setup_directories
    setup_database
    setup_redis
    setup_service
    setup_config
    setup_cron
    verify_installation

    echo -e "${GREEN}Monitoring system installation complete!${NC}"
    echo -e "\nNext steps:"
    echo "1. Review configuration in $MONITORING_DIR/config.py"
    echo "2. Update environment variables in $MONITORING_DIR/.env"
    echo "3. Initialize monitoring system: ./scripts/init_monitoring.sh"
    echo "4. Start monitoring service: systemctl start terminusa-monitoring"
    echo "5. Check monitoring dashboard: https://terminusa.online/admin/monitoring"
}

# Execute main function
main
