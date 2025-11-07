import os
from unittest.mock import MagicMock, patch

import django
from django.test import SimpleTestCase, override_settings
from django.core.cache import cache
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from coda.investing.services.unusual_whales_service import UnusualWhalesService


@override_settings(
    UNUSUAL_WHALES_ENABLED=True,
    UNUSUAL_WHALES_API_KEY='test-key',
    UW_CACHE_ENABLED=True,
    UW_CACHE_TTL_SECONDS=60,
)
class UnusualWhalesServiceCacheTests(SimpleTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    @patch('coda.investing.services.unusual_whales_service.requests.get')
    def test_get_flow_summary_reuses_cache(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {
                    'type': 'call',
                    'total_premium': 1_000_000,
                    'volume': 250,
                    'volume_oi_ratio': 0.55,
                    'trade_count': 6,
                    'has_sweep': True,
                    'created_at': timezone.now().isoformat(),
                }
            ]
        }
        mock_get.return_value = mock_response

        service = UnusualWhalesService()

        first = service.get_flow_summary_for_symbols(['AAPL'])
        self.assertIn('AAPL', first)
        self.assertEqual(mock_get.call_count, 1)
        self.assertEqual(first['AAPL']['cache_source'], 'live')

        second = service.get_flow_summary_for_symbols(['AAPL'])
        self.assertIn('AAPL', second)
        self.assertEqual(mock_get.call_count, 1, "Expected cached result to avoid second API call")
        self.assertEqual(second['AAPL']['cache_source'], 'cache')

        stats = service.last_fetch_stats
        self.assertIsNotNone(stats)
        self.assertGreaterEqual(stats.get('cache_hits', 0), 1)

