"""
Management command to export legacy position data to CSV for archival
Run this BEFORE deleting legacy models
"""
from django.core.management.base import BaseCommand
import csv
from datetime import datetime


class Command(BaseCommand):
    help = 'Export legacy ShortPut and covered_calls data to CSV files'

    def handle(self, *args, **options):
        from investing.models import ShortPut, covered_calls
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('📦 LEGACY POSITION DATA BACKUP'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # ============================================================
        # PART 1: Export ShortPut
        # ============================================================
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('📊 PART 1: Exporting ShortPut positions')
        self.stdout.write('=' * 80 + '\n')
        
        shortputs = ShortPut.objects.all()
        filename_sp = f'legacy_shortput_backup_{timestamp}.csv'
        
        if shortputs.exists():
            with open(filename_sp, 'w', newline='', encoding='utf-8') as csvfile:
                # Get all field names
                fields = [f.name for f in ShortPut._meta.get_fields() 
                         if not f.many_to_many and not f.one_to_many]
                
                writer = csv.DictWriter(csvfile, fieldnames=fields)
                writer.writeheader()
                
                for sp in shortputs:
                    row = {}
                    for field in fields:
                        try:
                            value = getattr(sp, field)
                            row[field] = str(value) if value is not None else ''
                        except AttributeError:
                            row[field] = ''
                    writer.writerow(row)
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ Exported {shortputs.count()} ShortPut records to {filename_sp}'))
        else:
            self.stdout.write('  No ShortPut records to export')
        
        # ============================================================
        # PART 2: Export covered_calls
        # ============================================================
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('📊 PART 2: Exporting covered_calls positions')
        self.stdout.write('=' * 80 + '\n')
        
        calls = covered_calls.objects.all()
        filename_cc = f'legacy_covered_calls_backup_{timestamp}.csv'
        
        if calls.exists():
            with open(filename_cc, 'w', newline='', encoding='utf-8') as csvfile:
                # Get all field names
                fields = [f.name for f in covered_calls._meta.get_fields() 
                         if not f.many_to_many and not f.one_to_many]
                
                writer = csv.DictWriter(csvfile, fieldnames=fields)
                writer.writeheader()
                
                for cc in calls:
                    row = {}
                    for field in fields:
                        try:
                            value = getattr(cc, field)
                            row[field] = str(value) if value is not None else ''
                        except AttributeError:
                            row[field] = ''
                    writer.writerow(row)
            
            self.stdout.write(self.style.SUCCESS(f'  ✅ Exported {calls.count()} covered_calls records to {filename_cc}'))
        else:
            self.stdout.write('  No covered_calls records to export')
        
        # ============================================================
        # SUMMARY
        # ============================================================
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('📊 BACKUP SUMMARY')
        self.stdout.write('=' * 80)
        self.stdout.write(f'✅ ShortPut backup: {filename_sp}')
        self.stdout.write(f'✅ covered_calls backup: {filename_cc}')
        self.stdout.write('=' * 80)
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Backup complete!'))
        self.stdout.write(self.style.SUCCESS('\nNext steps:'))
        self.stdout.write('  1. Review CSV files to ensure data captured')
        self.stdout.write('  2. Delete legacy models from models.py')
        self.stdout.write('  3. Create migration: python manage.py makemigrations')
        self.stdout.write('  4. Apply migration: python manage.py migrate')
        self.stdout.write('  5. Store CSV files in archive/ directory')

