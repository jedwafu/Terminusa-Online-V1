#!/bin/bash

# Exit on any error
set -e

# Error handling
handle_error() {
    echo "Error occurred in setup_static_files.sh"
    echo "Error on line $1"
    exit 1
}

trap 'handle_error $LINENO' ERR

# Create necessary directories
echo "Creating directories..."
mkdir -p static/css
mkdir -p static/js
mkdir -p static/fonts
mkdir -p templates

# Navigate to client directory
cd client || exit 1

# Install npm dependencies
echo "Installing client dependencies..."
if [ ! -d "node_modules" ]; then
    # Create temporary npm directories with proper permissions
    TEMP_NPM_DIR="/tmp/npm-$RANDOM"
    mkdir -p "$TEMP_NPM_DIR"/{cache,global}
    chmod -R 777 "$TEMP_NPM_DIR"

    # Install dependencies with proper npm config
    echo "Running npm install..."
    export NPM_CONFIG_CACHE="$TEMP_NPM_DIR/cache"
    export NPM_CONFIG_PREFIX="$TEMP_NPM_DIR/global"
    export NPM_CONFIG_UNSAFE_PERM=true
    
    if ! npm install --no-bin-links; then
        echo "npm install failed"
        rm -rf "$TEMP_NPM_DIR"
        exit 1
    fi

    # Clean up
    rm -rf "$TEMP_NPM_DIR"
    echo "npm dependencies installed successfully"
else
    echo "Node modules already installed"
fi

# Verify required files exist
echo "Verifying xterm.js files..."
required_files=(
    "node_modules/xterm/css/xterm.css"
    "node_modules/xterm/lib/xterm.js"
    "node_modules/xterm-addon-fit/lib/xterm-addon-fit.js"
    "node_modules/xterm-addon-web-links/lib/xterm-addon-web-links.js"
    "node_modules/xterm-addon-webgl/lib/xterm-addon-webgl.js"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "Required file not found: $file"
        exit 1
    fi
done

# Copy files
echo "Copying xterm.js files..."
cp node_modules/xterm/css/xterm.css ../static/css/ || exit 1
cp node_modules/xterm/lib/xterm.js ../static/js/ || exit 1
cp node_modules/xterm-addon-fit/lib/xterm-addon-fit.js ../static/js/ || exit 1
cp node_modules/xterm-addon-web-links/lib/xterm-addon-web-links.js ../static/js/ || exit 1
cp node_modules/xterm-addon-webgl/lib/xterm-addon-webgl.js ../static/js/ || exit 1

# Copy our custom files
echo "Copying custom files..."
cp css/style.css ../static/css/ || exit 1
cp js/terminal.js ../static/js/ || exit 1
cp index.html ../templates/ || exit 1

# Set permissions
echo "Setting permissions..."
chmod -R 755 ../static
chmod -R 755 ../templates

echo "Static files setup complete!"
exit 0
