# Scripts Directory

This folder contains development, deployment, database, and maintenance helpers. Safe-by-default, non-interactive.

## 📁 Directory Structure

```
scripts/
├── README.md         # Main documentation
├── docs/             # Additional documentation files
├── dev/              # Development server and local setup
├── deploy/           # Deployment scripts (UAT, Production, Heroku)
├── database/         # Database operations and migrations
│   └── migrations/   # SQL migration files
├── maintenance/      # One-off maintenance and validation scripts
├── testing/          # Test runners and test utilities
├── utils/            # Utility scripts (sync, audit, monitoring)
├── optimization/     # Optimization scripts (images, docs, static)
├── windows/          # Windows/PowerShell scripts
└── sharing/          # Repository sharing utilities
```

## 🚀 Quick Start

### Development Server
```bash
# Start dev server with production clone database
scripts/dev/dev_server.sh --port 8000

# Start with HTTPS (requires django-extensions)
scripts/dev/dev_server.sh --https

# Use local SQLite database
scripts/dev/dev_server.sh --settings local
```

### Deployment
```bash
# Deploy to UAT
scripts/deploy/uat.sh

# Deploy to Production (requires confirmation)
scripts/deploy/production.sh

# Deploy to Heroku
scripts/deploy/heroku.sh

# Deploy AI Services
scripts/deploy/ai_services.sh
```

### Database Operations
```bash
# Clone production database locally
scripts/database/clone_prod.sh

# Sync production data to local SQLite
scripts/database/sync_prod_to_local.sh

# Check production database state
scripts/database/check_production_state.py
```

### Testing
```bash
# Run test scripts
scripts/testing/test_payment_eligibility.py
scripts/testing/test_request_approval_workflow.py
```

### Utilities
```bash
# Sync branches
scripts/utils/sync_branches.sh

# Audit dependencies
scripts/utils/dependency_audit.py

# Monitor performance
scripts/utils/performance_monitor.py
```

## 📋 Script Categories

### `dev/` - Development
- **dev_server.sh** - Unified development server with multiple options

### `deploy/` - Deployment
- **uat.sh** - Deploy to UAT environment
- **production.sh** - Deploy to production (with safety checks)
- **heroku.sh** - Comprehensive Heroku deployment
- **ai_services.sh** - AI services specific deployment
- **runserver_uat.sh** - Run server connected to UAT database
- **runserver_prod.sh** - Run server connected to production database (⚠️ USE WITH CAUTION)

### `database/` - Database Operations
- **clone_prod.sh** - Clone production PostgreSQL database locally
- **sync_prod_to_local.sh** - Sync production data to local SQLite
- **pull_prod_data.py** - Pull production data for local analysis
- **check_production_state.py** - Check production database state
- **setup_database.py** - Database setup utilities
- **setup_local.py** - Local database setup
- **migrations/** - SQL migration files

### `maintenance/` - Maintenance
- **check_*.py** - Various validation and check scripts
- **bypass_*.py** - Maintenance bypass scripts

### `testing/` - Testing
- **test_*.py** - Test runner scripts

### `utils/` - Utilities
- **sync_branches.sh** - Sync git branches
- **dependency_audit.py** - Audit Python dependencies
- **performance_monitor.py** - Monitor application performance

### `optimization/` - Optimization
- **image_optimizer.py** - Optimize images
- **documentation_optimizer.py** - Optimize documentation
- **static_optimizer.py** - Optimize static files

### `windows/` - Windows Scripts
- **dev_up.ps1** - Windows development server startup
- **clone_prod_database.ps1** - Windows database clone
- **setup_env.ps1** - Windows environment setup

## 🔒 Safety Conventions

- **Bash scripts** are idempotent; use `set -euo pipefail`
- **All scripts** accept `--help` and print usage
- **Production scripts** require explicit `ENVIRONMENT=production` or confirmation
- **Never operate on production** unless explicitly intended
- **Database scripts** include safety checks and backups

## 📝 Script Conventions

1. **Error Handling**: All scripts exit on error (`set -e`)
2. **Help Text**: All scripts support `--help` flag
3. **Logging**: Scripts provide clear status messages
4. **Idempotency**: Scripts can be run multiple times safely
5. **Documentation**: Each script includes usage comments

## 🗑️ Deprecated Scripts (Removed)

The following duplicate scripts were removed during reorganization:

### Production Discovery (Consolidated)
- `production/discover_production.py` → Use `database/check_production_state.py`
- `production/production_discovery_fixed.py` → Removed
- `production/production_check.sh` → Removed
- `production/prod_check_final.sh` → Removed
- `production/run_prod_discovery.sh` → Removed
- `production/run_production_discovery.sh` → Removed

### Development Servers (Consolidated)
- `server/start_dev.sh` → Use `dev/dev_server.sh`
- `server/dev_server.py` → Use `dev/dev_server.sh`
- `server/start_server.py` → Use `dev/dev_server.sh`
- `server/run_local.py` → Use `dev/dev_server.sh`

### Optimization (Consolidated)
- `optimize_images.py` (root) → Use `optimization/image_optimizer.py`

## 🔄 Migration Notes

If you have scripts or documentation referencing old paths:

- `scripts/deploy_uat.sh` → `scripts/deploy/uat.sh`
- `scripts/runserver_uat.sh` → `scripts/deploy/runserver_uat.sh`
- `scripts/runserver_prod.sh` → `scripts/deploy/runserver_prod.sh`
- `scripts/clone_prod_database.sh` → `scripts/database/clone_prod.sh`
- `scripts/optimize_images.py` → `scripts/optimization/image_optimizer.py`
- `scripts/test_*.py` → `scripts/testing/test_*.py`

## 📚 Additional Documentation

Documentation files are located in the `docs/` directory:

- **[docs/README_CLONE_DATABASE.md](docs/README_CLONE_DATABASE.md)** - Database cloning guide
- **[docs/README_SYNC_PROD.md](docs/README_SYNC_PROD.md)** - Production sync guide
- **[docs/REORGANIZATION_SUMMARY.md](docs/REORGANIZATION_SUMMARY.md)** - Reorganization summary

---

**Last Updated:** December 2025  
**Structure Version:** 2.0 (Reorganized)
