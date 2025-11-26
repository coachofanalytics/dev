"""
Utility functions for accounts migrations to handle conditional operations
when CustomerUser table might not exist yet.
"""
from django.db import connection


def customeruser_table_exists():
    """Check if the accounts_customeruser table exists in the database"""
    db_table = 'accounts_customeruser'
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """, [db_table])
        return cursor.fetchone()[0]


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s;
        """, [table_name, column_name])
        return cursor.fetchone() is not None

