"""
Budget Data Backup Script

Phase 0 Task 0.1: Create comprehensive backup of all budget-related data
"""

from django.core.management.base import BaseCommand
from django.core import serializers
from django.utils import timezone
from finance.models import (
    Budget, CodaBudget, BudgetCategory, BudgetSubCategory,
    BudgetEstimateProjection, BudgetEstimationTemplate,
    MultiYearBudgetPlan
)
from finance.models_detailed_budget import BudgetItemDetail, BudgetEstimateItem
import json
import os


class Command(BaseCommand):
    help = "Create comprehensive backup of all budget data - Phase 0"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--output-dir',
            type=str,
            default='backups',
            help='Directory to store backup files'
        )
        parser.add_argument(
            '--format',
            type=str,
            default='json',
            choices=['json', 'xml', 'yaml'],
            help='Backup format'
        )
    
    def handle(self, *args, **options):
        output_dir = options['output_dir']
        format_type = options['format']
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('BUDGET DATA BACKUP'))
        self.stdout.write(self.style.SUCCESS(f'Timestamp: {timestamp}'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        # Backup each model
        models_to_backup = [
            ('budget', Budget),
            ('coda_budget', CodaBudget),
            ('budget_category', BudgetCategory),
            ('budget_subcategory', BudgetSubCategory),
            ('budget_estimate_projection', BudgetEstimateProjection),
            ('budget_estimation_template', BudgetEstimationTemplate),
            ('multi_year_budget_plan', MultiYearBudgetPlan),
            ('budget_item_detail', BudgetItemDetail),
            ('budget_estimate_item', BudgetEstimateItem),
        ]
        
        total_records = 0
        
        for model_name, model_class in models_to_backup:
            count = self._backup_model(
                model_class, model_name, output_dir, timestamp, format_type
            )
            total_records += count
        
        # Create summary file
        self._create_summary(output_dir, timestamp, models_to_backup, total_records)
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS(f'BACKUP COMPLETE'))
        self.stdout.write(self.style.SUCCESS(f'Total records backed up: {total_records}'))
        self.stdout.write(self.style.SUCCESS(f'Backup location: {output_dir}/'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        # Print restoration command
        self.stdout.write('\nTo restore from backup:')
        self.stdout.write(f'  python manage.py loaddata {output_dir}/*_{timestamp}.json')
    
    def _backup_model(self, model_class, model_name, output_dir, timestamp, format_type):
        """Backup a single model"""
        queryset = model_class.objects.all()
        count = queryset.count()
        
        if count == 0:
            self.stdout.write(f"  ⊘ {model_name:<30} (0 records - skipped)")
            return 0
        
        filename = f"{model_name}_{timestamp}.{format_type}"
        filepath = os.path.join(output_dir, filename)
        
        # Serialize data
        data = serializers.serialize(format_type, queryset)
        
        # Write to file
        with open(filepath, 'w') as f:
            f.write(data)
        
        self.stdout.write(self.style.SUCCESS(
            f"  ✓ {model_name:<30} ({count:>6} records) → {filename}"
        ))
        
        return count
    
    def _create_summary(self, output_dir, timestamp, models_to_backup, total_records):
        """Create backup summary file"""
        summary = {
            'timestamp': timestamp,
            'datetime': timezone.now().isoformat(),
            'total_records': total_records,
            'models': []
        }
        
        for model_name, model_class in models_to_backup:
            summary['models'].append({
                'name': model_name,
                'model': model_class.__name__,
                'count': model_class.objects.count()
            })
        
        summary_file = os.path.join(output_dir, f'backup_summary_{timestamp}.json')
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.stdout.write(f"\n  ✓ Summary created: backup_summary_{timestamp}.json")

