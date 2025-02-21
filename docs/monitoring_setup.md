# Terminusa Online Monitoring System Setup Guide

## Quick Start

```bash
# Initialize monitoring system
./scripts/setup_monitoring.sh

# Apply enhancements
./scripts/monitoring_enhancements.sh

# Verify setup
python manage.py manage_monitoring check
```

## System Requirements

- Ubuntu 20.04 or later
- Python 3.8+
- Redis 6.0+
- PostgreSQL 12+
- 2GB RAM minimum
- 20GB disk space

## Installation Steps

1. **Base Setup**
```bash
# Create required directories
mkdir -p /var/www/terminusa/monitoring
mkdir -p /var/log/terminusa/monitoring
mkdir -p /var/www/backups/monitoring

# Set permissions
chown -R www-data:www-data /var/www/terminusa/monitoring
chmod -R 755 /var/www/terminusa/monitoring
```

2. **Dependencies**
```bash
# System packages
apt-get update
apt-get install -y redis-server postgresql nginx

# Python packages
pip install -r requirements.txt
```

3. **Database Setup**
```bash
# Create monitoring database
python manage.py init_monitoring --create-db

# Run migrations
python manage.py migrate
```

4. **Service Configuration**
```bash
# Copy service files
cp terminusa-monitoring.service /etc/systemd/system/
systemctl daemon-reload

# Start services
systemctl enable terminusa-monitoring
systemctl start terminusa-monitoring
```

## Configuration

### Environment Variables

```ini
# .env
MONITORING_ENABLED=true
MONITORING_LOG_LEVEL=INFO
REDIS_HOST=localhost
REDIS_PORT=6379
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
```

### Monitoring Settings

```python
# config/monitoring.py
METRIC_CONFIG = {
    'collection_interval': 60,
    'retention_periods': {
        'raw': '1d',
        'hourly': '7d',
        'daily': '30d'
    }
}

ALERT_CONFIG = {
    'channels': {
        'email': {'enabled': True},
        'slack': {'enabled': True},
        'websocket': {'enabled': True}
    }
}
```

## Management Commands

### Basic Operations

```bash
# Check status
python manage.py manage_monitoring status

# Start/stop services
python manage.py manage_monitoring start
python manage.py manage_monitoring stop

# Create backup
python manage.py backup_monitoring

# Restore from backup
python manage.py restore_monitoring
```

### Maintenance

```bash
# Cleanup old data
python manage.py manage_monitoring cleanup --days=30

# Optimize storage
python manage.py manage_monitoring optimize-storage

# Test alerts
python manage.py manage_monitoring test-alerts
```

## Monitoring Dashboard

### Access

- URL: https://terminusa.online/admin/monitoring
- Authentication: Admin API key required

### Features

1. System Overview
   - Resource usage
   - Service status
   - Performance metrics

2. Game Metrics
   - Player activity
   - Transaction rates
   - System health

3. Alert Management
   - Active alerts
   - Alert history
   - Alert configuration

## Alert System

### Alert Levels

1. Critical
   - Immediate action required
   - All channels notified
   - Auto-escalation

2. Warning
   - Action needed soon
   - Standard notification
   - No escalation

3. Info
   - Informational only
   - Dashboard only

### Alert Channels

1. Email
   - Critical and warning alerts
   - HTML formatted
   - Configurable recipients

2. Slack
   - All alert levels
   - Rich formatting
   - Channel integration

3. WebSocket
   - Real-time updates
   - Dashboard integration
   - Interactive alerts

## Backup System

### Backup Types

1. Full Backup
   ```bash
   python manage.py backup_monitoring --type=full
   ```

2. Partial Backup
   ```bash
   python manage.py backup_monitoring --type=metrics
   python manage.py backup_monitoring --type=alerts
   ```

### Backup Schedule

- Daily: Metrics and alerts
- Weekly: Full system backup
- Monthly: Archive backup

## Performance Optimization

### Metric Storage

- Raw data: 24 hours
- Hourly aggregates: 7 days
- Daily aggregates: 30 days

### Caching

- Metric caching
- Alert caching
- Dashboard caching

### Compression

- Metric compression
- Log compression
- Backup compression

## Security

### Access Control

- Admin API key
- IP restrictions
- Role-based access

### Data Protection

- Encrypted connections
- Secure storage
- Regular backups

## Maintenance

### Regular Tasks

1. Daily
   - Check alerts
   - Review metrics
   - Verify backups

2. Weekly
   - Clean old data
   - Optimize storage
   - Check performance

3. Monthly
   - Full backup
   - System review
   - Update configuration

### Troubleshooting

1. Service Issues
   ```bash
   # Check service status
   systemctl status terminusa-monitoring

   # View logs
   tail -f /var/log/terminusa/monitoring/monitoring.log
   ```

2. Database Issues
   ```bash
   # Check connections
   python manage.py manage_monitoring check-db

   # Repair database
   python manage.py manage_monitoring repair-db
   ```

3. Alert Issues
   ```bash
   # Test alerts
   python manage.py manage_monitoring test-alerts

   # Clear alert queue
   python manage.py manage_monitoring clear-alerts
   ```

## Best Practices

1. Monitoring
   - Regular dashboard checks
   - Alert review
   - Performance monitoring

2. Maintenance
   - Regular backups
   - Log rotation
   - Data cleanup

3. Security
   - Access control
   - Data protection
   - Regular audits

## Support

- Documentation: /docs/monitoring_guide.md
- Email: admin@terminusa.online
- Slack: #monitoring-support
