"""
Smart Task Migration Management Command

Replaces the flawed dump_data function with intelligent task migration
that only moves completed tasks with evidence to TaskHistory.

Usage:
    python manage.py smart_migrate_tasks
    python manage.py smart_migrate_tasks --preview
    python manage.py smart_migrate_tasks --month 10 --year 2025
    python manage.py smart_migrate_tasks --rollback --month 10 --year 2025
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime

from management.services.smart_migration_service import SmartMigrationService


class Command(BaseCommand):
    help = 'Smart migration of completed tasks to TaskHistory with evidence validation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--preview',
            action='store_true',
            help='Preview what tasks would be migrated without actually migrating',
        )
        parser.add_argument(
            '--month',
            type=int,
            help='Target month for migration (1-12)',
        )
        parser.add_argument(
            '--year',
            type=int,
            help='Target year for migration',
        )
        parser.add_argument(
            '--rollback',
            action='store_true',
            help='Rollback a previous migration',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration without confirmation',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=== Smart Task Migration Service ===')
        )
        
        # Initialize service
        migration_service = SmartMigrationService()
        
        # Get target month/year
        target_month = options.get('month')
        target_year = options.get('year')
        
        if target_month is None or target_year is None:
            current_date = datetime.now()
            target_month = current_date.month
            target_year = current_date.year
        
        # Validate month/year
        if not (1 <= target_month <= 12):
            raise CommandError('Month must be between 1 and 12')
        
        if target_year < 2020 or target_year > 2030:
            raise CommandError('Year must be between 2020 and 2030')
        
        self.stdout.write(f'Target: {target_month}/{target_year}')
        
        # Handle rollback
        if options['rollback']:
            self.handle_rollback(migration_service, target_month, target_year, options)
            return
        
        # Handle preview
        if options['preview']:
            self.handle_preview(migration_service, target_month, target_year)
            return
        
        # Handle actual migration
        self.handle_migration(migration_service, target_month, target_year, options)
    
    def handle_preview(self, migration_service, target_month, target_year):
        """Handle migration preview."""
        self.stdout.write(
            self.style.WARNING('Generating migration preview...')
        )
        
        preview = migration_service.get_migration_preview(target_month, target_year)
        
        if 'error' in preview:
            self.stdout.write(
                self.style.ERROR(f'Error generating preview: {preview["error"]}')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(f'Preview for {target_month}/{target_year}:')
        )
        self.stdout.write(f'  Total eligible tasks: {preview["total_eligible_tasks"]}')
        self.stdout.write(f'  Total employees: {preview["total_employees"]}')
        self.stdout.write(f'  Migration criteria:')
        self.stdout.write(f'    - Minimum points: {preview["migration_criteria"]["minimum_points"]}')
        self.stdout.write(f'    - Require evidence: {preview["migration_criteria"]["require_evidence"]}')
        
        self.stdout.write('\nEmployee breakdown:')
        for emp_preview in preview['employee_previews']:
            self.stdout.write(f'  {emp_preview["employee_name"]}:')
            self.stdout.write(f'    - Tasks: {emp_preview["task_count"]}')
            self.stdout.write(f'    - Total points: {emp_preview["total_points"]}')
            
            for task in emp_preview['tasks']:
                evidence_status = '✓' if task['has_evidence'] else '✗'
                self.stdout.write(f'    - {task["activity_name"]}: {task["points"]} pts {evidence_status}')
    
    def handle_migration(self, migration_service, target_month, target_year, options):
        """Handle actual migration."""
        # Get preview first
        preview = migration_service.get_migration_preview(target_month, target_year)
        
        if 'error' in preview:
            self.stdout.write(
                self.style.ERROR(f'Error getting preview: {preview["error"]}')
            )
            return
        
        if preview['total_eligible_tasks'] == 0:
            self.stdout.write(
                self.style.WARNING('No eligible tasks found for migration.')
            )
            return
        
        # Show preview
        self.stdout.write(
            self.style.WARNING(f'About to migrate {preview["total_eligible_tasks"]} tasks for {preview["total_employees"]} employees.')
        )
        
        # Confirm migration
        if not options['force']:
            confirm = input('Do you want to proceed? (yes/no): ')
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write(
                    self.style.WARNING('Migration cancelled.')
                )
                return
        
        # Perform migration
        self.stdout.write(
            self.style.WARNING('Starting smart migration...')
        )
        
        result = migration_service.migrate_completed_tasks_to_history(target_month, target_year)
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Migration completed successfully!')
            )
            self.stdout.write(f'  Migrated: {result["migrated_count"]} tasks')
            self.stdout.write(f'  Skipped: {result["skipped_count"]} tasks')
            
            if result['errors']:
                self.stdout.write(
                    self.style.WARNING('Warnings:')
                )
                for error in result['errors']:
                    self.stdout.write(f'  - {error}')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Migration failed: {result["message"]}')
            )
            if 'error' in result:
                self.stdout.write(f'Error: {result["error"]}')
    
    def handle_rollback(self, migration_service, target_month, target_year, options):
        """Handle migration rollback."""
        self.stdout.write(
            self.style.WARNING(f'Rolling back migration for {target_month}/{target_year}...')
        )
        
        # Confirm rollback
        if not options['force']:
            confirm = input('Are you sure you want to rollback? This will delete TaskHistory records. (yes/no): ')
            if confirm.lower() not in ['yes', 'y']:
                self.stdout.write(
                    self.style.WARNING('Rollback cancelled.')
                )
                return
        
        result = migration_service.rollback_migration(target_month, target_year)
        
        if result['success']:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Rollback completed successfully!')
            )
            self.stdout.write(f'  Rolled back: {result["rolled_back_count"]} records')
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ Rollback failed: {result["message"]}')
            )
            if 'error' in result:
                self.stdout.write(f'Error: {result["error"]}')
