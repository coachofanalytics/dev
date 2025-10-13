# CODA Helper Scripts

This directory contains utility scripts for database setup, data migration, and other helper tasks.

## Database Scripts

### `create_budget_item_library.sql`
**Purpose:** Create budget item library with common budget items  
**Usage:**
```bash
# Local PostgreSQL
psql -d coda_db -f scripts/create_budget_item_library.sql

# Heroku PostgreSQL
heroku pg:psql --app codamakutano < scripts/create_budget_item_library.sql
```

**Creates:**
- Common budget categories
- Standard budget items
- Default approval policies

---

## Future Scripts

As the project grows, add scripts here for:

- **Data Migration:** `migrate_transaction_data.py`
- **Database Seeding:** `seed_test_data.py`
- **Backup/Restore:** `backup_database.sh`
- **Deployment:** `deploy_to_uat.sh`
- **Data Analysis:** `analyze_spending_patterns.py`

---

## Script Naming Convention

- **`.sql`** - Database scripts (DDL, DML)
- **`.py`** - Python utility scripts
- **`.sh`** - Shell scripts for automation
- **`deploy_*.sh`** - Deployment scripts
- **`migrate_*.py`** - Data migration scripts
- **`seed_*.py`** - Test data generation

---

## Best Practices

1. **Always test scripts locally first**
2. **Add comments explaining what the script does**
3. **Include usage examples in this README**
4. **Make scripts idempotent** (safe to run multiple times)
5. **Add error handling** (set -e for shell scripts)
6. **Document any prerequisites** (packages, permissions, etc.)

---

**Last Updated:** October 13, 2025

