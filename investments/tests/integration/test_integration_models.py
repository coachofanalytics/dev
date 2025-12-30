from django.test import TestCase
from django.utils.text import slugify
from investments.models import investment_content


class InvestmentContentIntegrationTests(TestCase):
    """
    Integration tests validate the interaction between:
    - Django ORM
    - Database layer
    - Model constraints
    """

    def test_create_and_retrieve_investment_content(self):
        """
        Ensure model saves and retrieves correctly from the database.
        """
        investment = investment_content.objects.create(
            title="Real Estate Investment",
            slug="real-estate-investment",
            description="Long-term property investment"
        )

        retrieved = investment_content.objects.get(slug="real-estate-investment")

        self.assertEqual(retrieved.title, "Real Estate Investment")
        self.assertEqual(retrieved.description, "Long-term property investment")

    def test_update_investment_content(self):
        """
        Ensure updates persist correctly in the database.
        """
        investment = investment_content.objects.create(
            title="Stock Market",
            slug="stock-market",
            description="Initial description"
        )

        investment.description = "Updated investment description"
        investment.save()

        refreshed = investment_content.objects.get(slug="stock-market")
        self.assertEqual(refreshed.description, "Updated investment description")

    def test_delete_investment_content(self):
        """
        Ensure deletion removes the record from the database.
        """
        investment = investment_content.objects.create(
            title="Crypto Assets",
            slug="crypto-assets",
            description="High risk investment"
        )

        investment.delete()
        self.assertFalse(
            investment_content.objects.filter(slug="crypto-assets").exists()
        )

    def test_slug_generation_logic(self):
        """
        Ensure slug formatting works correctly with Django utilities.
        """
        title = "Private Equity Fund"
        investment = investment_content.objects.create(
            title=title,
            slug=slugify(title),
            description="Equity-based investment"
        )

        self.assertEqual(investment.slug, "private-equity-fund")

    def test_multiple_records_integration(self):
        """
        Ensure multiple objects interact correctly within ORM.
        """
        investment_content.objects.bulk_create([
            investment_content(
                title="Bonds",
                slug="bonds",
                description="Low risk"
            ),
            investment_content(
                title="Commodities",
                slug="commodities",
                description="Inflation hedge"
            )
        ])

        self.assertEqual(investment_content.objects.count(), 2)
