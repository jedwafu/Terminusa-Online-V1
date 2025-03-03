#!/bin/bash
set -e

# Error handling
error_exit() {
    echo "Error: ${1:-"Unknown Error"}" 1>&2
    exit 1
}

# Ensure we're in the correct directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR" || error_exit "Could not change to script directory"

# Create directories
echo "Creating directories..."
mkdir -p static/css static/js static/fonts templates || error_exit "Failed to create directories"

# Set up npm environment
export HOME=${HOME:-/home/terminusa}
export NPM_CONFIG_PREFIX=${NPM_CONFIG_PREFIX:-$HOME/.npm}
export NPM_CONFIG_CACHE=${NPM_CONFIG_CACHE:-$HOME/.npm/cache}

# Create npm directories
mkdir -p "$NPM_CONFIG_PREFIX" "$NPM_CONFIG_CACHE" || error_exit "Failed to create npm directories"

# Navigate to client directory and install dependencies
echo "Installing dependencies..."
cd client || error_exit "Client directory not found"

# Clean existing installation
rm -rf node_modules package-lock.json

# Install specific versions
echo "Running npm install..."
npm install --no-bin-links \
    xterm@5.3.0 \
    xterm-addon-fit@0.8.0 \
    xterm-addon-web-links@0.9.0 \
    xterm-addon-webgl@0.16.0 || error_exit "npm install failed"

# Check for required files
echo "Verifying files..."
REQUIRED_FILES=(
    "node_modules/xterm/css/xterm.css"
    "node_modules/xterm/lib/xterm.js"
    "node_modules/xterm-addon-fit/lib/xterm-addon-fit.js"
    "node_modules/xterm-addon-web-links/lib/xterm-addon-web-links.js"
    "node_modules/xterm-addon-webgl/lib/xterm-addon-webgl.js"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        error_exit "Required file not found: $file"
    fi
done

# Copy files
echo "Copying files..."
cp node_modules/xterm/css/xterm.css ../static/css/ || error_exit "Failed to copy xterm.css"
cp node_modules/xterm/lib/xterm.js ../static/js/ || error_exit "Failed to copy xterm.js"
cp node_modules/xterm-addon-fit/lib/xterm-addon-fit.js ../static/js/ || error_exit "Failed to copy addon-fit.js"
cp node_modules/xterm-addon-web-links/lib/xterm-addon-web-links.js ../static/js/ || error_exit "Failed to copy addon-web-links.js"
cp node_modules/xterm-addon-webgl/lib/xterm-addon-webgl.js ../static/js/ || error_exit "Failed to copy addon-webgl.js"

# Copy custom files
cp css/style.css ../static/css/ || error_exit "Failed to copy style.css"
cp js/terminal.js ../static/js/ || error_exit "Failed to copy terminal.js"
cp index.html ../templates/ || error_exit "Failed to copy index.html"

# Set permissions
echo "Setting permissions..."
chmod -R 755 ../static || error_exit "Failed to set static permissions"
chmod -R 755 ../templates || error_exit "Failed to set templates permissions"

# Create symlinks
echo "Creating symlinks..."
cd ../templates || error_exit "Failed to change to templates directory"
ln -sf ../static/css/xterm.css . || error_exit "Failed to create xterm.css symlink"
ln -sf ../static/js/xterm.js . || error_exit "Failed to create xterm.js symlink"
ln -sf ../static/js/xterm-addon-fit.js . || error_exit "Failed to create addon-fit.js symlink"
ln -sf ../static/js/xterm-addon-web-links.js . || error_exit "Failed to create addon-web-links.js symlink"
ln -sf ../static/js/xterm-addon-webgl.js . || error_exit "Failed to create addon-webgl.js symlink"

echo "Static files setup completed successfully!"
