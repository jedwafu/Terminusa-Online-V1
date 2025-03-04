#!/bin/bash

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Export Flask app
export FLASK_APP=app.py

# Run migrations
echo "Running database migrations..."
flask db upgrade

# Check if migration was successful
if [ $? -eq 0 ]; then
    echo "Migration completed successfully"
else
    echo "Migration failed"
    exit 1
fi
