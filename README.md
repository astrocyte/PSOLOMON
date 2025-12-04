# PSOLOMON
**Predictive Safety Operations & Learning Management System**

Virtual website administrator for SST.NYC - Complete WordPress management system powered by Claude Code and MCP.

---

## What is PSOLOMON?

PSOLOMON is your AI-powered virtual website admin that:
- 🔧 Manages WordPress plugins and configuration
- 📚 Handles LearnDash LMS (courses, lessons, quizzes, enrollments)
- 🛒 Manages WooCommerce (products, orders, coupons)
- 👥 Runs the affiliate program
- 💾 Creates and manages backups
- 🔍 Optimizes SEO and content
- 📊 Tracks performance and analytics

**Just tell Claude what you need, and PSOLOMON handles it.**

---

## Project Structure

```
PSOLOMON/
├── mcp-server/              # MCP Server - Claude's interface to WordPress
│   ├── src/                 # All WordPress management tools
│   │   ├── server.py        # Main MCP server
│   │   ├── backup_manager.py
│   │   ├── learndash_manager.py
│   │   ├── woocommerce_manager.py
│   │   ├── wp_cli.py
│   │   └── wp_api.py
│   └── pyproject.toml
│
├── wordpress-plugins/       # Custom WordPress plugins
│   ├── sst-affiliate-manager/
│   │   ├── includes/
│   │   ├── admin/
│   │   └── sst-affiliate-manager.php
│   └── README.md
│
├── scripts/                 # Deployment & maintenance scripts
│   ├── deploy_plugin.sh     # Deploy plugins to production
│   ├── backup_website.sh    # Manual backup script
│   └── deploy_to_production.sh
│
├── docs/                    # Complete documentation
│   ├── AFFILIATE_MANAGER.md
│   ├── BACKUP_GUIDE.md
│   ├── LEARNDASH_GUIDE.md
│   ├── MCP_TOOLS.md
│   └── DEPLOYMENT.md
│
├── backups/                 # Local backups (git-ignored)
│   └── .gitkeep
│
├── .env.example             # Environment template
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

---

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/astrocyte/PSOLOMON.git
cd PSOLOMON
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Install MCP Server
```bash
cd mcp-server
pip install -e .
```

### 4. Use with Claude Code
```bash
# Claude Code automatically connects to PSOLOMON via MCP
# Just start using natural language commands!
```

---

## What Can PSOLOMON Do?

### WordPress Management
- "Show me site information"
- "List all active plugins"
- "Check for WordPress updates"

### Backup & Restore
- "Create a backup of the website"
- "List all backups"
- "Show me backup from last week"

### LearnDash LMS
- "Create a new course called 'Fall Prevention'"
- "Add a lesson to course ID 123"
- "Enroll user@email.com in the 10-Hour course"
- "Create a quiz with 10 questions"
- "List all students in a course"

### WooCommerce
- "Create a product for the 10-Hour course"
- "List recent orders"
- "Generate a sales report for this month"
- "Create a discount coupon"

### Affiliate Program
- "List pending affiliate applications"
- "Approve affiliate AFF-001"
- "Set commission rate to 15% for this affiliate"
- "Show affiliate performance stats"

### Content & SEO
- "Analyze SEO for post 123"
- "Search for posts about safety training"
- "Get recommendations for improving content"

---

## Architecture

### MCP Server (Model Context Protocol)
PSOLOMON uses MCP to give Claude direct access to WordPress:

```
Claude Code <---> MCP Server <---> WordPress (SSH/API)
```

**Available Tools:** 36+ MCP tools for complete WordPress management

### WordPress Plugins
Custom plugins built specifically for SST.NYC:
- **sst-affiliate-manager** - Complete affiliate program with WooCommerce integration
- More plugins added as needed

### Security
- ✅ SSH key authentication
- ✅ WordPress Application Passwords
- ✅ Environment variables (never committed)
- ✅ Nonce verification on all forms
- ✅ Capability checks (manage_options)

---

## Environment Variables

Required in `.env`:

```bash
# SSH Configuration
SSH_HOST=147.93.88.8
SSH_PORT=65002
SSH_USER=u629344933
SSH_PASSWORD=your_password
REMOTE_PATH=/home/u629344933/domains/sst.nyc/public_html

# WordPress API
WP_SITE_URL=https://sst.nyc
WP_USERNAME=admin
WP_APP_PASSWORD=your_app_password

# Optional
BACKUP_DIR=./backups
```

---

## Development Workflow

### Making Changes
```bash
# 1. Create feature branch
git checkout -b feature/new-capability

# 2. Make changes
# Edit files in mcp-server/ or wordpress-plugins/

# 3. Test locally
cd mcp-server && pytest

# 4. Commit and push
git add .
git commit -m "feat: Add new capability"
git push origin feature/new-capability

# 5. Merge to main
# Create PR or merge directly
```

### Deploying Plugins
```bash
# Deploy affiliate manager to production
./scripts/deploy_plugin.sh sst-affiliate-manager

# Or deploy all plugins
./scripts/deploy_all_plugins.sh
```

### Creating Backups
```bash
# Via Claude (recommended)
# Just say: "Create a backup"

# Or manually
./scripts/backup_website.sh
```

---

## Technologies

- **MCP Server:** Python 3.11+, FastAPI, Paramiko
- **WordPress:** 6.7+
- **LearnDash:** Latest version
- **WooCommerce:** Latest version
- **Claude Code:** AI-powered development environment
- **Git:** Version control and backup

---

## Repository Information

- **Primary Repo:** https://github.com/astrocyte/PSOLOMON
- **License:** Proprietary - SST.NYC
- **Maintainer:** Shawn Shirazi (via Claude Code)
- **Purpose:** Complete virtual admin for SST.NYC WordPress site

---

## Documentation

- [MCP Tools Reference](./docs/MCP_TOOLS.md) - Complete list of available tools
- [Affiliate Manager](./docs/AFFILIATE_MANAGER.md) - Affiliate program documentation
- [Backup Guide](./docs/BACKUP_GUIDE.md) - Backup and restore procedures
- [LearnDash Guide](./docs/LEARNDASH_GUIDE.md) - LMS management
- [Deployment](./docs/DEPLOYMENT.md) - How to deploy changes

---

## Support

For questions or issues:
1. Check documentation in `docs/`
2. Review error logs: `/wp-content/debug.log`
3. Ask Claude Code directly

---

## Version History

### v1.0 (December 3, 2025)
- Initial PSOLOMON release
- Unified MCP server + WordPress plugins
- Complete affiliate management system
- Backup functionality integrated
- LearnDash + WooCommerce management
- 36+ MCP tools available

---

**PSOLOMON: Your AI-powered WordPress admin, always ready to help.** 🚀

Built with Claude Code (https://claude.com/claude-code)
