#!/bin/bash
# PSOLOMON Plugin Deployment Script
# Deploy WordPress plugins to production and staging

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
SSH_HOST="147.93.88.8"
SSH_PORT="65002"
SSH_USER="u629344933"
SSH_PASS="RvALk23Zgdyw4Zn"
PROD_PATH="/home/u629344933/domains/sst.nyc/public_html/wp-content/plugins"
STAGING_PATH="/home/u629344933/domains/sst.nyc/public_html/staging/wp-content/plugins"

# Get plugin name from argument
PLUGIN_NAME="$1"
ENVIRONMENT="${2:-both}"  # both, staging, or production

if [ -z "$PLUGIN_NAME" ]; then
    echo -e "${RED}Usage: $0 <plugin-name> [environment]${NC}"
    echo -e "${YELLOW}Available plugins:${NC}"
    ls -1 ../wordpress-plugins/
    echo -e "${YELLOW}Environments: staging, production, both (default)${NC}"
    exit 1
fi

PLUGIN_PATH="../wordpress-plugins/$PLUGIN_NAME"

if [ ! -d "$PLUGIN_PATH" ]; then
    echo -e "${RED}Error: Plugin '$PLUGIN_NAME' not found in wordpress-plugins/${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}PSOLOMON Plugin Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Plugin: ${GREEN}$PLUGIN_NAME${NC}"
echo -e "Environment: ${GREEN}$ENVIRONMENT${NC}"
echo

# Function to deploy to a specific environment
deploy_to_env() {
    local env_name=$1
    local remote_path=$2

    echo -e "${YELLOW}[Deploying to $env_name]${NC}"

    # 1. Backup existing plugin on server
    echo -e "  → Creating backup..."
    sshpass -p "$SSH_PASS" ssh -p "$SSH_PORT" -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" \
        "cd $remote_path && if [ -d $PLUGIN_NAME ]; then tar -czf ${PLUGIN_NAME}_backup_$(date +%Y%m%d_%H%M%S).tar.gz $PLUGIN_NAME 2>/dev/null || true; fi" \
        2>&1 | grep -v "Warning:" || true

    # 2. Remove old plugin
    echo -e "  → Removing old version..."
    sshpass -p "$SSH_PASS" ssh -p "$SSH_PORT" -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" \
        "rm -rf $remote_path/$PLUGIN_NAME" 2>&1 | grep -v "Warning:" || true

    # 3. Upload new plugin
    echo -e "  → Uploading new version..."
    sshpass -p "$SSH_PASS" scp -r -P "$SSH_PORT" -o StrictHostKeyChecking=no \
        "$PLUGIN_PATH" "$SSH_USER@$SSH_HOST:$remote_path/" 2>&1 | grep -v "Warning:" || true

    # 4. Set correct permissions
    echo -e "  → Setting permissions..."
    sshpass -p "$SSH_PASS" ssh -p "$SSH_PORT" -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" \
        "cd $remote_path && find $PLUGIN_NAME -type d -exec chmod 755 {} \; && find $PLUGIN_NAME -type f -exec chmod 644 {} \;" \
        2>&1 | grep -v "Warning:" || true

    # 5. Clear WordPress cache
    echo -e "  → Clearing cache..."
    if [ "$env_name" = "Production" ]; then
        sshpass -p "$SSH_PASS" ssh -p "$SSH_PORT" -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" \
            "cd /home/u629344933/domains/sst.nyc/public_html && wp cache flush --allow-root" \
            2>&1 | grep -v "Warning:" || true
    else
        sshpass -p "$SSH_PASS" ssh -p "$SSH_PORT" -o StrictHostKeyChecking=no "$SSH_USER@$SSH_HOST" \
            "cd /home/u629344933/domains/sst.nyc/public_html/staging && wp cache flush --allow-root" \
            2>&1 | grep -v "Warning:" || true
    fi

    echo -e "${GREEN}  ✓ Deployed to $env_name${NC}"
    echo
}

# Deploy to selected environments
if [ "$ENVIRONMENT" = "staging" ] || [ "$ENVIRONMENT" = "both" ]; then
    deploy_to_env "Staging" "$STAGING_PATH"
fi

if [ "$ENVIRONMENT" = "production" ] || [ "$ENVIRONMENT" = "both" ]; then
    echo -e "${YELLOW}⚠️  Deploying to PRODUCTION${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" = "yes" ]; then
        deploy_to_env "Production" "$PROD_PATH"
    else
        echo -e "${YELLOW}Production deployment cancelled${NC}"
    fi
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo
echo -e "Next steps:"
echo -e "1. Test the plugin on staging: ${BLUE}https://staging.sst.nyc${NC}"
echo -e "2. Check WordPress Admin → Plugins"
echo -e "3. Monitor error logs for any issues"
echo
