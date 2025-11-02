"""
Management Command: Cleanup Old Position Data

Deletes expired/old data to keep database clean:
1. Processed OptionPlayRawData older than 60 days
2. Expired OptionPlayRawData
3. Rejected SuggestedPositions older than 30 days
4. Old mock positions

Usage:
    python manage.py cleanup_old_positions
    python manage.py cleanup_old_positions --dry-run  # Preview without deleting
    python manage.py cleanup_old_positions --days 90  # Custom retention period
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from investing.models import OptionPlayRawData, SuggestedPosition


class Command(BaseCommand):
    help = 'Cleanup old position data to keep database optimized'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview deletions without actually deleting',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=60,
            help='Retention period for processed data (default: 60 days)',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        retention_days = options['days']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No data will be deleted\n'))
        
        cutoff_date = timezone.now() - timedelta(days=retention_days)
        today = timezone.now().date()
        
        total_deleted = 0
        
        # ====================================================================
        # 1. Delete Processed OptionPlayRawData older than retention period
        # ====================================================================
        self.stdout.write(self.style.SUCCESS(f"\n📋 Cleanup Plan (Retention: {retention_days} days):\n"))
        
        old_processed = OptionPlayRawData.objects.filter(
            is_processed=True,
            processed_date__lt=cutoff_date
        )
        count_old_processed = old_processed.count()
        
        if count_old_processed > 0:
            self.stdout.write(f"1️⃣  Processed OptionPlay data older than {retention_days} days: {count_old_processed} records")
            if not dry_run:
                old_processed.delete()
                total_deleted += count_old_processed
        else:
            self.stdout.write(f"1️⃣  No old processed data found")
        
        # ====================================================================
        # 2. Delete Expired OptionPlayRawData (regardless of processing)
        # ====================================================================
        expired_raw = OptionPlayRawData.objects.filter(
            expiry__lt=today - timedelta(days=7)  # Keep for 7 days after expiry
        )
        count_expired = expired_raw.count()
        
        if count_expired > 0:
            self.stdout.write(f"2️⃣  Expired OptionPlay data (>7 days old): {count_expired} records")
            if not dry_run:
                expired_raw.delete()
                total_deleted += count_expired
        else:
            self.stdout.write(f"2️⃣  No expired data found")
        
        # ====================================================================
        # 3. Delete Rejected SuggestedPositions older than 30 days
        # ====================================================================
        old_rejected = SuggestedPosition.objects.filter(
            review_status='rejected',
            reviewed_at__lt=timezone.now() - timedelta(days=30)
        )
        count_rejected = old_rejected.count()
        
        if count_rejected > 0:
            self.stdout.write(f"3️⃣  Rejected suggestions older than 30 days: {count_rejected} records")
            if not dry_run:
                old_rejected.delete()
                total_deleted += count_rejected
        else:
            self.stdout.write(f"3️⃣  No old rejected suggestions")
        
        # ====================================================================
        # 4. Delete Converted SuggestedPositions (already used in batches)
        # ====================================================================
        old_converted = SuggestedPosition.objects.filter(
            review_status='converted',
            reviewed_at__lt=cutoff_date,
            created_position__isnull=False  # Has linked position
        )
        count_converted = old_converted.count()
        
        if count_converted > 0:
            self.stdout.write(f"4️⃣  Converted suggestions older than {retention_days} days: {count_converted} records")
            if not dry_run:
                old_converted.delete()
                total_deleted += count_converted
        else:
            self.stdout.write(f"4️⃣  No old converted suggestions")
        
        # ====================================================================
        # 5. Delete Expired SuggestedPositions (never reviewed)
        # ====================================================================
        expired_suggestions = SuggestedPosition.objects.filter(
            review_status='pending',
            expiration_date__lt=today - timedelta(days=7)
        )
        count_expired_sugg = expired_suggestions.count()
        
        if count_expired_sugg > 0:
            self.stdout.write(f"5️⃣  Expired pending suggestions: {count_expired_sugg} records")
            if not dry_run:
                expired_suggestions.delete()
                total_deleted += count_expired_sugg
        else:
            self.stdout.write(f"5️⃣  No expired pending suggestions")
        
        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"\n📊 CLEANUP SUMMARY:"))
        self.stdout.write(f"   Total records to delete: {total_deleted}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"\n⚠️  DRY RUN - No deletions performed. Run without --dry-run to execute."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"\n✅ Cleanup complete! Deleted {total_deleted} old records."
            ))
        
        # Recommendations
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("\n💡 Recommendations:"))
        self.stdout.write("   • Run this command weekly to keep database clean")
        self.stdout.write("   • Use --dry-run first to preview deletions")
        self.stdout.write("   • Adjust --days parameter based on your needs")
        self.stdout.write("   • Consider setting up a weekly cron job\n")

