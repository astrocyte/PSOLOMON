#!/bin/bash
# WordPress Site Backup Script
# Backs up both files and database to local directory

set -e  # Exit on error

# Configuration
SSH_HOST="147.93.88.8"
SSH_PORT="65002"
SSH_USER="u629344933"
SSH_PASS="RvALk23Zgdyw4Zn"
REMOTE_PATH="/home/u629344933/domains/sst.nyc/public_html"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== WordPress Backup Script ===${NC}"
echo -e "${BLUE}Timestamp: $TIMESTAMP${NC}\n"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# 1. Database Backup
echo -e "${YELLOW}[1/3] Backing up database...${NC}"
sshpass -p "$SSH_PASS" ssh -p "$SSH_PORT" -o StrictHostKeyChecking=no -o ConnectTimeout=30 "$SSH_USER@$SSH_HOST" \
    "cd $REMOTE_PATH && wp db export - --allow-root 2>/dev/null" > "$BACKUP_DIR/database_$TIMESTAMP.sql" 2>/dev/null

if [ -f "$BACKUP_DIR/database_$TIMESTAMP.sql" ]; then
    DB_SIZE=$(du -h "$BACKUP_DIR/database_$TIMESTAMP.sql" | cut -f1)
    echo -e "${GREEN}✓ Database backed up: $DB_SIZE${NC}"
else
    echo -e "${RED}✗ Database backup failed${NC}"
    exit 1
fi

# 2. WordPress Core Files (wp-content only, skip core files to save space)
echo -e "${YELLOW}[2/3] Backing up wp-content directory...${NC}"
mkdir -p "$BACKUP_DIR/files_$TIMESTAMP"

sshpass -p "$SSH_PASS" scp -r -P "$SSH_PORT" -o StrictHostKeyChecking=no \
    "$SSH_USER@$SSH_HOST:$REMOTE_PATH/wp-content" \
    "$BACKUP_DIR/files_$TIMESTAMP/" 2>&1 | grep -v "Warning: Permanently added"

if [ -d "$BACKUP_DIR/files_$TIMESTAMP/wp-content" ]; then
    FILES_SIZE=$(du -sh "$BACKUP_DIR/files_$TIMESTAMP" | cut -f1)
    echo -e "${GREEN}✓ Files backed up: $FILES_SIZE${NC}"
else
    echo -e "${RED}✗ Files backup failed${NC}"
    exit 1
fi

# 3. wp-config.php (important configuration)
echo -e "${YELLOW}[3/3] Backing up wp-config.php...${NC}"
sshpass -p "$SSH_PASS" scp -P "$SSH_PORT" -o StrictHostKeyChecking=no \
    "$SSH_USER@$SSH_HOST:$REMOTE_PATH/wp-config.php" \
    "$BACKUP_DIR/files_$TIMESTAMP/" 2>&1 | grep -v "Warning: Permanently added"

if [ -f "$BACKUP_DIR/files_$TIMESTAMP/wp-config.php" ]; then
    echo -e "${GREEN}✓ wp-config.php backed up${NC}"
else
    echo -e "${YELLOW}⚠ wp-config.php backup failed (may not have permissions)${NC}"
fi

# Create compressed archive
echo -e "${YELLOW}Creating compressed archive...${NC}"
tar -czf "$BACKUP_DIR/sst_nyc_backup_$TIMESTAMP.tar.gz" \
    -C "$BACKUP_DIR" \
    "database_$TIMESTAMP.sql" \
    "files_$TIMESTAMP"

ARCHIVE_SIZE=$(du -h "$BACKUP_DIR/sst_nyc_backup_$TIMESTAMP.tar.gz" | cut -f1)
echo -e "${GREEN}✓ Compressed archive created: $ARCHIVE_SIZE${NC}"

# Clean up uncompressed files
rm -f "$BACKUP_DIR/database_$TIMESTAMP.sql"
rm -rf "$BACKUP_DIR/files_$TIMESTAMP"

# Summary
echo -e "\n${GREEN}=== Backup Complete ===${NC}"
echo -e "Backup saved to: ${BLUE}$BACKUP_DIR/sst_nyc_backup_$TIMESTAMP.tar.gz${NC}"
echo -e "Archive size: ${BLUE}$ARCHIVE_SIZE${NC}"
echo -e "\n${YELLOW}To restore:${NC}"
echo -e "  1. Extract: tar -xzf sst_nyc_backup_$TIMESTAMP.tar.gz"
echo -e "  2. Upload files to server"
echo -e "  3. Import database: wp db import database_$TIMESTAMP.sql"

# List all backups
echo -e "\n${BLUE}=== Available Backups ===${NC}"
ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null | awk '{print $9, "(" $5 ")"}'
