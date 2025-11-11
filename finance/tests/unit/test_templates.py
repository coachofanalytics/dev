# finance/tests/unit/test_templates.py

from django.test import TestCase
from django.urls import reverse
from finance.models import OverBoughtSold

class OverBoughtSoldTemplateTests(TestCase):

    def test_template_used_for_overboughtsold_list(self):
        """
        Ensure the correct template is used when accessing the OverBoughtSold list page.
        """
        url = reverse('finance:overboughtsold_list')   # URL name from urls.py
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'finance/overboughtsold_list.html')  # template in your app

    def test_template_displays_records(self):
        """
        Verify that records display correctly in the template.
        """
        OverBoughtSold.objects.create(symbol="AAPL", description="Apple Inc.")
        OverBoughtSold.objects.create(symbol="TSLA", description="Tesla")

        url = reverse('finance:overboughtsold_list')
        response = self.client.get(url)

        self.assertContains(response, "AAPL")
        self.assertContains(response, "Tesla")
        self.assertContains(response, "📊 OverBoughtSold Records")  # title section from your template

    def test_template_displays_no_records_message(self):
        """
        Verify the 'No stocks available' message appears when no data exists.
        """
        OverBoughtSold.objects.all().delete()

        url = reverse('finance:overboughtsold_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No stocks available")
