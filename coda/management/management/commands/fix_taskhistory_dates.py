"""
Management command to fix TaskHistory date data quality issues.

This command addresses the critical issue where all TaskHistory records have NULL daf_date values.
"""

import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction

from management.models import TaskHistory


class Command(BaseCommand):
    help = 'Fix TaskHistory date data quality issues by populating NULL daf_date values'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--strategy',
            type=str,
            choices=['created_at', 'random', 'sequential'],
            default='created_at',
            help='Strategy for assigning dates: created_at, random, or sequential'
        )
        parser.add_argument(
            '--months-back',
            type=int,
            default=24,
            help='Number of months back to distribute dates (default: 24)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch (default: 100)'
        )
    
    def handle(self, *args, **options):
        """Main command handler."""
        strategy = options['strategy']
        months_back = options['months_back']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting TaskHistory Date Fix (Strategy: {strategy})')
        )
        self.stdout.write('=' * 60)
        
        try:
            # Get all TaskHistory records with NULL dates
            null_date_records = TaskHistory.objects.filter(daf_date__isnull=True)
            total_records = null_date_records.count()
            
            if total_records == 0:
                self.stdout.write(
                    self.style.SUCCESS('No records with NULL dates found. Data quality is good!')
                )
                return
            
            self.stdout.write(f'Found {total_records:,} records with NULL dates')
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('DRY RUN MODE - No changes will be made')
                )
            
            # Calculate date range
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=months_back * 30)
            
            self.stdout.write(f'Date range: {start_date} to {end_date}')
            
            # Process records in batches
            processed = 0
            errors = 0
            
            for i in range(0, total_records, batch_size):
                batch = null_date_records[i:i + batch_size]
                
                if not dry_run:
                    with transaction.atomic():
                        for record in batch:
                            try:
                                new_date = self._assign_date(record, strategy, start_date, end_date)
                                record.daf_date = new_date
                                record.save(update_fields=['daf_date'])
                                processed += 1
                            except Exception as e:
                                self.stdout.write(
                                    self.style.ERROR(f'Error updating record {record.id}: {e}')
                                )
                                errors += 1
                else:
                    # Dry run - just count
                    for record in batch:
                        new_date = self._assign_date(record, strategy, start_date, end_date)
                        processed += 1
                
                # Progress update
                if (i + batch_size) % (batch_size * 10) == 0:
                    self.stdout.write(f'Processed {i + batch_size:,} records...')
            
            # Final results
            self.stdout.write('\n' + '=' * 60)
            if dry_run:
                self.stdout.write(
                    self.style.SUCCESS(f'DRY RUN COMPLETE: Would update {processed:,} records')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully updated {processed:,} records')
                )
                if errors > 0:
                    self.stdout.write(
                        self.style.WARNING(f'Errors encountered: {errors}')
                    )
            
            # Verify results
            remaining_null = TaskHistory.objects.filter(daf_date__isnull=True).count()
            self.stdout.write(f'Remaining NULL dates: {remaining_null}')
            
            if remaining_null == 0:
                self.stdout.write(
                    self.style.SUCCESS('✅ All TaskHistory records now have valid dates!')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\nCommand failed: {str(e)}')
            )
            raise CommandError(f'Date fix failed: {str(e)}')
    
    def _assign_date(self, record, strategy, start_date, end_date):
        """Assign a date to a TaskHistory record based on the chosen strategy."""
        
        if strategy == 'created_at':
            # Use created_at field if available
            if record.created_at:
                return record.created_at.date()
            else:
                # Fallback to random if no created_at
                return self._random_date(start_date, end_date)
        
        elif strategy == 'random':
            # Assign random date within range
            return self._random_date(start_date, end_date)
        
        elif strategy == 'sequential':
            # Assign dates sequentially (older records get older dates)
            # This is a simplified approach - in practice you might want more sophisticated logic
            total_days = (end_date - start_date).days
            # Use record ID to determine position (assuming higher IDs are newer)
            position = (record.id % 1000) / 1000  # Normalize to 0-1
            days_offset = int(total_days * position)
            return start_date + timedelta(days=days_offset)
        
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
    
    def _random_date(self, start_date, end_date):
        """Generate a random date between start_date and end_date."""
        total_days = (end_date - start_date).days
        random_days = random.randint(0, total_days)
        return start_date + timedelta(days=random_days)

