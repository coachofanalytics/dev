#!/usr/bin/env python3
import sqlite3
import sys
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / 'db.sqlite3'
APP = 'main'
NAME = '0003_rename_emergencyhotline_emergencyhotlines'

if not DB.exists():
    print(f"Database not found: {DB}")
    sys.exit(2)

conn = sqlite3.connect(str(DB))
c = conn.cursor()
# ensure table exists
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='django_migrations'")
if not c.fetchone():
    print('django_migrations table not found in DB')
    conn.close()
    sys.exit(3)

c.execute('SELECT 1 FROM django_migrations WHERE app=? AND name=?', (APP, NAME))
if c.fetchone():
    print('Migration already recorded')
    conn.close()
    sys.exit(0)

c.execute("INSERT INTO django_migrations(app, name, applied) VALUES (?, ?, datetime('now'))", (APP, NAME))
conn.commit()
print('Inserted migration record for', APP, NAME)
conn.close()
