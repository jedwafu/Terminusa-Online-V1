#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Debug mode flag
DEBUG=false

# Service status tracking
declare -A SERVICE_STATUS

# Debug logging function
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $1${NC}"
    fi
}

# Error logging function
error_log() {
    echo -e "${RED}[ERROR] $1${NC}"
    if [ "$DEBUG" = true ]; then
        echo -e "${RED}[ERROR DETAILS] $2${NC}"
    fi
}

# Success logging function
success_log() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

# Info logging function
info_log() {
    echo -e "${YELLOW}[INFO] $1${NC}"
}

# Check service status
check_service() {
    local service=$1
    if systemctl is-active --quiet $service; then
        SERVICE_STATUS[$service]="running"
        debug_log "$service is running"
        return 0
    else
        SERVICE_STATUS[$service]="stopped"
        debug_log "$service is stopped"
        return 1
    fi
}

# Start a specific service
start_service() {
    local service=$1
    info_log "Starting $service..."
    
    case $service in
        "postgresql")
            systemctl start postgresql
            if check_service postgresql; then
                success_log "PostgreSQL started successfully"
            else
                error_log "Failed to start PostgreSQL" "$(systemctl status postgresql)"
                return 1
            fi
            ;;
        "nginx")
            systemctl start nginx
            if check_service nginx; then
                success_log "Nginx started successfully"
            else
                error_log "Failed to start Nginx" "$(systemctl status nginx)"
                return 1
            fi
            ;;
        "postfix")
            systemctl start postfix
            if check_service postfix; then
                success_log "Postfix started successfully"
            else
                error_log "Failed to start Postfix" "$(systemctl status postfix)"
                return 1
            fi
            ;;
        "gunicorn")
            debug_log "Starting Gunicorn with web_app.py"
            gunicorn -w 4 -b 0.0.0.0:8000 web_app:app --daemon
            if [ $? -eq 0 ]; then
                success_log "Gunicorn started successfully"
            else
                error_log "Failed to start Gunicorn" "Check logs/gunicorn.log for details"
                return 1
            fi
            ;;
        "game-server")
            debug_log "Starting game server with main.py"
            python main.py &
            if [ $? -eq 0 ]; then
                success_log "Game server started successfully"
            else
                error_log "Failed to start game server" "Check logs/game-server.log for details"
                return 1
            fi
            ;;
        *)
            error_log "Unknown service: $service"
            return 1
            ;;
    esac
}

# Stop a specific service
stop_service() {
    local service=$1
    info_log "Stopping $service..."
    
    case $service in
        "postgresql")
            systemctl stop postgresql
            if ! check_service postgresql; then
                success_log "PostgreSQL stopped successfully"
            else
                error_log "Failed to stop PostgreSQL" "$(systemctl status postgresql)"
                return 1
            fi
            ;;
        "nginx")
            systemctl stop nginx
            if ! check_service nginx; then
                success_log "Nginx stopped successfully"
            else
                error_log "Failed to stop Nginx" "$(systemctl status nginx)"
                return 1
            fi
            ;;
        "postfix")
            systemctl stop postfix
            if ! check_service postfix; then
                success_log "Postfix stopped successfully"
            else
                error_log "Failed to stop Postfix" "$(systemctl status postfix)"
                return 1
            fi
            ;;
        "gunicorn")
            pkill gunicorn
            if [ $? -eq 0 ]; then
                success_log "Gunicorn stopped successfully"
            else
                error_log "Failed to stop Gunicorn" "Process may not be running"
                return 1
            fi
            ;;
        "game-server")
            pkill -f "python main.py"
            if [ $? -eq 0 ]; then
                success_log "Game server stopped successfully"
            else
                error_log "Failed to stop game server" "Process may not be running"
                return 1
            fi
            ;;
        *)
            error_log "Unknown service: $service"
            return 1
            ;;
    esac
}

