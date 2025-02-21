#!/bin/bash

# Monitoring system enhancements script
echo "Enhancing monitoring system..."

# Configuration
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
trap 'echo -e "${RED}Enhancement failed${NC}"; exit 1' ERR

# Function to enhance monitoring system
enhance_monitoring() {
    echo -e "${YELLOW}Applying monitoring enhancements...${NC}"

    # Create enhanced directory structure
    mkdir -p $MONITORING_DIR/{data,cache,archive}
    mkdir -p $LOG_DIR/{metrics,alerts,system}
    mkdir -p $BACKUP_DIR/{daily,weekly,monthly}

    # Set up log rotation with compression
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

    # Set up metric aggregation cron jobs
    cat > /etc/cron.d/terminusa-monitoring-enhanced << EOL
# Metric aggregation
*/5 * * * * www-data /var/www/terminusa/venv/bin/python manage.py manage_monitoring aggregate-metrics --window=5min
0 * * * * www-data /var/www/terminusa/venv/bin/python manage.py manage_monitoring aggregate-metrics --window=1hour
0 0 * * * www-data /var/www/terminusa/venv/bin/python manage.py manage_monitoring aggregate-metrics --window=1day

# Enhanced backups
0 1 * * * www-data /var/www/terminusa/venv/bin/python manage.py backup_monitoring --type=full --compress
0 2 * * 0 www-data /var/www/terminusa/venv/bin/python manage.py backup_monitoring --type=full --compress --destination=weekly
0 3 1 * * www-data /var/www/terminusa/venv/bin/python manage.py backup_monitoring --type=full --compress --destination=monthly

# System maintenance
0 4 * * * www-data /var/www/terminusa/venv/bin/python manage.py manage_monitoring cleanup --older-than=30d
0 5 * * * www-data /var/www/terminusa/venv/bin/python manage.py manage_monitoring optimize-storage

# Health checks
*/15 * * * * www-data /var/www/terminusa/venv/bin/python manage.py manage_monitoring check-health --notify
EOL

    # Configure Redis for better performance
    cat > /etc/redis/redis-monitoring.conf << EOL
# Redis configuration for monitoring
port 6380
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
EOL

    # Set up dedicated monitoring service
    cat > /etc/systemd/system/terminusa-monitoring-enhanced.service << EOL
[Unit]
Description=Terminusa Enhanced Monitoring Service
After=network.target redis-server.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/terminusa
Environment="PATH=/var/www/terminusa/venv/bin"
Environment="MONITORING_ENHANCED=true"
ExecStart=/var/www/terminusa/venv/bin/python -m game_systems.monitoring_init --enhanced
Restart=always
RestartSec=5
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOL

    # Set up monitoring dashboard nginx configuration
    cat > /etc/nginx/conf.d/terminusa-monitoring.conf << EOL
# Monitoring dashboard configuration
location /admin/monitoring {
    proxy_pass http://127.0.0.1:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host \$host;
    proxy_cache_bypass \$http_upgrade;
    proxy_buffering off;
    
    # Security headers
    add_header X-Frame-Options "DENY";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options "nosniff";
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline';";
    
    # Access control
    auth_request /auth/admin;
    error_page 401 = /admin/login;
}

# WebSocket endpoint for real-time monitoring
location /ws/monitoring {
    proxy_pass http://127.0.0.1:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
EOL

    # Set up monitoring cache configuration
    cat > $MONITORING_DIR/cache_config.json << EOL
{
    "metrics": {
        "ttl": 3600,
        "max_size": 1000000,
        "compression": true
    },
    "alerts": {
        "ttl": 86400,
        "max_size": 10000
    },
    "reports": {
        "ttl": 604800,
        "max_size": 1000
    }
}
EOL

    # Set up enhanced monitoring configuration
    cat > $MONITORING_DIR/enhanced_config.json << EOL
{
    "metric_collection": {
        "intervals": {
            "system": 60,
            "application": 30,
            "database": 300
        },
        "retention": {
            "raw": 86400,
            "hourly": 604800,
            "daily": 2592000
        },
        "aggregation": {
            "windows": ["5min", "1hour", "1day"],
            "functions": ["avg", "min", "max", "count"]
        }
    },
    "alerting": {
        "channels": {
            "email": {
                "enabled": true,
                "throttle": 300
            },
            "slack": {
                "enabled": true,
                "throttle": 300
            },
            "websocket": {
                "enabled": true,
                "throttle": 0
            }
        },
        "thresholds": {
            "cpu": {
                "warning": 80,
                "critical": 90
            },
            "memory": {
                "warning": 85,
                "critical": 95
            },
            "disk": {
                "warning": 85,
                "critical": 95
            }
        }
    },
    "optimization": {
        "compression": {
            "enabled": true,
            "algorithm": "gzip",
            "level": 6
        },
        "caching": {
            "enabled": true,
            "strategy": "lru",
            "max_size": "1GB"
        },
        "cleanup": {
            "enabled": true,
            "schedule": "daily",
            "retention": "30d"
        }
    }
}
EOL

    # Reload systemd and nginx
    systemctl daemon-reload
    systemctl reload nginx

    # Start enhanced monitoring service
    systemctl enable terminusa-monitoring-enhanced
    systemctl start terminusa-monitoring-enhanced

    echo -e "${GREEN}Monitoring enhancements completed!${NC}"
    echo -e "\nEnhanced features:"
    echo "- Improved metric collection and storage"
    echo "- Advanced alerting system"
    echo "- Better performance optimization"
    echo "- Enhanced backup system"
    echo "- Improved security"
    
    echo -e "\nNext steps:"
    echo "1. Review monitoring dashboard at: https://terminusa.online/admin/monitoring"
    echo "2. Check enhanced logs in: $LOG_DIR"
    echo "3. Verify backup system in: $BACKUP_DIR"
}

# Execute enhancements
enhance_monitoring
