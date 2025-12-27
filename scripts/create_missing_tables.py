import sqlite3
import os
p = os.path.join(os.path.dirname(__file__), '..', 'db.sqlite3')
print('DB path:', os.path.abspath(p))
conn = sqlite3.connect(p)
c = conn.cursor()

# Create EmergencyHotlines table if missing
try:
    c.execute("SELECT 1 FROM main_emergencyhotlines LIMIT 1")
    print('main_emergencyhotlines already exists')
except Exception:
    print('Creating main_emergencyhotlines')
    c.execute('''
    CREATE TABLE main_emergencyhotlines (
        id integer PRIMARY KEY AUTOINCREMENT,
        name varchar(100) NOT NULL,
        number varchar(32) NOT NULL,
        is_active bool NOT NULL DEFAULT 1,
        sort_order integer NOT NULL DEFAULT 0
    )
    ''')

# Create EmergencyHelpActivations table if missing
try:
    c.execute("SELECT 1 FROM main_emergencyhelpactivations LIMIT 1")
    print('main_emergencyhelpactivations already exists')
except Exception:
    print('Creating main_emergencyhelpactivations')
    c.execute('''
    CREATE TABLE main_emergencyhelpactivations (
        id integer PRIMARY KEY AUTOINCREMENT,
        event_type varchar(32) NOT NULL,
        name varchar(100),
        phone varchar(32),
        location varchar(255),
        notes text,
        ip_address varchar(45),
        created_at datetime
    )
    ''')

conn.commit()
conn.close()
print('Done')