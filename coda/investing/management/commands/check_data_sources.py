"""
Check Data Sources - Debug position data availability

Usage:
    python manage.py check_data_sources

Purpose:
- Check if OptionPlayRawData exists
- Check if SuggestedPositions exist
- Debug why mock data is being used

Author: CODA Development Team
Created: November 2, 2025
"""

from django.core.management.base import BaseCommand
from investing.models import OptionPlayRawData, SuggestedPosition


class Command(BaseCommand):
    help = 'Check data sources availability'
    
    def handle(self, *args, **options):
        self.stdout.write("=" * 70)
        self.stdout.write(self.style.SUCCESS("🔍 DATA SOURCES CHECK"))
        self.stdout.write("=" * 70)
        
        # Check OptionPlayRawData
        raw_total = OptionPlayRawData.objects.count()
        raw_unprocessed = OptionPlayRawData.objects.filter(is_processed=False).count()
        raw_processed = OptionPlayRawData.objects.filter(is_processed=True).count()
        
        self.stdout.write(f"\n📊 OPTIONPLAY RAW DATA:")
        self.stdout.write(f"  Total Entries: {raw_total}")
        self.stdout.write(f"  Unprocessed: {raw_unprocessed}")
        self.stdout.write(f"  Processed: {raw_processed}")
        
        if raw_total == 0:
            self.stdout.write(self.style.WARNING("\n  ⚠️  NO RAW DATA FOUND!"))
            self.stdout.write("\n  To upload CSV data:")
            self.stdout.write("  1. Download CSV from OptionPlay.com")
            self.stdout.write("  2. Run: python manage.py import_optionplay_csv short_puts file.csv")
            self.stdout.write("  3. Or upload via Django admin\n")
        else:
            # Show sample
            samples = OptionPlayRawData.objects.filter(is_processed=False)[:5]
            if samples:
                self.stdout.write(f"\n  Sample Unprocessed:")
                for s in samples:
                    self.stdout.write(f"    • {s.symbol}: ${s.premium}, IV={s.iv_rank}%, DTE={s.days_to_expiry}")
        
        # Check SuggestedPositions
        sugg_total = SuggestedPosition.objects.count()
        sugg_scored = SuggestedPosition.objects.filter(ai_score__isnull=False).count()
        sugg_pending = SuggestedPosition.objects.filter(review_status='pending').count()
        
        self.stdout.write(f"\n📋 SUGGESTED POSITIONS:")
        self.stdout.write(f"  Total Positions: {sugg_total}")
        self.stdout.write(f"  AI Scored: {sugg_scored}")
        self.stdout.write(f"  Pending Review: {sugg_pending}")
        
        if sugg_total == 0:
            self.stdout.write(self.style.WARNING("\n  ⚠️  NO SUGGESTED POSITIONS!"))
            self.stdout.write("\n  To create positions:")
            self.stdout.write("  1. Upload OptionPlay CSV (see above)")
            self.stdout.write("  2. Run: python manage.py import_optionplay_csv short_puts file.csv --convert")
            self.stdout.write("  3. Or fetch from API (when available)\n")
        else:
            # Show top scored
            top_5 = SuggestedPosition.objects.filter(ai_score__isnull=False).order_by('-ai_score')[:5]
            if top_5:
                self.stdout.write(f"\n  Top 5 Scored:")
                for i, s in enumerate(top_5, 1):
                    self.stdout.write(f"    {i}. {s.symbol}: {s.ai_score}/100 ({s.ai_rating})")
        
        self.stdout.write("\n" + "=" * 70)
        
        # Diagnosis
        if raw_total == 0 and sugg_total == 0:
            self.stdout.write(self.style.ERROR("❌ NO DATA FOUND - System will use mock data"))
            self.stdout.write("\n📝 RECOMMENDED ACTIONS:")
            self.stdout.write("  1. Upload OptionPlay CSV via Django admin")
            self.stdout.write("  2. Go to: /admin/investing/optionplayrawdata/")
            self.stdout.write("  3. Click 'Import CSV' (if available)")
            self.stdout.write("  4. Or use management command:")
            self.stdout.write("     python manage.py import_optionplay_csv short_puts yourfile.csv --convert")
        elif raw_total > 0 and sugg_total == 0:
            self.stdout.write(self.style.WARNING("⚠️  Raw data exists but not converted"))
            self.stdout.write("\n📝 TO CONVERT:")
            self.stdout.write(f"  python manage.py import_optionplay_csv short_puts dummy.csv --convert --max-positions 20")
        elif sugg_total > 0:
            self.stdout.write(self.style.SUCCESS("✅ DATA READY - AI scoring active!"))
            self.stdout.write("\n📝 VIEW IN UI:")
            self.stdout.write("  https://codamakutano.herokuapp.com/investing/managed/staff/suggestions/")
        
        self.stdout.write("\n" + "=" * 70)

