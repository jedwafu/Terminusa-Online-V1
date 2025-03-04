#!/bin/bash
# Improved setup_static_files.sh script
# This script sets up static files for Terminusa Online

# Enable error handling
set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to create directory safely
create_dir() {
    if [ ! -d "$1" ]; then
        log_info "Creating directory: $1"
        mkdir -p "$1" || { log_error "Failed to create directory: $1"; exit 1; }
    else
        log_info "Directory already exists: $1"
    fi
}

# Function to copy file with validation
copy_file() {
    log_info "Copying $1 to $2"
    cp "$1" "$2" || { log_error "Failed to copy $1 to $2"; exit 1; }
    if [ ! -f "$2" ]; then
        log_error "File not found after copy: $2"
        exit 1
    fi
}

# Function to create symlink safely
create_symlink() {
    log_info "Creating symlink: $1 -> $2"
    ln -sf "$1" "$2" || { log_error "Failed to create symlink: $1 -> $2"; exit 1; }
}

# Main script starts here
log_info "Starting static files setup"

# Check for npm
if ! command_exists npm; then
    log_error "npm is not installed. Please install Node.js and npm first."
    exit 1
fi

# Create base directories
log_info "Creating base directories"
create_dir "static/css"
create_dir "static/js"
create_dir "static/fonts"
create_dir "templates"

# Set up npm configuration
log_info "Setting up npm configuration"
create_dir "$HOME/.npm"
export NPM_CONFIG_PREFIX="$HOME/.npm"
export NPM_CONFIG_CACHE="$HOME/.npm/cache"

# Install dependencies
log_info "Installing dependencies"
cd client || { log_error "client directory not found"; exit 1; }

# Clean up previous installations
log_info "Cleaning up previous installations"
rm -rf node_modules package-lock.json

# Install packages with error handling
log_info "Installing npm packages"
npm install --no-bin-links xterm@5.3.0 || { log_error "Failed to install xterm"; exit 1; }
npm install --no-bin-links xterm-addon-fit@0.8.0 || { log_error "Failed to install xterm-addon-fit"; exit 1; }
npm install --no-bin-links xterm-addon-web-links@0.9.0 || { log_error "Failed to install xterm-addon-web-links"; exit 1; }
npm install --no-bin-links xterm-addon-webgl@0.16.0 || { log_error "Failed to install xterm-addon-webgl"; exit 1; }

# Check installation
if [ ! -d "node_modules/xterm" ]; then
    log_error "Error: npm install failed, xterm module not found"
    exit 1
fi

# Copy files with validation
log_info "Copying files to static directories"
copy_file "node_modules/xterm/css/xterm.css" "../static/css/"
copy_file "node_modules/xterm/lib/xterm.js" "../static/js/"
copy_file "node_modules/xterm-addon-fit/lib/xterm-addon-fit.js" "../static/js/"
copy_file "node_modules/xterm-addon-web-links/lib/xterm-addon-web-links.js" "../static/js/"
copy_file "node_modules/xterm-addon-webgl/lib/xterm-addon-webgl.js" "../static/js/"

copy_file "css/style.css" "../static/css/"
copy_file "js/terminal.js" "../static/js/"
copy_file "index.html" "../templates/"

# Create symlinks with validation
log_info "Creating symlinks in templates directory"
cd ../templates || { log_error "templates directory not found"; exit 1; }
create_symlink "../static/css/xterm.css" "xterm.css"
create_symlink "../static/js/xterm.js" "xterm.js"
create_symlink "../static/js/xterm-addon-fit.js" "xterm-addon-fit.js"
create_symlink "../static/js/xterm-addon-web-links.js" "xterm-addon-web-links.js"
create_symlink "../static/js/xterm-addon-webgl.js" "xterm-addon-webgl.js"

log_success "Static files setup completed successfully"
