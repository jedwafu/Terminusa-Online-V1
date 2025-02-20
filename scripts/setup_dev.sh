#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Error handling
set -e
trap 'last_command=$current_command; current_command=$BASH_COMMAND' DEBUG
trap 'echo -e "${RED}\"${last_command}\" command failed with exit code $?.${NC}"' EXIT

# Logging functions
log_info() {
    echo -e "${YELLOW}[INFO] $1${NC}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Check Python version
check_python() {
    log_info "Checking Python version..."
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed!"
        exit 1
    fi
    
    python3_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$python3_version < 3.10" | bc -l) )); then
        log_error "Python 3.10 or later is required!"
        exit 1
    fi
    
    log_success "Python $python3_version found"
}

# Check PostgreSQL
check_postgresql() {
    log_info "Checking PostgreSQL..."
    if ! command -v psql &> /dev/null; then
        log_error "PostgreSQL is not installed!"
        echo "Please install PostgreSQL:"
        echo "1. sudo apt update"
        echo "2. sudo apt install postgresql postgresql-contrib"
        echo "3. sudo systemctl enable postgresql"
        echo "4. sudo systemctl start postgresql"
        exit 1
    fi
    
    if ! systemctl is-active --quiet postgresql; then
        log_error "PostgreSQL is not running!"
        exit 1
    fi
    
    log_success "PostgreSQL is installed and running"
}

# Check Redis
check_redis() {
    log_info "Checking Redis..."
    if ! command -v redis-cli &> /dev/null; then
        log_error "Redis is not installed!"
        echo "Please install Redis:"
        echo "1. sudo apt update"
        echo "2. sudo apt install redis-server"
        echo "3. sudo systemctl enable redis-server"
        echo "4. sudo systemctl start redis-server"
        exit 1
    fi
    
    if ! systemctl is-active --quiet redis-server; then
        log_error "Redis is not running!"
        exit 1
    fi
    
    log_success "Redis is installed and running"
}

# Create virtual environment
create_venv() {
    log_info "Creating virtual environment..."
    if [ -d "venv" ]; then
        log_info "Virtual environment already exists, recreating..."
        rm -rf venv
    fi
    python3 -m venv venv
    source venv/bin/activate
    log_success "Virtual environment created and activated"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    log_success "Dependencies installed"
}

# Create required directories
create_directories() {
    log_info "Creating required directories..."
    mkdir -p logs
    mkdir -p instance
    mkdir -p static/downloads
    mkdir -p data/{market,combat,social,ai}
    log_success "Directories created"
}

# Set file permissions
set_permissions() {
    log_info "Setting file permissions..."
    chmod -R 755 static
    chmod +x *.py
    chmod +x scripts/*.py
    chmod +x *.sh
    log_success "Permissions set"
}

# Initialize environment file
init_env() {
    log_info "Initializing environment file..."
    if [ ! -f ".env" ]; then
        cp .env.example .env
        log_info "Please update .env file with your configuration"
        read -p "Press Enter after updating .env file..."
    else
        log_info ".env file already exists"
    fi
    log_success "Environment file initialized"
}

# Initialize database
init_database() {
    log_info "Initializing database..."
    python scripts/init_database.py
    log_success "Database initialized"
}

# Install pre-commit hooks
install_hooks() {
    log_info "Installing pre-commit hooks..."
    pre-commit install
    log_success "Pre-commit hooks installed"
}

# Main setup function
main() {
    log_info "Starting development environment setup..."
    
    # Check requirements
    check_python
    check_postgresql
    check_redis
    
    # Setup virtual environment and dependencies
    create_venv
    install_dependencies
    
    # Setup project structure
    create_directories
    set_permissions
    init_env
    
    # Initialize database
    init_database
    
    # Setup development tools
    install_hooks
    
    log_success "Development environment setup complete!"
    
    # Print next steps
    echo
    echo "Next steps:"
    echo "1. Update the .env file with your configuration"
    echo "2. Run 'source venv/bin/activate' to activate the virtual environment"
    echo "3. Run 'python app_final.py' to start the development server"
    echo "4. Visit http://localhost:5000 to view the application"
}

# Run main function
main
