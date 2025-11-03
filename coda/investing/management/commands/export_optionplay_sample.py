"""
Export sample of OptionPlay raw data for analysis
"""
import csv
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from investing.models import OptionPlayRawData


class Command(BaseCommand):
    help = 'Export sample OptionPlay data to CSV for quality filter analysis'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Number of records to export (default: 50)'
        )
        parser.add_argument(
            '--output',
            type=str,
            default='sample_optionplay_data.csv',
            help='Output filename (default: sample_optionplay_data.csv)'
        )
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Only export active positions (not expired)'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        output_file = options['output']
        active_only = options['active_only']
        
        self.stdout.write("=" * 80)
        self.stdout.write(f"📊 Exporting OptionPlay Sample Data")
        self.stdout.write("=" * 80)
        
        # Build queryset
        queryset = OptionPlayRawData.objects.all().order_by('-created_at')
        
        if active_only:
            today = timezone.now().date()
            queryset = queryset.filter(expiry__gte=today)
            self.stdout.write(f"✅ Filter: Active positions only (expiry >= {today})")
        
        total_count = queryset.count()
        records = queryset[:limit]
        
        self.stdout.write(f"📊 Total in database: {total_count}")
        self.stdout.write(f"📤 Exporting: {min(limit, total_count)} records")
        
        # Export to CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'id',
                'symbol',
                'price',
                'sell_strike',
                'buy_strike',
                'premium',
                'expiry',
                'dte',
                'iv_rank',
                'annual_return',
                'distance_to_strike',
                'width',
                'prem_width',
                'earnings_flag',
                'strategy_type',
                'created_at',
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for record in records:
                writer.writerow({
                    'id': record.id,
                    'symbol': record.symbol,
                    'price': record.price,
                    'sell_strike': record.sell_strike,
                    'buy_strike': record.buy_strike,
                    'premium': record.premium,
                    'expiry': record.expiry,
                    'dte': record.dte,
                    'iv_rank': record.iv_rank,
                    'annual_return': record.annual_return,
                    'distance_to_strike': record.distance_to_strike,
                    'width': record.width,
                    'prem_width': record.prem_width,
                    'earnings_flag': record.earnings_flag,
                    'strategy_type': record.strategy_type or 'unknown',
                    'created_at': record.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                })
        
        self.stdout.write("=" * 80)
        self.stdout.write(f"✅ Export complete: {output_file}")
        self.stdout.write("=" * 80)
        
        # Calculate statistics
        self.stdout.write("\n📊 DATA QUALITY STATISTICS:")
        self.stdout.write("-" * 80)
        
        if records:
            premiums = [r.premium for r in records if r.premium]
            iv_ranks = [r.iv_rank for r in records if r.iv_rank is not None]
            dtes = [r.dte for r in records if r.dte is not None]
            
            if premiums:
                avg_premium = sum(premiums) / len(premiums)
                min_premium = min(premiums)
                max_premium = max(premiums)
                self.stdout.write(f"💰 Premium: ${avg_premium:.2f} avg (${min_premium:.2f} - ${max_premium:.2f})")
            
            if iv_ranks:
                avg_iv = sum(iv_ranks) / len(iv_ranks)
                min_iv = min(iv_ranks)
                max_iv = max(iv_ranks)
                self.stdout.write(f"📊 IV Rank: {avg_iv:.1f}% avg ({min_iv:.1f}% - {max_iv:.1f}%)")
            
            if dtes:
                avg_dte = sum(dtes) / len(dtes)
                min_dte = min(dtes)
                max_dte = max(dtes)
                self.stdout.write(f"📅 DTE: {avg_dte:.0f} days avg ({min_dte} - {max_dte})")
        
        self.stdout.write("-" * 80)
        self.stdout.write(f"\n💡 Use this data to set realistic quality filters!")
        self.stdout.write(f"   Example: If avg IV Rank is 5%, don't filter at 40%\n")