# Show service status
show_status() {
    info_log "Checking service status..."
    printf "${YELLOW}%-20s %-10s %-20s${NC}\n" "Service" "Status" "Details"
    echo "----------------------------------------------------"
    
    check_service postgresql
    printf "%-20s %-10s %-20s\n" "PostgreSQL" "${SERVICE_STATUS[postgresql]}" "Database Server"
    
    check_service nginx
    printf "%-20s %-10s %-20s\n" "Nginx" "${SERVICE_STATUS[nginx]}" "Web Server"
    
    check_service postfix
    printf "%-20s %-10s %-20s\n" "Postfix" "${SERVICE_STATUS[postfix]}" "Mail Server"
    
    if pgrep gunicorn >/dev/null; then
        printf "%-20s %-10s %-20s\n" "Gunicorn" "running" "Application Server"
    else
        printf "%-20s %-10s %-20s\n" "Gunicorn" "stopped" "Application Server"
    fi
    
    if pgrep -f "python main.py" >/dev/null; then
        printf "%-20s %-10s %-20s\n" "Game Server" "running" "Game Service"
    else
        printf "%-20s %-10s %-20s\n" "Game Server" "stopped" "Game Service"
    fi
}

# Show help message
show_help() {
    echo -e "${YELLOW}Terminusa Online Server Management${NC}"
    echo
    echo "Usage: $0 [options] [service]"
    echo
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  -d, --debug    Enable debug output"
    echo "  start          Start all services or specific service"
    echo "  stop           Stop all services or specific service"
    echo "  restart        Restart all services or specific service"
    echo "  status         Show service status"
    echo
    echo "Services:"
    echo "  postgresql     Database server"
    echo "  nginx         Web server"
    echo "  postfix       Mail server"
    echo "  gunicorn      Application server"
    echo "  game-server   Game server"
    echo "  all           All services"
    echo
    echo "Examples:"
    echo "  $0 start                # Start all services"
    echo "  $0 start postgresql     # Start only PostgreSQL"
    echo "  $0 stop nginx          # Stop only Nginx"
    echo "  $0 status              # Show all service status"
    echo "  $0 -d start           # Start all services with debug output"
}

# Main script execution
main() {
    # Process command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -d|--debug)
                DEBUG=true
                shift
                ;;
            start|stop|restart|status)
                ACTION=$1
                shift
                ;;
            postgresql|nginx|postfix|gunicorn|game-server|all)
                SERVICE=$1
                shift
                ;;
            *)
                error_log "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # Check if running as root
    if [ "$EUID" -ne 0 ]; then 
        error_log "Please run as root"
        exit 1
    fi

    # Create logs directory
    mkdir -p logs

    # Process the action
    case $ACTION in
        start)
            if [ "$SERVICE" = "all" ] || [ -z "$SERVICE" ]; then
                info_log "Starting all services..."
                start_service postgresql
                start_service nginx
                start_service postfix
                start_service gunicorn
                start_service game-server
            else
                start_service $SERVICE
            fi
            ;;
        stop)
            if [ "$SERVICE" = "all" ] || [ -z "$SERVICE" ]; then
                info_log "Stopping all services..."
                stop_service game-server
                stop_service gunicorn
                stop_service nginx
                stop_service postfix
                stop_service postgresql
            else
                stop_service $SERVICE
            fi
            ;;
        restart)
            if [ "$SERVICE" = "all" ] || [ -z "$SERVICE" ]; then
                info_log "Restarting all services..."
                stop_service game-server
                stop_service gunicorn
                stop_service nginx
                stop_service postfix
                stop_service postgresql
                sleep 2
                start_service postgresql
                start_service postfix
                start_service nginx
                start_service gunicorn
                start_service game-server
            else
                stop_service $SERVICE
                sleep 2
                start_service $SERVICE
            fi
            ;;
        status)
            show_status
            ;;
        *)
            show_help
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"
