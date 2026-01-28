import sqlite3
from pathlib import Path
DB = Path(__file__).resolve().parents[1] / 'db.sqlite3'
conn = sqlite3.connect(str(DB))
c = conn.cursor()
c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='django_migrations'")
if not c.fetchone()[0]:
    print('django_migrations table missing')
else:
    c.execute('SELECT app, name, applied FROM django_migrations ORDER BY app, name')
    rows = c.fetchall()
    print('Total rows in django_migrations:', len(rows))
    for r in rows:
        if r[0]=='main' or len(rows)<50:
            print(r)
conn.close()
