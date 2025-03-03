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

# Function to check if a command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo "$1 is required but not installed."
        exit 1
    fi
}

# Check required commands
check_command npm
check_command node

# Create necessary directories
echo "Creating directories..."
mkdir -p static/css
mkdir -p static/js
mkdir -p static/fonts
mkdir -p templates
mkdir -p logs

# Set up logging
LOG_FILE="logs/setup.log"
exec 1> >(tee -a "$LOG_FILE")
exec 2> >(tee -a "$LOG_FILE" >&2)

echo "Starting setup at $(date)"

# Navigate to client directory
cd client || exit 1

# Clean existing installation
echo "Cleaning existing installation..."
rm -rf node_modules
rm -f package-lock.json

# Create temporary npm directories with proper permissions
TEMP_NPM_DIR="/tmp/npm-$RANDOM"
mkdir -p "$TEMP_NPM_DIR"/{cache,global}
chmod -R 777 "$TEMP_NPM_DIR"

# Set npm config
echo "Configuring npm..."
export NPM_CONFIG_CACHE="$TEMP_NPM_DIR/cache"
export NPM_CONFIG_PREFIX="$TEMP_NPM_DIR/global"
export NPM_CONFIG_UNSAFE_PERM=true

# Install dependencies
echo "Installing client dependencies..."
npm install --no-bin-links --force \
    xterm@5.3.0 \
    xterm-addon-fit@0.8.0 \
    xterm-addon-web-links@0.9.0 \
    xterm-addon-webgl@0.16.0

# Verify installation
echo "Verifying installation..."
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
        rm -rf "$TEMP_NPM_DIR"
        exit 1
    fi
done

# Copy xterm.js files
echo "Copying xterm.js files..."
cp node_modules/xterm/css/xterm.css ../static/css/ || exit 1
cp node_modules/xterm/lib/xterm.js ../static/js/ || exit 1
cp node_modules/xterm-addon-fit/lib/xterm-addon-fit.js ../static/js/ || exit 1
cp node_modules/xterm-addon-web-links/lib/xterm-addon-web-links.js ../static/js/ || exit 1
cp node_modules/xterm-addon-webgl/lib/xterm-addon-webgl.js ../static/js/ || exit 1

# Copy custom files
echo "Copying custom files..."
cp css/style.css ../static/css/ || exit 1
cp js/terminal.js ../static/js/ || exit 1
cp index.html ../templates/ || exit 1

# Set permissions
echo "Setting permissions..."
chmod -R 755 ../static
chmod -R 755 ../templates
chmod -R 755 ../logs

# Clean up
echo "Cleaning up..."
rm -rf "$TEMP_NPM_DIR"

# Create symbolic links if needed
echo "Creating symbolic links..."
ln -sf ../static/css/xterm.css ../templates/
ln -sf ../static/js/xterm.js ../templates/
ln -sf ../static/js/xterm-addon-fit.js ../templates/
ln -sf ../static/js/xterm-addon-web-links.js ../templates/
ln -sf ../static/js/xterm-addon-webgl.js ../templates/

# Verify final setup
echo "Verifying final setup..."
final_required_files=(
    "../static/css/xterm.css"
    "../static/css/style.css"
    "../static/js/xterm.js"
    "../static/js/terminal.js"
    "../static/js/xterm-addon-fit.js"
    "../static/js/xterm-addon-web-links.js"
    "../static/js/xterm-addon-webgl.js"
    "../templates/index.html"
)

for file in "${final_required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "Final verification failed: $file not found"
        exit 1
    fi
done

# Set up static file serving
echo "Setting up static file serving..."
if [ ! -f "../static/.htaccess" ]; then
    cat > "../static/.htaccess" << EOL
Header set Cache-Control "max-age=3600, public"
AddType application/javascript .js
AddType text/css .css
EOL
fi

# Create version file
echo "Creating version file..."
VERSION="1.0.0"
echo "$VERSION" > "../static/version.txt"

echo "Static files setup completed successfully at $(date)"
echo "Log file available at $LOG_FILE"
exit 0
