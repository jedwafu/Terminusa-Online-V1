#!/bin/bash

# Deployment script for both development and production
echo "Starting deployment..."

# Configuration
PROD_SERVER="46.250.228.210"
PROD_USER="root"
APP_DIR="/var/www/terminusa"
BACKUP_DIR="/var/www/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Error handling
set -e
trap 'echo -e "${RED}Deployment failed${NC}"; exit 1' ERR

# Function to deploy to production
deploy_production() {
    echo -e "${YELLOW}Preparing for production deployment...${NC}"

    # Create backup directory if it doesn't exist
    ssh $PROD_USER@$PROD_SERVER "mkdir -p $BACKUP_DIR"

    # Backup current version
    echo -e "${YELLOW}Creating backup of current version...${NC}"
    ssh $PROD_USER@$PROD_SERVER "if [ -d $APP_DIR ]; then tar -czf $BACKUP_DIR/terminusa_$TIMESTAMP.tar.gz -C $APP_DIR .; fi"

    # Build and optimize static assets
    echo -e "${YELLOW}Building and optimizing static assets...${NC}"
    npm run build
    python manage.py collectstatic --noinput
    python manage.py compress --force

    # Create deployment package
    echo -e "${YELLOW}Creating deployment package...${NC}"
    tar -czf deploy.tar.gz \
        --exclude='*.pyc' \
        --exclude='__pycache__' \
        --exclude='.git' \
        --exclude='.env' \
        --exclude='node_modules' \
        --exclude='tests' \
        --exclude='*.log' \
        .

    # Upload deployment package
    echo -e "${YELLOW}Uploading deployment package...${NC}"
    scp deploy.tar.gz $PROD_USER@$PROD_SERVER:/tmp/

    # Deploy on production server
    echo -e "${YELLOW}Deploying on production server...${NC}"
    ssh $PROD_USER@$PROD_SERVER << 'EOF'
        # Stop services
        systemctl stop terminusa
        systemctl stop terminusa-terminal

        # Clear application directory
        rm -rf $APP_DIR/*

        # Extract new version
        mkdir -p $APP_DIR
        tar -xzf /tmp/deploy.tar.gz -C $APP_DIR

        # Set permissions
        chown -R www-data:www-data $APP_DIR
        chmod -R 755 $APP_DIR

        # Install/update dependencies
        cd $APP_DIR
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt

        # Run database migrations
        python manage.py migrate --noinput

        # Clear cache
        python manage.py clear_cache

        # Update static files
        python manage.py collectstatic --noinput

        # Reload Nginx configuration
        nginx -t && systemctl reload nginx

        # Start services
        systemctl start terminusa
        systemctl start terminusa-terminal

        # Clean up
        rm /tmp/deploy.tar.gz

        # Verify services
        systemctl status terminusa
        systemctl status terminusa-terminal
EOF

    echo -e "${GREEN}Production deployment completed successfully!${NC}"

    # Verify deployment
    echo -e "${YELLOW}Verifying deployment...${NC}"
    curl -s https://terminusa.online/health | grep -q "ok" && \
        echo -e "${GREEN}Main website is up${NC}" || \
        echo -e "${RED}Main website verification failed${NC}"

    curl -s https://play.terminusa.online/health | grep -q "ok" && \
        echo -e "${GREEN}Game server is up${NC}" || \
        echo -e "${RED}Game server verification failed${NC}"

    # Cleanup local deployment files
    rm deploy.tar.gz
}

# Function to rollback production
rollback_production() {
    echo -e "${YELLOW}Available backups:${NC}"
    ssh $PROD_USER@$PROD_SERVER "ls -lt $BACKUP_DIR"

    read -p "Enter backup timestamp to restore (YYYYMMDD_HHMMSS): " BACKUP_TIMESTAMP

    # Verify backup exists
    ssh $PROD_USER@$PROD_SERVER "test -f $BACKUP_DIR/terminusa_$BACKUP_TIMESTAMP.tar.gz" || {
        echo -e "${RED}Backup not found${NC}"
        exit 1
    }

    echo -e "${YELLOW}Rolling back to backup from $BACKUP_TIMESTAMP...${NC}"

    ssh $PROD_USER@$PROD_SERVER << EOF
        # Stop services
        systemctl stop terminusa
        systemctl stop terminusa-terminal

        # Clear application directory
        rm -rf $APP_DIR/*

        # Restore from backup
        tar -xzf $BACKUP_DIR/terminusa_$BACKUP_TIMESTAMP.tar.gz -C $APP_DIR

        # Set permissions
        chown -R www-data:www-data $APP_DIR
        chmod -R 755 $APP_DIR

        # Activate virtual environment
        cd $APP_DIR
        source venv/bin/activate

        # Run database migrations
        python manage.py migrate --noinput

        # Clear cache
        python manage.py clear_cache

        # Reload Nginx configuration
        nginx -t && systemctl reload nginx

        # Start services
        systemctl start terminusa
        systemctl start terminusa-terminal
EOF

    echo -e "${GREEN}Rollback completed successfully!${NC}"
}

# Function to deploy locally
deploy_local() {
    echo -e "${YELLOW}Starting local deployment...${NC}"

    # Install dependencies
    pip install -r requirements.txt

    # Run migrations
    python manage.py migrate

    # Collect static files
    python manage.py collectstatic --noinput

    # Start development server
    python manage.py runserver
}

# Main deployment logic
case "$1" in
    "production")
        deploy_production
        ;;
    "rollback")
        rollback_production
        ;;
    "local")
        deploy_local
        ;;
    *)
        echo "Usage: $0 {production|rollback|local}"
        echo "  production: Deploy to production server"
        echo "  rollback: Rollback production to previous version"
        echo "  local: Deploy locally for development"
        exit 1
        ;;
esac

echo -e "\n${GREEN}Deployment process completed!${NC}"
