import os
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import django
from django.test import SimpleTestCase

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from coda.investing.services.capital_allocation_service import CapitalAllocationService


def make_suggestion(**overrides):
    default = {
        'id': overrides.get('id', 1),
        'symbol': overrides.get('symbol', 'AAPL'),
        'strategy': overrides.get('strategy', 'covered_call'),
        'strategy_display': overrides.get('strategy_display', 'Covered Call'),
        'probability_of_profit': overrides.get('probability_of_profit', Decimal('80')),
        'ai_score': overrides.get('ai_score', Decimal('78')),
        'premium_collected': overrides.get('premium_collected', Decimal('320')),
        'capital_required': overrides.get('capital_required', Decimal('2500')),
        'max_profit': overrides.get('max_profit', Decimal('320')),
        'max_loss': overrides.get('max_loss', Decimal('2500')),
        'dte': overrides.get('dte', 35),
        'notes': overrides.get('notes', ''),
        'positions': overrides.get('positions', []),
        'api_response_data': overrides.get('api_response_data', {}),
    }

    class DummySuggestion(SimpleNamespace):
        def get_strategy_display(self_inner):
            return self_inner.strategy_display

    return DummySuggestion(**default)


class CapitalAllocationServiceTests(SimpleTestCase):
    @patch('coda.investing.services.capital_allocation_service.UnusualWhalesService')
    def test_recommend_allocations_hits_target(self, mock_whales):
        mock_service = mock_whales.return_value
        mock_service.is_enabled.return_value = True
        mock_service.get_flow_summary_for_symbols.return_value = {
            'AAPL': {
                'flow_score': 82,
                'sentiment': 'bullish',
                'sentiment_score': 72,
                'unusual_calls': 10,
                'unusual_puts': 0,
                'premium_spent': 750000,
                'volume_oi_ratio': 0.5,
                'timing_signal': '🟢 ENTER NOW (Heavy buying flow detected!)',
            },
            'MSFT': {
                'flow_score': 78,
                'sentiment': 'bullish',
                'sentiment_score': 68,
                'unusual_calls': 6,
                'unusual_puts': 0,
                'premium_spent': 520000,
                'volume_oi_ratio': 0.42,
                'timing_signal': '🟢 ENTER NOW (Heavy buying flow detected!)',
            },
        }

        suggestions = [
            make_suggestion(id=1, symbol='AAPL', premium_collected=Decimal('260'), capital_required=Decimal('2400')),
            make_suggestion(id=2, symbol='MSFT', premium_collected=Decimal('210'), capital_required=Decimal('2300'), strategy='bull_put_spread', strategy_display='Bull Put Spread'),
        ]

        service = CapitalAllocationService()
        summary = service.recommend_allocations(suggestions)

        self.assertTrue(summary['meets_target'])
        self.assertEqual(len(summary['allocations']), 2)
        totals = summary['totals']
        self.assertGreaterEqual(totals['coverage_pct'], Decimal('100'))
        for allocation in summary['allocations']:
            self.assertLessEqual(allocation['capital_used'], Decimal('3000'))

    @patch('coda.investing.services.capital_allocation_service.UnusualWhalesService')
    def test_recommend_allocations_filters_low_flow(self, mock_whales):
        mock_service = mock_whales.return_value
        mock_service.is_enabled.return_value = True
        mock_service.get_flow_summary_for_symbols.return_value = {
            'TSLA': {
                'flow_score': 20,
                'sentiment': 'bearish',
                'sentiment_score': 22,
                'unusual_calls': 1,
                'unusual_puts': 8,
                'premium_spent': -120000,
                'volume_oi_ratio': 0.05,
                'timing_signal': '🔴 WAIT/SKIP (Heavy selling flow detected!)',
            }
        }

        suggestion = make_suggestion(
            id=3,
            symbol='TSLA',
            premium_collected=Decimal('300'),
            capital_required=Decimal('2500'),
            probability_of_profit=Decimal('75'),
        )

        service = CapitalAllocationService()
        summary = service.recommend_allocations([suggestion])

        self.assertFalse(summary['allocations'])
        self.assertIn('No allocations met probability/flow thresholds.', summary['notes'])

