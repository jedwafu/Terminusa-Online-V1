# Terminusa Online Monitoring Troubleshooting Guide

## Quick Diagnostics

### Check System Status
```bash
# Check all services
systemctl status terminusa-monitoring
systemctl status redis
systemctl status postgresql

# Check logs
tail -f /var/log/terminusa/monitoring/*.log

# Check resources
python manage.py manage_monitoring check-resources
```

### Common Issues and Solutions

## 1. Service Not Starting

### Symptoms
- Service fails to start
- `systemctl status terminusa-monitoring` shows failed state
- No monitoring data available

### Solutions

1. **Check Permissions**
```bash
# Fix directory permissions
chown -R www-data:www-data /var/www/terminusa/monitoring
chmod -R 755 /var/www/terminusa/monitoring

# Fix log permissions
chown -R www-data:www-data /var/log/terminusa/monitoring
chmod -R 755 /var/log/terminusa/monitoring
```

2. **Check Configuration**
```bash
# Verify config file
python manage.py manage_monitoring verify-config

# Reset configuration if needed
python manage.py manage_monitoring reset-config
```

3. **Check Dependencies**
```bash
# Verify Python packages
source /var/www/terminusa/venv/bin/activate
pip install -r requirements-monitoring.txt

# Check system dependencies
apt-get install -y redis-server postgresql nginx
```

## 2. Database Connection Issues

### Symptoms
- Database errors in logs
- Monitoring data not being stored
- "Connection refused" errors

### Solutions

1. **Check Database Service**
```bash
# Check PostgreSQL status
systemctl status postgresql

# Check database connection
python manage.py manage_monitoring check-db
```

2. **Reset Database Connection**
```bash
# Restart PostgreSQL
systemctl restart postgresql

# Clear connection pool
python manage.py manage_monitoring clear-connections
```

3. **Verify Database Settings**
```bash
# Check database configuration
python manage.py manage_monitoring show-config database

# Reset database if needed
python manage.py manage_monitoring reset-db
```

## 3. Redis Cache Issues

### Symptoms
- Slow monitoring performance
- Cache misses
- Memory warnings

### Solutions

1. **Check Redis Status**
```bash
# Check Redis service
systemctl status redis

# Check Redis memory
redis-cli info memory

# Clear Redis cache
redis-cli FLUSHDB
```

2. **Optimize Redis**
```bash
# Set memory limit
redis-cli CONFIG SET maxmemory 1gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Enable persistence
redis-cli CONFIG SET appendonly yes
```

3. **Monitor Redis Performance**
```bash
# Watch Redis metrics
redis-cli monitor

# Check slow operations
redis-cli slowlog get
```

## 4. Metric Collection Issues

### Symptoms
- Missing metrics
- Incomplete data
- Collection errors

### Solutions

1. **Check Collector Status**
```bash
# Verify metric collection
python manage.py manage_monitoring check-metrics

# Reset metric collector
python manage.py manage_monitoring reset-collector
```

2. **Clear Metric Cache**
```bash
# Clear metric cache
python manage.py manage_monitoring clear-metrics

# Restart collection
python manage.py manage_monitoring restart-collector
```

3. **Debug Collection**
```bash
# Enable debug logging
python manage.py manage_monitoring set-log-level DEBUG

# Watch metric collection
tail -f /var/log/terminusa/monitoring/metrics.log
```

## 5. Alert System Issues

### Symptoms
- Missing alerts
- Delayed notifications
- Alert spam

### Solutions

1. **Check Alert Configuration**
```bash
# Verify alert settings
python manage.py manage_monitoring show-config alerts

# Test alert system
python manage.py manage_monitoring test-alerts
```

2. **Reset Alert System**
```bash
# Clear alert queue
python manage.py manage_monitoring clear-alerts

# Reset alert configuration
python manage.py manage_monitoring reset-alerts
```

3. **Debug Notifications**
```bash
# Check notification channels
python manage.py manage_monitoring check-notifications

# Test specific channels
python manage.py manage_monitoring test-notification-channel email
python manage.py manage_monitoring test-notification-channel slack
```

## 6. WebSocket Connection Issues

### Symptoms
- Dashboard not updating
- Real-time data missing
- Connection errors

### Solutions

