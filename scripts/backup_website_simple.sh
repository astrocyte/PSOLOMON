#!/bin/bash
# Simple WordPress Backup Script
# Downloads database and wp-content to local backups directory

set -e

BACKUP_DIR="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/sst_nyc_$TIMESTAMP"

echo "=== WordPress Backup ==="
echo "Timestamp: $TIMESTAMP"
echo

# Create backup directories
mkdir -p "$BACKUP_PATH"

# 1. Backup Database
echo "[1/2] Backing up database..."
sshpass -p 'RvALk23Zgdyw4Zn' ssh -p 65002 -o StrictHostKeyChecking=no u629344933@147.93.88.8 \
    'cd /home/u629344933/domains/sst.nyc/public_html && wp db export - --allow-root' \
    > "$BACKUP_PATH/database.sql" 2>/dev/null

DB_SIZE=$(du -h "$BACKUP_PATH/database.sql" | awk '{print $1}')
echo "✓ Database backed up: $DB_SIZE"

# 2. Backup wp-content
echo "[2/2] Backing up wp-content (this may take a while)..."
sshpass -p 'RvALk23Zgdyw4Zn' scp -r -P 65002 -o StrictHostKeyChecking=no \
    u629344933@147.93.88.8:/home/u629344933/domains/sst.nyc/public_html/wp-content \
    "$BACKUP_PATH/" 2>&1 | grep -v "Warning:" || true

FILES_SIZE=$(du -sh "$BACKUP_PATH/wp-content" | awk '{print $1}')
echo "✓ Files backed up: $FILES_SIZE"

# 3. Backup wp-config.php
echo "[3/3] Backing up wp-config.php..."
sshpass -p 'RvALk23Zgdyw4Zn' scp -P 65002 -o StrictHostKeyChecking=no \
    u629344933@147.93.88.8:/home/u629344933/domains/sst.nyc/public_html/wp-config.php \
    "$BACKUP_PATH/" 2>&1 | grep -v "Warning:" || true
echo "✓ wp-config.php backed up"

# 4. Create compressed archive
echo
echo "Creating compressed archive..."
tar -czf "$BACKUP_DIR/sst_nyc_$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "sst_nyc_$TIMESTAMP"

ARCHIVE_SIZE=$(du -h "$BACKUP_DIR/sst_nyc_$TIMESTAMP.tar.gz" | awk '{print $1}')
echo "✓ Archive created: $ARCHIVE_SIZE"

# Clean up uncompressed files
rm -rf "$BACKUP_PATH"

echo
echo "=== Backup Complete ==="
echo "Saved to: $BACKUP_DIR/sst_nyc_$TIMESTAMP.tar.gz"
echo "Size: $ARCHIVE_SIZE"
echo
echo "To restore:"
echo "  tar -xzf $BACKUP_DIR/sst_nyc_$TIMESTAMP.tar.gz"
echo

# List all backups
echo "=== All Backups ==="
ls -lh "$BACKUP_DIR"/*.tar.gz 2>/dev/null | awk '{print $9, "(" $5 ")"}' || echo "No backups found"
