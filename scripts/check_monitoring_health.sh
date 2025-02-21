#!/bin/bash

# Monitoring system health check script
echo "Checking monitoring system health..."

# Configuration
MONITORING_DIR="/var/www/terminusa/monitoring"
LOG_DIR="/var/log/terminusa/monitoring"
VENV_DIR="/var/www/terminusa/venv"
REPORT_FILE="$LOG_DIR/health_report_$(date +%Y%m%d_%H%M%S).txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Error handling
set -e
trap 'echo -e "${RED}Health check failed${NC}"; exit 1' ERR

# Function to check system resources
check_resources() {
    echo -e "${YELLOW}Checking system resources...${NC}"
    
    # CPU Usage
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d. -f1)
    if [ $CPU_USAGE -gt 80 ]; then
        echo -e "${RED}High CPU usage: $CPU_USAGE%${NC}"
    else
        echo -e "${GREEN}CPU usage normal: $CPU_USAGE%${NC}"
    fi
    
    # Memory Usage
    MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
    if [ $MEM_USAGE -gt 85 ]; then
        echo -e "${RED}High memory usage: $MEM_USAGE%${NC}"
    else
        echo -e "${GREEN}Memory usage normal: $MEM_USAGE%${NC}"
    fi
    
    # Disk Usage
    DISK_USAGE=$(df -h / | awk 'NR==2 {print int($5)}')
    if [ $DISK_USAGE -gt 85 ]; then
        echo -e "${RED}High disk usage: $DISK_USAGE%${NC}"
    else
        echo -e "${GREEN}Disk usage normal: $DISK_USAGE%${NC}"
    fi
}

# Function to check services
check_services() {
    echo -e "${YELLOW}Checking services...${NC}"
    
    # Check monitoring service
    if systemctl is-active --quiet terminusa-monitoring; then
        echo -e "${GREEN}Monitoring service is running${NC}"
    else
        echo -e "${RED}Monitoring service is not running${NC}"
    fi
    
    # Check Redis
    if systemctl is-active --quiet redis-server; then
        echo -e "${GREEN}Redis is running${NC}"
        redis-cli ping > /dev/null && echo -e "${GREEN}Redis is responsive${NC}"
    else
        echo -e "${RED}Redis is not running${NC}"
    fi
    
    # Check PostgreSQL
    if systemctl is-active --quiet postgresql; then
        echo -e "${GREEN}PostgreSQL is running${NC}"
        pg_isready && echo -e "${GREEN}PostgreSQL is responsive${NC}"
    else
        echo -e "${RED}PostgreSQL is not running${NC}"
    fi
}

