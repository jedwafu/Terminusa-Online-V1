#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

info_log() {
    echo -e "${YELLOW}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

# Create logs directory
mkdir -p logs

# Verify required environment variables
required_vars=(
    "MAIN_APP_DIR"
    "MAIN_STATIC_DIR"
    "DATABASE_URL"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES_DB"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        error_log "Required environment variable $var is not set"
        exit 1
    fi
done

# Setup static files
setup_static_files() {
    info_log "Setting up static files..."
    
    # Create directories with error handling
    info_log "Creating static directories..."
    sudo mkdir -p "$MAIN_STATIC_DIR/css" || { error_log "Failed to create CSS directory"; return 1; }
    sudo mkdir -p "$MAIN_STATIC_DIR/js" || { error_log "Failed to create JS directory"; return 1; }
    sudo mkdir -p "$MAIN_STATIC_DIR/images" || { error_log "Failed to create images directory"; return 1; }
    
    # Verify source directories exist
    [ -d "./static/css" ] || { error_log "Source CSS directory not found"; return 1; }
    [ -d "./static/js" ] || { error_log "Source JS directory not found"; return 1; }

    # Backup existing files if they exist
    if [ -d "$MAIN_STATIC_DIR" ]; then
        info_log "Backing up existing static files..."
        sudo cp -r "$MAIN_STATIC_DIR" "$BACKUP_DIR" || { error_log "Failed to create backup"; return 1; }
    fi
    
    # Copy files with error handling
    info_log "Copying static files..."
    sudo cp -r "./static/css/"* "$MAIN_STATIC_DIR/css/" || { error_log "Failed to copy CSS files"; return 1; }
    sudo cp -r "./static/js/"* "$MAIN_STATIC_DIR/js/" || { error_log "Failed to copy JS files"; return 1; }
    sudo cp -r "./static/images/"* "$MAIN_STATIC_DIR/images/" 2>/dev/null || info_log "No images found"
    
    # Set permissions
    info_log "Setting permissions..."
    sudo chown -R www-data:www-data "$MAIN_APP_DIR" || { error_log "Failed to set ownership"; return 1; }
    sudo chmod -R 755 "$MAIN_APP_DIR" || { error_log "Failed to set permissions"; return 1; }
    sudo find "$MAIN_STATIC_DIR" -type f -exec chmod 644 {} \;
    
    success_log "Static files setup completed successfully"
    return 0
}

# Main deployment function
deploy() {
    info_log "Starting deployment..."
    
    # Setup static files
    setup_static_files || {
        error_log "Static files setup failed"
        return 1
    }
    
    # Restart services
    info_log "Restarting services..."
    sudo systemctl restart nginx
    sudo systemctl restart terminusa
    
    success_log "Deployment completed successfully"
}

# Execute deployment
deploy
