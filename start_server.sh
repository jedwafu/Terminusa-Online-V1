#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Debug mode flag
DEBUG=false

# Service status tracking
declare -A SERVICE_STATUS
declare -A SERVICE_PIDS
declare -A SERVICE_PORTS
declare -A SERVICE_LOGS
declare -A SERVICE_REQUIRED

# Initialize arrays
SERVICE_PORTS=(
    ["postgresql"]="5432"
    ["nginx"]="80"
    ["gunicorn"]="8000"
    ["game-server"]="5000"
    ["postfix"]="25"
)

SERVICE_LOGS=(
    ["postgresql"]="/var/log/postgresql/postgresql-main.log"
    ["nginx"]="/var/log/nginx/error.log"
    ["gunicorn"]="logs/gunicorn.log"
    ["game-server"]="logs/game-server.log"
    ["postfix"]="/var/log/mail.log"
)

# Mark required services
SERVICE_REQUIRED=(
    ["postgresql"]="true"
    ["nginx"]="true"
    ["gunicorn"]="true"
    ["game-server"]="true"
    ["postfix"]="true"
)

# Optional services - will be added only if installed
OPTIONAL_SERVICES=(
    "redis"
    "elasticsearch"
)

# Monitoring variables
MONITOR_INTERVAL=5  # seconds
MONITOR_RUNNING=true

# Debug logging function
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

# Error logging function
error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    if [ "$DEBUG" = true ] && [ ! -z "$2" ]; then
        echo -e "${RED}[ERROR DETAILS] $2${NC}"
    fi
    logger -t "terminusa" "ERROR: $1"
}

# Success logging function
success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    logger -t "terminusa" "SUCCESS: $1"
}

# Info logging function
info_log() {
    echo -e "${YELLOW}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    logger -t "terminusa" "INFO: $1"
}

# Check if a service is installed
check_service_installed() {
    local service=$1
    case $service in
        "postgresql")
            command -v psql >/dev/null 2>&1
            return $?
            ;;
        "nginx")
            command -v nginx >/dev/null 2>&1
            return $?
            ;;
        "redis")
            command -v redis-server >/dev/null 2>&1
            return $?
            ;;
        "elasticsearch")
            systemctl list-unit-files | grep -q elasticsearch.service
            return $?
            ;;
        "postfix")
            command -v postfix >/dev/null 2>&1
            return $?
            ;;
        *)
            return 0  # Assume Python services are always available
            ;;
    esac
}

# Initialize optional services
initialize_optional_services() {
    info_log "Checking for optional services..."
    for service in "${OPTIONAL_SERVICES[@]}"; do
        if check_service_installed "$service"; then
            info_log "Found optional service: $service"
            case $service in
                "redis")
                    SERVICE_PORTS[$service]="6379"
                    SERVICE_LOGS[$service]="/var/log/redis/redis-server.log"
                    SERVICE_REQUIRED[$service]="false"
                    ;;
                "elasticsearch")
                    SERVICE_PORTS[$service]="9200"
                    SERVICE_LOGS[$service]="/var/log/elasticsearch/elasticsearch.log"
                    SERVICE_REQUIRED[$service]="false"
                    ;;
            esac
        else
            debug_log "Optional service not installed: $service"
        fi
    done
}

[Previous service monitoring and management code remains the same...]

# Main script execution
main() {
    # Initialize optional services first
    initialize_optional_services

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
            start|stop|restart|status|monitor)
                ACTION=$1
                shift
                ;;
            postgresql|nginx|gunicorn|game-server|postfix|redis|elasticsearch|all)
                SERVICE=$1
                if [ "$SERVICE" != "all" ] && ! check_service_installed "$SERVICE"; then
                    error_log "Service $SERVICE is not installed"
                    exit 1
                fi
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

    # Set up trap for cleanup
    trap cleanup SIGINT SIGTERM

    # Initialize if needed
    if [ "$ACTION" = "start" ]; then
        initialize_services || exit 1
    fi

    # Process the action
    case $ACTION in
        start)
            if [ "$SERVICE" = "all" ] || [ -z "$SERVICE" ]; then
                info_log "Starting all services..."
                # Start required services first
                for service in "${!SERVICE_REQUIRED[@]}"; do
                    if [ "${SERVICE_REQUIRED[$service]}" = "true" ]; then
                        start_service "$service"
                    fi
                done
                # Start optional services if installed
                for service in "${OPTIONAL_SERVICES[@]}"; do
                    if check_service_installed "$service"; then
                        start_service "$service"
                    fi
                done
            else
                start_service "$SERVICE"
            fi
            ;;
        stop)
            if [ "$SERVICE" = "all" ] || [ -z "$SERVICE" ]; then
                info_log "Stopping all services..."
                # Stop in reverse order
                for service in "${OPTIONAL_SERVICES[@]}"; do
                    if check_service_installed "$service"; then
                        stop_service "$service"
                    fi
                done
                for service in "${!SERVICE_REQUIRED[@]}"; do
                    if [ "${SERVICE_REQUIRED[$service]}" = "true" ]; then
                        stop_service "$service"
                    fi
                done
            else
                stop_service "$SERVICE"
            fi
            ;;
        restart)
            if [ "$SERVICE" = "all" ] || [ -z "$SERVICE" ]; then
                info_log "Restarting all services..."
                # Stop everything first
                for service in "${OPTIONAL_SERVICES[@]}"; do
                    if check_service_installed "$service"; then
                        stop_service "$service"
                    fi
                done
                for service in "${!SERVICE_REQUIRED[@]}"; do
                    if [ "${SERVICE_REQUIRED[$service]}" = "true" ]; then
                        stop_service "$service"
                    fi
                done
                sleep 2
                # Start everything back up
                for service in "${!SERVICE_REQUIRED[@]}"; do
                    if [ "${SERVICE_REQUIRED[$service]}" = "true" ]; then
                        start_service "$service"
                    fi
                done
                for service in "${OPTIONAL_SERVICES[@]}"; do
                    if check_service_installed "$service"; then
                        start_service "$service"
                    fi
                done
            else
                stop_service "$SERVICE"
                sleep 2
                start_service "$SERVICE"
            fi
            ;;
        status)
            show_status
            ;;
        monitor)
            monitor_services
            ;;
        *)
            show_help
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"