# Function to check logs
check_logs() {
    echo -e "${YELLOW}Checking logs...${NC}"
    
    # Check for errors in logs
    ERROR_COUNT=$(grep -i "error" $LOG_DIR/*.log | wc -l)
    if [ $ERROR_COUNT -gt 0 ]; then
        echo -e "${RED}Found $ERROR_COUNT errors in logs${NC}"
        grep -i "error" $LOG_DIR/*.log | tail -n 5
    else
        echo -e "${GREEN}No errors found in logs${NC}"
    fi
    
    # Check log sizes
    for log in $LOG_DIR/*.log; do
        SIZE=$(du -h "$log" | cut -f1)
        echo "Log file $log size: $SIZE"
    done
}

# Function to check metrics
check_metrics() {
    echo -e "${YELLOW}Checking metrics...${NC}"
    
    # Activate virtual environment
    source $VENV_DIR/bin/activate
    
    # Check metric collection
    python manage.py manage_monitoring check-metrics
    
    # Check metric storage
    METRIC_COUNT=$(redis-cli keys "metrics:*" | wc -l)
    echo "Total metrics stored: $METRIC_COUNT"
}

# Function to check alerts
check_alerts() {
    echo -e "${YELLOW}Checking alerts...${NC}"
    
    # Check active alerts
    source $VENV_DIR/bin/activate
    python manage.py manage_monitoring show-alerts --active
    
    # Check alert channels
    python manage.py manage_monitoring check-notifications
}

# Function to check backups
check_backups() {
    echo -e "${YELLOW}Checking backups...${NC}"
    
    # Check latest backup
    LATEST_BACKUP=$(ls -t /var/www/backups/monitoring/pre_* 2>/dev/null | head -n1)
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_TIME=$(stat -c %y "$LATEST_BACKUP")
        echo -e "${GREEN}Latest backup: $BACKUP_TIME${NC}"
    else
        echo -e "${RED}No backups found${NC}"
    fi
    
    # Check backup space
    BACKUP_SPACE=$(du -sh /var/www/backups/monitoring 2>/dev/null | cut -f1)
    echo "Backup space used: $BACKUP_SPACE"
}

# Function to check database
check_database() {
    echo -e "${YELLOW}Checking database...${NC}"
    
    # Check connections
    CONNECTIONS=$(psql -U terminusa_monitor -d terminusa_monitoring -c "SELECT count(*) FROM pg_stat_activity;" -t)
    echo "Active database connections: $CONNECTIONS"
    
    # Check database size
    DB_SIZE=$(psql -U terminusa_monitor -d terminusa_monitoring -c "SELECT pg_size_pretty(pg_database_size('terminusa_monitoring'));" -t)
    echo "Database size: $DB_SIZE"
}

# Function to check security
check_security() {
    echo -e "${YELLOW}Checking security...${NC}"
    
    # Check file permissions
    find $MONITORING_DIR -type f -perm /o=w -ls
    
    # Check SSL certificates
    if [ -f "/etc/ssl/certs/terminusa.crt" ]; then
        CERT_EXPIRY=$(openssl x509 -enddate -noout -in /etc/ssl/certs/terminusa.crt)
        echo "SSL certificate expiry: $CERT_EXPIRY"
    fi
}

# Function to check performance
check_performance() {
    echo -e "${YELLOW}Checking performance...${NC}"
    
    # Check response times
    curl -w "\nTime taken: %{time_total}s\n" -o /dev/null -s https://terminusa.online/health
    
    # Check cache hit ratio
    CACHE_HITS=$(redis-cli info stats | grep hit_rate)
    echo "Cache hit ratio: $CACHE_HITS"
}

# Function to generate report
generate_report() {
    echo -e "${YELLOW}Generating health report...${NC}"
    
    {
        echo "=== Terminusa Monitoring Health Report ==="
        echo "Date: $(date)"
        echo ""
        echo "System Resources:"
        check_resources
        echo ""
        echo "Services:"
        check_services
        echo ""
        echo "Logs:"
        check_logs
        echo ""
        echo "Metrics:"
        check_metrics
        echo ""
        echo "Alerts:"
        check_alerts
        echo ""
        echo "Backups:"
        check_backups
        echo ""
        echo "Database:"
        check_database
        echo ""
        echo "Security:"
        check_security
        echo ""
        echo "Performance:"
        check_performance
        echo ""
        echo "=== End Report ==="
    } > "$REPORT_FILE"
    
    echo -e "${GREEN}Health report generated: $REPORT_FILE${NC}"
}

# Function to send notifications
send_notifications() {
    echo -e "${YELLOW}Sending notifications...${NC}"
    
    # Check for critical issues
    CRITICAL_ISSUES=$(grep -i "critical\|error" "$REPORT_FILE" | wc -l)
    
    if [ $CRITICAL_ISSUES -gt 0 ]; then
        # Send email
        mail -s "Monitoring Health Check Alert" admin@terminusa.online < "$REPORT_FILE"
        
        # Send Slack notification
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"Monitoring Health Check Alert: $CRITICAL_ISSUES critical issues found\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
}

# Main health check process
main() {
    echo -e "${YELLOW}Starting monitoring system health check...${NC}"
    
    # Run checks
    check_resources
    check_services
    check_logs
    check_metrics
    check_alerts
    check_backups
    check_database
    check_security
    check_performance
    
    # Generate report
    generate_report
    
    # Send notifications if needed
    send_notifications
    
    echo -e "${GREEN}Health check completed!${NC}"
    echo "Report available at: $REPORT_FILE"
}

# Execute main function
main
