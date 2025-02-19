#!/bin/bash

# Create images directory if it doesn't exist
mkdir -p static/images

# Create a temporary directory for image generation
TEMP_DIR=$(mktemp -d)

# Generate matrix code effect using ImageMagick
convert -size 800x600 xc:black \
  -font "Courier" -pointsize 20 -fill "#00FF41" \
  -gravity center -annotate 0 "$(cat /dev/urandom | tr -dc 'A-Za-z0-9' | fold -w 100 | head -n 30)" \
  "$TEMP_DIR/matrix-code.png"

# Generate matrix rain effect
convert -size 800x600 xc:black \
  -font "Courier" -pointsize 15 -fill "#00FF41" \
  -gravity north -annotate 0 "$(cat /dev/urandom | tr -dc '01' | fold -w 80 | head -n 40)" \
  "$TEMP_DIR/matrix-rain.png"

# Create hero background
convert -size 1920x1080 xc:black \
  -fill "#001100" -draw "rectangle 0,0 1920,1080" \
  -blur 0x5 \
  "$TEMP_DIR/hero-bg.jpg"

# Move generated images to static directory
mv "$TEMP_DIR/matrix-code.png" static/images/
mv "$TEMP_DIR/matrix-rain.png" static/images/
mv "$TEMP_DIR/hero-bg.jpg" static/images/

# Clean up
rm -rf "$TEMP_DIR"

# Set permissions
chmod 644 static/images/*

echo "Matrix-themed images have been generated and set up"

# Create symbolic links if needed
ln -sf $(pwd)/static/images /var/www/terminusa/static/images 2>/dev/null || true
