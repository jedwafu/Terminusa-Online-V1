#!/bin/bash

# Terminusa Online Deployment Script
# This script handles deployment and management of the Terminusa Online server

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVER_DIR="$(pwd)"
VENV_DIR="$SERVER_DIR/venv"
BACKUP_DIR="$SERVER_DIR/backups"
LOG_DIR="$SERVER_DIR/logs"
CONFIG_FILE="$SERVER_DIR/config.toml"
SERVER_PROCESS="rustyhack_server"
CLIENT_PROCESS="rustyhack_client"
WEB_DIR="/var/www/html/terminusa.online"
PLAY_DIR="/var/www/html/play.terminusa.online"
MARKETPLACE_DIR="/var/www/html/marketplace.terminusa.online"

# Function to display script usage
show_usage() {
    echo -e "${BLUE}Terminusa Online Deployment Script${NC}"
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start         - Start the server"
    echo "  stop          - Stop the server"
    echo "  restart       - Restart the server"
    echo "  status        - Check server status"
    echo "  update        - Update the server from git repository"
    echo "  backup        - Create a backup of the server data"
    echo "  restore       - Restore from a backup"
    echo "  logs          - View server logs"
    echo "  config        - Edit server configuration"
    echo "  deploy-web    - Deploy web components"
    echo "  deploy-client - Deploy client components"
    echo "  deploy-all    - Deploy all components"
    echo "  help          - Show this help message"
    echo ""
}

# Function to check if the server is running
is_server_running() {
    if pgrep -x "$SERVER_PROCESS" > /dev/null; then
        return 0 # Running
    else
        return 1 # Not running
    fi
}

# Function to start the server
start_server() {
    echo -e "${BLUE}Starting Terminusa Online server...${NC}"
    
    # Check if server is already running
    if is_server_running; then
        echo -e "${YELLOW}Server is already running!${NC}"
        return
    fi
    
    # Activate virtual environment if it exists
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    # Create log directory if it doesn't exist
    mkdir -p "$LOG_DIR"
    
    # Start the server
    cd "$SERVER_DIR" || exit
    nohup "$SERVER_DIR/target/release/$SERVER_PROCESS" > "$LOG_DIR/server.log" 2>&1 &
    
    # Check if server started successfully
    sleep 2
    if is_server_running; then
        echo -e "${GREEN}Server started successfully!${NC}"
    else
        echo -e "${RED}Failed to start server. Check logs for details.${NC}"
    fi
    
    # Deactivate virtual environment if it was activated
    if [ -d "$VENV_DIR" ]; then
        deactivate
    fi
}

# Function to stop the server
stop_server() {
    echo -e "${BLUE}Stopping Terminusa Online server...${NC}"
    
    # Check if server is running
    if ! is_server_running; then
        echo -e "${YELLOW}Server is not running!${NC}"
        return
    fi
    
    # Stop the server gracefully
    pkill -TERM -x "$SERVER_PROCESS"
    
    # Wait for server to stop
    echo -e "${YELLOW}Waiting for server to stop...${NC}"
    for i in {1..10}; do
        if ! is_server_running; then
            echo -e "${GREEN}Server stopped successfully!${NC}"
            return
        fi
        sleep 1
    done
    
    # Force kill if server didn't stop gracefully
    echo -e "${YELLOW}Server did not stop gracefully. Forcing shutdown...${NC}"
    pkill -KILL -x "$SERVER_PROCESS"
    
    if ! is_server_running; then
        echo -e "${GREEN}Server stopped successfully!${NC}"
    else
        echo -e "${RED}Failed to stop server!${NC}"
    fi
}

# Function to restart the server
restart_server() {
    echo -e "${BLUE}Restarting Terminusa Online server...${NC}"
    stop_server
    sleep 2
    start_server
}

