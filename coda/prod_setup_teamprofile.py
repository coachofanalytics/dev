#!/usr/bin/env python
"""
Production: Create TeamProfile table with all fields.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from django.db import connection

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS accounts_teamprofile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES accounts_customeruser(id) ON DELETE CASCADE,
    priority INTEGER DEFAULT 0,
    total_points INTEGER DEFAULT 0,
    is_manually_assigned BOOLEAN DEFAULT FALSE,
    last_promoted TIMESTAMP WITH TIME ZONE NULL,
    promotion_notes TEXT DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS accounts_teamprofile_user_id_idx ON accounts_teamprofile(user_id);
CREATE INDEX IF NOT EXISTS accounts_teamprofile_priority_total_points_idx ON accounts_teamprofile(priority, total_points DESC);
CREATE INDEX IF NOT EXISTS accounts_teamprofile_is_manually_assigned_idx ON accounts_teamprofile(is_manually_assigned);
CREATE INDEX IF NOT EXISTS accounts_teamprofile_last_promoted_idx ON accounts_teamprofile(last_promoted);
"""

cursor = connection.cursor()
try:
    cursor.execute(CREATE_TABLE_SQL)
    print("✅ TeamProfile table created successfully")
    print("✅ All indexes created")
except Exception as e:
    print(f"⚠️ Error: {e}")

