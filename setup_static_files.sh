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
NGINX_ROOT="/var/www/terminusa"
NGINX_STATIC_DIR="$NGINX_ROOT/static"
BACKUP_DIR="$NGINX_ROOT/static_backup"
PROJECT_ROOT=$(pwd)

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

# Create nginx static directory structure
log_info "Creating nginx static directory structure..."
sudo mkdir -p $NGINX_STATIC_DIR/{css,js,images}
check_command "Failed to create nginx static directories"

# Copy static files
log_info "Copying static files..."

# Copy CSS files with verification
log_info "Copying CSS files..."
REQUIRED_CSS=("style.css" "buttons.css" "alerts.css" "auth.css")
for css_file in "${REQUIRED_CSS[@]}"; do
    source_file="$PROJECT_ROOT/static/css/$css_file"
    target_file="$NGINX_STATIC_DIR/css/$css_file"
    
    if [ ! -f "$source_file" ]; then
        log_error "Required CSS file missing in source: $css_file"
        exit 1
    fi
    
    sudo cp "$source_file" "$target_file"
    check_command "Failed to copy $css_file"
    
    # Verify the copy
    if ! verify_file "$target_file"; then
        log_error "Failed to verify copied file: $css_file"
        if [ -d "$BACKUP_DIR" ]; then
            log_info "Restoring from backup..."
            sudo rm -rf $NGINX_STATIC_DIR
            sudo mv $BACKUP_DIR $NGINX_STATIC_DIR
        fi
        exit 1
    fi
    log_success "Successfully copied and verified $css_file"
done

# Copy remaining static files
log_info "Copying remaining static files..."
if [ -d "$PROJECT_ROOT/static/js" ]; then
    sudo cp -r $PROJECT_ROOT/static/js/* $NGINX_STATIC_DIR/js/ 2>/dev/null || true
fi
if [ -d "$PROJECT_ROOT/static/images" ]; then
    sudo cp -r $PROJECT_ROOT/static/images/* $NGINX_STATIC_DIR/images/ 2>/dev/null || true
fi

# Set permissions
log_info "Setting permissions..."
sudo chown -R www-data:www-data $NGINX_ROOT
sudo chmod -R 755 $NGINX_ROOT
check_command "Failed to set permissions"

# Print directory structure for verification
log_info "Static files structure:"
ls -R $NGINX_STATIC_DIR

# Verify file permissions and ownership
log_info "Final verification:"
ls -la $NGINX_STATIC_DIR/css/

# Test nginx configuration
log_info "Testing nginx configuration..."
sudo nginx -t
check_command "Nginx configuration test failed"

# Reload nginx to apply changes
log_info "Reloading nginx..."
sudo systemctl reload nginx
check_command "Failed to reload nginx"

# Clear nginx cache
log_info "Clearing nginx cache..."
sudo rm -rf /var/cache/nginx/*
check_command "Failed to clear nginx cache"

# Final verification
log_info "Verifying file access..."
for css_file in "${REQUIRED_CSS[@]}"; do
    if ! sudo -u www-data test -r "$NGINX_STATIC_DIR/css/$css_file"; then
        log_error "www-data cannot read $css_file"
        exit 1
    fi
    log_success "www-data can read $css_file"
done

log_success "Static files setup completed successfully"
