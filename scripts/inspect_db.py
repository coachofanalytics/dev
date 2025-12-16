import sqlite3
import os
p = os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3')
print('DB path:', os.path.abspath(p))
if not os.path.exists(p):
    print('No db.sqlite3 found')
    exit(0)
conn = sqlite3.connect(p)
c = conn.cursor()
print('\nTables:')
for row in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"):
    print(' -', row[0])
print('\nDjango migrations applied (latest 100):')
for row in c.execute('SELECT app, name, applied FROM django_migrations ORDER BY applied DESC LIMIT 100'):
    print(row)

# Show if main tables exist
for t in ('main_emergencyhelpactivation','main_emergencyhelpactivations','main_emergencyhotline','main_emergencyhotlines'):
    try:
        c.execute(f"SELECT count(*) FROM {t} LIMIT 1")
        print('\nTable exists:', t)
    except Exception as e:
        print('\nMissing or error for table:', t, '->', e)
conn.close()