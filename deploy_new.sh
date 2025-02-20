#!/bin/bash

# Stop services function with enhanced screen session handling
stop_services() {
    info_log "Stopping services..."
    
    # Kill all screen sessions first
    info_log "Stopping screen sessions..."
    screen -ls | grep -o '[0-9]*\.terminusa-[^ ]*' | while read -r session; do
        info_log "Killing screen session: $session"
        screen -S "$session" -X quit
    done
    
    # Double check and force kill any remaining screen sessions
    screen -ls | grep -o '[0-9]*\.terminusa-[^ ]*' | while read -r session; do
        info_log "Force killing screen session: $session"
        screen -S "$session" -X quit
        kill $(echo "$session" | cut -d. -f1) 2>/dev/null
    done
    
    # Stop system services
    info_log "Stopping system services..."
    systemctl stop nginx
    systemctl stop redis-server
    systemctl stop postgresql
    systemctl stop postfix
    
    # Kill any processes on our ports
    for service in "${!SERVICE_PORTS[@]}"; do
        IFS=',' read -ra PORTS <<< "${SERVICE_PORTS[$service]}"
        for port in "${PORTS[@]}"; do
            if check_port $port; then
                info_log "Killing process on port $port..."
                kill_port_process $port
            fi
        done
    done
    
    success_log "All services stopped"
}

# Make the script executable
chmod +x deploy_new.sh
