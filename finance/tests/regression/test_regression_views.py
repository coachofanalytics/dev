from datetime import timedelta
from django.utils import timezone
from django.urls import reverse
from django.test import TestCase
from finance.models import OverBoughtSold


class OverBoughtSoldViewRegressionTests(TestCase):
    def _url(self):
        return reverse("finance:overboughtsold_list")

    def test_ordering_recent_first(self):
        # Distinct timestamps avoid ties
        OverBoughtSold.objects.create(
            symbol="OLD", created_at=timezone.now() - timedelta(minutes=1)
        )
        OverBoughtSold.objects.create(symbol="NEW", created_at=timezone.now())

        resp = self.client.get(self._url())
        self.assertEqual(resp.status_code, 200)

        # Assert on the ordered queryset in context
        records = list(resp.context["records"])
        self.assertGreaterEqual(len(records), 2)
        self.assertEqual(records[0].symbol, "NEW")
        self.assertEqual(records[1].symbol, "OLD")
