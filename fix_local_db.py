import sqlite3

def create_missing_table():
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # FinancialServiceRequest table structure from 0001_initial
    # id (BigAutoField), created_at (DateTimeField), updated_at (DateTimeField), 
    # service_type (CharField), status (CharField), details (TextField), user_id (ForeignKey)
    
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS finance_financialservicerequest (
                "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                "created_at" datetime NOT NULL,
                "updated_at" datetime NOT NULL,
                "service_type" varchar(50) NOT NULL,
                "status" varchar(20) NOT NULL,
                "details" text NOT NULL,
                "user_id" bigint NOT NULL REFERENCES "accounts_customeruser" ("id") DEFERRABLE INITIALLY DEFERRED
            )
        ''')
        conn.commit()
        print("Table finance_financialservicerequest created successfully (if it didn't exist).")
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_missing_table()
