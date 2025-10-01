"""
Fix Budget Category Foreign Key Constraint

The Budget model has a foreign key pointing to the wrong category table.
This script fixes the constraint to point to the correct table.
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Fix Budget model category foreign key constraint"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually execute the fix (default is dry-run)'
        )
    
    def handle(self, *args, **options):
        execute = options['execute']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        if execute:
            self.stdout.write(self.style.WARNING('FIXING BUDGET CATEGORY CONSTRAINT'))
        else:
            self.stdout.write(self.style.SUCCESS('BUDGET CATEGORY CONSTRAINT FIX (DRY RUN)'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        with connection.cursor() as cursor:
            # 1. Check current constraint
            self.stdout.write("1. Current Constraint:")
            cursor.execute("""
                SELECT 
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_name = 'finance_budget'
                  AND kcu.column_name = 'category_id';
            """)
            
            result = cursor.fetchone()
            if result:
                constraint_name, column_name, foreign_table = result
                self.stdout.write(f"  Constraint: {constraint_name}")
                self.stdout.write(f"  References: {foreign_table}")
                
                if foreign_table == 'finance_budgetcategory':
                    self.stdout.write(self.style.SUCCESS("\n  ✓ Constraint is already correct!"))
                    return
                
                self.stdout.write(self.style.WARNING(f"\n  ✗ Wrong table: {foreign_table}"))
                self.stdout.write(f"  Should be: finance_budgetcategory")
            
            # 2. Check if correct table exists
            self.stdout.write("\n2. Checking correct category table:")
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'finance_budgetcategory';
            """)
            
            if cursor.fetchone()[0] > 0:
                cursor.execute("SELECT COUNT(*) FROM finance_budgetcategory;")
                count = cursor.fetchone()[0]
                self.stdout.write(self.style.SUCCESS(f"  ✓ finance_budgetcategory exists with {count} records"))
            else:
                self.stdout.write(self.style.ERROR("  ✗ finance_budgetcategory table does not exist!"))
                return
            
            # 3. Check wrong table
            self.stdout.write("\n3. Checking wrong category table:")
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'finance_budget_category';
            """)
            
            if cursor.fetchone()[0] > 0:
                cursor.execute("SELECT COUNT(*) FROM finance_budget_category;")
                count = cursor.fetchone()[0]
                self.stdout.write(f"  - finance_budget_category exists with {count} records")
            
            # 4. Fix the constraint
            if execute:
                self.stdout.write("\n4. Fixing constraint...")
                
                try:
                    # Drop the wrong constraint
                    self.stdout.write(f"  - Dropping constraint {constraint_name}...")
                    cursor.execute(f"ALTER TABLE finance_budget DROP CONSTRAINT {constraint_name};")
                    
                    # Add correct constraint
                    self.stdout.write("  - Adding correct constraint...")
                    cursor.execute("""
                        ALTER TABLE finance_budget 
                        ADD CONSTRAINT finance_budget_category_id_correct_fk
                        FOREIGN KEY (category_id) 
                        REFERENCES finance_budgetcategory(id);
                    """)
                    
                    self.stdout.write(self.style.SUCCESS("\n  ✓ Constraint fixed successfully!"))
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"\n  ✗ Error: {e}"))
                    raise
            else:
                self.stdout.write("\n4. Would fix constraint (DRY RUN):")
                self.stdout.write(f"  - Would drop: {constraint_name}")
                self.stdout.write("  - Would add: finance_budget_category_id_correct_fk")
                self.stdout.write("  - Referencing: finance_budgetcategory(id)")
                self.stdout.write("\nRun with --execute to actually fix")
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.SUCCESS('DONE'))
        self.stdout.write('='*80 + '\n')


