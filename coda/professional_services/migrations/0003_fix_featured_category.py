# Fix the FeaturedCategory table structure

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('professional_services', '0002_training_responses'),
    ]

    operations = [
        # Rename the incorrect column and add missing columns
        migrations.RunSQL(
            sql="""
            -- Rename category_name to title if it exists
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.columns
                          WHERE table_name = 'data_featuredcategory' AND column_name = 'category_name') THEN
                    ALTER TABLE data_featuredcategory RENAME COLUMN category_name TO title;
                END IF;
            END $$;

            -- Add missing columns if they don't exist
            ALTER TABLE data_featuredcategory
            ADD COLUMN IF NOT EXISTS created_by_id INTEGER REFERENCES accounts_customeruser(id),
            ADD COLUMN IF NOT EXISTS description TEXT DEFAULT '',
            ADD COLUMN IF NOT EXISTS is_active INTEGER DEFAULT 1;

            -- Change title column type if needed
            ALTER TABLE data_featuredcategory ALTER COLUMN title TYPE VARCHAR(25);
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]