"""
Management Command: Import OptionPlay CSV Data

Imports CSV files exported from OptionPlay.com into OptionPlayRawData table
Supports: Credit Spreads, Short Puts, Covered Calls

Usage:
    python manage.py import_optionplay_csv credit_spreads path/to/credit_spread.csv
    python manage.py import_optionplay_csv short_puts path/to/shortput.csv
    python manage.py import_optionplay_csv covered_calls path/to/covered_calls.csv
    
    # Auto-convert to suggestions after import
    python manage.py import_optionplay_csv short_puts shortput.csv --convert
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
import csv
from datetime import datetime
import os

from investing.models import OptionPlayRawData, SuggestedPosition
from investing.services.optionplay_converter import OptionPlayConverterService

User = get_user_model()


class Command(BaseCommand):
    help = 'Import OptionPlay CSV data into database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'strategy_type',
            type=str,
            choices=['credit_spreads', 'short_puts', 'covered_calls'],
            help='Type of CSV file to import'
        )
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to CSV file'
        )
        parser.add_argument(
            '--convert',
            action='store_true',
            help='Automatically convert to SuggestedPositions after import'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            default=1,
            help='ID of user who uploaded (default: 1)'
        )
        parser.add_argument(
            '--min-premium',
            type=float,
            default=1.0,
            help='Minimum premium to convert (default: $1.00)'
        )
        parser.add_argument(
            '--min-iv',
            type=float,
            default=20.0,
            help='Minimum IV rank to convert (default: 20%%)'
        )
        parser.add_argument(
            '--symbols',
            type=str,
            help='Comma-separated list of symbols to convert (e.g., AAPL,MSFT,TSLA)'
        )
        parser.add_argument(
            '--max-positions',
            type=int,
            default=10,
            help='Maximum positions to convert (default: 10)'
        )
    
    def handle(self, *args, **options):
        strategy_type = options['strategy_type']
        csv_file = options['csv_file']
        auto_convert = options['convert']
        user_id = options['user_id']
        
        # Validate file exists
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f"❌ File not found: {csv_file}"))
            return
        
        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"⚠️ User {user_id} not found, using None"))
            user = None
        
        self.stdout.write(f"\n📂 Importing {strategy_type} from: {csv_file}")
        self.stdout.write(f"👤 Uploaded by: {user.get_full_name() if user else 'System'}\n")
        
        # Import based on type
        if strategy_type == 'credit_spreads':
            imported, errors = self._import_credit_spreads(csv_file, user)
        elif strategy_type == 'short_puts':
            imported, errors = self._import_short_puts(csv_file, user)
        elif strategy_type == 'covered_calls':
            imported, errors = self._import_covered_calls(csv_file, user)
        
        # Summary
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"\n✅ IMPORT COMPLETE"))
        self.stdout.write(f"   Successfully imported: {len(imported)}")
        self.stdout.write(f"   Errors: {len(errors)}")
        
        if errors:
            self.stdout.write(self.style.WARNING(f"\n⚠️ ERRORS:"))
            for error in errors[:10]:  # Show first 10 errors
                self.stdout.write(f"   - {error}")
        
        # Auto-convert if requested
        if auto_convert and imported:
            self.stdout.write(self.style.SUCCESS(f"\n🔄 Converting to SuggestedPositions with filters..."))
            
            # Build filters from command options
            filters = {
                'min_premium': Decimal(str(options['min_premium'])),
                'min_iv_rank': Decimal(str(options['min_iv'])),
                'max_positions': options['max_positions'],
                'dte_min': 30,  # Default range
                'dte_max': 60,
            }
            
            # Add symbol filter if provided
            if options['symbols']:
                symbols_list = [s.strip().upper() for s in options['symbols'].split(',')]
                filters['symbols'] = symbols_list
                self.stdout.write(f"   📍 Filtering for symbols: {', '.join(symbols_list)}")
            
            self.stdout.write(f"   💵 Min Premium: ${filters['min_premium']}")
            self.stdout.write(f"   📊 Min IV Rank: {filters['min_iv_rank']}%")
            self.stdout.write(f"   🎯 Max Positions: {filters['max_positions']}")
            
            converter = OptionPlayConverterService()
            
            raw_data_ids = [r.id for r in imported]
            raw_data_qs = OptionPlayRawData.objects.filter(id__in=raw_data_ids)
            
            suggestions, conv_errors = converter.bulk_convert(raw_data_qs, filters=filters)
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ Converted {len(suggestions)} positions (from {len(imported)} imported)"))
            self.stdout.write(f"   Filtered out: {len(imported) - len(suggestions) - len(conv_errors)}")
            if conv_errors:
                self.stdout.write(self.style.WARNING(f"   Errors: {len(conv_errors)}"))
        
        self.stdout.write("\n" + "=" * 60 + "\n")
    
    def _import_credit_spreads(self, csv_file, user):
        """
        Import credit spreads CSV
        Format: Symbol,Strategy,Type,Price,Sell Strike,Buy Strike,Expiry,Premium,Width,Prem/Width,IV Rank,Earnings Date
        """
        imported = []
        errors = []
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    # Parse data
                    symbol = row['Symbol'].strip().upper()
                    spread_strategy = row['Strategy'].strip()  # Bearish/Bullish
                    option_type = row['Type'].strip()  # Call/Put
                    stock_price = self._parse_decimal(row['Price'])
                    sell_strike = self._parse_decimal(row['Sell Strike'])
                    buy_strike = self._parse_decimal(row['Buy Strike'])
                    expiry = self._parse_date(row['Expiry'])
                    premium = self._parse_decimal(row['Premium'])
                    width = self._parse_decimal(row['Width'])
                    prem_width = self._parse_decimal(row['Prem/Width'].replace('%', ''))
                    iv_rank = self._parse_decimal(row['IV Rank'].replace('%', ''))
                    earnings_date = row.get('Earnings Date', '').strip()
                    
                    # Calculate DTE
                    dte = (expiry - datetime.now().date()).days
                    
                    # Skip if expired
                    if dte < 0:
                        self.stdout.write(self.style.WARNING(f"⏭️  Row {row_num}: {symbol} expired, skipping"))
                        continue
                    
                    # Create OptionPlayRawData
                    raw_data = OptionPlayRawData.objects.create(
                        strategy_type='credit_spread',
                        symbol=symbol,
                        spread_strategy=spread_strategy,
                        option_type=option_type,
                        stock_price=stock_price,
                        sell_strike=sell_strike,
                        buy_strike=buy_strike,
                        expiry=expiry,
                        days_to_expiry=dte,
                        premium=premium,
                        width=width,
                        prem_width_ratio=prem_width,
                        iv_rank=iv_rank,
                        earnings_date=earnings_date,
                        uploaded_by=user,
                        csv_row_data=dict(row)
                    )
                    
                    imported.append(raw_data)
                    self.stdout.write(self.style.SUCCESS(f"✅ Row {row_num}: {symbol} {spread_strategy} {option_type} Spread"))
                
                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    errors.append(error_msg)
                    self.stdout.write(self.style.ERROR(f"❌ {error_msg}"))
        
        return imported, errors
    
    def _import_short_puts(self, csv_file, user):
        """
        Import short puts CSV
        Format: Symbol,Action,Expiry,Days To Expiry,Strike Price,Mid Price,Stock Price,
                Raw Return,Annualized Return,Distance To Strike,IV Rank,Earnings Date,Earnings Flag
        """
        imported = []
        errors = []
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):
                try:
                    symbol = row['Symbol'].strip().upper()
                    expiry = self._parse_date(row['Expiry'])
                    dte = int(row['Days To Expiry'])
                    strike = self._parse_decimal(row['Strike Price'])
                    premium = self._parse_decimal(row['Mid Price'])
                    stock_price = self._parse_decimal(row['Stock Price'])
                    iv_rank = self._parse_decimal(row.get('Implied Volatility Rank', '0').replace('%', ''))
                    raw_return = self._parse_decimal(row.get('Raw Return', '0').replace('%', ''))
                    annualized_return = self._parse_decimal(row.get('Annualized Return', '0').replace('%', ''))
                    distance_to_strike = self._parse_decimal(row.get('Distance To Strike', '0').replace('%', ''))
                    earnings_date = row.get('Earnings Date', '').strip()
                    earnings_flag = row.get('Earnings Flag', '').strip()
                    
                    # Skip if expired
                    if dte < 0:
                        self.stdout.write(self.style.WARNING(f"⏭️  Row {row_num}: {symbol} expired, skipping"))
                        continue
                    
                    # Create OptionPlayRawData
                    raw_data = OptionPlayRawData.objects.create(
                        strategy_type='short_put',
                        symbol=symbol,
                        stock_price=stock_price,
                        sell_strike=strike,
                        expiry=expiry,
                        days_to_expiry=dte,
                        premium=premium,
                        iv_rank=iv_rank,
                        raw_return=raw_return,
                        annualized_return=annualized_return,
                        distance_to_strike=distance_to_strike,
                        earnings_date=earnings_date,
                        earnings_flag=earnings_flag,
                        uploaded_by=user,
                        csv_row_data=dict(row)
                    )
                    
                    imported.append(raw_data)
                    self.stdout.write(self.style.SUCCESS(f"✅ Row {row_num}: {symbol} Short Put @ ${strike}"))
                
                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    errors.append(error_msg)
                    self.stdout.write(self.style.ERROR(f"❌ {error_msg}"))
        
        return imported, errors
    
    def _import_covered_calls(self, csv_file, user):
        """Import covered calls CSV"""
        # Similar to short puts
        return self._import_short_puts(csv_file, user)  # Same format
    
    def _parse_decimal(self, value_str):
        """Parse string to Decimal, handling $, commas"""
        if not value_str or value_str.strip() == '':
            return Decimal('0')
        cleaned = str(value_str).replace('$', '').replace(',', '').strip()
        return Decimal(cleaned)
    
    def _parse_date(self, date_str):
        """Parse date string to date object"""
        # Format: 08/02/2024 or 07/19/2024
        return datetime.strptime(date_str.strip(), '%m/%d/%Y').date()

