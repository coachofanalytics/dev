from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace
import unittest

from coda.investing.utils import build_preview_payloads


class StaffDashboardPreviewTests(unittest.TestCase):
    def test_build_preview_payloads_includes_leg_details(self):
        suggestion = SimpleNamespace(
            id=1,
            symbol='AAPL',
            strategy='covered_call',
            probability_of_profit=Decimal('75'),
            ai_score=Decimal('78'),
            premium_collected=Decimal('240'),
            capital_required=Decimal('2500'),
            max_profit=Decimal('240'),
            max_loss=Decimal('2500'),
            dte=45,
            notes='Preview leg inspection',
            positions=[
                {
                    'type': 'call',
                    'direction': 'short',
                    'contracts': 1,
                    'strike': 150,
                    'expiration': (date.today() + timedelta(days=45)).isoformat(),
                    'premium': 2.40,
                    'delta': 0.25,
                    'theta': -0.05,
                }
            ],
            api_response_data={
                'unusual_whales': {
                    'flow_score': 82,
                    'timing_signal': '🟢 ENTER NOW (Heavy buying flow detected!)',
                    'sentiment': 'bullish',
                    'sentiment_score': 70,
                }
            },
        )

        suggestion.get_strategy_display = lambda: 'Covered Call'

        payloads = build_preview_payloads([suggestion], [])
        self.assertEqual(len(payloads), 1)
        payload = payloads[suggestion.id]

        self.assertEqual(payload['symbol'], 'AAPL')
        self.assertEqual(payload['strategy'], 'Covered Call')
        self.assertEqual(payload['timing_signal'], '🟢 ENTER NOW (Heavy buying flow detected!)')
        self.assertEqual(payload['flow_score'], 82)
        self.assertEqual(len(payload['legs']), 1)
        leg = payload['legs'][0]
        self.assertEqual(leg['type'], 'call')
        self.assertEqual(leg['direction'], 'short')
        self.assertEqual(leg['strike'], 150)

