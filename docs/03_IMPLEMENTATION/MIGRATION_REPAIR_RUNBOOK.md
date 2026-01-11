# Migration Repair Runbook

## Problem
When running `poetry run python coda/manage.py migrate`, you may encounter:
```
psycopg2.errors.DuplicateColumn: column "image2_id" of relation "accounts_userprofile" already exists
```
This occurs when applying migration `accounts.0003_userprofile_image2` on a database where the column already exists but Django's migration state doesn't reflect it.

## Root Cause
This typically happens in:
- Local clone databases where the column was manually added
- Production/Heroku databases where a previous migration was applied without Django recording its state
- CI test databases that were partially migrated

## Solution: Fake the Migration

**Do NOT edit historical migrations.** Instead, tell Django to mark the migration as applied without actually running it.

### Local Clone DB

1. **Verify column exists (Optional but Recommended):**
   ```bash
   poetry run python coda/manage.py dbshell
   ```
   In the PostgreSQL prompt:
   ```sql
   \d accounts_userprofile
   ```
   Look for `image2_id` in the column list.

2. **Fake the migration:**
   ```bash
   poetry run python coda/manage.py migrate accounts 0003_userprofile_image2 --fake
   ```
   This tells Django to mark `accounts.0003_userprofile_image2` as applied without actually running its database operations.

3. **Continue normal migrations:**
   ```bash
   poetry run python coda/manage.py migrate
   ```

### Heroku Production

1. **Fake the migration:**
   ```bash
   heroku run python coda/manage.py migrate accounts 0003_userprofile_image2 --fake --app <your-app-name>
   ```
   Replace `<your-app-name>` with your actual Heroku app name.

2. **Continue normal migrations:**
   ```bash
   heroku run python coda/manage.py migrate --app <your-app-name>
   ```

## Important Notes

- **Only use `--fake` when you are certain the database schema already matches what the migration would create.**
- This approach ensures that Django's internal migration state is consistent with your database, allowing future migrations to run smoothly.
- If the column does NOT exist in the database, do NOT use `--fake` - let the migration run normally.

## Verification

After faking the migration, verify it's marked as applied:
```bash
poetry run python coda/manage.py showmigrations accounts
```

You should see `[X] 0003_userprofile_image2` (marked with X).
