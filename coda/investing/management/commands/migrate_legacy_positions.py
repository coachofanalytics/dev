"""
Management command to migrate legacy ShortPut and covered_calls models to OptionsPosition
This is a ONE-TIME migration - will be deleted after successful execution
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
import re


class Command(BaseCommand):
    help = 'Migrate legacy ShortPut and covered_calls data to OptionsPosition model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually migrating',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No data will be changed\n'))
        
        # Import here to avoid circular imports
        from investing.models import ShortPut, covered_calls, OptionsPosition, ManagedTradingAccount
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        
        # Stats
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        # Get or create a system user for migration
        try:
            system_user = User.objects.filter(is_staff=True).first()
            if not system_user:
                self.stdout.write(self.style.ERROR('❌ No staff user found for migration'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error getting system user: {e}'))
            return
        
        # Get default trading account
        try:
            default_account = ManagedTradingAccount.objects.first()
        except Exception:
            default_account = None
        
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('📦 LEGACY POSITION MIGRATION'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        
        # ============================================================
        # PART 1: Migrate ShortPut (2 records)
        # ============================================================
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('📊 PART 1: Migrating ShortPut positions')
        self.stdout.write('=' * 80 + '\n')
        
        shortputs = ShortPut.objects.all()
        self.stdout.write(f'Found {shortputs.count()} ShortPut records\n')
        
        for sp in shortputs:
            try:
                # Parse data
                symbol = sp.symbol or 'UNKNOWN'
                stock_price = self._parse_decimal(sp.stock_price)
                annualized_return = self._parse_decimal(sp.annualized_return)
                
                # Create migration data
                migration_data = {
                    'user': system_user,
                    'symbol': symbol,
                    'strategy': 'short_put',
                    'status': 'closed',  # Historical position
                    'quantity': 1,  # Default
                    'underlying_price': stock_price or Decimal('0.00'),
                    'notes': f'Migrated from legacy ShortPut model (ID: {sp.id})',
                    'is_paper_trade': False,
                }
                
                if default_account:
                    migration_data['account'] = default_account
                
                if dry_run:
                    self.stdout.write(f'  Would migrate: {symbol} (ShortPut ID: {sp.id})')
                    self.stdout.write(f'    → Strategy: short_put, Status: closed')
                else:
                    with transaction.atomic():
                        OptionsPosition.objects.create(**migration_data)
                        self.stdout.write(self.style.SUCCESS(f'  ✅ Migrated: {symbol} (ShortPut ID: {sp.id})'))
                
                migrated_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Error migrating ShortPut ID {sp.id}: {e}'))
                error_count += 1
        
        # ============================================================
        # PART 2: Migrate covered_calls (33 records)
        # ============================================================
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('📊 PART 2: Migrating covered_calls positions')
        self.stdout.write('=' * 80 + '\n')
        
        calls = covered_calls.objects.all()
        self.stdout.write(f'Found {calls.count()} covered_calls records\n')
        
        for cc in calls:
            try:
                # Parse data
                symbol = cc.symbol or 'UNKNOWN'
                strike_price = self._parse_price_string(cc.strike_price)
                stock_price = Decimal(str(cc.stock_price)) if cc.stock_price else Decimal('0.00')
                mid_price = self._parse_price_string(cc.mid_price)
                bid_price = self._parse_price_string(cc.bid_price)
                ask_price = self._parse_price_string(cc.ask_price)
                dte = cc.days_to_expiry if cc.days_to_expiry else 0
                expiry = cc.expiry
                
                # Determine if expired
                is_expired = expiry and expiry < datetime.now(timezone.utc)
                status = 'expired' if is_expired else 'closed'
                
                # Create migration data
                migration_data = {
                    'user': system_user,
                    'symbol': symbol,
                    'strategy': 'covered_call',
                    'status': status,
                    'quantity': 1,  # Default
                    'underlying_price': stock_price,
                    'strike_price': strike_price or Decimal('0.00'),
                    'premium': mid_price or Decimal('0.00'),
                    'days_to_expiration': dte,
                    'expiration_date': expiry,
                    'notes': f'Migrated from legacy covered_calls model (ID: {cc.id}). Original data: DTE={dte}, IV Rank={cc.implied_volatility_rank}',
                    'is_paper_trade': False,
                }
                
                if default_account:
                    migration_data['account'] = default_account
                
                if dry_run:
                    self.stdout.write(f'  Would migrate: {symbol} ${strike_price} (covered_calls ID: {cc.id})')
                    self.stdout.write(f'    → Strategy: covered_call, Status: {status}, DTE: {dte}')
                else:
                    with transaction.atomic():
                        OptionsPosition.objects.create(**migration_data)
                        self.stdout.write(self.style.SUCCESS(
                            f'  ✅ Migrated: {symbol} ${strike_price} call, DTE:{dte} (covered_calls ID: {cc.id})'
                        ))
                
                migrated_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ❌ Error migrating covered_calls ID {cc.id}: {e}'))
                error_count += 1
        
        # ============================================================
        # SUMMARY
        # ============================================================
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('📊 MIGRATION SUMMARY')
        self.stdout.write('=' * 80)
        self.stdout.write(f'✅ Successfully migrated: {migrated_count} positions')
        self.stdout.write(f'⏭️  Skipped: {skipped_count} positions')
        self.stdout.write(f'❌ Errors: {error_count} positions')
        self.stdout.write('=' * 80)
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 This was a DRY RUN - no data was changed'))
            self.stdout.write(self.style.WARNING('Run without --dry-run to actually migrate the data'))
        else:
            self.stdout.write(self.style.SUCCESS('\n🎉 Migration complete!'))
            self.stdout.write(self.style.SUCCESS('\nNext steps:'))
            self.stdout.write('  1. Verify migrated data in OptionsPosition model')
            self.stdout.write('  2. If everything looks good, delete legacy models from models.py')
            self.stdout.write('  3. Create new migration to drop legacy tables')
            self.stdout.write('  4. Run: python manage.py makemigrations')
            self.stdout.write('  5. Run: python manage.py migrate')
    
    def _parse_decimal(self, value):
        """Parse various formats to Decimal"""
        if not value:
            return None
        
        try:
            # Remove any non-numeric characters except decimal point and minus
            cleaned = re.sub(r'[^\d.-]', '', str(value))
            return Decimal(cleaned) if cleaned else None
        except (InvalidOperation, ValueError):
            return None
    
    def _parse_price_string(self, value):
        """Parse price strings like '$1,440.00' to Decimal"""
        if not value:
            return None
        
        try:
            # Remove $, commas, spaces
            cleaned = str(value).replace('$', '').replace(',', '').strip()
            return Decimal(cleaned) if cleaned else None
        except (InvalidOperation, ValueError):
            return None

