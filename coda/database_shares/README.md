# Database Sharing Setup

This directory contains scripts and documentation for sharing a limited database export with developers.

## Files

### Essential Files
- **`limited_export_fixed.json`** - The fixed database export containing 5 target users and their related data (1.6 MB)
- **`setup_reference_data.py`** - Script to create all required reference data before loading the export
- **`fix_exported_data.py`** - Script to fix boolean None values and foreign key issues in the export

### Documentation
- **`README.md`** - This file (overview and quick start)
- **`SETUP_INSTRUCTIONS.md`** - Detailed step-by-step setup instructions
- **`QUICK_TEST_GUIDE.md`** - Quick reference guide for testing
- **`FK_DEPENDENCIES_CHECK.md`** - Reference documentation for foreign key dependencies

## Quick Start

1. **Create the database:**
   ```bash
   psql -U coda -d postgres -c "CREATE DATABASE coda_limited;"
   ```

2. **Configure environment:**
   Ensure `coda/dev.env` has `DB_TYPE=limited` and database connection settings.

3. **Run migrations:**
   ```bash
   cd coda
   poetry run python manage.py migrate
   ```

4. **Create reference data:**
   ```bash
   cd coda
   poetry run python ../database_shares/setup_reference_data.py
   ```

5. **Load the fixture:**
   ```bash
   cd coda
   poetry run python manage.py loaddata ../database_shares/limited_export_fixed.json
   ```

## What's Included

The export contains:
- **5 target users**: coda_info, eunice, gndahiro, ckarugu, EDWINORWA
- **User-related data**: profiles, credentials, login history, trackers
- **Finance data**: transactions, budgets, budget requests, loan applications
- **Management data**: task links

Reference data (categories, departments, companies, etc.) is created by the setup script.

## Troubleshooting

See `SETUP_INSTRUCTIONS.md` for detailed troubleshooting steps.

## Notes

- The export has been fixed to handle `None` boolean values and foreign key references
- All signals are configured to skip during `loaddata` to prevent errors
- The setup script is idempotent - safe to run multiple times
