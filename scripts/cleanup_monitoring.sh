#!/bin/bash

# Monitoring system cleanup script
echo "Starting monitoring system cleanup..."

# Configuration
MONITORING_DIR="/var/www/terminusa/monitoring"
LOG_DIR="/var/log/terminusa/monitoring"
BACKUP_DIR="/var/www/backups/monitoring"
DATA_DIR="/var/www/terminusa/monitoring/data"
CACHE_DIR="/var/www/terminusa/monitoring/cache"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Error handling
set -e
trap 'echo -e "${RED}Cleanup failed${NC}"; exit 1' ERR

# Function to cleanup old metrics
cleanup_metrics() {
    echo -e "${YELLOW}Cleaning up old metrics...${NC}"

    # Raw metrics (older than 1 day)
    find $DATA_DIR/metrics/raw -type f -mtime +1 -delete

    # Hourly aggregates (older than 7 days)
    find $DATA_DIR/metrics/hourly -type f -mtime +7 -delete

    # Daily aggregates (older than 30 days)
    find $DATA_DIR/metrics/daily -type f -mtime +30 -delete

    # Monthly aggregates (older than 365 days)
    find $DATA_DIR/metrics/monthly -type f -mtime +365 -delete

    echo -e "${GREEN}Metrics cleanup completed${NC}"
}

# Function to cleanup old logs
cleanup_logs() {
    echo -e "${YELLOW}Cleaning up old logs...${NC}"

    # System logs (older than 14 days)
    find $LOG_DIR/system -type f -mtime +14 -delete

    # Metric logs (older than 7 days)
    find $LOG_DIR/metrics -type f -mtime +7 -delete

    # Alert logs (older than 30 days)
    find $LOG_DIR/alerts -type f -mtime +30 -delete

    # Compress logs older than 1 day
    find $LOG_DIR -type f -mtime +1 -name "*.log" -exec gzip {} \;

    echo -e "${GREEN}Logs cleanup completed${NC}"
}

# Function to cleanup old backups
cleanup_backups() {
    echo -e "${YELLOW}Cleaning up old backups...${NC}"

    # Daily backups (older than 7 days)
    find $BACKUP_DIR/daily -type f -mtime +7 -delete

    # Weekly backups (older than 4 weeks)
    find $BACKUP_DIR/weekly -type f -mtime +28 -delete

    # Monthly backups (older than 12 months)
    find $BACKUP_DIR/monthly -type f -mtime +365 -delete

    echo -e "${GREEN}Backups cleanup completed${NC}"
}

# Function to cleanup cache
cleanup_cache() {
    echo -e "${YELLOW}Cleaning up cache...${NC}"

    # Clear old cache files
    find $CACHE_DIR -type f -mtime +1 -delete

    # Clear Redis cache
    redis-cli -n 0 --raw keys "monitoring:cache:*" | xargs -r redis-cli -n 0 del

    echo -e "${GREEN}Cache cleanup completed${NC}"
}

# Function to cleanup database
cleanup_database() {
    echo -e "${YELLOW}Cleaning up database...${NC}"

    # Connect to database and cleanup old records
    psql -U terminusa_user -d terminusa_db << EOF
    -- Delete old alerts
    DELETE FROM monitoring_alert WHERE created_at < NOW() - INTERVAL '30 days';

    -- Delete old metrics
    DELETE FROM monitoring_metric WHERE timestamp < NOW() - INTERVAL '30 days';

    -- Delete old logs
    DELETE FROM monitoring_log WHERE created_at < NOW() - INTERVAL '30 days';

    -- Vacuum tables
    VACUUM FULL monitoring_alert;
    VACUUM FULL monitoring_metric;
    VACUUM FULL monitoring_log;
EOF

    echo -e "${GREEN}Database cleanup completed${NC}"
}

# Function to optimize storage
optimize_storage() {
    echo -e "${YELLOW}Optimizing storage...${NC}"

    # Compress old files
    find $DATA_DIR -type f -mtime +1 -not -name "*.gz" -exec gzip {} \;

    # Remove empty directories
    find $MONITORING_DIR -type d -empty -delete

    # Optimize database
    psql -U terminusa_user -d terminusa_db -c "VACUUM ANALYZE;"

    echo -e "${GREEN}Storage optimization completed${NC}"
}

# Function to verify cleanup
verify_cleanup() {
    echo -e "${YELLOW}Verifying cleanup...${NC}"

    # Check disk usage
    df -h $MONITORING_DIR

    # Check database size
    psql -U terminusa_user -d terminusa_db << EOF
    SELECT pg_size_pretty(pg_database_size('terminusa_db'));
    SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
    FROM pg_tables
    WHERE tablename LIKE 'monitoring_%'
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
EOF

    # Check Redis memory usage
    redis-cli info memory | grep "used_memory_human"

    echo -e "${GREEN}Cleanup verification completed${NC}"
}

# Function to generate cleanup report
generate_report() {
    echo -e "${YELLOW}Generating cleanup report...${NC}"

    REPORT_FILE="$LOG_DIR/cleanup_report_$(date +%Y%m%d_%H%M%S).txt"

    {
        echo "=== Monitoring System Cleanup Report ==="
        echo "Date: $(date)"
        echo ""
        echo "Storage Usage:"
        df -h $MONITORING_DIR
        echo ""
        echo "Database Size:"
        psql -U terminusa_user -d terminusa_db -c "SELECT pg_size_pretty(pg_database_size('terminusa_db'));"
        echo ""
        echo "Redis Memory Usage:"
        redis-cli info memory | grep "used_memory_human"
        echo ""
        echo "Files Cleaned:"
        echo "- Metrics: $(find $DATA_DIR/metrics -type f | wc -l) files"
        echo "- Logs: $(find $LOG_DIR -type f | wc -l) files"
        echo "- Backups: $(find $BACKUP_DIR -type f | wc -l) files"
        echo "- Cache: $(find $CACHE_DIR -type f | wc -l) files"
        echo ""
        echo "=== End Report ==="
    } > "$REPORT_FILE"

    echo -e "${GREEN}Cleanup report generated: $REPORT_FILE${NC}"
}

# Main cleanup process
main() {
    echo -e "${YELLOW}Starting monitoring system cleanup...${NC}"

    # Run cleanup steps
    cleanup_metrics
    cleanup_logs
    cleanup_backups
    cleanup_cache
    cleanup_database
    optimize_storage
    verify_cleanup
    generate_report

    echo -e "${GREEN}Monitoring system cleanup completed!${NC}"
    echo -e "\nNext steps:"
    echo "1. Review cleanup report"
    echo "2. Check system performance"
    echo "3. Verify monitoring functionality"
}

# Execute main function
main
