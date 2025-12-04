# WordPress Backup Guide for SST.NYC

## Recommended: Hostinger Built-in Backups

### Access Hostinger Backups
1. Go to https://hpanel.hostinger.com
2. Navigate to: **Websites** → **sst.nyc** → **Backups**
3. View available backups (Hostinger creates automatic weekly backups)
4. Click **Download** to get a complete site backup

**Advantages:**
- ✅ Automatic weekly backups
- ✅ Includes files + database
- ✅ No server storage consumed
- ✅ One-click restore
- ✅ Managed by Hostinger (reliable)

---

## Alternative: All-in-One WP Migration Plugin

You already have this installed! Use it for quick backups.

### Create Backup via Plugin
1. Go to WordPress Admin → **All-in-One WP Migration** → **Export**
2. Choose export destination (File, Google Drive, etc.)
3. Wait for backup to complete
4. Download the .wpress file

**Location on server:**
```
/home/u629344933/domains/sst.nyc/public_html/wp-content/ai1wm-backups/
```

### Download Plugin Backup Locally
```bash
sshpass -p 'RvALk23Zgdyw4Zn' scp -P 65002 -o StrictHostKeyChecking=no \
    'u629344933@147.93.88.8:/home/u629344933/domains/sst.nyc/public_html/wp-content/ai1wm-backups/*.wpress' \
    ./backups/
```

---

## Custom Script: Local Development Backups

Use our custom script when you need a local copy for development.

### Run Backup Script
```bash
./backup_website_simple.sh
```

**What it backs up:**
- Database (SQL dump)
- wp-content directory (plugins, themes, uploads)
- wp-config.php

**Output:**
```
./backups/sst_nyc_YYYYMMDD_HHMMSS.tar.gz
```

**Restore:**
```bash
# Extract
tar -xzf backups/sst_nyc_YYYYMMDD_HHMMSS.tar.gz

# Upload files
scp -r sst_nyc_YYYYMMDD_HHMMSS/wp-content user@server:/path/

# Import database
wp db import sst_nyc_YYYYMMDD_HHMMSS/database.sql
```

---

## Backup Schedule Recommendation

### Daily/Weekly (Automatic)
- ✅ **Hostinger automatic backups** (weekly)
- No action required!

### Before Major Changes
1. Go to hPanel → Backups → **Create Backup**
2. Wait 5-10 minutes
3. Proceed with changes

### Local Development Copy (As Needed)
```bash
./backup_website_simple.sh
```

---

## Emergency Restore

### From Hostinger Backup
1. Go to hPanel → Backups
2. Select backup date
3. Click **Restore**
4. Wait for confirmation
5. Clear WordPress cache

### From Plugin Backup
1. WordPress Admin → All-in-One WP Migration → **Import**
2. Upload .wpress file
3. Click **Import**
4. Wait for completion
5. Re-login to WordPress

### From Local Backup
1. Extract .tar.gz file
2. Upload via SCP/SFTP
3. Import database via wp-cli
4. Update wp-config.php if needed
5. Run: `wp cache flush`

---

## What to Backup

### Critical Files
✅ Database (all content, settings, users)
✅ wp-content/plugins/ (custom plugins)
✅ wp-content/themes/ (custom themes)
✅ wp-content/uploads/ (media files)
✅ wp-config.php (database credentials, security keys)

### Not Critical (Can Skip)
❌ WordPress core files (can reinstall)
❌ Default themes (can reinstall)
❌ Cache files
❌ Log files

---

## Backup Storage

### Git-Ignored Directories
```
./backups/           # Local backups (git-ignored)
*.tar.gz             # Compressed archives (git-ignored)
*.sql                # Database dumps (git-ignored)
*.wpress             # Plugin backups (git-ignored)
```

### Recommended Storage
1. **Hostinger backups** - Automatic, off-site
2. **Local backups** - `./backups/` directory (development only)
3. **External** - Google Drive, Dropbox (for critical backups)

**Never commit backups to git!** (Already in .gitignore)

---

## Quick Commands

### List Available Backups
```bash
# Hostinger backups
# Go to hPanel → Backups

# Plugin backups (on server)
sshpass -p 'RvALk23Zgdyw4Zn' ssh -p 65002 u629344933@147.93.88.8 \
    'ls -lh /home/u629344933/domains/sst.nyc/public_html/wp-content/ai1wm-backups/'

# Local backups
ls -lh ./backups/
```

### Create Manual Database Backup
```bash
sshpass -p 'RvALk23Zgdyw4Zn' ssh -p 65002 u629344933@147.93.88.8 \
    'cd /home/u629344933/domains/sst.nyc/public_html && wp db export - --allow-root' \
    > ./backups/database_$(date +%Y%m%d).sql
```

### Download wp-content Only
```bash
sshpass -p 'RvALk23Zgdyw4Zn' scp -r -P 65002 \
    u629344933@147.93.88.8:/home/u629344933/domains/sst.nyc/public_html/wp-content \
    ./backups/wp-content_$(date +%Y%m%d)/
```

---

## Best Practices

1. ✅ **Before major updates** - Create manual backup
2. ✅ **Before plugin changes** - Quick backup via plugin
3. ✅ **Monthly** - Download a local copy
4. ✅ **After big changes** - Test restore process
5. ✅ **Keep 3 backups** - Current, last week, last month

---

## Backup Size Estimates

**Database:** ~50-200 MB (grows with content)
**wp-content:** ~1-5 GB (depends on media uploads)
**Total compressed:** ~500 MB - 2 GB

**Storage needed:** Plan for 5-10 GB for multiple backup versions

---

## Troubleshooting

### Backup Too Large
- Use Hostinger backups (no local storage)
- Exclude wp-content/uploads in custom script
- Compress with higher ratio: `tar -czf9`

### Download Failed
- Check internet connection
- Use `rsync` instead of `scp` (resumes failed transfers)
- Download in parts (database first, then files)

### Restore Issues
- Check file permissions (should be 644 for files, 755 for directories)
- Verify database credentials in wp-config.php
- Clear all caches after restore
- Check .htaccess file

---

## Related Documentation

- [Affiliate Enhancements](./AFFILIATE_ENHANCEMENTS.md)
- [Testing Guide](./TESTING_GUIDE.md)
- [Code Review](./CODE_REVIEW_AFFILIATE_ENHANCEMENTS.md)
