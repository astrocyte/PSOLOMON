# PSOLOMON Deployment Scripts

Automation scripts for deploying and maintaining WordPress components.

## Available Scripts

### `deploy_plugin.sh`
Deploy WordPress plugins to staging and/or production.

**Usage:**
```bash
# Deploy to both staging and production (with confirmation)
./deploy_plugin.sh sst-affiliate-manager

# Deploy to staging only
./deploy_plugin.sh sst-affiliate-manager staging

# Deploy to production only
./deploy_plugin.sh sst-affiliate-manager production
```

**What it does:**
1. ✅ Creates backup of existing plugin on server
2. ✅ Removes old version
3. ✅ Uploads new version via SCP
4. ✅ Sets correct file permissions (755 for dirs, 644 for files)
5. ✅ Clears WordPress cache
6. ✅ Asks for confirmation before production deployment

**Example:**
```bash
$ ./deploy_plugin.sh sst-affiliate-manager staging

========================================
PSOLOMON Plugin Deployment
========================================
Plugin: sst-affiliate-manager
Environment: staging

[Deploying to Staging]
  → Creating backup...
  → Removing old version...
  → Uploading new version...
  → Setting permissions...
  → Clearing cache...
  ✓ Deployed to Staging

========================================
Deployment Complete!
========================================
```

---

### `backup_website.sh`
Create full WordPress backup (database + files).

**Usage:**
```bash
./backup_website.sh
```

**What it backs up:**
- Database (SQL dump via wp-cli)
- wp-content directory (plugins, themes, uploads)
- wp-config.php
- Creates compressed .tar.gz archive in ../backups/

---

### `backup_website_simple.sh`
Simplified backup script with minimal output.

**Usage:**
```bash
./backup_website_simple.sh
```

Same as `backup_website.sh` but with cleaner output.

---

## Configuration

All scripts use these SSH credentials (configured in scripts):
- **Host:** 147.93.88.8
- **Port:** 65002
- **User:** u629344933
- **Password:** (stored in scripts)

**Production Path:** `/home/u629344933/domains/sst.nyc/public_html`
**Staging Path:** `/home/u629344933/domains/sst.nyc/public_html/staging`

---

## Best Practices

### Before Deploying
1. Test changes locally first
2. Commit changes to git
3. Deploy to staging first
4. Test on staging thoroughly
5. Then deploy to production

### Deployment Workflow
```bash
# 1. Make changes to plugin
cd wordpress-plugins/sst-affiliate-manager
# Edit files...

# 2. Test locally (if possible)

# 3. Commit to git
cd ../..
git add wordpress-plugins/sst-affiliate-manager
git commit -m "fix: Update affiliate manager"
git push

# 4. Deploy to staging
./scripts/deploy_plugin.sh sst-affiliate-manager staging

# 5. Test on staging
# Visit https://staging.sst.nyc

# 6. Deploy to production
./scripts/deploy_plugin.sh sst-affiliate-manager production
```

### Rollback
If deployment causes issues:

```bash
# SSH to server
ssh -p 65002 u629344933@147.93.88.8

# Find backup
cd /home/u629344933/domains/sst.nyc/public_html/wp-content/plugins
ls -lh *backup*.tar.gz

# Restore from backup
tar -xzf sst-affiliate-manager_backup_20251203_160000.tar.gz

# Clear cache
cd /home/u629344933/domains/sst.nyc/public_html
wp cache flush --allow-root
```

---

## Adding New Scripts

When creating new deployment scripts:

1. **Use the template structure:**
   - Colors for output
   - Clear section headers
   - Error handling with `set -e`
   - Confirmation for production changes

2. **Follow naming convention:**
   - `deploy_*.sh` - Deployment scripts
   - `backup_*.sh` - Backup scripts
   - `restore_*.sh` - Restore scripts

3. **Make executable:**
   ```bash
   chmod +x scripts/your_script.sh
   ```

4. **Document in this README**

5. **Test on staging first!**

---

## Troubleshooting

### "Permission denied"
```bash
chmod +x scripts/deploy_plugin.sh
```

### "Plugin not found"
Check that plugin exists in `wordpress-plugins/` directory:
```bash
ls -la wordpress-plugins/
```

### "SSH connection failed"
- Check VPN connection
- Verify SSH credentials in script
- Test manual SSH: `ssh -p 65002 u629344933@147.93.88.8`

### "Deployment succeeded but plugin not working"
1. Check WordPress error logs: `/wp-content/debug.log`
2. Verify file permissions: `644` for files, `755` for directories
3. Clear all caches (WordPress, browser, CDN)
4. Check plugin is activated in WordPress Admin

---

## Security Notes

⚠️ **These scripts contain credentials!**
- Never commit to public repositories
- Keep scripts in private repos only
- Use environment variables for sensitive data (future improvement)

Current status: ✅ Scripts are in private repo only

---

## Future Enhancements

Planned improvements:
- [ ] Use .env for credentials (remove hardcoded passwords)
- [ ] Add database migration scripts
- [ ] Create automated testing before deployment
- [ ] Add Slack/email notifications for deployments
- [ ] Database search/replace for staging URL updates
- [ ] Automated rollback on error detection
