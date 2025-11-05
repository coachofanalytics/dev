#!/usr/bin/env python
"""
Fix migration dependency issue by manually inserting stub migration record.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
try:
    cursor.execute(
        "INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, NOW())",
        ['accounts', '0001_initial_stub']
    )
    print("✅ Migration record inserted successfully")
except Exception as e:
    print(f"⚠️ Error (might already exist): {e}")

