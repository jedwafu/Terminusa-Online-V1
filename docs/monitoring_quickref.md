# Terminusa Online Monitoring Quick Reference

## Common Commands

### Service Management
```bash
# Start monitoring
systemctl start terminusa-monitoring

# Stop monitoring
systemctl stop terminusa-monitoring

# Restart monitoring
systemctl restart terminusa-monitoring

# Check status
systemctl status terminusa-monitoring
```

### Monitoring Management
```bash
# Initialize monitoring
./scripts/init_monitoring.sh

# Apply enhancements
./scripts/monitoring_enhancements.sh

# Run cleanup
./scripts/cleanup_monitoring.sh

# Check system health
python manage.py manage_monitoring check
```

### Backup Operations
```bash
# Create full backup
python manage.py backup_monitoring --type=full

# Create specific backup
python manage.py backup_monitoring --type=metrics
python manage.py backup_monitoring --type=alerts
python manage.py backup_monitoring --type=config

# Restore from backup
python manage.py restore_monitoring --backup-dir=/path/to/backup
```

## Quick Health Checks

### System Health
```bash
# Check all services
python manage.py manage_monitoring status

# Check specific component
python manage.py manage_monitoring check-component [system|database|cache]

# View recent alerts
python manage.py manage_monitoring show-alerts --last=24h
```

### Log Locations
```
Application Logs: /var/log/terminusa/monitoring/app.log
Alert Logs:      /var/log/terminusa/monitoring/alerts.log
Metric Logs:     /var/log/terminusa/monitoring/metrics.log
System Logs:     /var/log/terminusa/monitoring/system.log
```

### Configuration Files
```
Main Config:     config/monitoring_config.py
Alert Config:    config/monitoring.py
Service Config:  /etc/systemd/system/terminusa-monitoring.service
Nginx Config:    /etc/nginx/conf.d/terminusa-monitoring.conf
```

## Common Issues & Solutions

### High CPU Usage
```bash
# Check system resources
python manage.py manage_monitoring check-resources

# View top processes
top -c -p $(pgrep -d',' -f terminusa)

# Restart if needed
systemctl restart terminusa-monitoring
```

### Memory Issues
```bash
# Check memory usage
python manage.py manage_monitoring check-memory

# Clear cache
python manage.py manage_monitoring clear-cache

# Clean old data
./scripts/cleanup_monitoring.sh
```

### Database Issues
```bash
# Check connections
python manage.py manage_monitoring check-db

# View slow queries
python manage.py manage_monitoring show-slow-queries

# Optimize database
python manage.py manage_monitoring optimize-db
```

### Alert System Issues
```bash
# Test alerts
python manage.py manage_monitoring test-alerts

# Clear alert queue
python manage.py manage_monitoring clear-alerts

# Reset alert configuration
python manage.py manage_monitoring reset-alerts
```

## Monitoring Dashboard

### Access
```
URL: https://terminusa.online/admin/monitoring
Auth: Admin API key required
```

### Common Views
- System Overview: `/admin/monitoring/`
- Alert Management: `/admin/monitoring/alerts`
- Metric Explorer: `/admin/monitoring/metrics`
- Performance: `/admin/monitoring/performance`

## Alert Levels

### Critical Alerts
- Immediate action required
- All channels notified
- Auto-escalation after 5 minutes
- Example: Service down, Database unreachable

### Warning Alerts
- Action needed soon
- Standard notification
- No auto-escalation
- Example: High CPU usage, Low disk space

### Info Alerts
- Informational only
- Dashboard display only
- No notifications
- Example: Service restart, Backup completed

## Metric Types

### System Metrics
- CPU Usage
- Memory Usage
- Disk Space
- Network Traffic

### Application Metrics
- Response Time
- Error Rate
- Active Users
- Transaction Rate

### Database Metrics
- Query Performance
- Connection Count
- Cache Hit Ratio
- Table Size

## Maintenance Tasks

### Daily
```bash
# Check system health
python manage.py manage_monitoring check

# Review alerts
python manage.py manage_monitoring show-alerts

# Verify backups
python manage.py manage_monitoring verify-backups
```

### Weekly
```bash
# Clean old data
./scripts/cleanup_monitoring.sh

# Optimize storage
python manage.py manage_monitoring optimize

# Full backup
python manage.py backup_monitoring --type=full
```

### Monthly
```bash
# System review
python manage.py manage_monitoring report

# Performance optimization
python manage.py manage_monitoring optimize-all

# Configuration review
python manage.py manage_monitoring verify-config
```

## Emergency Procedures

### Service Recovery
1. Check logs: `tail -f /var/log/terminusa/monitoring/*.log`
2. Stop service: `systemctl stop terminusa-monitoring`
3. Clear temporary files: `rm -rf /var/www/terminusa/monitoring/tmp/*`
4. Start service: `systemctl start terminusa-monitoring`
5. Verify: `python manage.py manage_monitoring check`

### Data Recovery
1. Stop service: `systemctl stop terminusa-monitoring`
2. Backup current data: `./scripts/backup_monitoring.sh`
3. Restore from backup: `python manage.py restore_monitoring`
4. Verify data: `python manage.py manage_monitoring verify-data`
5. Start service: `systemctl start terminusa-monitoring`

### Alert Recovery
1. Stop alerts: `python manage.py manage_monitoring pause-alerts`
2. Clear queue: `python manage.py manage_monitoring clear-alerts`
3. Reset config: `python manage.py manage_monitoring reset-alerts`
4. Test alerts: `python manage.py manage_monitoring test-alerts`
5. Resume alerts: `python manage.py manage_monitoring resume-alerts`

## Support Resources

### Documentation
- Full Guide: `/docs/monitoring_guide.md`
- Setup Guide: `/docs/monitoring_setup.md`
- API Reference: `/docs/monitoring_api.md`

### Contact
- Email: admin@terminusa.online
- Slack: #monitoring-support
- Emergency: On-call support

### Tools
- Dashboard: https://terminusa.online/admin/monitoring
- Logs: `/var/log/terminusa/monitoring/`
- Scripts: `/scripts/`
