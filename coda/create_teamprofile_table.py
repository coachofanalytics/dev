#!/usr/bin/env python
"""
Manually create TeamProfile table in database.
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
    category VARCHAR(100),
    priority INTEGER DEFAULT 0,
    total_points NUMERIC(10, 2) DEFAULT 0.00,
    education_points NUMERIC(10, 2) DEFAULT 0.00,
    performance_points NUMERIC(10, 2) DEFAULT 0.00,
    tenure_points NUMERIC(10, 2) DEFAULT 0.00,
    kcc_bonus_points NUMERIC(10, 2) DEFAULT 0.00,
    is_manually_assigned BOOLEAN DEFAULT FALSE,
    assignment_notes TEXT,
    last_points_update TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS accounts_teamprofile_user_id_idx ON accounts_teamprofile(user_id);
CREATE INDEX IF NOT EXISTS accounts_teamprofile_category_idx ON accounts_teamprofile(category);
CREATE INDEX IF NOT EXISTS accounts_teamprofile_total_points_idx ON accounts_teamprofile(total_points);
"""

cursor = connection.cursor()
try:
    cursor.execute(CREATE_TABLE_SQL)
    print("✅ TeamProfile table created successfully")
except Exception as e:
    print(f"⚠️ Error: {e}")

