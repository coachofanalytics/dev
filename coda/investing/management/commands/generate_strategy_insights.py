from django.core.management.base import BaseCommand
from django.utils import timezone

from ...services.strategy_insights_service import StrategyInsightsService


class Command(BaseCommand):
    help = "Generate OptionPlay vs Unusual Whales overlap and rotation insights."

    def add_arguments(self, parser):
        parser.add_argument(
            '--lookback',
            type=int,
            default=7,
            help='Lookback window in days (default: 7)',
        )

    def handle(self, *args, **options):
        lookback = options['lookback']
        service = StrategyInsightsService(lookback_days=lookback, as_of=timezone.now())
        report = service.build_report()

        overlap = report['overlap']
        rotation = report['rotation']
        outcomes = report['outcomes']
        streaks = report['streaks']

        self.stdout.write(self.style.MIGRATE_HEADING("Strategy Insights Report"))
        self.stdout.write(f"Window: {report['window_start']:%Y-%m-%d} → {report['generated_at']:%Y-%m-%d} ({lookback} days)")
        self.stdout.write("")

        self.stdout.write(self.style.HTTP_INFO("Overlap Summary"))
        self.stdout.write(f"  OptionPlay ideas: {overlap.optionplay_total}")
        self.stdout.write(f"  Unusual Whales ideas: {overlap.whales_total}")
        self.stdout.write(f"  Overlapping symbol/strategy/DTE combos: {overlap.overlap_count}")
        self.stdout.write(f"  Overlap ratio (OptionPlay confirmed by UW): {overlap.overlap_ratio}")
        if overlap.primary_symbols:
            self.stdout.write("  Top overlap symbols:")
            for symbol, count in overlap.primary_symbols:
                self.stdout.write(f"    • {symbol}: {count}")
        else:
            self.stdout.write("  Top overlap symbols: none recorded in window")
        self.stdout.write("")

        self.stdout.write(self.style.HTTP_INFO("Rotation Mix"))
        for bucket, count in rotation.mix.items():
            ratio = rotation.mix_ratio.get(bucket, 0)
            variance = rotation.suggested_target_variance.get(bucket, 0)
            self.stdout.write(f"  {bucket.replace('_', ' ').title()}: {count} ({ratio}) | variance vs target: {variance}")
        if rotation.top_symbols:
            self.stdout.write("  Most frequent pending symbols:")
            for symbol, count in rotation.top_symbols[:5]:
                self.stdout.write(f"    • {symbol}: {count}")
        self.stdout.write("")

        self.stdout.write(self.style.HTTP_INFO("Outcome Snapshot"))
        self.stdout.write(f"  Evaluated outcomes: {outcomes.total}")
        if outcomes.win_rate is not None:
            self.stdout.write(f"  Win rate: {outcomes.win_rate} | Loss rate: {outcomes.loss_rate} | Breakeven: {outcomes.breakeven_rate}")
        else:
            self.stdout.write("  No outcomes recorded in this window.")
        for bucket, data in outcomes.by_bucket.items():
            self.stdout.write(
                f"    - {bucket.replace('_', ' ').title()}: {data['count']} | wins {data['win_rate']} | losses {data['loss_rate']} | breakeven {data['breakeven_rate']}"
            )
        self.stdout.write("")

        self.stdout.write(self.style.HTTP_INFO("Consistency Streaks"))
        if streaks.average_streak:
            self.stdout.write(f"  Average streak: {streaks.average_streak} | Max streak: {streaks.max_streak}")
        else:
            self.stdout.write("  No repeated suggestions detected in window.")
        if streaks.repeating_symbols:
            self.stdout.write("  Symbols with repeat appearances:")
            for symbol, count in streaks.repeating_symbols[:5]:
                self.stdout.write(f"    • {symbol}: {count}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("Done. Insights generated without persisting new records."))





