#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

info_log() {
    echo -e "${YELLOW}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[INFO] $(date '+%Y-%m-%极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

info_log() {
    echo -e "${YELLOW}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

# Create logs directory
mkdir -p logs

# Verify required environment variables
required_vars=(
    "MAIN_APP_DIR"
    "MAIN_STATIC_DIR"
    "DATABASE_URL"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES_DB"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        error_log "Required environment variable $var is not set"
        exit 1
    fi
done

# Setup static files
setup_static_files() {
    info_log "Setting up static files..."
    
    # Create directories with error handling
    info_log "Creating static directories..."
    sudo mkdir -p "$MAIN_STATIC_DIR/css" || { error_log "Failed to create CSS directory"; return 1; }
    sudo mkdir -p "$MAIN_STATIC_DIR/js" || { error_log "Failed to create JS directory"; return 1; }
    sudo mkdir -p "$MAIN_STATIC_DIR/images" || { error_log "Failed to create images directory"; return 1; }
    
    # Verify source directories exist
    [ -d "./static/css" ] || { error_log "Source CSS directory not found"; return 1; }
    [ -d "./static/js" ] || { error_log "Source JS directory not found"; return 1; }

    # Backup existing files if they exist
    if [ -d "$MAIN_STATIC_DIR" ]; then
        info_log "Backing up existing static files..."
        sudo cp -r "$MAIN_STATIC_DIR" "$BACKUP_DIR" || { error_log "Failed to create backup极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

info_log() {
    echo -e "${YELLOW}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

# Create logs directory
mkdir极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

info_log() {
    echo -e "${YELLOW}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

# Create logs directory
mkdir -p logs

# Verify required environment variables
required_vars=(
    "MAIN_APP_DIR"
    "MAIN_STATIC_DIR"
    "DATABASE_URL"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES_DB"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        error_log "Required environment variable $var is not set"
        exit 1
    fi
done

# Setup static files
setup_static_files() {
    info_log "Setting up static files..."
    
    # Create directories with error handling
    info_log "Creating static directories..."
    sudo mkdir -p "$MAIN_STATIC_DIR/css" || { error_log "Failed to create CSS directory"; return 1; }
    sudo mkdir -p "$MAIN_STATIC_DIR/js" || { error_log "Failed to create JS directory"; return 1; }
    sudo mkdir -p "$MAIN_STATIC_DIR/images" || { error_log "Failed to create images directory"; return 1; }
    
    # Verify source directories exist
    [ -d "./static/css" ] || { error_log "Source CSS directory not found"; return 1; }
    [ -d "./static/js极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' #极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

info_log() {
    echo -e "${YELLOW}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

# Create logs directory
mkdir -p logs

# Verify required environment variables
required_vars=(
    "MAIN_APP_DIR"
    "MAIN_STATIC_DIR"
    "DATABASE_URL"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
   极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

info_log() {
    echo -e "${YELLOW}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

# Create logs directory
mkdir -p logs

# Verify required environment variables
required_vars=(
    "MAIN_APP_DIR"
    "MAIN_STATIC_DIR"
    "DATABASE_URL"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES_DB"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        error_log "Required environment variable $极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

info_log() {
    echo -e "${YELLOW}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

# Create logs directory
mkdir -p logs

# Verify required environment variables
required_vars=(
    "MAIN_APP_DIR"
    "MAIN_STATIC_DIR"
    "DATABASE_URL"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES_DB"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        error_log "Required environment variable $var is not set"
        exit 1
    fi
done

# Setup static files
setup_static_files() {
    info_log "Setting up static files..."
    
    # Create directories with error handling
    info_log "Creating static directories..."
    sudo mkdir -p "$MAIN_STATIC_DIR/css" || { error_log "Failed to create CSS directory"; return 1; }
    sudo mkdir -p "$MAIN_STATIC_DIR/js" || { error_log "Failed to create JS directory"; return 1; }
    sudo mkdir -p "$MAIN_STATIC_DIR/images" || { error_log "Failed to create images directory"; return 1; }
    
    # Verify source directories exist
    [ -d "./static/css" ] || { error_log "Source CSS directory not found"; return 1; }
    [ -d "./static/js" ] || { error_log "Source JS directory not found"; return 1; }

    # Backup existing files if they exist
    if [ -d "$MAIN_STATIC_DIR" ]; then
        info_log "Backing up existing static files..."
        sudo cp -r "$MAIN_STATIC_DIR" "$BACKUP_DIR" || { error_log "Failed to create backup"; return 1; }
    fi
    
    # Copy files with error handling
    info_log "Copying static files..."
    sudo cp -r "./static/css/"* "$MAIN_STATIC_DIR/css/" || { error_log "Failed to copy CSS files"; return 1; }
    sudo cp -r "./static/js/"* "$MAIN_STATIC_DIR/js/" || { error_log "Failed to copy JS files"; return 1; }
    sudo cp -r "./static/images/"* "$MAIN_STATIC_DIR/images/" 2>/dev/null || info_log "极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') -极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}"
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

info_log() {
    echo -e "${YELLOW}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}
    echo "[INFO] $(date '+%Y-%m-%d %极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

info_log() {
    echo -e "${YELLOW}[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

# Create logs directory
mkdir -p logs

# Verify required environment variables
required_vars=(
    "MAIN_APP_DIR"
    "MAIN_STATIC_DIR"
    "DATABASE_URL"
    "POSTGRES_USER"
    "POSTGRES_PASSWORD"
    "POSTGRES_DB"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        error_log "Required environment variable $var is not set"
        exit 1
    fi
done

# Setup static files
setup_static_files() {
    info_log "Setting up static files..."
    
    # Create directories with error handling
    info_log "Creating static directories..."
    sudo mkdir -p "$MAIN_STATIC_DIR/css" || { error_log "Failed to create CSS directory"; return 1; }
    sudo mkdir -p "$MAIN_STATIC_DIR/js" || { error_log "Failed to create JS directory"; return 1; }
    sudo mkdir -p "$MAIN_STATIC_DIR/images" || { error_log "Failed to create images directory"; return 1; }
    
    # Verify source directories exist
    [ -d "./static/css" ] || { error_log "Source CSS directory not found"; return 1; }
    [ -d "./static/js" ] || { error_log "Source JS directory not found"; return 1; }

    # Backup existing files if they exist
    if [ -d "$MAIN_STATIC_DIR" ]; then
        info_log "Backing up existing static files..."
        sudo cp -r "$MAIN_STATIC_DIR" "$BACKUP_DIR" || { error_log "Failed to create backup"; return 1; }
    fi
    
    # Copy files with error handling
    info_log "Copying static files..."
    sudo cp -r "./static/css/"* "$MAIN_STATIC_DIR/css/" || { error_log "Failed to copy CSS files"; return 1; }
    sudo cp -r "./static/js/"* "$MAIN_STATIC_DIR/js/" || { error_log "Failed to copy JS files"; return 1; }
    sudo cp -r "./static/images/"* "$MAIN极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %极简版：
<create_file>
<path>deploy.sh极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[极简版：
<create_file>
<path>deploy.sh</path>
极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/deploy.log
}

success_log() {
    echo -e "${GREEN}[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}
    echo "[SUCCESS] $(date '+%极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Logging functions
debug_log() {
    if [ "$DEBUG" = true ]; then
        echo -e "${BLUE}[DEBUG] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}
    fi
}

error_log() {
    echo -e "${RED}[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1${NC}
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1极简版：
<create_file>
<path>deploy.sh</path>
<content>
#!/bin/bash

# Load configuration
source .env

# Colors for output
RED='\033[0
