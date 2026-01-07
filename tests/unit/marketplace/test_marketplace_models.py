from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()
BusinessProfile = apps.get_model('marketplace', 'BusinessProfile')
InvestmentOpportunity = apps.get_model('marketplace', 'InvestmentOpportunity')
JobOpportunity = apps.get_model('marketplace', 'JobOpportunity')
JobApplication = apps.get_model('marketplace', 'JobApplication')


class MarketplaceModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='biz', password='pass')

    def test_business_profile_and_increment(self):
        bp = BusinessProfile.objects.create(user=self.user, company_name='C', industry='I')
        self.assertEqual(bp.profile_views, 0)
        bp.increment_views()
        bp.refresh_from_db()
        self.assertEqual(bp.profile_views, 1)

    def test_investment_slug_generation(self):
        opp = InvestmentOpportunity.objects.create(business=self.user, title='My Opportunity', description='d', amount_seeking=Decimal('100.00'), minimum_investment=Decimal('10.00'), equity_percentage=Decimal('1.00'), industry='I')
        self.assertTrue(opp.slug)

    def test_job_application_unique_constraint(self):
        job = JobOpportunity.objects.create(business=self.user, title='Dev', description='d', requirements='r', responsibilities='r', location='loc')
        applicant = User.objects.create_user(username='applicant', password='p')
        JobApplication.objects.create(job=job, applicant=applicant, cover_letter='cl', resume='resume.pdf')
        with self.assertRaises(Exception):
            # duplicate application should violate unique_together
            JobApplication.objects.create(job=job, applicant=applicant, cover_letter='cl2', resume='resume2.pdf')
