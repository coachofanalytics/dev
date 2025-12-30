from django.test import TestCase
from investments.models import investment_content


class InvestmentContentModelTest(TestCase):

    def setUp(self):
        self.investment = investment_content.objects.create(
            title="Renewable Energy Fund",
            slug="renewable-energy-fund",
            description="Investment focused on clean and sustainable energy projects."
        )

    def test_investment_content_creation(self):
        """Test that an investment content object is created correctly"""
        self.assertEqual(self.investment.title, "Renewable Energy Fund")
        self.assertEqual(self.investment.slug, "renewable-energy-fund")
        self.assertIsNotNone(self.investment.description)

    def test_title_max_length(self):
        """Test title max length"""
        max_length = self.investment._meta.get_field("title").max_length
        self.assertEqual(max_length, 50)

    def test_slug_is_required(self):
        """Test slug cannot be null"""
        self.assertFalse(self.investment._meta.get_field("slug").null)

    def test_description_can_be_null(self):
        """Test description allows null values"""
        investment = investment_content.objects.create(
            title="SME Growth Fund",
            slug="sme-growth-fund"
        )
        self.assertIsNone(investment.description)

    def test_string_representation(self):
        """Optional: test string representation if __str__ exists"""
        self.assertEqual(str(self.investment), self.investment.title)
