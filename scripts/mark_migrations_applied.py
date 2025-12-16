import sqlite3, os, datetime
p = os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3')
conn = sqlite3.connect(p)
c = conn.cursor()
now = datetime.datetime.utcnow().isoformat(sep=' ')
for name in ('0002_rename_emergencyhelpactivation_emergencyhelpactivations','0003_rename_emergencyhotline_emergencyhotlines'):
    c.execute("SELECT COUNT(*) FROM django_migrations WHERE app='main' AND name=?", (name,))
    if c.fetchone()[0]==0:
        print('Inserting migration', name)
        c.execute("INSERT INTO django_migrations(app, name, applied) VALUES(?,?,?)", ('main', name, now))
    else:
        print('Already recorded', name)
conn.commit()
conn.close()
print('Done')