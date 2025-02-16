#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Reinstalling Terminusa Online Dependencies${NC}"

# Activate virtual environment if not already activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Uninstall problematic packages
echo -e "${YELLOW}Removing problematic packages...${NC}"
pip uninstall -y pyOpenSSL cryptography

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}Installing server dependencies...${NC}"
pip install -r requirements-server.txt

# Verify installations
echo -e "${YELLOW}Verifying installations...${NC}"
pip list | grep -E "pyOpenSSL|cryptography"

echo -e "${GREEN}Dependencies reinstalled successfully!${NC}"
echo -e "${YELLOW}Now restart the server:${NC}"
echo -e "  ${GREEN}sudo systemctl restart gunicorn${NC}"
