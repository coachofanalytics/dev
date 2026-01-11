# Migration Fake Runbook

## Problem: Duplicate Column Error on Clone/Prod DB

When applying migrations on a cloned or production database, you may encounter:

```
Postgres error: DuplicateColumn: column "image2_id" ... already exists applying accounts.0003_userprofile_image2.
```

This is a **data state issue**, not a code issue. The column exists in the database, but Django's migration history doesn't record that the migration was applied.

## Solution: Use --fake Flag

Mark the migration as applied without actually running it:

```bash
poetry run python coda/manage.py migrate accounts 0003_userprofile_image2 --fake
```

This tells Django: "This migration has already been applied in the database, just mark it as done in the migration history."

## When to Use --fake

Use `--fake` when:
- Column/table already exists in DB but migration isn't recorded
- You've manually applied schema changes
- Working with a cloned DB that has different migration state

**DO NOT use --fake** when:
- The column/table doesn't actually exist
- You want to actually apply the migration
- You're unsure about the database state

## Verification

After using --fake, verify the migration is recorded:

```bash
poetry run python coda/manage.py showmigrations accounts
```

The migration should show as `[X]` (applied) instead of `[ ]` (not applied).

## General Pattern

For any migration that fails with "already exists" error:

1. Verify the column/table actually exists in DB
2. Use `--fake` to mark migration as applied
3. Continue with remaining migrations

```bash
# Example: Fake a specific migration
poetry run python coda/manage.py migrate <app_name> <migration_name> --fake

# Example: Fake all migrations for an app (use with caution)
poetry run python coda/manage.py migrate <app_name> --fake
```

