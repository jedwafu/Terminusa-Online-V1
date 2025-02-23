#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    set -a
    source .env
    set +a
else
    echo "Error: .env file not found"
    exit 1
fi

# Set up static directory structure
STATIC_DIR="${STATIC_DIR:-/var/www/terminusa/static}"
SOURCE_DIR="${SOURCE_DIR:-./static}"

# Create directories with error handling
mkdir -p "$STATIC_DIR/css" || { echo "Error: Failed to create CSS directory"; exit 1; }
mkdir -p "$STATIC_DIR/js" || { echo "Error: Failed to create JS directory"; exit 1; }
mkdir -p "$STATIC_DIR/images" || { echo "Error: Failed to images directory"; exit 1; }

# Verify source directories exist
[ -d "$SOURCE_DIR/css" ] || { echo "Error: Source CSS directory not found"; exit 1; }
[ -d "$SOURCE_DIR/js" ] || { echo "Error: Source JS directory not found"; exit 1; }

# Copy files with error handling
cp -r "$SOURCE_DIR/css/"* "$STATIC_DIR/css/" || { echo "Error: Failed to copy CSS files"; exit 1; }
cp -r "$SOURCE_DIR/js/"* "$STATIC_DIR/js/" || { echo "Error: Failed to copy JS files"; exit 1; }
cp -r "$SOURCE_DIR/images/"* "$STATIC_DIR/images/" 2>/dev/null || echo "Warning: No images found"

# Set permissions
chown -R www-data:www-data "$STATIC_DIR" || { echo "Error: Failed to set ownership"; exit 1; }
chmod -R 755 "$STATIC_DIR" || { echo "Error: Failed to set permissions"; exit 1; }

# Verify nginx directory exists
if [ ! -d "/var/www/terminusa" ]; then
    echo "Error: Nginx directory /var/www/terminusa not found"
    exit 1
fi

# Create symbolic link
ln -sfn "$STATIC_DIR" "/var/www/terminusa/static" || { echo "Error: Failed to create symbolic link"; exit 1; }

# Restart Flask application
systemctl restart terminusa || { echo "Error: Failed to restart terminusa service"; exit 1; }

echo "Static files have been successfully set up for Flask"
