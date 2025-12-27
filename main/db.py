import os
from django.db import connection
from django.apps import apps
from django.db.utils import ProgrammingError

import datetime

def clear():
    if os.name == 'nt':  # for Windows
        _ = os.system('cls')
    else:  # for Linux and Mac
        _ = os.system('clear')

def all_tables():
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = cursor.fetchall()
        for table in tables:
            print(table[0])
    except Exception as e:
        print("Error listing tables:", str(e))
    finally:
        cursor.close()


def django_migration():
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT * FROM django_migrations")
        results = cursor.fetchall()
        for row in results:
            print(row)
    except Exception as e:
        print("Error querying django_migrations table:", str(e))
    finally:
        cursor.close()

def delete_table_records(mytable):
    table_names = connection.introspection.table_names()
    if mytable._meta.db_table in table_names:
        mytable.objects.all().delete()


def delete_table(mytable):
    cursor = connection.cursor()
    try:
        cursor.execute(f'DROP TABLE IF EXISTS "{mytable}"')
        print(f"Table {mytable} deleted successfully!")
    except ProgrammingError as e:
        print(f"Error deleting table {mytable}: {str(e)}")
    finally:
        cursor.close()


def delete_migrations(myapp):
    cursor = connection.cursor()
    try:
        cursor.execute("DELETE FROM django_migrations WHERE app = %s", [myapp])
        connection.commit()
        print(f"Entries deleted successfully from django_migrations table for app '{myapp}'!")
    except Exception as e:
        print("Error deleting entries from django_migrations table:", str(e))
    finally:
        cursor.close()