# Using MCP Backup Tools with Claude Code

## Overview

You now have WordPress backup functionality integrated directly into your MCP server! Just tell Claude to create a backup and it handles everything.

## How It Works

The MCP server now has 3 new tools:
1. **wp_create_backup** - Creates and downloads complete WordPress backup
2. **wp_list_backups** - Shows all local backups
3. **wp_delete_backup** - Removes old backups

## Usage Examples

### Create a Backup

Just say:
```
"Create a backup of the WordPress site"
```

Or:
```
"Backup the website"
```

Claude will:
1. Connect to your server via SSH
2. Export database using wp-cli
3. Download wp-content directory via SFTP
4. Download wp-config.php
5. Create compressed .tar.gz archive
6. Save to `./backups/sst_nyc_YYYYMMDD_HHMMSS.tar.gz`

**Example output:**
```
Backup Created Successfully!

Timestamp: 20251203_153000
Archive: ./backups/sst_nyc_20251203_153000.tar.gz
Total Size: 856.3 MB

Backed up:
- Database: ✓ 45.2 MB
- Files: ✓ 823.1 MB

The backup is saved locally and excluded from git via .gitignore
```

### List Available Backups

```
"Show me all backups"
```

Or:
```
"List backups"
```

**Example output:**
```
Available Backups:

- sst_nyc_20251203_153000.tar.gz
  Size: 856.3 MB
  Created: 2025-12-03 15:30:00

- sst_nyc_20251201_120000.tar.gz
  Size: 842.1 MB
  Created: 2025-12-01 12:00:00
```

### Delete Old Backup

```
"Delete backup sst_nyc_20251201_120000.tar.gz"
```

**Example output:**
```
✓ Backup deleted: sst_nyc_20251201_120000.tar.gz
```

### Database Only Backup

```
"Create a database-only backup"
```

This will backup just the database, skipping files (faster, smaller).

### Files Only Backup

```
"Create a files-only backup"
```

This will backup wp-content directory without the database.

## Backup Contents

Each backup includes:

✅ **Database** (SQL dump)
- All WordPress tables
- Posts, pages, users, settings
- WooCommerce data
- LearnDash courses
- Affiliate data

✅ **wp-content/** directory
- `/plugins/` - All installed plugins
- `/themes/` - All themes
- `/uploads/` - All media files

✅ **wp-config.php**
- Database credentials
- Security keys
- WordPress configuration

❌ **NOT included:**
- WordPress core files (can be reinstalled)
- Cache files
- Temporary files

## Storage Location

**Local Directory:** `./backups/`

**Git Status:** Excluded (in .gitignore)

**Typical Sizes:**
- Database: 40-200 MB
- Files: 500 MB - 2 GB
- Total compressed: 500 MB - 1.5 GB

## Restore Process

To restore a backup:

```bash
# 1. Extract the backup
tar -xzf backups/sst_nyc_20251203_153000.tar.gz

# 2. Upload files to server
scp -r sst_nyc_20251203_153000/wp-content/* \
    u629344933@147.93.88.8:/home/u629344933/domains/sst.nyc/public_html/wp-content/

# 3. Import database
sshpass -p 'RvALk23Zgdyw4Zn' ssh -p 65002 u629344933@147.93.88.8 \
    'cd /home/u629344933/domains/sst.nyc/public_html && wp db import - --allow-root' \
    < sst_nyc_20251203_153000/database.sql

# 4. Clear cache
wp cache flush
```

Or use Hostinger's backup restore feature (easier!).

## Best Practices

1. **Before Major Changes**
   - "Create a backup before I make changes"
   - Proceed with confidence!

2. **Regular Backups**
   - Weekly: "Create a backup"
   - Keep 3-5 recent backups

3. **Clean Up Old Backups**
   - "Delete old backups" (keeps latest 3)
   - Or manually: "Delete backup sst_nyc_OLD.tar.gz"

4. **Test Restores**
   - Occasionally test restoring to staging
   - Verify backup integrity

## MCP Configuration

The backup tools use your existing MCP configuration:

**Required in `.env`:**
```bash
SSH_HOST=147.93.88.8
SSH_PORT=65002
SSH_USER=u629344933
SSH_PASSWORD=RvALk23Zgdyw4Zn
REMOTE_PATH=/home/u629344933/domains/sst.nyc/public_html
```

Already configured! No additional setup needed.

## Advantages Over Manual Backups

✅ **Faster** - Just ask Claude, no manual commands
✅ **Consistent** - Same process every time
✅ **Automated** - Downloads, compresses, saves automatically
✅ **Git-safe** - Never committed to repository
✅ **Convenient** - Use natural language

## Troubleshooting

### "Backup failed: Connection refused"
- Check VPN/network connection
- Verify SSH credentials in .env

### "Disk space full"
- Delete old backups: "List backups" then "Delete backup X"
- Check `./backups/` directory size

### "Backup too slow"
- Create database-only backup (much faster)
- Files backup can take 5-10 minutes for large sites

### "Can't find backup"
- Check `./backups/` directory
- Run: "List backups"

## Related Documentation

- [BACKUP_GUIDE.md](./BACKUP_GUIDE.md) - Complete backup guide
- [README.md](./README.md) - Project overview
- [AFFILIATE_ENHANCEMENTS.md](./AFFILIATE_ENHANCEMENTS.md) - Affiliate features

## Technical Details

**Python Module:** `wordpress-mcp-server/src/backup_manager.py`

**Key Functions:**
- `create_backup()` - Main backup function
- `list_backups()` - List local backups
- `delete_backup()` - Remove backup file

**Dependencies:**
- `paramiko` - SSH/SFTP client
- `tarfile` - Archive creation
- WordPress wp-cli (on server)

---

**Now go ahead and try it!**

Just say: "Create a backup" and watch it work! 🚀
