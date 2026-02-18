#!/usr/bin/env python3
import sqlite3, datetime, sys
DB='db.sqlite3'
APP='main'
M2='0002_rename_emergencyhelpactivation_emergencyhelpactivations'
M3='0003_rename_emergencyhotline_emergencyhotlines'
try:
    conn=sqlite3.connect(DB)
    cur=conn.cursor()
    cur.execute("SELECT name, applied FROM django_migrations WHERE app=? ORDER BY applied",(APP,))
    rows=cur.fetchall()
    print('CURRENT MIGRATIONS FOR',APP)
    for r in rows:
        print(r)
    names=[r[0] for r in rows]
    if M2 in names and M3 in names:
        print('\nNo action needed.')
        sys.exit(0)
    # find ref time from 0009 if present
    ref=None
    for r in rows:
        if r[0].startswith('0009'):
            ref=r[1]
            break
    if ref:
        try:
            ref_dt=datetime.datetime.fromisoformat(ref)
        except Exception:
            ref_dt=datetime.datetime.now()
    else:
        ref_dt=datetime.datetime.now()
    inserts=[]
    if M3 not in names:
        inserts.append((M3, ref_dt - datetime.timedelta(seconds=1)))
    if M2 not in names:
        inserts.append((M2, ref_dt - datetime.timedelta(seconds=2)))
    for name,dt in inserts:
        ts=dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        cur.execute("INSERT INTO django_migrations(app,name,applied) VALUES(?,?,?)",(APP,name,ts))
        print('Inserted',name,ts)
    if inserts:
        conn.commit()
    print('\nFINAL MIGRATIONS FOR',APP)
    cur.execute("SELECT name, applied FROM django_migrations WHERE app=? ORDER BY applied",(APP,))
    for r in cur.fetchall():
        print(r)
    conn.close()
except Exception as e:
    print('ERROR:',e)
    sys.exit(1)
