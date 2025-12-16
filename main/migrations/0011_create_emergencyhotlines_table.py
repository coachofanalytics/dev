"""
Manual migration to ensure the `main_emergencyhotlines` table exists on the database (Heroku Postgres).

Why this migration: the project history and runtime have shown cases where migration records
exist but the physical DB table is missing (especially on remote DBs). This migration will
create the missing table if it does not exist, without modifying other tables or data.

Approach:
- Use a Python migration (`RunPython`) so we can run different SQL depending on the DB backend
  (Postgres vs SQLite). The creation uses `IF NOT EXISTS` semantics where supported and
  appropriate column definitions per backend.
- The reverse operation drops the table if it exists. Drop is provided for rollback convenience
  but be cautious: dropping will remove data — only run reverses if you mean to remove that data.

How to run on Heroku:
  git add main/migrations/0011_create_emergencyhotlines_table.py
  git commit -m "Ensure emergencyhotlines table exists on DB"
  git push heroku HEAD:main
  heroku run python manage.py migrate main -a <your-app-name>

Note: This migration only creates the DB table. If your codebase still references the old
field names (`number`, `is_active`) update those references to `phone` and `active`.
"""

from django.db import migrations


def create_table_if_missing(apps, schema_editor):
    """Create the `main_emergencyhotlines` table if absent. Handles Postgres and SQLite."""
    conn = schema_editor.connection
    vendor = conn.vendor
    cursor = conn.cursor()

    if vendor == "postgresql":
        # Use serial for auto-incrementing primary key on Postgres
        sql = """
        CREATE TABLE IF NOT EXISTS main_emergencyhotlines (
            id serial PRIMARY KEY,
            name varchar(255) NOT NULL,
            phone varchar(20) NOT NULL,
            active boolean NOT NULL DEFAULT true,
            sort_order integer NOT NULL DEFAULT 0
        );
        """
    elif vendor == "sqlite":
        # SQLite: use integer primary key autoincrement
        sql = """
        CREATE TABLE IF NOT EXISTS main_emergencyhotlines (
            id integer PRIMARY KEY AUTOINCREMENT,
            name varchar(255) NOT NULL,
            phone varchar(20) NOT NULL,
            active boolean NOT NULL DEFAULT 1,
            sort_order integer NOT NULL DEFAULT 0
        );
        """
    else:
        # Fallback: try a generic SQL statement (may work on other DBs)
        sql = """
        CREATE TABLE IF NOT EXISTS main_emergencyhotlines (
            id serial PRIMARY KEY,
            name varchar(255) NOT NULL,
            phone varchar(20) NOT NULL,
            active boolean NOT NULL DEFAULT true,
            sort_order integer NOT NULL DEFAULT 0
        );
        """

    cursor.execute(sql)


def drop_table_if_exists(apps, schema_editor):
    """Reverse: drop the table if it exists. WARNING: this will remove data in the table."""
    conn = schema_editor.connection
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS main_emergencyhotlines;")


class Migration(migrations.Migration):

    dependencies = [
        ("main", "0010_auto_20251126_1849"),
    ]

    operations = [
        migrations.RunPython(create_table_if_missing, reverse_code=drop_table_if_exists),
    ]
