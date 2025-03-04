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

# Get absolute paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATIC_DIR="${SCRIPT_DIR}/static"
TEMPLATES_DIR="${SCRIPT_DIR}/templates"
CLIENT_DIR="${SCRIPT_DIR}/client"

# Check if client directory exists
if [ ! -d "${CLIENT_DIR}" ]; then
    log_error "Client directory not found: ${CLIENT_DIR}"
    exit 1
fi

# Install dependencies
log_info "Installing dependencies"

# Clean up previous installations
log_info "Cleaning up previous installations"
rm -rf "${CLIENT_DIR}/node_modules" "${CLIENT_DIR}/package-lock.json"

# Create package.json if it doesn't exist
if [ ! -f "${CLIENT_DIR}/package.json" ]; then
    log_info "Creating package.json"
    echo '{
  "name": "terminusa-client",
  "version": "1.0.0",
  "private": true
}' > "${CLIENT_DIR}/package.json"
fi

# Install packages with error handling
log_info "Installing npm packages"
(cd "${CLIENT_DIR}" && \
npm install --no-bin-links \
  xterm@5.3.0 \
  xterm-addon-fit@0.8.0 \
  xterm-addon-web-links@0.9.0 \
  xterm-addon-webgl@0.16.0) || { log_error "Failed to install npm packages"; exit 1; }

# Check installation
if [ ! -d "${CLIENT_DIR}/node_modules/xterm" ]; then
    log_error "Error: npm install failed, xterm module not found"
    exit 1
fi

# Get absolute paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATIC_DIR="${SCRIPT_DIR}/static"
TEMPLATES_DIR="${SCRIPT_DIR}/templates"
CLIENT_DIR="${SCRIPT_DIR}/client"

# Copy files with validation
log_info "Copying files to static directories"
copy_file "${CLIENT_DIR}/node_modules/xterm/css/xterm.css" "${STATIC_DIR}/css/xterm.css"
copy_file "${CLIENT_DIR}/node_modules/xterm/lib/xterm.js" "${STATIC_DIR}/js/xterm.js"
copy_file "${CLIENT_DIR}/node_modules/xterm-addon-fit/lib/xterm-addon-fit.js" "${STATIC_DIR}/js/xterm-addon-fit.js"
copy_file "${CLIENT_DIR}/node_modules/xterm-addon-web-links/lib/xterm-addon-web-links.js" "${STATIC_DIR}/js/xterm-addon-web-links.js"
copy_file "${CLIENT_DIR}/node_modules/xterm-addon-webgl/lib/xterm-addon-webgl.js" "${STATIC_DIR}/js/xterm-addon-webgl.js"

copy_file "${CLIENT_DIR}/css/style.css" "${STATIC_DIR}/css/style.css"
copy_file "${CLIENT_DIR}/js/terminal.js" "${STATIC_DIR}/js/terminal.js"
copy_file "${CLIENT_DIR}/index.html" "${TEMPLATES_DIR}/index.html"

# Create symlinks with validation
log_info "Creating symlinks in templates directory"
create_symlink "${STATIC_DIR}/css/xterm.css" "${TEMPLATES_DIR}/xterm.css"
create_symlink "${STATIC_DIR}/js/xterm.js" "${TEMPLATES_DIR}/xterm.js"
create_symlink "${STATIC_DIR}/js/xterm-addon-fit.js" "${TEMPLATES_DIR}/xterm-addon-fit.js"
create_symlink "${STATIC_DIR}/js/xterm-addon-web-links.js" "${TEMPLATES_DIR}/xterm-addon-web-links.js"
create_symlink "${STATIC_DIR}/js/xterm-addon-webgl.js" "${TEMPLATES_DIR}/xterm-addon-webgl.js"

log_success "Static files setup completed successfully"
