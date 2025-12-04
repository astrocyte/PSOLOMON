# PSOLOMON Documentation

Complete documentation for the Predictive Safety Operations & Learning Management System.

## Documentation Index

### Core System
- **[AFFILIATE_ENHANCEMENTS.md](./AFFILIATE_ENHANCEMENTS.md)** - Complete affiliate program documentation
  - Deactivate/reactivate functionality
  - Custom commission rates
  - Coupon management
  - API reference

- **[CODE_REVIEW_AFFILIATE_ENHANCEMENTS.md](./CODE_REVIEW_AFFILIATE_ENHANCEMENTS.md)** - Security review
  - Code quality assessment
  - Security audit
  - Performance considerations
  - Deployment verification

- **[TESTING_GUIDE.md](./TESTING_GUIDE.md)** - Testing procedures
  - Test scenarios for all features
  - Edge cases
  - Browser compatibility
  - Regression testing

### Backup & Maintenance
- **[BACKUP_GUIDE.md](./BACKUP_GUIDE.md)** - Backup and restore procedures
  - Hostinger built-in backups
  - All-in-One WP Migration
  - Custom backup scripts
  - Emergency restore procedures

- **[MCP_BACKUP_USAGE.md](./MCP_BACKUP_USAGE.md)** - MCP backup tools usage
  - How to use backup commands with Claude
  - Examples and best practices

## Quick Links

### For Daily Operations
- Creating backups: See [MCP_BACKUP_USAGE.md](./MCP_BACKUP_USAGE.md)
- Managing affiliates: See [AFFILIATE_ENHANCEMENTS.md](./AFFILIATE_ENHANCEMENTS.md)
- Testing changes: See [TESTING_GUIDE.md](./TESTING_GUIDE.md)

### For Troubleshooting
- Security issues: See [CODE_REVIEW](./CODE_REVIEW_AFFILIATE_ENHANCEMENTS.md)
- Backup problems: See [BACKUP_GUIDE.md](./BACKUP_GUIDE.md)
- Test failures: See [TESTING_GUIDE.md](./TESTING_GUIDE.md)

## MCP Tools Available

### WordPress Management
- `wp_get_info` - Site information
- `wp_plugin_list` - List plugins
- `wp_theme_list` - List themes
- `wp_post_list` - List posts/pages
- `wp_check_updates` - Check for updates

### Backup Management
- `wp_create_backup` - Create complete backup
- `wp_list_backups` - List available backups
- `wp_delete_backup` - Delete old backups

### LearnDash LMS
- `ld_create_course` - Create course
- `ld_create_lesson` - Create lesson
- `ld_create_quiz` - Create quiz
- `ld_enroll_user` - Enroll student
- `ld_create_group` - Create group

### WooCommerce
- `wc_create_product` - Create product
- `wc_list_orders` - List orders
- `wc_create_coupon` - Create coupon
- `wc_get_sales_report` - Sales reports

### SEO & Content
- `seo_analyze_post` - Analyze SEO
- `elementor_extract_content` - Extract Elementor content
- `image_optimize` - Optimize images

## Getting Help

### Ask Claude Code
Just describe what you need:
- "Create a backup"
- "List all courses"
- "Show me recent orders"
- "Analyze SEO for this post"

### Check Documentation
All detailed procedures are in this docs/ directory.

### Error Logs
Production: `/home/u629344933/domains/sst.nyc/logs/`
WordPress: `/wp-content/debug.log`

## Contributing

When adding new documentation:
1. Create a new .md file in this directory
2. Add it to this README index
3. Link it from relevant docs
4. Use clear headings and examples

## Version History

See main [README.md](../README.md) for version history and changelog.
