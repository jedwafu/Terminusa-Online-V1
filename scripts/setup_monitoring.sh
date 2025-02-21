#!/bin/bash

# Monitoring system setup script
echo "Setting up monitoring system..."

# Configuration
LOG_DIR="/var/log/terminusa"
MONITORING_DIR="/var/www/terminusa/monitoring"
BACKUP_DIR="/var/www/backups"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Error handling
set -e
trap 'echo -e "${RED}Setup failed${NC}"; exit 1' ERR

# Create required directories
echo -e "${YELLOW}Creating required directories...${NC}"
mkdir -p $LOG_DIR/monitoring
mkdir -p $MONITORING_DIR/data
mkdir -p $BACKUP_DIR

# Set permissions
echo -e "${YELLOW}Setting permissions...${NC}"
chown -R www-data:www-data $LOG_DIR
chmod -R 755 $LOG_DIR
chown -R www-data:www-data $MONITORING_DIR
chmod -R 755 $MONITORING_DIR

# Configure monitoring service
echo -e "${YELLOW}Configuring monitoring service...${NC}"
cat > /etc/systemd/system/terminusa-monitoring.service << EOL
[Unit]
Description=Terminusa Monitoring Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/terminusa
Environment="PATH=/var/www/terminusa/venv/bin"
ExecStart=/var/www/terminusa/venv/bin/python -m game_systems.monitoring_init
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# Configure log rotation
echo -e "${YELLOW}Configuring log rotation...${NC}"
cat > /etc/logrotate.d/terminusa-monitoring << EOL
/var/log/terminusa/monitoring/*.log {
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

# Initialize monitoring database
echo -e "${YELLOW}Initializing monitoring database...${NC}"
python manage.py migrate monitoring

# Configure monitoring settings
echo -e "${YELLOW}Configuring monitoring settings...${NC}"
cat > $MONITORING_DIR/config.json << EOL
{
    "email": {
        "enabled": true,
        "from": "monitoring@terminusa.online",
        "recipients": ["admin@terminusa.online"]
    },
    "slack": {
        "enabled": true,
        "webhook_url": "${SLACK_WEBHOOK_URL}",
        "channel": "#monitoring"
    },
    "metrics": {
        "collection_interval": 60,
        "retention_days": {
            "raw": 1,
            "hourly": 7,
            "daily": 30
        }
    },
    "alerts": {
        "throttling": {
            "default": 300,
            "critical": 60
        }
    }
}
EOL

# Setup monitoring cron jobs
echo -e "${YELLOW}Setting up monitoring cron jobs...${NC}"
cat > /etc/cron.d/terminusa-monitoring << EOL
# Metric cleanup
0 0 * * * www-data /var/www/terminusa/venv/bin/python manage.py cleanup_metrics

# Backup monitoring data
0 1 * * * www-data /var/www/terminusa/venv/bin/python manage.py backup_monitoring_data

# Check monitoring system
*/5 * * * * www-data /var/www/terminusa/venv/bin/python manage.py check_monitoring_health
EOL

# Reload systemd
echo -e "${YELLOW}Reloading systemd...${NC}"
systemctl daemon-reload

# Enable and start monitoring service
echo -e "${YELLOW}Starting monitoring service...${NC}"
systemctl enable terminusa-monitoring
systemctl start terminusa-monitoring

# Verify monitoring setup
echo -e "${YELLOW}Verifying monitoring setup...${NC}"
if systemctl is-active --quiet terminusa-monitoring; then
    echo -e "${GREEN}Monitoring service is running${NC}"
else
    echo -e "${RED}Monitoring service failed to start${NC}"
    exit 1
fi

# Check monitoring endpoints
echo -e "${YELLOW}Checking monitoring endpoints...${NC}"
curl -s https://terminusa.online/health | grep -q "ok" && \
    echo -e "${GREEN}Health check endpoint is responding${NC}" || \
    echo -e "${RED}Health check endpoint failed${NC}"

curl -s https://terminusa.online/api/monitoring/metrics -H "Authorization: Bearer ${ADMIN_TOKEN}" | grep -q "success" && \
    echo -e "${GREEN}Metrics endpoint is responding${NC}" || \
    echo -e "${RED}Metrics endpoint failed${NC}"

# Setup monitoring dashboard
echo -e "${YELLOW}Setting up monitoring dashboard...${NC}"
python manage.py collectstatic --noinput
python manage.py compress --force

# Initialize alert templates
echo -e "${YELLOW}Initializing alert templates...${NC}"
python manage.py init_alert_templates

echo -e "${GREEN}Monitoring setup completed successfully!${NC}"
echo -e "\nMonitoring Dashboard: https://terminusa.online/admin/monitoring"
echo -e "Log Directory: $LOG_DIR/monitoring"
echo -e "Configuration: $MONITORING_DIR/config.json"

# Print monitoring commands
echo -e "\n${YELLOW}Useful Commands:${NC}"
echo "View monitoring logs: tail -f $LOG_DIR/monitoring/monitoring.log"
echo "Check service status: systemctl status terminusa-monitoring"
echo "Restart monitoring: systemctl restart terminusa-monitoring"
echo "View metrics: curl -H 'Authorization: Bearer \${ADMIN_TOKEN}' https://terminusa.online/api/monitoring/metrics"
