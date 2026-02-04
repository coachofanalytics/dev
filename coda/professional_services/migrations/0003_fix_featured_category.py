# Fix the FeaturedCategory table structure
# This migration is for fixing existing PostgreSQL production tables only
# In tests (SQLite), the 0001_initial creates the correct structure already

from django.db import migrations, models, connection
import django.db.models.deletion
import django.utils.timezone


def fix_featured_category_postgresql(apps, schema_editor):
    """
    Fix FeaturedCategory table structure in PostgreSQL only.
    SQLite doesn't need this fix as 0001_initial creates the correct structure.
    """
    if connection.vendor != 'postgresql':
        # Skip for non-PostgreSQL databases (e.g., SQLite in tests)
        return
    
    # PostgreSQL-specific table fixes
    with connection.cursor() as cursor:
        # Check and rename category_name to title if it exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'data_featuredcategory' AND column_name = 'category_name'
        """)
        if cursor.fetchone():
            cursor.execute("ALTER TABLE data_featuredcategory RENAME COLUMN category_name TO title")
        
        # Add missing columns if they don't exist
        cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'data_featuredcategory' AND column_name = 'created_by_id') THEN
                    ALTER TABLE data_featuredcategory ADD COLUMN created_by_id INTEGER REFERENCES accounts_customeruser(id);
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'data_featuredcategory' AND column_name = 'description') THEN
                    ALTER TABLE data_featuredcategory ADD COLUMN description TEXT DEFAULT '';
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                              WHERE table_name = 'data_featuredcategory' AND column_name = 'is_active') THEN
                    ALTER TABLE data_featuredcategory ADD COLUMN is_active INTEGER DEFAULT 1;
                END IF;
            END $$;
        """)


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('professional_services', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            fix_featured_category_postgresql,
            reverse_code=migrations.RunPython.noop,
        ),
    ]