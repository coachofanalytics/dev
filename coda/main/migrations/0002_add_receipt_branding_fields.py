# Generated manually - Add receipt branding fields to Company model
# Note: Using raw SQL to avoid migration dependency conflicts
# Company model already exists, we're just adding new columns

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        # No dependencies - using raw SQL to avoid conflicts
        # The Company table already exists in the database
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- Add logo column (ImageField stores file path)
                ALTER TABLE main_company 
                ADD COLUMN IF NOT EXISTS logo VARCHAR(255) NULL;
                
                -- Add receipt_email column (EmailField)
                ALTER TABLE main_company 
                ADD COLUMN IF NOT EXISTS receipt_email VARCHAR(255) NULL;
                
                -- Add display_name column (CharField)
                ALTER TABLE main_company 
                ADD COLUMN IF NOT EXISTS display_name VARCHAR(100) NULL;
                
                -- Add address column (CharField)
                ALTER TABLE main_company 
                ADD COLUMN IF NOT EXISTS address VARCHAR(255) NULL;
            """,
            reverse_sql="""
                -- Remove columns (reverse migration)
                ALTER TABLE main_company DROP COLUMN IF EXISTS logo;
                ALTER TABLE main_company DROP COLUMN IF EXISTS receipt_email;
                ALTER TABLE main_company DROP COLUMN IF EXISTS display_name;
                ALTER TABLE main_company DROP COLUMN IF EXISTS address;
            """
        ),
    ]

