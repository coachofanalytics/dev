"""
Management Command: Fetch High-Probability Positions

Fetches positions from OptionPlay/Thinkorswim and saves to SuggestedPosition model.

Usage:
    python manage.py fetch_positions
    python manage.py fetch_positions --source optionplay
    python manage.py fetch_positions --source thinkorswim
    python manage.py fetch_positions --probability 75 --premium 150 --dte-min 40
"""

from django.core.management.base import BaseCommand
from decimal import Decimal
from investing.services import PositionFetcherService


class Command(BaseCommand):
    help = 'Fetch high-probability positions from OptionPlay/Thinkorswim APIs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--source',
            type=str,
            choices=['auto', 'optionplay', 'thinkorswim', 'mock'],
            default='auto',
            help='API source (auto = try OptionPlay, fallback to Thinkorswim)'
        )
        parser.add_argument(
            '--probability',
            type=int,
            default=70,
            help='Minimum probability of profit % (default: 70)'
        )
        parser.add_argument(
            '--premium',
            type=int,
            default=100,
            help='Minimum premium in dollars (default: 100)'
        )
        parser.add_argument(
            '--dte-min',
            type=int,
            default=30,
            help='Minimum days to expiration (default: 30)'
        )
        parser.add_argument(
            '--dte-max',
            type=int,
            default=60,
            help='Maximum days to expiration (default: 60)'
        )
        parser.add_argument(
            '--max-positions',
            type=int,
            default=5,
            help='Maximum positions to fetch (default: 5)'
        )
        parser.add_argument(
            '--symbols',
            type=str,
            default='',
            help='Comma-separated symbols (e.g., SPY,QQQ,AAPL) - default: all high-liquidity'
        )
    
    def handle(self, *args, **options):
        self.stdout.write("="*70)
        self.stdout.write(self.style.SUCCESS("🤖 AUTOMATED POSITION FETCHER"))
        self.stdout.write("="*70)
        
        # Parse filters from command arguments
        filters = {
            'probability_min': options['probability'],
            'premium_min': options['premium'],
            'dte_min': options['dte_min'],
            'dte_max': options['dte_max'],
            'strategies': [
                'bull_put_spread',
                'bear_call_spread',
                'bull_call_spread',
                'bear_put_spread'
            ],
            'max_positions': options['max_positions']
        }
        
        # Parse symbols
        if options['symbols']:
            filters['symbols'] = [s.strip().upper() for s in options['symbols'].split(',')]
        
        # Display configuration
        self.stdout.write("\n📋 Fetch Configuration:")
        self.stdout.write(f"   Source: {options['source']}")
        self.stdout.write(f"   Minimum Probability: {filters['probability_min']}%")
        self.stdout.write(f"   Minimum Premium: ${filters['premium_min']}")
        self.stdout.write(f"   DTE Range: {filters['dte_min']}-{filters['dte_max']} days")
        self.stdout.write(f"   Strategies: {', '.join(filters['strategies'])}")
        self.stdout.write(f"   Max Positions: {filters['max_positions']}")
        if 'symbols' in filters:
            self.stdout.write(f"   Symbols: {', '.join(filters['symbols'])}")
        self.stdout.write("")
        
        # Initialize fetcher service
        fetcher = PositionFetcherService()
        
        # Fetch positions based on source
        try:
            if options['source'] == 'mock':
                self.stdout.write(self.style.WARNING("🎭 Using MOCK data (for testing)..."))
                positions = fetcher._get_mock_positions(filters)
                suggested = fetcher._save_suggested_positions(positions, source='manual')
            
            elif options['source'] == 'optionplay':
                self.stdout.write("🔄 Fetching from OptionPlay API...")
                positions = fetcher._fetch_from_optionplay(filters)
                suggested = fetcher._save_suggested_positions(positions, source='optionplay')
            
            elif options['source'] == 'thinkorswim':
                self.stdout.write("🔄 Fetching from Thinkorswim/TD Ameritrade...")
                positions = fetcher._fetch_from_thinkorswim(filters)
                suggested = fetcher._save_suggested_positions(positions, source='thinkorswim')
            
            else:  # auto
                self.stdout.write("🔄 Auto-fetching (OptionPlay → Thinkorswim fallback)...")
                suggested = fetcher.fetch_high_probability_positions(filters)
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Fetch failed: {e}"))
            import traceback
            traceback.print_exc()
            return
        
        # Display results
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS(f"✅ SUCCESS: Fetched {len(suggested)} positions"))
        self.stdout.write("="*70)
        
        if suggested:
            self.stdout.write("\n📊 Fetched Positions:")
            for i, pos in enumerate(suggested, 1):
                self.stdout.write(
                    f"\n{i}. {pos.symbol} - {pos.get_strategy_display()} "
                    f"({pos.probability_of_profit}% prob)"
                )
                self.stdout.write(f"   Premium: ${pos.premium_collected} | DTE: {pos.dte} days")
                self.stdout.write(f"   Max Profit: ${pos.max_profit} | Max Loss: ${pos.max_loss}")
                self.stdout.write(f"   Source: {pos.get_source_display()}")
                self.stdout.write(f"   Meets Criteria: {'✅ YES' if pos.meets_criteria else '❌ NO'}")
        
        # Next steps
        self.stdout.write("\n" + "="*70)
        self.stdout.write("📝 Next Steps:")
        self.stdout.write("   1. Review positions in Django Admin:")
        self.stdout.write("      → /admin/investing/suggestedposition/")
        self.stdout.write("   2. Or use staff review interface:")
        self.stdout.write("      → /investing/managed/staff/suggestions/")
        self.stdout.write("   3. Approve/edit positions, then create batch for client")
        self.stdout.write("="*70)

