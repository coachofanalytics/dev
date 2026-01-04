from django.test import SimpleTestCase
from django.urls import reverse, resolve

from investments.views import daily_trades_list


class DailyTradesURLTest(SimpleTestCase):

    def test_daily_trades_list_url_resolves(self):
        """
        URL name resolves to correct view function
        """
        url = reverse("investments:daily_trades_list")
        self.assertEqual(resolve(url).func, daily_trades_list)

    def test_daily_trades_list_url_path(self):
        """
        URL path is correct (with app prefix)
        """
        url = reverse("investments:daily_trades_list")
        self.assertEqual(url, "/investments/daily_trades_list")
