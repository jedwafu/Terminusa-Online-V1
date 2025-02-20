#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if port is in use
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Kill process using port
kill_port() {
    local port=$1
    local pid=$(lsof -t -i:$port)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}Port $port is in use by PID $pid. Stopping process...${NC}"
        kill -15 $pid
        sleep 2
        if kill -0 $pid 2>/dev/null; then
            kill -9 $pid
            sleep 1
        fi
        echo -e "${GREEN}Process stopped${NC}"
    else
        echo -e "${RED}No process found using port $port${NC}"
    fi
}

# Show port status
show_port_status() {
    local port=$1
    echo -e "${YELLOW}Checking port $port...${NC}"
    if check_port $port; then
        pid=$(lsof -t -i:$port)
        process=$(ps -p $pid -o comm=)
        echo -e "${RED}Port $port is in use by process $process (PID: $pid)${NC}"
        lsof -i :$port
    else
        echo -e "${GREEN}Port $port is free${NC}"
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [check|kill|status] port"
    echo "  check port  - Check if port is in use"
    echo "  kill port   - Kill process using port"
    echo "  status port - Show detailed port status"
    echo
    echo "Example: $0 status 5000"
}

# Main
case "$1" in
    check)
        if [ -z "$2" ]; then
            show_usage
            exit 1
        fi
        if check_port $2; then
            echo -e "${RED}Port $2 is in use${NC}"
            exit 1
        else
            echo -e "${GREEN}Port $2 is free${NC}"
            exit 0
        fi
        ;;
    kill)
        if [ -z "$2" ]; then
            show_usage
            exit 1
        fi
        kill_port $2
        ;;
    status)
        if [ -z "$2" ]; then
            show_usage
            exit 1
        fi
        show_port_status $2
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