1. **Check WebSocket Service**
```bash
# Verify WebSocket status
python manage.py manage_monitoring check-websocket

# Reset WebSocket connections
python manage.py manage_monitoring reset-websocket
```

2. **Debug Connections**
```bash
# Monitor WebSocket traffic
python manage.py manage_monitoring monitor-websocket

# Check connection logs
tail -f /var/log/terminusa/monitoring/websocket.log
```

## 7. Performance Issues

### Symptoms
- High CPU usage
- Memory leaks
- Slow response times

### Solutions

1. **Check Resource Usage**
```bash
# Monitor system resources
top -c -p $(pgrep -d',' -f terminusa)

# Check memory usage
python manage.py manage_monitoring check-memory
```

2. **Optimize Performance**
```bash
# Clear caches
python manage.py manage_monitoring clear-cache

# Optimize database
python manage.py manage_monitoring optimize-db
```

3. **Debug Performance**
```bash
# Enable performance logging
python manage.py manage_monitoring enable-performance-logging

# Generate performance report
python manage.py manage_monitoring performance-report
```

## 8. Backup and Recovery Issues

### Symptoms
- Failed backups
- Corrupted backups
- Recovery errors

### Solutions

1. **Check Backup Status**
```bash
# Verify backup system
python manage.py manage_monitoring check-backups

# List available backups
python manage.py manage_monitoring list-backups
```

2. **Test Backup/Restore**
```bash
# Create test backup
python manage.py backup_monitoring --type=test

# Test restore process
python manage.py restore_monitoring --dry-run
```

## Emergency Recovery

### Complete System Reset
```bash
# Stop services
systemctl stop terminusa-monitoring

# Backup current data
./scripts/backup_monitoring.sh

# Reset system
./scripts/cleanup_monitoring.sh
./scripts/init_monitoring.sh

# Restore from backup
python manage.py restore_monitoring
```

### Emergency Contacts

- System Administrator: admin@terminusa.online
- Emergency Support: +1-XXX-XXX-XXXX
- Slack Channel: #monitoring-emergency

## Preventive Maintenance

### Daily Checks
```bash
# Check system health
python manage.py manage_monitoring check

# Review alerts
python manage.py manage_monitoring show-alerts

# Verify backups
python manage.py manage_monitoring verify-backups
```

### Weekly Maintenance
```bash
# Clean old data
./scripts/cleanup_monitoring.sh

# Optimize storage
python manage.py manage_monitoring optimize

# Test recovery
python manage.py manage_monitoring test-recovery
```

### Monthly Review
```bash
# Generate system report
python manage.py manage_monitoring report

# Review performance
python manage.py manage_monitoring analyze-performance

# Update configuration
python manage.py manage_monitoring update-config
```

## Logging Reference

### Log Locations
- Application: `/var/log/terminusa/monitoring/app.log`
- Metrics: `/var/log/terminusa/monitoring/metrics.log`
- Alerts: `/var/log/terminusa/monitoring/alerts.log`
- WebSocket: `/var/log/terminusa/monitoring/websocket.log`
- System: `/var/log/terminusa/monitoring/system.log`

### Log Levels
- ERROR: Critical issues requiring immediate attention
- WARNING: Important issues that need investigation
- INFO: Normal operational information
- DEBUG: Detailed debugging information

## Configuration Reference

### Key Files
- Main Config: `config/monitoring_config.py`
- Environment: `/var/www/terminusa/monitoring/.env`
- Service: `/etc/systemd/system/terminusa-monitoring.service`
- Nginx: `/etc/nginx/conf.d/terminusa-monitoring.conf`

### Important Directories
- Monitoring: `/var/www/terminusa/monitoring`
- Logs: `/var/log/terminusa/monitoring`
- Backups: `/var/www/backups/monitoring`
- Data: `/var/www/terminusa/monitoring/data`

## Support Resources

### Documentation
- Setup Guide: `/docs/monitoring_setup.md`
- API Reference: `/docs/monitoring_api.md`
- Quick Reference: `/docs/monitoring_quickref.md`

### Tools
- Dashboard: https://terminusa.online/admin/monitoring
- Health Check: https://terminusa.online/health
- API: https://terminusa.online/api/monitoring

### Community
- GitHub Issues: https://github.com/terminusa/monitoring/issues
- Discord: #monitoring-support
- Wiki: https://wiki.terminusa.online/monitoring
