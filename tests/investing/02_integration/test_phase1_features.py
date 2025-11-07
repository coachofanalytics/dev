"""
Integration tests for Managed Trading Phase 1 enhancements.

Focus:
- Zapier webhook endpoints
- Heatmap context data for staff suggestions
- Unusual Whales metadata propagation
"""

from decimal import Decimal
from datetime import date, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from investing.models import SuggestedPosition

User = get_user_model()


class PhaseOneFeatureTests(TestCase):
    """Validate Phase 1 feature wiring for Managed Trading staff tools."""

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(
            username="phase1_staff",
            email="phase1_staff@example.com",
            password="strong-pass-123",
            is_staff=True,
            is_active=True,
        )
        self.client.force_login(self.staff_user)

    def _create_suggestion(self, symbol="AAPL", capital=Decimal("1000.00"), score=Decimal("80.00")):
        """Helper to create a SuggestedPosition with baseline data."""
        return SuggestedPosition.objects.create(
            source="optionplay",
            symbol=symbol,
            strategy="bull_put_spread",
            positions=[
                {"type": "short_put", "strike": 170, "contracts": 1, "premium": 1.50},
                {"type": "long_put", "strike": 165, "contracts": 1, "premium": 0.60},
            ],
            expiration_date=date.today() + timedelta(days=45),
            dte=45,
            premium_collected=Decimal("150.00"),
            capital_required=capital,
            max_profit=Decimal("150.00"),
            max_loss=Decimal("850.00"),
            breakeven=Decimal("168.50"),
            probability_of_profit=score,
            position_delta=Decimal("0.12"),
            position_theta=Decimal("0.03"),
            position_gamma=Decimal("0.01"),
            position_vega=Decimal("0.05"),
            ai_score=score,
            ai_rating="GOOD",
            api_response_data={
                "unusual_whales": {
                    "flow_score": 82.0,
                    "sentiment": "bullish",
                    "timing_signal": "🟢 ENTER NOW (Heavy buying flow detected!)",
                }
            },
        )

    def test_zapier_push_requires_configuration(self):
        """Webhook should respond with 503 when no Zapier webhook URL is set."""
        suggestion = self._create_suggestion()
        response = self.client.post(
            reverse("investing:zapier_position_push"),
            {"suggestion_id": suggestion.id},
        )
        self.assertEqual(response.status_code, 503)
        self.assertFalse(response.json().get("success"))

    @override_settings(ZAPIER_POSITION_WEBHOOK="https://hooks.zapier.test/abc123")
    def test_zapier_push_sends_payload(self):
        """Ensure Zapier push constructs payload and calls external hook."""
        suggestion = self._create_suggestion(symbol="TSLA", capital=Decimal("4200.00"), score=Decimal("92.0"))

        with mock.patch("investing.views.managed_trading.webhooks.requests.post") as mock_post:
            mock_response = mock.Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response

            response = self.client.post(
                reverse("investing:zapier_position_push"),
                {"suggestion_id": suggestion.id},
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))

        mock_post.assert_called_once()
        _, kwargs = mock_post.call_args
        payload = kwargs.get("json", {})
        self.assertEqual(payload["symbol"], "TSLA")
        self.assertEqual(payload["record_type"], "suggested_position")
        self.assertIn("api_response", payload)
        self.assertEqual(payload["api_response"]["unusual_whales"]["flow_score"], 82.0)

    def test_suggestions_view_includes_heatmap_context(self):
        """Heatmap data should be present in staff suggestions view."""
        self._create_suggestion(symbol="NVDA", capital=Decimal("2500.00"), score=Decimal("88.0"))
        self._create_suggestion(symbol="MSFT", capital=Decimal("1800.00"), score=Decimal("75.0"))

        response = self.client.get(reverse("investing:suggested_positions_list"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("heatmap_symbols", response.context)
        heatmap = response.context["heatmap_symbols"]
        self.assertGreaterEqual(len(heatmap), 2)
        symbols = {item["symbol"] for item in heatmap}
        self.assertTrue({"NVDA", "MSFT"}.issubset(symbols))
        self.assertTrue(all("total_capital" in item for item in heatmap))
        self.assertTrue(all("position_count" in item for item in heatmap))

    @override_settings(
        ENVIRONMENT="local",
    )
    @mock.patch("investing.views.managed_trading.position_suggestions.UnusualWhalesService")
    @mock.patch("investing.views.managed_trading.position_suggestions.PositionFetcherService.fetch_high_probability_positions")
    def test_fetch_positions_invokes_unusual_whales(self, mock_fetcher, mock_whales):
        suggestion = self._create_suggestion(symbol="SPY", capital=Decimal("1500.00"), score=Decimal("80.0"))
        mock_fetcher.return_value = [suggestion]
        mock_service = mock_whales.return_value
        mock_service.is_enabled.return_value = True
        mock_service.apply_flow_to_suggestions.return_value = {'enriched': 1, 'symbols_requested': 1}

        response = self.client.post(reverse("investing:fetch_positions_now"), {
            'probability_min': 70,
            'premium_min': 100,
            'dte_min': 30,
            'dte_max': 60,
            'max_positions': 5,
        })

        self.assertRedirects(response, reverse("investing:suggested_positions_list"))
        mock_service.apply_flow_to_suggestions.assert_called_once()
        messages = [m.message for m in response.wsgi_request._messages]
        self.assertTrue(any("UW signals" in msg for msg in messages))

