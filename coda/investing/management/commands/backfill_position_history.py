"""
Backfill Position History
Populate OptionsPositionHistory for existing closed positions

Purpose:
- Import historical trades for ML training
- One-time migration of past data
- Build initial ML dataset

Usage:
    # Backfill all closed positions
    python manage.py backfill_position_history
    
    # Backfill specific account
    python manage.py backfill_position_history --account-id 71
    
    # Dry run (preview only)
    python manage.py backfill_position_history --dry-run

When to Use:
- After deploying OptionsPositionHistory model
- When importing old trading data
- To rebuild ML training dataset

Author: CODA Development Team
Created: November 2, 2025
Part of: AI Position Scoring System (Week 1)
"""

from django.core.management.base import BaseCommand
from django.db.models import Q
from investing.models import OptionsPosition, OptionsPositionHistory
from investing.services.position_history_collector import PositionHistoryCollector


class Command(BaseCommand):
    help = 'Backfill OptionsPositionHistory for closed positions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--account-id',
            type=int,
            help='Backfill only for specific account ID'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be backfilled (no changes)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-create history even if exists (destructive!)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('📊 Position History Backfill'))
        self.stdout.write('=' * 60)
        
        # Build queryset
        queryset = OptionsPosition.objects.filter(status='closed')
        
        # Filter by account if specified
        if options['account_id']:
            queryset = queryset.filter(account_id=options['account_id'])
            self.stdout.write(f"🎯 Filtering to account ID: {options['account_id']}")
        
        # Exclude positions that already have history (unless --force)
        if not options['force']:
            queryset = queryset.exclude(outcome_history__isnull=False)
        
        total_positions = queryset.count()
        
        if total_positions == 0:
            self.stdout.write(self.style.WARNING('⚠️  No positions to backfill'))
            return
        
        self.stdout.write(f"\n📋 Found {total_positions} closed positions to process\n")
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))
            for position in queryset[:10]:  # Show first 10
                self.stdout.write(
                    f"  • {position.symbol} ({position.strategy}) - "
                    f"P&L: ${position.realized_pnl or 0:.2f}"
                )
            if total_positions > 10:
                self.stdout.write(f"  ... and {total_positions - 10} more")
            return
        
        # Confirm if large batch
        if total_positions > 50 and not options['force']:
            confirm = input(f"\n⚠️  About to backfill {total_positions} positions. Continue? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING('Cancelled'))
                return
        
        # Bulk collect
        collector = PositionHistoryCollector()
        
        self.stdout.write(f"\n🚀 Processing {total_positions} positions...\n")
        
        results = collector.bulk_collect(queryset)
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ BACKFILL COMPLETE'))
        self.stdout.write(f"  • Created: {results['created']}")
        self.stdout.write(f"  • Skipped: {results['skipped']}")
        self.stdout.write(f"  • Errors: {results['errors']}")
        
        if results['created'] > 0:
            # Show statistics
            histories = OptionsPositionHistory.objects.all()
            total = histories.count()
            wins = histories.filter(was_profitable=True).count()
            losses = total - wins
            win_rate = (wins / total * 100) if total > 0 else 0
            
            self.stdout.write('\n📊 CURRENT DATASET STATS:')
            self.stdout.write(f"  • Total Trades: {total}")
            self.stdout.write(f"  • Wins: {wins} ({win_rate:.1f}%)")
            self.stdout.write(f"  • Losses: {losses}")
            
            # Top performing symbols
            from django.db.models import Count, Avg
            top_symbols = (
                histories.values('position__symbol')
                .annotate(
                    count=Count('id'),
                    win_rate=Avg('was_profitable'),
                    avg_return=Avg('actual_return_percentage')
                )
                .filter(count__gte=2)  # At least 2 trades
                .order_by('-win_rate')[:5]
            )
            
            if top_symbols:
                self.stdout.write('\n🏆 TOP PERFORMING SYMBOLS:')
                for sym in top_symbols:
                    symbol = sym['position__symbol']
                    wr = sym['win_rate'] * 100
                    avg_ret = sym['avg_return']
                    count = sym['count']
                    self.stdout.write(
                        f"  • {symbol}: {wr:.0f}% win rate, "
                        f"{avg_ret:.1f}% avg return ({count} trades)"
                    )
        
        self.stdout.write('\n' + '=' * 60)

