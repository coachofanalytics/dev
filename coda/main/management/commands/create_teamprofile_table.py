"""
Management command to create TeamProfile table using Django's schema editor.

This is needed because accounts app has no migrations.
Safe approach - creates only TeamProfile table, doesn't touch existing tables.

Usage:
    python manage.py create_teamprofile_table
    python manage.py create_teamprofile_table --drop-first  # Recreate
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Create TeamProfile table using Django schema editor'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--drop-first',
            action='store_true',
            help='Drop existing table before creating',
        )
    
    def handle(self, *args, **options):
        drop_first = options['drop_first']
        
        self.stdout.write(self.style.SUCCESS('\n🏗️ Creating TeamProfile Table\n'))
        self.stdout.write('=' * 70 + '\n')
        
        from accounts.models import TeamProfile
        
        # Check if table exists
        table_exists = self._table_exists('accounts_teamprofile')
        
        if table_exists:
            if drop_first:
                self.stdout.write(
                    self.style.WARNING('Dropping existing table...')
                )
                with connection.schema_editor() as schema_editor:
                    schema_editor.delete_model(TeamProfile)
                self.stdout.write('  ✅ Dropped')
            else:
                self.stdout.write(
                    self.style.WARNING('Table already exists!')
                )
                self.stdout.write(
                    '\nUse --drop-first to recreate, or skip if table is correct.\n'
                )
                return
        
        # Create table
        self.stdout.write('Creating table...')
        
        try:
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(TeamProfile)
            
            self.stdout.write(
                self.style.SUCCESS('  ✅ Table created successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Error creating table: {str(e)}')
            )
            return
        
        # Verify table
        self.stdout.write('\nVerifying table...')
        
        if self._table_exists('accounts_teamprofile'):
            self.stdout.write(self.style.SUCCESS('  ✅ Table exists'))
            
            # Count columns
            column_count = self._count_columns('accounts_teamprofile')
            self.stdout.write(f'  ✅ Columns: {column_count}')
            
            # Count indexes
            index_count = self._count_indexes('accounts_teamprofile')
            self.stdout.write(f'  ✅ Indexes: {index_count}')
            
        else:
            self.stdout.write(
                self.style.ERROR('  ❌ Table not found after creation')
            )
            return
        
        # Test model
        self.stdout.write('\nTesting Django model...')
        
        try:
            from accounts.models import TeamProfile
            
            # Get count
            count = TeamProfile.objects.count()
            self.stdout.write(
                self.style.SUCCESS(f'  ✅ Model works! Current records: {count}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Model error: {str(e)}')
            )
            return
        
        # Success summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(
            self.style.SUCCESS('\n✅ TeamProfile table created successfully!')
        )
        self.stdout.write('\n📝 Next steps:')
        self.stdout.write('  1. python manage.py create_team_groups')
        self.stdout.write('  2. python manage.py verify_team_members')
        self.stdout.write('  3. python manage.py assign_manual_team_members')
        self.stdout.write('\n')
    
    def _table_exists(self, table_name):
        """Check if table exists in database"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                )
            """, [table_name])
            return cursor.fetchone()[0]
    
    def _count_columns(self, table_name):
        """Count columns in table"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.columns 
                WHERE table_name = %s
            """, [table_name])
            return cursor.fetchone()[0]
    
    def _count_indexes(self, table_name):
        """Count indexes on table"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM pg_indexes 
                WHERE tablename = %s
            """, [table_name])
            return cursor.fetchone()[0]

