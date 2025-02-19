#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check command status
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Success${NC}"
    else
        echo -e "${RED}✗ Failed${NC}"
        exit 1
    fi
}

echo -e "${YELLOW}Setting up Terminusa Online database...${NC}"

# Check if running in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}Please activate virtual environment first${NC}"
    exit 1
fi

# Install requirements
echo -e "\n${YELLOW}Installing requirements...${NC}"
pip install -r requirements.txt
check_status

# Set Flask environment variables
export FLASK_APP=init_db.py
export PYTHONPATH=$PWD

# Initialize database
echo -e "\n${YELLOW}Initializing database...${NC}"
python init_db.py
check_status

# Initialize migrations
echo -e "\n${YELLOW}Initializing migrations...${NC}"
if [ ! -d "migrations" ]; then
    flask db init
    check_status
fi

# Create initial migration
echo -e "\n${YELLOW}Creating initial migration...${NC}"
flask db migrate -m "Initial database setup"
check_status

# Apply migrations
echo -e "\n${YELLOW}Applying migrations...${NC}"
flask db upgrade
check_status

echo -e "\n${GREEN}Database setup completed successfully!${NC}"
echo -e "You can now start the application with:"
echo -e "  python app_final.py"
echo -e "And the terminal server with:"
echo -e "  python terminal_server.py"
