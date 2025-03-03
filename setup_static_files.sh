#!/bin/bash
set -e

echo "Setting up static files..."

# Create directories
mkdir -p static/css static/js static/fonts templates || exit 1

# Set up npm project
cd client || exit 1
rm -rf node_modules package-lock.json

# Install packages
npm install --no-bin-links xterm@5.3.0 \
    xterm-addon-fit@0.8.0 \
    xterm-addon-web-links@0.9.0 \
    xterm-addon-webgl@0.16.0 || exit 1

# Check installation
if [ ! -d "node_modules/xterm" ]; then
    echo "Error: npm install failed"
    exit 1
fi

# Copy files
cp node_modules/xterm/css/xterm.css ../static/css/ || exit 1
cp node_modules/xterm/lib/xterm.js ../static/js/ || exit 1
cp node_modules/xterm-addon-fit/lib/xterm-addon-fit.js ../static/js/ || exit 1
cp node_modules/xterm-addon-web-links/lib/xterm-addon-web-links.js ../static/js/ || exit 1
cp node_modules/xterm-addon-webgl/lib/xterm-addon-webgl.js ../static/js/ || exit 1

# Copy custom files
cp css/style.css ../static/css/ || exit 1
cp js/terminal.js ../static/js/ || exit 1
cp index.html ../templates/ || exit 1

# Create symlinks
cd ../templates || exit 1
ln -sf ../static/css/xterm.css .
ln -sf ../static/js/xterm.js .
ln -sf ../static/js/xterm-addon-fit.js .
ln -sf ../static/js/xterm-addon-web-links.js .
ln -sf ../static/js/xterm-addon-webgl.js .

echo "Setup completed successfully!"
