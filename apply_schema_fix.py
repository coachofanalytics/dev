"""One-time runner to apply fix_missing_tables.sql via the Django DB connection.

Usage on Heroku:
    heroku run python apply_schema_fix.py -a codadev

Safe to run multiple times: the SQL uses IF NOT EXISTS guards for tables,
columns and indexes. Constraint additions will only run once (re-running
after success would raise duplicate_object, which simply aborts the txn
with no changes since everything already exists).
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "coda_project.settings")
django.setup()

from django.db import connection, transaction  # noqa: E402

with open("fix_missing_tables.sql", "r", encoding="utf-8") as fh:
    sql = fh.read()

try:
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute(sql)
    print("SCHEMA FIX APPLIED OK")
except Exception as exc:  # noqa: BLE001
    # If everything already exists a duplicate constraint error is expected.
    print(f"SCHEMA FIX NOT APPLIED (likely already present): {exc}")
