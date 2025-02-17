#!/bin/bash

# Stop the server
echo "Stopping the server..."
bash start_server.sh stop

# Apply database migrations
echo "Applying database migrations..."
python -m flask db upgrade head

# Apply the patch
echo "Applying code changes..."
git apply announcements.patch

# Copy template and CSS files
echo "Updating template and CSS files..."
cp templates/announcements_updated.html templates/announcements.html
cp static/css/announcements.css static/css/

# Restart the server
echo "Restarting the server..."
bash start_server.sh restart

echo "Deployment complete!"
echo "Please verify the following:"
echo "1. The announcements page is accessible"
echo "2. Only admin users can create/edit/delete announcements"
echo "3. The design and layout are properly applied"