# Function to check server status
check_status() {
    echo -e "${BLUE}Checking Terminusa Online server status...${NC}"
    
    if is_server_running; then
        echo -e "${GREEN}Server is running!${NC}"
        # Get server process info
        echo -e "${BLUE}Server process information:${NC}"
        ps -ef | grep "$SERVER_PROCESS" | grep -v grep
        
        # Get server resource usage
        echo -e "${BLUE}Server resource usage:${NC}"
        top -b -n 1 -p "$(pgrep -x "$SERVER_PROCESS")" | tail -n 2
    else
        echo -e "${YELLOW}Server is not running!${NC}"
    fi
    
    # Check disk space
    echo -e "${BLUE}Disk space usage:${NC}"
    df -h | grep -E '(Filesystem|/$)'
    
    # Check memory usage
    echo -e "${BLUE}Memory usage:${NC}"
    free -h
}

# Function to update the server from git repository
update_server() {
    echo -e "${BLUE}Updating Terminusa Online server...${NC}"
    
    # Check if git is installed
    if ! command -v git &> /dev/null; then
        echo -e "${RED}Git is not installed. Please install git first.${NC}"
        return
    }
    
    # Check if .git directory exists
    if [ ! -d "$SERVER_DIR/.git" ]; then
        echo -e "${RED}Not a git repository. Cannot update.${NC}"
        return
    }
    
    # Create backup before updating
    create_backup
    
    # Pull latest changes
    cd "$SERVER_DIR" || exit
    git pull
    
    # Build the project
    echo -e "${BLUE}Building the project...${NC}"
    cargo build --release
    
    echo -e "${GREEN}Update completed!${NC}"
    echo -e "${YELLOW}You may need to restart the server to apply changes.${NC}"
}

# Function to create a backup
create_backup() {
    echo -e "${BLUE}Creating backup...${NC}"
    
    # Create backup directory if it doesn't exist
    mkdir -p "$BACKUP_DIR"
    
    # Create timestamp for backup filename
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/terminusa_backup_$TIMESTAMP.tar.gz"
    
    # Create backup
    tar -czf "$BACKUP_FILE" -C "$SERVER_DIR" \
        --exclude="target" \
        --exclude=".git" \
        --exclude="venv" \
        --exclude="backups" \
        --exclude="logs" \
        .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Backup created successfully: $BACKUP_FILE${NC}"
    else
        echo -e "${RED}Failed to create backup!${NC}"
    fi
}

# Function to restore from a backup
restore_backup() {
    echo -e "${BLUE}Restore from backup...${NC}"
    
    # Check if backup directory exists
    if [ ! -d "$BACKUP_DIR" ]; then
        echo -e "${RED}Backup directory does not exist!${NC}"
        return
    fi
    
    # List available backups
    echo -e "${BLUE}Available backups:${NC}"
    ls -1 "$BACKUP_DIR" | grep -E "^terminusa_backup_[0-9]{8}_[0-9]{6}\.tar\.gz$" | cat -n
    
    # Ask user to select a backup
    echo -e "${YELLOW}Enter the number of the backup to restore (or 0 to cancel):${NC}"
    read -r selection
    
    if [ "$selection" = "0" ]; then
        echo -e "${YELLOW}Restore cancelled.${NC}"
        return
    fi
    
    # Get the selected backup file
    BACKUP_FILE=$(ls -1 "$BACKUP_DIR" | grep -E "^terminusa_backup_[0-9]{8}_[0-9]{6}\.tar\.gz$" | sed -n "${selection}p")
    
    if [ -z "$BACKUP_FILE" ]; then
        echo -e "${RED}Invalid selection!${NC}"
        return
    fi
    
    BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILE"
    
    # Confirm restoration
    echo -e "${RED}WARNING: This will overwrite the current server files!${NC}"
    echo -e "${YELLOW}Are you sure you want to restore from $BACKUP_FILE? (y/n)${NC}"
    read -r confirm
    
    if [ "$confirm" != "y" ]; then
        echo -e "${YELLOW}Restore cancelled.${NC}"
        return
    fi
    
    # Stop the server before restoring
    stop_server
    
    # Create a temporary directory for extraction
    TEMP_DIR=$(mktemp -d)
    
    # Extract backup to temporary directory
    tar -xzf "$BACKUP_PATH" -C "$TEMP_DIR"
    
    # Copy files from temporary directory to server directory
    rsync -av --exclude="target" --exclude=".git" --exclude="venv" --exclude="backups" --exclude="logs" "$TEMP_DIR/" "$SERVER_DIR/"
    
    # Remove temporary directory
    rm -rf "$TEMP_DIR"
    
    echo -e "${GREEN}Restore completed!${NC}"
    echo -e "${YELLOW}You may need to rebuild and restart the server.${NC}"
}

