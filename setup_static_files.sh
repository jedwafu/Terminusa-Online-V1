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
NGINX_ROOT="/var/www/terminusa"
NGINX_STATIC_DIR="$NGINX_ROOT/static"
BACKUP_DIR="$NGINX_ROOT/static_backup"

# Function to check if command succeeded
check_command() {
    if [ $? -ne 0 ]; then
        log_error "$1"
        exit 1
    fi
}

# Function to verify directory exists and is writable
verify_dir() {
    if [ ! -d "$1" ]; then
        log_error "Directory not found: $1"
        return 1
    fi
    if [ ! -w "$1" ]; then
        log_error "Directory not writable: $1"
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

# Create nginx root directory if it doesn't exist
log_info "Creating nginx root directory..."
sudo mkdir -p $NGINX_ROOT
check_command "Failed to create nginx root directory"

# Backup existing files
if [ -d "$NGINX_STATIC_DIR" ]; then
    log_info "Backing up existing static files..."
    sudo rm -rf $BACKUP_DIR
    sudo mv $NGINX_STATIC_DIR $BACKUP_DIR
    check_command "Failed to backup existing files"
fi

# Create nginx static directory
log_info "Creating nginx static directory..."
sudo mkdir -p $NGINX_STATIC_DIR
check_command "Failed to create nginx static directory"

# Copy static files
log_info "Copying static files..."
sudo cp -r $STATIC_DIR/* $NGINX_STATIC_DIR/
check_command "Failed to copy static files"

# Set permissions
log_info "Setting permissions..."
sudo chown -R www-data:www-data $NGINX_ROOT
sudo chmod -R 755 $NGINX_ROOT
check_command "Failed to set permissions"

# Verify CSS files exist
log_info "Verifying CSS files..."
REQUIRED_CSS=("style.css" "buttons.css" "alerts.css")
for css_file in "${REQUIRED_CSS[@]}"; do
    if [ ! -f "$NGINX_STATIC_DIR/css/$css_file" ]; then
        log_error "Required CSS file missing: $css_file"
        if [ -d "$BACKUP_DIR" ]; then
            log_info "Restoring from backup..."
            sudo rm -rf $NGINX_STATIC_DIR
            sudo mv $BACKUP_DIR $NGINX_STATIC_DIR
        fi
        exit 1
    fi
done

# Print directory structure for verification
log_info "Static files structure:"
ls -R $NGINX_STATIC_DIR

# Test nginx configuration
log_info "Testing nginx configuration..."
sudo nginx -t
check_command "Nginx configuration test failed"

# Clear nginx cache
log_info "Clearing nginx cache..."
sudo rm -rf /var/cache/nginx/*
check_command "Failed to clear nginx cache"

# Restart nginx
log_info "Restarting nginx..."
sudo systemctl restart nginx
check_command "Failed to restart nginx"

log_success "Static files setup completed successfully"

# Verify file permissions
log_info "Final permission verification:"
ls -la $NGINX_STATIC_DIR/css/
