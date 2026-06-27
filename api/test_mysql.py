import pymysql

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="inflow_db",
    port=3306
)

print("Connected successfully!")
conn.close()