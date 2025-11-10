from django.test import SimpleTestCase
from django.urls import reverse, resolve
from finance.views import (
    Default_Payment_Fees_list,
    Default_Payment_Fees_create,
    Default_Payment_Fees_update,
    Default_Payment_Fees_delete,
)


class DefaultPaymentFeesURLIntegrationTest(SimpleTestCase):
    """Tests that finance URLs resolve to the correct view functions."""

    def test_list_url_resolves_correctly(self):
        url = reverse("Default_Payment_Fees_list")
        resolver = resolve(url)
        self.assertEqual(resolver.func, Default_Payment_Fees_list)

    def test_create_url_resolves_correctly(self):
        url = reverse("Default_Payment_Fees_create")
        resolver = resolve(url)
        self.assertEqual(resolver.func, Default_Payment_Fees_create)

    def test_update_url_resolves_correctly(self):
        url = reverse("Default_Payment_Fees_update", kwargs={"pk": 1})
        resolver = resolve(url)
        self.assertEqual(resolver.func, Default_Payment_Fees_update)

    def test_delete_url_resolves_correctly(self):
        url = reverse("Default_Payment_Fees_delete", kwargs={"pk": 1})
        resolver = resolve(url)
        self.assertEqual(resolver.func, Default_Payment_Fees_delete)
