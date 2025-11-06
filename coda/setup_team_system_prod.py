#!/usr/bin/env python
"""
Setup Team System for Production Database
Creates table and adds all necessary columns.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from django.db import connection

print("\n" + "="*70)
print("🚀 SETTING UP TEAM SYSTEM FOR PRODUCTION")
print("="*70)

# Complete table creation with ALL fields
CREATE_TABLE_SQL = """
-- Drop table if exists (clean slate)
DROP TABLE IF EXISTS accounts_teamprofile CASCADE;

-- Create complete TeamProfile table
CREATE TABLE accounts_teamprofile (
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

-- Create indexes
CREATE INDEX accounts_teamprofile_user_id_idx ON accounts_teamprofile(user_id);
CREATE INDEX accounts_teamprofile_priority_total_points_idx ON accounts_teamprofile(priority, total_points DESC);
CREATE INDEX accounts_teamprofile_is_manually_assigned_idx ON accounts_teamprofile(is_manually_assigned);
CREATE INDEX accounts_teamprofile_last_promoted_idx ON accounts_teamprofile(last_promoted);
"""

cursor = connection.cursor()
try:
    print("\n📊 Creating accounts_teamprofile table...")
    cursor.execute(CREATE_TABLE_SQL)
    print("✅ Table created successfully with all fields:")
    print("   - user_id (FK to CustomerUser)")
    print("   - priority (INTEGER)")
    print("   - total_points (INTEGER)")
    print("   - is_manually_assigned (BOOLEAN)")
    print("   - last_promoted (TIMESTAMP)")
    print("   - promotion_notes (TEXT)")
    print("   - created_at (TIMESTAMP)")
    print("   - updated_at (TIMESTAMP)")
    print("✅ All indexes created")
    print("\n" + "="*70)
    print("✅ PRODUCTION TEAM SYSTEM SETUP COMPLETE!")
    print("="*70)
    print("\nNext steps:")
    print("  1. python manage.py create_team_groups")
    print("  2. python manage.py assign_manual_team_members")
    print("="*70 + "\n")
except Exception as e:
    print(f"❌ Error: {e}")

