#!/bin/bash
set -e

# Create directories
mkdir -p static/css static/js static/fonts templates

# Set up npm
mkdir -p "$HOME/.npm"
export NPM_CONFIG_PREFIX="$HOME/.npm"
export NPM_CONFIG_CACHE="$HOME/.npm/cache"

# Install dependencies
cd client
rm -rf node_modules package-lock.json

# Install packages
npm install --no-bin-links xterm@5.3.0
npm install --no-bin-links xterm-addon-fit@0.8.0
npm install --no-bin-links xterm-addon-web-links@0.9.0
npm install --no-bin-links xterm-addon-webgl@0.16.0

# Check installation
if [ ! -d "node_modules/xterm" ]; then
    echo "Error: npm install failed"
    exit 1
fi

# Copy files
cp node_modules/xterm/css/xterm.css ../static/css/
cp node_modules/xterm/lib/xterm.js ../static/js/
cp node_modules/xterm-addon-fit/lib/xterm-addon-fit.js ../static/js/
cp node_modules/xterm-addon-web-links/lib/xterm-addon-web-links.js ../static/js/
cp node_modules/xterm-addon-webgl/lib/xterm-addon-webgl.js ../static/js/

cp css/style.css ../static/css/
cp js/terminal.js ../static/js/
cp index.html ../templates/

# Create symlinks
cd ../templates
ln -sf ../static/css/xterm.css .
ln -sf ../static/js/xterm.js .
ln -sf ../static/js/xterm-addon-fit.js .
ln -sf ../static/js/xterm-addon-web-links.js .
ln -sf ../static/js/xterm-addon-webgl.js .
