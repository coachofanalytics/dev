from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

User = get_user_model()
SubscriptionPlan = apps.get_model('payments', 'SubscriptionPlan')
UserSubscription = apps.get_model('payments', 'UserSubscription')


class SubscriptionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='erin', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic', slug='basic', description='Test', price=Decimal('10.00'), duration_days=30
        )

    def test_user_subscription_activate_cancel(self):
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        self.assertEqual(sub.status, 'pending')
        sub.activate()
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'active')
        self.assertIsNotNone(sub.start_date)
        self.assertIsNotNone(sub.end_date)
        # cancel
        sub.cancel()
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'cancelled')

    def test_days_remaining_property(self):
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        sub.activate()
        self.assertTrue(sub.days_remaining() >= 0)
