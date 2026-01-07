from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model

User = get_user_model()
InvestmentOpportunity = apps.get_model('marketplace', 'InvestmentOpportunity')


class PerformanceTests(TestCase):
    def test_bulk_create_investment_opportunities(self):
        user = User.objects.create_user(username='perf', password='p')
        objs = [InvestmentOpportunity(business=user, title=f'Opp {i}', slug=f'opp-{i}', description='d', amount_seeking=1, minimum_investment=1, equity_percentage=0, industry='x') for i in range(200)]
        InvestmentOpportunity.objects.bulk_create(objs)
        self.assertEqual(InvestmentOpportunity.objects.count(), 200)

    def test_index_metadata_present(self):
        # ensure model has defined indexes (meta)
        meta = InvestmentOpportunity._meta
        self.assertTrue(hasattr(meta, 'ordering'))
