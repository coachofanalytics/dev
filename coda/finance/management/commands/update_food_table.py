"""
Management command to update existing Food table with new fields

Adds fields that are in the new model but missing from the database
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Update Food table with new fields from enhanced model'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write('Updating finance_food table...')
            
            # Add missing columns to finance_food table
            updates = [
                # Add category field
                {
                    'name': 'category',
                    'sql': """
                        ALTER TABLE finance_food 
                        ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'other';
                    """
                },
                # Rename unit_price to current_unit_price if needed
                {
                    'name': 'current_unit_price',
                    'sql': """
                        DO $$ 
                        BEGIN
                            IF EXISTS (SELECT 1 FROM information_schema.columns 
                                      WHERE table_name='finance_food' AND column_name='unit_price') 
                               AND NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                              WHERE table_name='finance_food' AND column_name='current_unit_price')
                            THEN
                                ALTER TABLE finance_food RENAME COLUMN unit_price TO current_unit_price;
                            END IF;
                        END $$;
                    """
                },
                # Add unit_of_measurement field
                {
                    'name': 'unit_of_measurement',
                    'sql': """
                        ALTER TABLE finance_food 
                        ADD COLUMN IF NOT EXISTS unit_of_measurement VARCHAR(20) DEFAULT 'kg';
                    """
                },
                # Add current_supplier_id field
                {
                    'name': 'current_supplier_id',
                    'sql': """
                        ALTER TABLE finance_food 
                        ADD COLUMN IF NOT EXISTS current_supplier_id BIGINT REFERENCES finance_supplier(id) ON DELETE SET NULL;
                    """
                },
                # Add currency field
                {
                    'name': 'currency',
                    'sql': """
                        ALTER TABLE finance_food 
                        ADD COLUMN IF NOT EXISTS currency VARCHAR(3) DEFAULT 'KES';
                    """
                },
                # Add created_by_id field
                {
                    'name': 'created_by_id',
                    'sql': """
                        ALTER TABLE finance_food 
                        ADD COLUMN IF NOT EXISTS created_by_id BIGINT REFERENCES accounts_customeruser(id) ON DELETE SET NULL;
                    """
                },
                # Add created_at field
                {
                    'name': 'created_at',
                    'sql': """
                        ALTER TABLE finance_food 
                        ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                    """
                },
                # Add updated_at field
                {
                    'name': 'updated_at',
                    'sql': """
                        ALTER TABLE finance_food 
                        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
                    """
                },
                # Add is_active field
                {
                    'name': 'is_active',
                    'sql': """
                        ALTER TABLE finance_food 
                        ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
                    """
                },
            ]
            
            for update in updates:
                try:
                    cursor.execute(update['sql'])
                    self.stdout.write(self.style.SUCCESS(f"✅ Added/verified column: {update['name']}"))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"⚠️  {update['name']}: {e}"))
            
            # Create index on category
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS finance_food_category_idx 
                    ON finance_food(category);
                """)
                self.stdout.write(self.style.SUCCESS("✅ Created index on category"))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️  Index: {e}"))
            
            self.stdout.write(self.style.SUCCESS('\n🎉 Food table updated successfully!'))
            self.stdout.write('\nNext: Refresh your browser to load the dashboard')

