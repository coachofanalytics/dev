#!/usr/bin/env python
"""
Script to create management tables manually
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/coda')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.local_settings')
django.setup()

from django.db import connection

def create_management_tables():
    """Create management tables manually"""
    
    # Create management_task table
    create_task_table = """
    CREATE TABLE IF NOT EXISTS management_task (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group VARCHAR(255) NOT NULL DEFAULT 'Group A',
        groupname_id INTEGER NOT NULL DEFAULT 1,
        category_id INTEGER NOT NULL DEFAULT 1,
        employee_id INTEGER NOT NULL DEFAULT 999,
        activity_name VARCHAR(255) NOT NULL,
        description TEXT,
        deadline DATE,
        submission VARCHAR(255),
        point INTEGER DEFAULT 0,
        mxpoint INTEGER DEFAULT 0,
        mxearning DECIMAL(10,2) DEFAULT 0.00,
        late_penalty DECIMAL(3,2) DEFAULT 1.00,
        is_active BOOLEAN DEFAULT 1,
        featured BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (groupname_id) REFERENCES management_taskgroups(id),
        FOREIGN KEY (category_id) REFERENCES management_taskcategory(id),
        FOREIGN KEY (employee_id) REFERENCES auth_user(id)
    );
    """
    
    # Create management_taskcategory table
    create_category_table = """
    CREATE TABLE IF NOT EXISTS management_taskcategory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(55) NOT NULL UNIQUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Create management_taskgroups table
    create_groups_table = """
    CREATE TABLE IF NOT EXISTS management_taskgroups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """
    
    # Create management_taskhistory table
    create_history_table = """
    CREATE TABLE IF NOT EXISTS management_taskhistory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group VARCHAR(255) NOT NULL DEFAULT 'Group A',
        category_id INTEGER NOT NULL DEFAULT 1,
        employee_id INTEGER NOT NULL DEFAULT 999,
        activity_name VARCHAR(255) NOT NULL,
        description TEXT,
        deadline DATE,
        submission VARCHAR(255),
        point INTEGER DEFAULT 0,
        mxpoint INTEGER DEFAULT 0,
        mxearning DECIMAL(10,2) DEFAULT 0.00,
        late_penalty DECIMAL(3,2) DEFAULT 1.00,
        is_active BOOLEAN DEFAULT 1,
        featured BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES management_taskcategory(id),
        FOREIGN KEY (employee_id) REFERENCES auth_user(id)
    );
    """
    
    with connection.cursor() as cursor:
        try:
            print("Creating management_taskcategory table...")
            cursor.execute(create_category_table)
            
            print("Creating management_taskgroups table...")
            cursor.execute(create_groups_table)
            
            print("Creating management_task table...")
            cursor.execute(create_task_table)
            
            print("Creating management_taskhistory table...")
            cursor.execute(create_history_table)
            
            # Insert default category
            cursor.execute("""
                INSERT OR IGNORE INTO management_taskcategory (id, title) 
                VALUES (1, 'PBR')
            """)
            
            # Insert default group
            cursor.execute("""
                INSERT OR IGNORE INTO management_taskgroups (id, title) 
                VALUES (1, 'Default Group')
            """)
            
            print("Management tables created successfully!")
            
        except Exception as e:
            print(f"Error creating tables: {e}")

if __name__ == "__main__":
    create_management_tables()

