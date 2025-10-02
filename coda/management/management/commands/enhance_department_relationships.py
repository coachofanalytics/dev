"""
Management command to enhance data model with proper department relationships.

This command addresses the issue where employee categories are used as a proxy for departments.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from accounts.models import CustomerUser, Department


class Command(BaseCommand):
    help = 'Enhance data model with proper department relationships'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--strategy',
            type=str,
            choices=['create_missing', 'map_existing', 'validate_only'],
            default='map_existing',
            help='Strategy for department relationships: create_missing, map_existing, or validate_only'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        strategy = options['strategy']
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS(f'Enhancing Department Relationships (Strategy: {strategy})')
        )
        self.stdout.write('=' * 60)
        
        try:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('DRY RUN MODE - No changes will be made')
                )
            
            # Analyze current state
            self._analyze_current_state()
            
            if strategy == 'validate_only':
                self._validate_department_mapping()
            elif strategy == 'create_missing':
                self._create_missing_departments(dry_run)
            elif strategy == 'map_existing':
                self._map_existing_departments(dry_run)
            
            self.stdout.write(
                self.style.SUCCESS('\nDepartment relationship enhancement completed!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nCommand failed: {str(e)}')
            )
            raise CommandError(f'Department enhancement failed: {str(e)}')
    
    def _analyze_current_state(self):
        """Analyze the current state of departments and employee categories."""
        self.stdout.write('\nCURRENT STATE ANALYSIS:')
        self.stdout.write('-' * 40)
        
        # Count departments
        dept_count = Department.objects.count()
        self.stdout.write(f'Total Departments: {dept_count}')
        
        # Count employees by category
        from django.db.models import Count
        employee_categories = CustomerUser.objects.values('category').annotate(
            count=Count('id')
        ).order_by('category')
        
        self.stdout.write(f'\nEmployee Categories:')
        for cat in employee_categories:
            category = cat['category']
            count = cat['count']
            self.stdout.write(f'  Category {category}: {count} employees')
        
        # Check if any employees have department relationships
        # (This would need to be implemented in the model)
        self.stdout.write(f'\nNote: Department relationships need to be added to CustomerUser model')
    
    def _validate_department_mapping(self):
        """Validate the current department mapping logic."""
        self.stdout.write('\nDEPARTMENT MAPPING VALIDATION:')
        self.stdout.write('-' * 40)
        
        # Current mapping from TaskHistoryAnalyzer
        category_to_dept = {
            '999': 'Other',
            '1': 'IT',
            '2': 'HR',
            '3': 'Finance',
            '4': 'Marketing',
            '5': 'Operations'
        }
        
        # Check which categories exist in the database
        existing_categories = set(CustomerUser.objects.values_list('category', flat=True).distinct())
        mapped_categories = set(category_to_dept.keys())
        
        self.stdout.write(f'Existing categories: {sorted(existing_categories)}')
        self.stdout.write(f'Mapped categories: {sorted(mapped_categories)}')
        
        unmapped_categories = existing_categories - mapped_categories
        if unmapped_categories:
            self.stdout.write(
                self.style.WARNING(f'Unmapped categories: {sorted(unmapped_categories)}')
            )
        
        unused_mappings = mapped_categories - existing_categories
        if unused_mappings:
            self.stdout.write(
                self.style.WARNING(f'Unused mappings: {sorted(unused_mappings)}')
            )
    
    def _create_missing_departments(self, dry_run):
        """Create missing departments based on employee categories."""
        self.stdout.write('\nCREATING MISSING DEPARTMENTS:')
        self.stdout.write('-' * 40)
        
        # Get all unique categories
        categories = CustomerUser.objects.values_list('category', flat=True).distinct()
        
        # Department mapping
        category_to_dept = {
            '999': 'Other',
            '1': 'IT',
            '2': 'HR',
            '3': 'Finance',
            '4': 'Marketing',
            '5': 'Operations'
        }
        
        created_count = 0
        
        for category in categories:
            category_str = str(category)
            if category_str in category_to_dept:
                dept_name = category_to_dept[category_str]
                
                # Check if department already exists
                if not Department.objects.filter(name=dept_name).exists():
                    if not dry_run:
                        Department.objects.create(
                            name=dept_name,
                            description=f'Department for category {category}',
                            is_active=True
                        )
                        created_count += 1
                        self.stdout.write(f'Created department: {dept_name}')
                    else:
                        created_count += 1
                        self.stdout.write(f'Would create department: {dept_name}')
        
        self.stdout.write(f'\n{"Would create" if dry_run else "Created"} {created_count} departments')
    
    def _map_existing_departments(self, dry_run):
        """Map existing departments to employee categories."""
        self.stdout.write('\nMAPPING EXISTING DEPARTMENTS:')
        self.stdout.write('-' * 40)
        
        # This would require adding a department field to CustomerUser model
        # For now, we'll just document what needs to be done
        
        self.stdout.write('To implement proper department relationships:')
        self.stdout.write('1. Add department field to CustomerUser model')
        self.stdout.write('2. Create migration to add the field')
        self.stdout.write('3. Update TaskHistoryAnalyzer to use the new field')
        self.stdout.write('4. Create data migration to populate the field')
        
        # Show current mapping logic
        category_to_dept = {
            '999': 'Other',
            '1': 'IT',
            '2': 'HR',
            '3': 'Finance',
            '4': 'Marketing',
            '5': 'Operations'
        }
        
        self.stdout.write(f'\nCurrent mapping logic:')
        for category, dept in category_to_dept.items():
            employee_count = CustomerUser.objects.filter(category=category).count()
            self.stdout.write(f'  Category {category} -> {dept} ({employee_count} employees)')
    
    def _create_model_enhancement_script(self):
        """Create a script to enhance the CustomerUser model."""
        script_content = '''
# Model Enhancement for CustomerUser
# Add this to accounts/models.py

from django.db import models

class CustomerUser(models.Model):
    # ... existing fields ...
    
    # Add department relationship
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Employee department'
    )
    
    # Migration command to run:
    # python manage.py makemigrations accounts
    # python manage.py migrate
        '''
        
        with open('/Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV/department_model_enhancement.py', 'w') as f:
            f.write(script_content)
        
        self.stdout.write('Created department_model_enhancement.py with model changes')

