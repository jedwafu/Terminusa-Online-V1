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
PROJECT_ROOT=$(pwd)
STATIC_DIR="$PROJECT_ROOT/static"
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

# Clean up old nginx configurations
log_info "Cleaning up old nginx configurations..."
sudo rm -f /etc/nginx/sites-enabled/terminusa.conf
sudo rm -f /etc/nginx/sites-available/terminusa
sudo rm -f /etc/nginx/sites-available/terminusa.conf
sudo rm -f /etc/nginx/conf.d/terminusa.conf

# Install new nginx configurations
log_info "Installing new nginx configurations..."
sudo cp nginx/terminusa.conf /etc/nginx/sites-available/
sudo cp nginx/terminusa-terminal.conf /etc/nginx/conf.d/
sudo ln -sf /etc/nginx/sites-available/terminusa.conf /etc/nginx/sites-enabled/

# Verify source static directory exists
if [ ! -d "$STATIC_DIR" ]; then
    log_error "Source static directory not found: $STATIC_DIR"
    exit 1
fi

# Verify CSS files exist in source
log_info "Verifying source CSS files..."
REQUIRED_CSS=("style.css" "buttons.css" "alerts.css")
for css_file in "${REQUIRED_CSS[@]}"; do
    if [ ! -f "$STATIC_DIR/css/$css_file" ]; then
        log_error "Required CSS file missing in source: $css_file"
        exit 1
    fi
    log_success "Found $css_file"
done

# Stop nginx before making changes
log_info "Stopping nginx..."
sudo systemctl stop nginx
check_command "Failed to stop nginx"

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
for css_file in "${REQUIRED_CSS[@]}"; do
    log_info "Copying $css_file..."
    sudo cp "$STATIC_DIR/css/$css_file" "$NGINX_STATIC_DIR/css/"
    check_command "Failed to copy $css_file"
    
    # Verify the copy
    if ! verify_file "$NGINX_STATIC_DIR/css/$css_file"; then
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
if [ -d "$STATIC_DIR/js" ]; then
    sudo cp -r $STATIC_DIR/js/* $NGINX_STATIC_DIR/js/ 2>/dev/null || true
fi
if [ -d "$STATIC_DIR/images" ]; then
    sudo cp -r $STATIC_DIR/images/* $NGINX_STATIC_DIR/images/ 2>/dev/null || true
fi

# Set permissions
log_info "Setting permissions..."
sudo chown -R www-data:www-data $NGINX_ROOT
sudo chmod -R 755 $NGINX_ROOT
check_command "Failed to set permissions"

# Print directory structure for verification
log_info "Static files structure:"
ls -R $NGINX_STATIC_DIR

# Test nginx configuration
log_info "Testing nginx configuration..."
sudo nginx -t
check_command "Nginx configuration test failed"

# Start nginx
log_info "Starting nginx..."
sudo systemctl start nginx
check_command "Failed to start nginx"

# Verify nginx is running
if ! systemctl is-active --quiet nginx; then
    log_error "nginx failed to start"
    exit 1
fi

# Test file access
log_info "Testing file access..."
for css_file in "${REQUIRED_CSS[@]}"; do
    if ! sudo -u www-data test -r "$NGINX_STATIC_DIR/css/$css_file"; then
        log_error "www-data cannot read $css_file"
        exit 1
    fi
    log_success "www-data can read $css_file"
done

# Clear nginx cache
log_info "Clearing nginx cache..."
sudo rm -rf /var/cache/nginx/*
check_command "Failed to clear nginx cache"

# Verify file permissions and ownership
log_info "Final verification:"
ls -la $NGINX_STATIC_DIR/css/

# Test nginx configuration one last time
log_info "Final nginx configuration test..."
sudo nginx -t
check_command "Final nginx configuration test failed"

# Reload nginx to apply changes
log_info "Reloading nginx..."
sudo systemctl reload nginx
check_command "Failed to reload nginx"

# Print nginx configuration status
log_info "Nginx configuration files:"
echo "sites-available:"
ls -la /etc/nginx/sites-available/
echo "sites-enabled:"
ls -la /etc/nginx/sites-enabled/
echo "conf.d:"
ls -la /etc/nginx/conf.d/

log_info "Static files in nginx directory:"
ls -la $NGINX_STATIC_DIR/css/

log_success "Static files setup completed successfully"
