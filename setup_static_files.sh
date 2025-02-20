#!/bin/bash

# Exit on error
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Log functions
log_info() { echo -e "${YELLOW}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Define directories
STATIC_DIR="static"
NGINX_STATIC_DIR="/var/www/terminusa/static"
BACKUP_DIR="/var/www/terminusa/static_backup"

# Function to check if command succeeded
check_command() {
    if [ $? -ne 0 ]; then
        log_error "$1"
        exit 1
    fi
}

# Function to verify file exists and is readable
verify_file() {
    if [ ! -f "$1" ]; then
        log_error "File not found: $1"
        return 1
    fi
    if [ ! -r "$1" ]; then
        log_error "File not readable: $1"
        return 1
    fi
    return 0
}

log_info "Starting static files setup..."

# Verify source static directory exists
if [ ! -d "$STATIC_DIR" ]; then
    log_error "Source static directory not found!"
    exit 1
fi

# Create necessary directories
log_info "Creating directories..."
mkdir -p $STATIC_DIR/{css,js,images,img}
sudo mkdir -p $NGINX_STATIC_DIR
check_command "Failed to create directories"

# Backup existing files
if [ -d "$NGINX_STATIC_DIR" ]; then
    log_info "Backing up existing static files..."
    sudo rm -rf $BACKUP_DIR
    sudo mv $NGINX_STATIC_DIR $BACKUP_DIR
    check_command "Failed to backup existing files"
fi

# Copy static files
log_info "Copying static files..."
sudo cp -r $STATIC_DIR/* $NGINX_STATIC_DIR/
check_command "Failed to copy static files"

# Set permissions
log_info "Setting permissions..."
sudo chown -R www-data:www-data $NGINX_STATIC_DIR
sudo chmod -R 755 $NGINX_STATIC_DIR
check_command "Failed to set permissions"

# Verify critical CSS files
log_info "Verifying CSS files..."
REQUIRED_CSS=("base.css" "style.css" "buttons.css" "alerts.css")
for css_file in "${REQUIRED_CSS[@]}"; do
    if ! verify_file "$NGINX_STATIC_DIR/css/$css_file"; then
        if [ -d "$BACKUP_DIR" ]; then
            log_info "Restoring from backup..."
            sudo rm -rf $NGINX_STATIC_DIR
            sudo mv $BACKUP_DIR $NGINX_STATIC_DIR
        fi
        exit 1
    fi
done

# Verify nginx configuration
log_info "Testing nginx configuration..."
sudo nginx -t
check_command "Nginx configuration test failed"

# Clear nginx cache
log_info "Clearing nginx cache..."
sudo rm -rf /var/cache/nginx/*
check_command "Failed to clear nginx cache"

# Verify nginx is running
if ! systemctl is-active --quiet nginx; then
    log_info "Starting nginx..."
    sudo systemctl start nginx
    check_command "Failed to start nginx"
fi

log_success "Static files setup completed successfully"

# Print verification information
echo -e "\nStatic files structure:"
ls -la $NGINX_STATIC_DIR/css/
