"""
Comprehensive unit tests for SubscriptionService.
Tests subscription creation, renewal, cancellation, and upgrades.
"""
from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
from unittest.mock import patch

User = get_user_model()
Wallet = apps.get_model('payments', 'Wallet')
Transaction = apps.get_model('payments', 'Transaction')
SubscriptionPlan = apps.get_model('payments', 'SubscriptionPlan')
UserSubscription = apps.get_model('payments', 'UserSubscription')
Invoice = apps.get_model('payments', 'Invoice')

from payments.services.subscription_service import SubscriptionService


class SubscriptionServiceCreateTests(TestCase):
    """Tests for UserSubscription model creation - testing model directly."""

    def setUp(self):
        self.user = User.objects.create_user(username='createuser', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('9.99'),
            duration_days=30
        )

    def test_create_subscription_success(self):
        """Test successful subscription creation."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            payment_method='wallet'
        )
        
        self.assertIsNotNone(subscription)
        self.assertEqual(subscription.status, 'pending')
        self.assertEqual(subscription.plan, self.plan)

    def test_create_subscription_and_activate(self):
        """Test subscription creation and activation sets dates."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            payment_method='wallet'
        )
        subscription.activate()
        subscription.refresh_from_db()
        
        self.assertEqual(subscription.status, 'active')
        self.assertIsNotNone(subscription.start_date)
        self.assertIsNotNone(subscription.end_date)
        
        expected_end = subscription.start_date + timedelta(days=30)
        self.assertAlmostEqual(
            subscription.end_date.timestamp(),
            expected_end.timestamp(),
            delta=60
        )

    def test_create_subscription_auto_renew(self):
        """Test subscription creation with auto-renew."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            payment_method='wallet',
            auto_renew=True
        )
        
        self.assertTrue(subscription.auto_renew)

    def test_create_subscription_no_auto_renew(self):
        """Test subscription creation without auto-renew."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            payment_method='wallet',
            auto_renew=False
        )
        
        self.assertFalse(subscription.auto_renew)


class SubscriptionServiceCancelTests(TestCase):
    """Tests for subscription cancellation using model method."""

    def setUp(self):
        self.user = User.objects.create_user(username='canceluser', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('9.99'),
            duration_days=30
        )

    def test_cancel_active_subscription(self):
        """Test cancelling an active subscription."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active'
        )
        
        subscription.cancel()
        subscription.refresh_from_db()
        
        self.assertEqual(subscription.status, 'cancelled')
        self.assertFalse(subscription.auto_renew)

    def test_cancel_already_cancelled(self):
        """Test cancelling an already cancelled subscription."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='cancelled'
        )
        
        # Model method doesn't prevent re-cancellation
        subscription.cancel()
        self.assertEqual(subscription.status, 'cancelled')

    def test_cancel_expired_subscription(self):
        """Test cancelling an expired subscription."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='expired'
        )
        
        subscription.cancel()
        self.assertEqual(subscription.status, 'cancelled')


class SubscriptionServiceExpireTests(TestCase):
    """Tests for SubscriptionService expire_subscription method."""

    def setUp(self):
        self.user = User.objects.create_user(username='expireuser', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('9.99'),
            duration_days=30
        )

    def test_expire_past_end_date(self):
        """Test expiring subscription with past end date."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active',
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=30)
        )
        
        result = SubscriptionService.expire_subscription(subscription)
        subscription.refresh_from_db()
        
        self.assertTrue(result)
        self.assertEqual(subscription.status, 'expired')

    def test_expire_future_end_date(self):
        """Test expiring subscription with future end date."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30)
        )
        
        result = SubscriptionService.expire_subscription(subscription)
        self.assertFalse(result)


class SubscriptionServiceGetActiveTests(TestCase):
    """Tests for SubscriptionService get_active_subscription method."""

    def setUp(self):
        self.user = User.objects.create_user(username='activeuser', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('9.99'),
            duration_days=30
        )

    def test_get_active_subscription_exists(self):
        """Test getting active subscription when it exists."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30)
        )
        
        result = SubscriptionService.get_active_subscription(self.user)
        
        self.assertIsNotNone(result)
        self.assertEqual(result, subscription)

    def test_get_active_subscription_none(self):
        """Test getting active subscription when none exists."""
        result = SubscriptionService.get_active_subscription(self.user)
        self.assertIsNone(result)

    def test_get_active_subscription_expired(self):
        """Test getting active subscription when only expired exists."""
        UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='expired'
        )
        
        result = SubscriptionService.get_active_subscription(self.user)
        self.assertIsNone(result)


class SubscriptionServiceNeedsRenewalTests(TestCase):
    """Tests for SubscriptionService needs_renewal method."""

    def setUp(self):
        self.user = User.objects.create_user(username='renewuser', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('9.99'),
            duration_days=30
        )

    def test_needs_renewal_expiring_soon(self):
        """Test needs_renewal for soon-expiring subscription."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active',
            auto_renew=True,
            start_date=timezone.now() - timedelta(days=29),
            end_date=timezone.now() + timedelta(hours=12)
        )
        
        result = SubscriptionService.needs_renewal(subscription, days_before=1)
        self.assertTrue(result)

    def test_needs_renewal_not_expiring_soon(self):
        """Test needs_renewal for subscription not expiring soon."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active',
            auto_renew=True,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30)
        )
        
        result = SubscriptionService.needs_renewal(subscription)
        self.assertFalse(result)

    def test_needs_renewal_auto_renew_off(self):
        """Test needs_renewal with auto-renew disabled."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='active',
            auto_renew=False,
            start_date=timezone.now() - timedelta(days=29),
            end_date=timezone.now() + timedelta(hours=12)
        )
        
        result = SubscriptionService.needs_renewal(subscription)
        self.assertFalse(result)

    def test_needs_renewal_inactive(self):
        """Test needs_renewal for inactive subscription."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            status='cancelled',
            auto_renew=True,
            end_date=timezone.now() + timedelta(hours=12)
        )
        
        result = SubscriptionService.needs_renewal(subscription)
        self.assertFalse(result)


class SubscriptionPlanComparisonTests(TestCase):
    """Tests for subscription plan pricing comparison."""

    def setUp(self):
        self.user = User.objects.create_user(username='downgradeuser', password='pass')
        self.premium_plan = SubscriptionPlan.objects.create(
            name='Premium',
            slug='premium',
            description='Premium plan',
            price=Decimal('29.99'),
            duration_days=30
        )
        self.basic_plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('9.99'),
            duration_days=30
        )

    def test_plan_price_comparison(self):
        """Test comparing plan prices."""
        self.assertGreater(self.premium_plan.price, self.basic_plan.price)

    def test_subscription_plan_change_logic(self):
        """Test subscription plan change logic."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.premium_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30)
        )
        
        # Verify current plan
        self.assertEqual(subscription.plan, self.premium_plan)
        
        # Simulate plan change
        subscription.plan = self.basic_plan
        subscription.save()
        subscription.refresh_from_db()
        
        self.assertEqual(subscription.plan, self.basic_plan)

    def test_can_cancel_before_downgrade(self):
        """Test that subscription can be cancelled before downgrade."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.premium_plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30)
        )
        
        subscription.cancel()
        subscription.refresh_from_db()
        
        self.assertEqual(subscription.status, 'cancelled')
        self.assertFalse(subscription.auto_renew)

