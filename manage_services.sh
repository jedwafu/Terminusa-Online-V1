#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check command status
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Success${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        exit 1
    fi
}

# Function to check if a service is running
check_service() {
    if systemctl is-active --quiet $1; then
        echo -e "${GREEN}$1 is running${NC}"
        return 0
    else
        echo -e "${RED}$1 is not running${NC}"
        return 1
    fi
}

# Function to start all services
start_services() {
    echo -e "${YELLOW}Starting Terminusa Online services...${NC}"
    
    echo -e "\n${YELLOW}Starting PostgreSQL...${NC}"
    systemctl start postgresql
    check_status
    
    echo -e "\n${YELLOW}Starting Redis...${NC}"
    systemctl start redis-server
    check_status
    
    echo -e "\n${YELLOW}Starting Nginx...${NC}"
    systemctl start nginx
    check_status
    
    echo -e "\n${YELLOW}Starting Terminusa service...${NC}"
    systemctl start terminusa.service
    check_status
    
    echo -e "\n${GREEN}All services started successfully!${NC}"
}

# Function to stop all services
stop_services() {
    echo -e "${YELLOW}Stopping Terminusa Online services...${NC}"
    
    echo -e "\n${YELLOW}Stopping Terminusa service...${NC}"
    systemctl stop terminusa.service
    check_status
    
    echo -e "\n${YELLOW}Stopping Nginx...${NC}"
    systemctl stop nginx
    check_status
    
    echo -e "\n${YELLOW}Stopping Redis...${NC}"
    systemctl stop redis-server
    check_status
    
    echo -e "\n${YELLOW}Stopping PostgreSQL...${NC}"
    systemctl stop postgresql
    check_status
    
    echo -e "\n${GREEN}All services stopped successfully!${NC}"
}

# Function to restart all services
restart_services() {
    echo -e "${YELLOW}Restarting Terminusa Online services...${NC}"
    stop_services
    sleep 2
    start_services
}

# Function to check status of all services
check_all_services() {
    echo -e "${YELLOW}Checking Terminusa Online services status...${NC}"
    
    services=("postgresql" "redis-server" "nginx" "terminusa" "terminusa-terminal")
    all_running=true
    
    for service in "${services[@]}"; do
        if ! check_service $service; then
            all_running=false
        fi
    done
    
    echo -e "\n${YELLOW}Checking logs...${NC}"
    echo -e "Main logs: /var/log/terminusa/app.log"
    echo -e "Terminal logs: /var/log/terminusa/terminal.log"
    echo -e "Nginx access logs: /var/log/nginx/terminusa.access.log"
    echo -e "Nginx error logs: /var/log/nginx/terminusa.error.log"
    
    if [ "$all_running" = true ]; then
        echo -e "\n${GREEN}All services are running properly!${NC}"
    else
        echo -e "\n${RED}Some services are not running. Please check the logs for details.${NC}"
    fi
}

# Function to show usage
show_usage() {
    echo "Usage: $0 {start|stop|restart|status}"
    echo "  start   - Start all Terminusa Online services"
    echo "  stop    - Stop all Terminusa Online services"
    echo "  restart - Restart all Terminusa Online services"
    echo "  status  - Check status of all services"
}

# Main script
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        check_all_services
        ;;
    *)
        show_usage
        exit 1
        ;;
esac

exit 0
