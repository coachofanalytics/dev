from django.test import TestCase
from investments.models import investment_content


class InvestmentContentRegressionTests(TestCase):
    """
    Regression tests ensure previously working model behavior
    continues to function after updates or refactoring.
    """

    def setUp(self):
        self.investment = investment_content.objects.create(
            title="Agribusiness Growth Fund",
            slug="agribusiness-growth-fund",
            description="Investment focused on scalable agribusiness projects."
        )

    def test_existing_record_retrievable(self):
        """Ensure saved investment content can still be retrieved"""
        investment = investment_content.objects.get(slug="agribusiness-growth-fund")
        self.assertEqual(investment.title, "Agribusiness Growth Fund")

    def test_title_not_modified_unexpectedly(self):
        """Ensure title remains unchanged unless explicitly updated"""
        investment = investment_content.objects.get(id=self.investment.id)
        self.assertEqual(investment.title, "Agribusiness Growth Fund")

    def test_description_allows_null(self):
        """Ensure description field supports null values"""
        investment = investment_content.objects.create(
            title="Real Estate Fund",
            slug="real-estate-fund"
        )
        self.assertIsNone(investment.description)

    def test_slug_stored_as_string(self):
        """Ensure slug is stored correctly as a string"""
        investment = investment_content.objects.get(slug="agribusiness-growth-fund")
        self.assertIsInstance(investment.slug, str)

    def test_multiple_records_can_exist(self):
        """Ensure multiple investment contents can coexist"""
        investment_content.objects.create(
            title="Tech Innovation Fund",
            slug="tech-innovation-fund",
            description="Technology-driven investment opportunities."
        )
        self.assertEqual(investment_content.objects.count(), 2)

    def test_delete_does_not_affect_other_records(self):
        """Ensure deleting one record does not affect others"""
        investment_content.objects.create(
            title="Healthcare Fund",
            slug="healthcare-fund"
        )
        self.investment.delete()
        self.assertEqual(investment_content.objects.count(), 1)

    def test_model_string_representation_safe(self):
        """Ensure model does not raise errors when converted to string"""
        investment = investment_content.objects.first()
        self.assertTrue(str(investment))
