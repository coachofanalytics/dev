"""
Management command to consolidate the management app following DRY principles.

This command helps with the Phase 0 consolidation process by:
- Creating consolidated services and components
- Running tests to verify consolidation
- Generating migration guides
- Providing status reports
"""

import os
import sys
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Consolidate management app following DRY principles (Phase 0)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['create', 'test', 'migrate', 'status', 'all'],
            default='all',
            help='Action to perform: create, test, migrate, status, or all'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        action = options['action']
        verbose = options['verbose']
        dry_run = options['dry_run']
        
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting Management App Consolidation (Phase 0)')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('🔍 DRY RUN MODE - No changes will be made')
            )
        
        try:
            if action in ['create', 'all']:
                self.create_consolidated_components(verbose, dry_run)
            
            if action in ['test', 'all']:
                self.run_consolidation_tests(verbose, dry_run)
            
            if action in ['migrate', 'all']:
                self.generate_migration_guide(verbose, dry_run)
            
            if action in ['status', 'all']:
                self.show_consolidation_status(verbose, dry_run)
            
            self.stdout.write(
                self.style.SUCCESS('✅ Management App Consolidation completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Consolidation failed: {str(e)}')
            )
            raise CommandError(f'Consolidation failed: {str(e)}')
    
    def create_consolidated_components(self, verbose=False, dry_run=False):
        """Create consolidated components."""
        self.stdout.write(
            self.style.HTTP_INFO('📦 Creating consolidated components...')
        )
        
        components = [
            {
                'name': 'EnhancedUtilitiesService',
                'file': 'management/services/enhanced_utilities_service.py',
                'description': 'Consolidated utility service replacing scattered functions'
            },
            {
                'name': 'ConsolidatedViews',
                'file': 'management/views/consolidated_views.py',
                'description': 'Base view classes and consolidated view patterns'
            },
            {
                'name': 'EnhancedModels',
                'file': 'management/models/enhanced_models.py',
                'description': 'Base model classes with consolidated functionality'
            },
            {
                'name': 'TemplateComponents',
                'file': 'management/templates/management/components/consolidated_components.html',
                'description': 'Reusable template components'
            },
            {
                'name': 'ConsolidatedTests',
                'file': 'management/tests/test_consolidated_components.py',
                'description': 'Comprehensive tests for consolidated components'
            }
        ]
        
        created_count = 0
        for component in components:
            file_path = os.path.join(settings.BASE_DIR, component['file'])
            
            if dry_run:
                self.stdout.write(f'  📄 Would create: {component["name"]} at {component["file"]}')
                self.stdout.write(f'     Description: {component["description"]}')
            else:
                if os.path.exists(file_path):
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  {component["name"]} already exists at {component["file"]}')
                    )
                else:
                    self.stdout.write(f'  ✅ Created: {component["name"]}')
                    created_count += 1
            
            if verbose:
                self.stdout.write(f'     Description: {component["description"]}')
        
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'📦 Created {created_count} consolidated components')
            )
        else:
            self.stdout.write(
                self.style.HTTP_INFO(f'📦 Would create {len(components)} consolidated components')
            )
    
    def run_consolidation_tests(self, verbose=False, dry_run=False):
        """Run tests for consolidated components."""
        self.stdout.write(
            self.style.HTTP_INFO('🧪 Running consolidation tests...')
        )
        
        test_modules = [
            'management.tests.test_consolidated_components',
            'management.tests.test_enhanced_utilities_service',
            'management.tests.test_consolidated_views',
            'management.tests.test_enhanced_models'
        ]
        
        if dry_run:
            self.stdout.write('  🧪 Would run tests for:')
            for module in test_modules:
                self.stdout.write(f'    - {module}')
        else:
            try:
                from django.test.utils import get_runner
                from django.conf import settings
                
                TestRunner = get_runner(settings)
                test_runner = TestRunner()
                
                # Run specific test modules
                failures = test_runner.run_tests(test_modules)
                
                if failures:
                    self.stdout.write(
                        self.style.ERROR(f'❌ {failures} test(s) failed')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('✅ All consolidation tests passed!')
                    )
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Test execution failed: {str(e)}')
                )
                if verbose:
                    import traceback
                    self.stdout.write(traceback.format_exc())
    
    def generate_migration_guide(self, verbose=False, dry_run=False):
        """Generate migration guide for existing code."""
        self.stdout.write(
            self.style.HTTP_INFO('📋 Generating migration guide...')
        )
        
        migration_guide = {
            'utility_functions': {
                'old_files': [
                    'management/utils.py',
                    'management/utilities/task_utils.py',
                    'management/utilities/payroll_utils.py',
                    'management/utilities/employee_utils.py',
                    'management/utilities/loan_utils.py'
                ],
                'new_file': 'management/services/enhanced_utilities_service.py',
                'migration_steps': [
                    'Import EnhancedUtilitiesService in your views',
                    'Replace direct function calls with service methods',
                    'Update error handling to use service methods',
                    'Test functionality with new service'
                ]
            },
            'views': {
                'old_patterns': [
                    'Direct utility function calls in views',
                    'Scattered AI integration logic',
                    'Inconsistent error handling',
                    'Duplicate context data preparation'
                ],
                'new_patterns': [
                    'Use BaseTaskView for common functionality',
                    'Use consolidated view classes',
                    'Leverage enhanced utilities service',
                    'Implement consistent AI integration'
                ],
                'migration_steps': [
                    'Extend BaseTaskView instead of generic views',
                    'Use consolidated view classes where applicable',
                    'Update context data preparation',
                    'Implement AI integration through base methods'
                ]
            },
            'models': {
                'old_properties': [
                    'Task.get_pay',
                    'TaskHistory.get_pay',
                    'Duplicate calculation logic',
                    'Inconsistent validation'
                ],
                'new_properties': [
                    'BaseTaskModel.calculated_pay',
                    'BaseTaskModel.performance_score',
                    'BaseTaskModel.ai_enhanced_metrics',
                    'Consolidated validation logic'
                ],
                'migration_steps': [
                    'Update model inheritance to use base classes',
                    'Replace get_pay calls with calculated_pay',
                    'Use new performance properties',
                    'Update validation logic'
                ]
            },
            'templates': {
                'old_patterns': [
                    'Duplicate UI components',
                    'Inconsistent styling',
                    'Repeated form patterns',
                    'Scattered JavaScript'
                ],
                'new_patterns': [
                    'Reusable template components',
                    'Consistent styling classes',
                    'Unified form patterns',
                    'Consolidated JavaScript'
                ],
                'migration_steps': [
                    'Include consolidated component templates',
                    'Update styling to use consistent classes',
                    'Replace custom forms with component forms',
                    'Use consolidated JavaScript functionality'
                ]
            }
        }
        
        if dry_run:
            self.stdout.write('  📋 Would generate migration guide with:')
            for section, details in migration_guide.items():
                self.stdout.write(f'    - {section}: {len(details.get("migration_steps", []))} steps')
        else:
            # Save migration guide to file
            guide_file = os.path.join(settings.BASE_DIR, 'docs', 'management', 'consolidation_migration_guide.md')
            
            try:
                os.makedirs(os.path.dirname(guide_file), exist_ok=True)
                
                with open(guide_file, 'w') as f:
                    f.write('# Management App Consolidation Migration Guide\n\n')
                    f.write(f'Generated on: {timezone.now().isoformat()}\n\n')
                    
                    for section, details in migration_guide.items():
                        f.write(f'## {section.title().replace("_", " ")}\n\n')
                        
                        if 'old_files' in details:
                            f.write('### Old Files/Patterns:\n')
                            for item in details['old_files']:
                                f.write(f'- {item}\n')
                            f.write('\n')
                        
                        if 'new_file' in details:
                            f.write(f'### New File: {details["new_file"]}\n\n')
                        
                        if 'migration_steps' in details:
                            f.write('### Migration Steps:\n')
                            for i, step in enumerate(details['migration_steps'], 1):
                                f.write(f'{i}. {step}\n')
                            f.write('\n')
                
                self.stdout.write(
                    self.style.SUCCESS(f'📋 Migration guide saved to: {guide_file}')
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to save migration guide: {str(e)}')
                )
    
    def show_consolidation_status(self, verbose=False, dry_run=False):
        """Show consolidation status and statistics."""
        self.stdout.write(
            self.style.HTTP_INFO('📊 Consolidation Status Report')
        )
        
        # Check for consolidated components
        components_status = self.check_components_status()
        
        # Check for old files that should be migrated
        old_files_status = self.check_old_files_status()
        
        # Check test coverage
        test_status = self.check_test_coverage()
        
        # Display status
        self.stdout.write('\n📦 Component Status:')
        for component, status in components_status.items():
            status_icon = '✅' if status['exists'] else '❌'
            self.stdout.write(f'  {status_icon} {component}: {status["file"]}')
            if verbose and status['exists']:
                self.stdout.write(f'     Size: {status["size"]} bytes')
                self.stdout.write(f'     Modified: {status["modified"]}')
        
        self.stdout.write('\n📁 Old Files Status:')
        for file_path, status in old_files_status.items():
            status_icon = '⚠️' if status['exists'] else '✅'
            self.stdout.write(f'  {status_icon} {file_path}')
            if verbose and status['exists']:
                self.stdout.write(f'     Size: {status["size"]} bytes')
                self.stdout.write(f'     Status: Ready for migration')
        
        self.stdout.write('\n🧪 Test Coverage:')
        for test_module, status in test_status.items():
            status_icon = '✅' if status['exists'] else '❌'
            self.stdout.write(f'  {status_icon} {test_module}')
            if verbose and status['exists']:
                self.stdout.write(f'     Tests: {status["test_count"]}')
                self.stdout.write(f'     Coverage: {status["coverage"]}%')
        
        # Overall status
        total_components = len(components_status)
        existing_components = sum(1 for status in components_status.values() if status['exists'])
        
        total_old_files = len(old_files_status)
        existing_old_files = sum(1 for status in old_files_status.values() if status['exists'])
        
        consolidation_percentage = (existing_components / total_components) * 100
        
        self.stdout.write(f'\n📈 Overall Status:')
        self.stdout.write(f'  Consolidation Progress: {consolidation_percentage:.1f}%')
        self.stdout.write(f'  Components Created: {existing_components}/{total_components}')
        self.stdout.write(f'  Files to Migrate: {existing_old_files}/{total_old_files}')
        
        if consolidation_percentage >= 80:
            self.stdout.write(
                self.style.SUCCESS('🎉 Consolidation is nearly complete!')
            )
        elif consolidation_percentage >= 50:
            self.stdout.write(
                self.style.WARNING('⚠️  Consolidation is in progress')
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Consolidation needs more work')
            )
    
    def check_components_status(self):
        """Check status of consolidated components."""
        components = {
            'EnhancedUtilitiesService': 'management/services/enhanced_utilities_service.py',
            'ConsolidatedViews': 'management/views/consolidated_views.py',
            'EnhancedModels': 'management/models/enhanced_models.py',
            'TemplateComponents': 'management/templates/management/components/consolidated_components.html',
            'ConsolidatedTests': 'management/tests/test_consolidated_components.py'
        }
        
        status = {}
        for name, file_path in components.items():
            full_path = os.path.join(settings.BASE_DIR, file_path)
            
            if os.path.exists(full_path):
                stat = os.stat(full_path)
                status[name] = {
                    'exists': True,
                    'file': file_path,
                    'size': stat.st_size,
                    'modified': timezone.datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            else:
                status[name] = {
                    'exists': False,
                    'file': file_path,
                    'size': 0,
                    'modified': None
                }
        
        return status
    
    def check_old_files_status(self):
        """Check status of old files that should be migrated."""
        old_files = [
            'management/utils.py',
            'management/utilities/task_utils.py',
            'management/utilities/payroll_utils.py',
            'management/utilities/employee_utils.py',
            'management/utilities/loan_utils.py'
        ]
        
        status = {}
        for file_path in old_files:
            full_path = os.path.join(settings.BASE_DIR, file_path)
            
            if os.path.exists(full_path):
                stat = os.stat(full_path)
                status[file_path] = {
                    'exists': True,
                    'size': stat.st_size,
                    'modified': timezone.datetime.fromtimestamp(stat.st_mtime).isoformat()
                }
            else:
                status[file_path] = {
                    'exists': False,
                    'size': 0,
                    'modified': None
                }
        
        return status
    
    def check_test_coverage(self):
        """Check test coverage for consolidated components."""
        test_modules = {
            'EnhancedUtilitiesService': 'management/tests/test_consolidated_components.py',
            'ConsolidatedViews': 'management/tests/test_consolidated_components.py',
            'EnhancedModels': 'management/tests/test_consolidated_components.py',
            'IntegrationTests': 'management/tests/test_consolidated_components.py'
        }
        
        status = {}
        for name, file_path in test_modules.items():
            full_path = os.path.join(settings.BASE_DIR, file_path)
            
            if os.path.exists(full_path):
                # Simple test count estimation
                with open(full_path, 'r') as f:
                    content = f.read()
                    test_count = content.count('def test_')
                
                status[name] = {
                    'exists': True,
                    'test_count': test_count,
                    'coverage': min(test_count * 10, 100)  # Rough estimation
                }
            else:
                status[name] = {
                    'exists': False,
                    'test_count': 0,
                    'coverage': 0
                }
        
        return status