# Function to view server logs
view_logs() {
    echo -e "${BLUE}Viewing server logs...${NC}"
    
    # Check if log directory exists
    if [ ! -d "$LOG_DIR" ]; then
        echo -e "${RED}Log directory does not exist!${NC}"
        return
    fi
    
    # Check if log file exists
    if [ ! -f "$LOG_DIR/server.log" ]; then
        echo -e "${RED}Server log file does not exist!${NC}"
        return
    }
    
    # View logs with less
    less "$LOG_DIR/server.log"
}

# Function to edit server configuration
edit_config() {
    echo -e "${BLUE}Editing server configuration...${NC}"
    
    # Check if config file exists
    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${YELLOW}Config file does not exist. Creating a new one...${NC}"
        touch "$CONFIG_FILE"
    fi
    
    # Open config file with default editor
    if [ -n "$EDITOR" ]; then
        $EDITOR "$CONFIG_FILE"
    else
        nano "$CONFIG_FILE"
    fi
    
    echo -e "${GREEN}Configuration updated!${NC}"
    echo -e "${YELLOW}You may need to restart the server to apply changes.${NC}"
}

# Function to deploy web components
deploy_web() {
    echo -e "${BLUE}Deploying web components...${NC}"
    
    # Check if web directories exist
    mkdir -p "$WEB_DIR"
    mkdir -p "$PLAY_DIR"
    mkdir -p "$MARKETPLACE_DIR"
    
    # Deploy main website
    echo -e "${BLUE}Deploying main website...${NC}"
    rsync -av "$SERVER_DIR/web/" "$WEB_DIR/"
    
    # Deploy play website
    echo -e "${BLUE}Deploying play website...${NC}"
    rsync -av "$SERVER_DIR/play/" "$PLAY_DIR/"
    
    # Deploy marketplace website
    echo -e "${BLUE}Deploying marketplace website...${NC}"
    rsync -av "$SERVER_DIR/marketplace/" "$MARKETPLACE_DIR/"
    
    # Set permissions
    chown -R www-data:www-data "$WEB_DIR"
    chown -R www-data:www-data "$PLAY_DIR"
    chown -R www-data:www-data "$MARKETPLACE_DIR"
    
    echo -e "${GREEN}Web components deployed successfully!${NC}"
}

# Function to deploy client components
deploy_client() {
    echo -e "${BLUE}Deploying client components...${NC}"
    
    # Build client
    echo -e "${BLUE}Building client...${NC}"
    cd "$SERVER_DIR" || exit
    cargo build --release --bin "$CLIENT_PROCESS"
    
    # Copy client to web directory
    echo -e "${BLUE}Copying client to web directory...${NC}"
    cp "$SERVER_DIR/target/release/$CLIENT_PROCESS" "$WEB_DIR/downloads/"
    
    echo -e "${GREEN}Client components deployed successfully!${NC}"
}

# Function to deploy all components
deploy_all() {
    echo -e "${BLUE}Deploying all components...${NC}"
    
    # Create backup before deployment
    create_backup
    
    # Stop server
    stop_server
    
    # Update from git
    update_server
    
    # Deploy web components
    deploy_web
    
    # Deploy client components
    deploy_client
    
    # Start server
    start_server
    
    echo -e "${GREEN}All components deployed successfully!${NC}"
}

# Main script execution
case "$1" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        restart_server
        ;;
    status)
        check_status
        ;;
    update)
        update_server
        ;;
    backup)
        create_backup
        ;;
    restore)
        restore_backup
        ;;
    logs)
        view_logs
        ;;
    config)
        edit_config
        ;;
    deploy-web)
        deploy_web
        ;;
    deploy-client)
        deploy_client
        ;;
    deploy-all)
        deploy_all
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        show_usage
        exit 1
        ;;
esac

exit 0
