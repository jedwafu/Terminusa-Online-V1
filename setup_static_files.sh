#!/bin/bash

# Setup script for static files in Terminusa Online

# Exit on any error
set -e

# Create necessary directories
echo "Creating directories..."
mkdir -p static/css
mkdir -p static/js
mkdir -p static/fonts

# Navigate to client directory
cd client

# Install npm dependencies
echo "Installing client dependencies..."
npm install

# Copy xterm.js files
echo "Copying xterm.js files..."
cp node_modules/xterm/css/xterm.css ../static/css/
cp node_modules/xterm/lib/xterm.js ../static/js/
cp node_modules/xterm-addon-fit/lib/xterm-addon-fit.js ../static/js/
cp node_modules/xterm-addon-web-links/lib/xterm-addon-web-links.js ../static/js/
cp node_modules/xterm-addon-webgl/lib/xterm-addon-webgl.js ../static/js/

# Copy our custom files
echo "Copying custom files..."
cp css/style.css ../static/css/
cp js/terminal.js ../static/js/
cp index.html ../templates/

# Set permissions
echo "Setting permissions..."
chmod -R 755 ../static
chmod -R 755 ../templates

echo "Static files setup complete!"
