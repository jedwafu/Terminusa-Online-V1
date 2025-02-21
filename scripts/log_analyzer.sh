#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Log directories
LOG_DIR="/var/log/terminusa"
NGINX_LOG="/var/log/nginx"
SYSTEM_LOG="/var/log"

echo -e "${YELLOW}Starting log analysis...${NC}"

# Parse application logs
analyze_app_logs() {
    echo -e "\n${YELLOW}Analyzing application logs...${NC}"
    
    # Error frequency
    echo -e "\nError frequency in last hour:"
    grep "ERROR" "$LOG_DIR/app.log" | grep "$(date -d '1 hour ago' +'%H:')" | sort | uniq -c | sort -nr
    
    # Warning patterns
    echo -e "\nWarning patterns:"
    grep "WARNING" "$LOG_DIR/app.log" | grep "$(date +'%Y-%m-%d')" | sort | uniq -c | sort -nr
    
    # Critical events
    echo -e "\nCritical events:"
    grep "CRITICAL" "$LOG_DIR/app.log" | tail -n 10
}

# Analyze security events
analyze_security_events() {
    echo -e "\n${YELLOW}Analyzing security events...${NC}"
    
    # Failed login attempts
    echo -e "\nFailed login patterns:"
    grep "Failed login" "$LOG_DIR/security.log" | sort | uniq -c | sort -nr | head -n 10
    
    # Unauthorized access attempts
    echo -e "\nUnauthorized access attempts:"
    grep "Unauthorized" "$LOG_DIR/security.log" | sort | uniq -c | sort -nr | head -n 10
    
    # Suspicious activities
    echo -e "\nSuspicious activities:"
    grep -E "injection|exploit|attack" "$LOG_DIR/security.log" | tail -n 10
}

# Analyze performance logs
analyze_performance() {
    echo -e "\n${YELLOW}Analyzing performance logs...${NC}"
    
    # Slow queries
    echo -e "\nSlow database queries:"
    grep "slow query" "$LOG_DIR/app.log" | sort | uniq -c | sort -nr | head -n 10
    
    # High latency requests
    echo -e "\nHigh latency requests:"
    grep "high latency" "$LOG_DIR/app.log" | sort | uniq -c | sort -nr | head -n 10
    
    # Resource usage spikes
    echo -e "\nResource usage spikes:"
    grep "resource spike" "$LOG_DIR/monitoring.log" | tail -n 10
}

# Analyze system logs
analyze_system_logs() {
    echo -e "\n${YELLOW}Analyzing system logs...${NC}"
    
    # System errors
    echo -e "\nSystem errors:"
    grep "error" "$SYSTEM_LOG/syslog" | grep "$(date +'%b %d')" | sort | uniq -c | sort -nr | head -n 10
    
    # Service failures
    echo -e "\nService failures:"
    grep "failed" "$SYSTEM_LOG/syslog" | grep "$(date +'%b %d')" | sort | uniq -c | sort -nr | head -n 10
}

# Generate alerts
generate_alerts() {
    echo -e "\n${YELLOW}Generating alerts...${NC}"
    
    ALERT_FILE="log_alerts_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "=== Log Analysis Alerts ==="
        echo "Generated: $(date)"
        echo "-------------------------"
        
        # Critical errors
        echo -e "\nCritical Errors:"
        grep "CRITICAL" "$LOG_DIR/app.log" | tail -n 5
        
        # Security alerts
        echo -e "\nSecurity Alerts:"
        grep -E "injection|exploit|attack" "$LOG_DIR/security.log" | tail -n 5
        
        # Performance alerts
        echo -e "\nPerformance Alerts:"
        grep "high latency" "$LOG_DIR/app.log" | tail -n 5
        
        # System alerts
        echo -e "\nSystem Alerts:"
        grep "error" "$SYSTEM_LOG/syslog" | grep "$(date +'%b %d')" | tail -n 5
        
    } > "$ALERT_FILE"
    
    echo -e "${GREEN}Alerts generated: $ALERT_FILE${NC}"
}

# Generate analysis report
generate_report() {
    echo -e "\n${YELLOW}Generating analysis report...${NC}"
    
    REPORT_FILE="log_analysis_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "=== Log Analysis Report ==="
        echo "Generated: $(date)"
        echo "-------------------------"
        
        # Error statistics
        echo -e "\nError Statistics:"
        grep "ERROR" "$LOG_DIR/app.log" | wc -l | xargs echo "Total errors:"
        grep "WARNING" "$LOG_DIR/app.log" | wc -l | xargs echo "Total warnings:"
        grep "CRITICAL" "$LOG_DIR/app.log" | wc -l | xargs echo "Critical events:"
        
        # Security statistics
        echo -e "\nSecurity Statistics:"
        grep "Failed login" "$LOG_DIR/security.log" | wc -l | xargs echo "Failed logins:"
        grep "Unauthorized" "$LOG_DIR/security.log" | wc -l | xargs echo "Unauthorized attempts:"
        
        # Performance statistics
        echo -e "\nPerformance Statistics:"
        grep "slow query" "$LOG_DIR/app.log" | wc -l | xargs echo "Slow queries:"
        grep "high latency" "$LOG_DIR/app.log" | wc -l | xargs echo "High latency requests:"
        
        # System statistics
        echo -e "\nSystem Statistics:"
        grep "error" "$SYSTEM_LOG/syslog" | grep "$(date +'%b %d')" | wc -l | xargs echo "System errors today:"
        grep "failed" "$SYSTEM_LOG/syslog" | grep "$(date +'%b %d')" | wc -l | xargs echo "Service failures today:"
        
    } > "$REPORT_FILE"
    
    echo -e "${GREEN}Report generated: $REPORT_FILE${NC}"
}

# Run all analysis functions
analyze_app_logs
analyze_security_events
analyze_performance
analyze_system_logs
generate_alerts
generate_report

echo -e "\n${GREEN}Log analysis completed${NC}"
