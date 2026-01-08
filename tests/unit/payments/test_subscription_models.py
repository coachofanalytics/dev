"""
Comprehensive unit tests for Subscription models.
Tests subscription plan, user subscription, activation, renewal, and cancellation.
"""
from django.test import TestCase
from django.apps import apps
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta

User = get_user_model()
SubscriptionPlan = apps.get_model('payments', 'SubscriptionPlan')
UserSubscription = apps.get_model('payments', 'UserSubscription')


class SubscriptionPlanBasicTests(TestCase):
    """Basic tests for SubscriptionPlan model."""

    def test_plan_creation(self):
        """Test creating a subscription plan."""
        plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('9.99'),
            duration_days=30
        )
        self.assertEqual(plan.name, 'Basic')
        self.assertEqual(plan.price, Decimal('9.99'))
        self.assertEqual(plan.duration_days, 30)

    def test_plan_str_representation(self):
        """Test plan string representation."""
        plan = SubscriptionPlan.objects.create(
            name='Premium',
            slug='premium',
            description='Premium plan',
            price=Decimal('29.99'),
            duration_days=30
        )
        expected = 'Premium - $29.99/30 days'
        self.assertEqual(str(plan), expected)

    def test_plan_default_values(self):
        """Test plan default values."""
        plan = SubscriptionPlan.objects.create(
            name='Test',
            slug='test',
            description='Test plan',
            price=Decimal('10.00')
        )
        self.assertEqual(plan.duration_days, 30)
        self.assertTrue(plan.is_active)
        self.assertFalse(plan.is_featured)
        self.assertEqual(plan.billing_period, 'per month')


class SubscriptionPlanValidationTests(TestCase):
    """Tests for subscription plan field validations."""

    def test_price_min_value_zero(self):
        """Test that zero price is valid."""
        plan = SubscriptionPlan.objects.create(
            name='Free',
            slug='free',
            description='Free plan',
            price=Decimal('0.00'),
            duration_days=30
        )
        self.assertEqual(plan.price, Decimal('0.00'))

    def test_price_positive_value(self):
        """Test positive price is valid."""
        plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('10.00'),
            duration_days=30
        )
        self.assertEqual(plan.price, Decimal('10.00'))

    def test_slug_unique_constraint(self):
        """Test slug must be unique."""
        from django.db import IntegrityError
        SubscriptionPlan.objects.create(
            name='Plan A',
            slug='unique-slug',
            description='First plan',
            price=Decimal('10.00')
        )
        with self.assertRaises(IntegrityError):
            SubscriptionPlan.objects.create(
                name='Plan B',
                slug='unique-slug',
                description='Second plan',
                price=Decimal('20.00')
            )


class SubscriptionPlanFeaturesTests(TestCase):
    """Tests for subscription plan features."""

    def test_features_default_empty_list(self):
        """Test features defaults to empty list."""
        plan = SubscriptionPlan.objects.create(
            name='Test',
            slug='test',
            description='Test plan',
            price=Decimal('10.00')
        )
        self.assertEqual(plan.features, [])

    def test_features_with_list(self):
        """Test features with list of features."""
        features = ['Feature 1', 'Feature 2', 'Feature 3']
        plan = SubscriptionPlan.objects.create(
            name='Test',
            slug='test',
            description='Test plan',
            price=Decimal('10.00'),
            features=features
        )
        self.assertEqual(plan.features, features)


class UserSubscriptionBasicTests(TestCase):
    """Basic tests for UserSubscription model."""

    def setUp(self):
        self.user = User.objects.create_user(username='subuser', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('10.00'),
            duration_days=30
        )

    def test_subscription_creation(self):
        """Test creating a user subscription."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        self.assertEqual(sub.user, self.user)
        self.assertEqual(sub.plan, self.plan)
        self.assertEqual(sub.status, 'pending')

    def test_subscription_str_representation(self):
        """Test subscription string representation."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        expected = f'{self.user.username} - {self.plan.name} ({sub.status})'
        self.assertEqual(str(sub), expected)

    def test_default_values(self):
        """Test subscription default values."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        self.assertEqual(sub.status, 'pending')
        self.assertTrue(sub.auto_renew)
        self.assertEqual(sub.payment_method, 'wallet')


class UserSubscriptionActivationTests(TestCase):
    """Tests for subscription activation."""

    def setUp(self):
        self.user = User.objects.create_user(username='activateuser', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('10.00'),
            duration_days=30
        )

    def test_activate_subscription(self):
        """Test activating a subscription."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        sub.activate()
        sub.refresh_from_db()
        
        self.assertEqual(sub.status, 'active')
        self.assertIsNotNone(sub.start_date)
        self.assertIsNotNone(sub.end_date)

    def test_activate_sets_correct_end_date(self):
        """Test activation sets correct end date based on plan duration."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        sub.activate()
        sub.refresh_from_db()
        
        expected_end = sub.start_date + timedelta(days=30)
        self.assertAlmostEqual(
            sub.end_date.timestamp(),
            expected_end.timestamp(),
            delta=60  # Allow 60 seconds variance
        )


class UserSubscriptionCancellationTests(TestCase):
    """Tests for subscription cancellation."""

    def setUp(self):
        self.user = User.objects.create_user(username='canceluser', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('10.00'),
            duration_days=30
        )

    def test_cancel_subscription(self):
        """Test cancelling a subscription."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        sub.activate()
        sub.cancel()
        sub.refresh_from_db()
        
        self.assertEqual(sub.status, 'cancelled')
        self.assertFalse(sub.auto_renew)


class UserSubscriptionValidityTests(TestCase):
    """Tests for subscription validity checking."""

    def setUp(self):
        self.user = User.objects.create_user(username='validuser', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('10.00'),
            duration_days=30
        )

    def test_is_valid_active_subscription(self):
        """Test is_valid returns True for active subscription."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        sub.activate()
        
        self.assertTrue(sub.is_valid())

    def test_is_valid_expired_subscription(self):
        """Test is_valid returns False for expired subscription."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        sub.status = 'active'
        sub.start_date = timezone.now() - timedelta(days=60)
        sub.end_date = timezone.now() - timedelta(days=30)
        sub.save()
        
        self.assertFalse(sub.is_valid())

    def test_is_valid_cancelled_subscription(self):
        """Test is_valid returns False for cancelled subscription."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        sub.activate()
        sub.cancel()
        
        self.assertFalse(sub.is_valid())

    def test_is_valid_pending_subscription(self):
        """Test is_valid returns False for pending subscription."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        
        self.assertFalse(sub.is_valid())


class UserSubscriptionDaysRemainingTests(TestCase):
    """Tests for days remaining calculations."""

    def setUp(self):
        self.user = User.objects.create_user(username='daysuser', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('10.00'),
            duration_days=30
        )

    def test_days_remaining_active_subscription(self):
        """Test days_remaining for active subscription."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        sub.activate()
        
        days = sub.days_remaining()
        self.assertGreaterEqual(days, 29)  # Should be close to 30

    def test_days_remaining_expired_subscription(self):
        """Test days_remaining returns 0 for expired subscription."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        sub.status = 'expired'
        sub.save()
        
        self.assertEqual(sub.days_remaining(), 0)

    def test_days_until_expiry_property(self):
        """Test days_until_expiry property."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        sub.activate()
        
        self.assertEqual(sub.days_until_expiry, sub.days_remaining())


class UserSubscriptionRenewalNotificationTests(TestCase):
    """Tests for renewal notification property."""

    def setUp(self):
        self.user = User.objects.create_user(username='renewuser', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('10.00'),
            duration_days=30
        )

    def test_needs_renewal_notification_expiring_soon(self):
        """Test needs_renewal_notification for soon-expiring subscription."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        sub.status = 'active'
        sub.start_date = timezone.now() - timedelta(days=25)
        sub.end_date = timezone.now() + timedelta(days=5)
        sub.save()
        
        self.assertTrue(sub.needs_renewal_notification)

    def test_needs_renewal_notification_not_expiring_soon(self):
        """Test needs_renewal_notification for not-soon-expiring subscription."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        sub.activate()
        
        self.assertFalse(sub.needs_renewal_notification)

    def test_needs_renewal_notification_inactive_subscription(self):
        """Test needs_renewal_notification for inactive subscription."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        
        self.assertFalse(sub.needs_renewal_notification)


class UserSubscriptionPaymentMethodTests(TestCase):
    """Tests for subscription payment methods."""

    def setUp(self):
        self.user = User.objects.create_user(username='paymentuser', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('10.00'),
            duration_days=30
        )

    def test_default_payment_method_wallet(self):
        """Test default payment method is wallet."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        self.assertEqual(sub.payment_method, 'wallet')

    def test_payment_method_stripe(self):
        """Test stripe payment method."""
        sub = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            payment_method='stripe'
        )
        self.assertEqual(sub.payment_method, 'stripe')

    def test_payment_method_mpesa(self):
        """Test mpesa payment method."""
        sub = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            payment_method='mpesa'
        )
        self.assertEqual(sub.payment_method, 'mpesa')

    def test_payment_method_paypal(self):
        """Test paypal payment method."""
        sub = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            payment_method='paypal'
        )
        self.assertEqual(sub.payment_method, 'paypal')


class UserSubscriptionStatusTransitionTests(TestCase):
    """Tests for subscription status transitions."""

    def setUp(self):
        self.user = User.objects.create_user(username='statususer', password='pass')
        self.plan = SubscriptionPlan.objects.create(
            name='Basic',
            slug='basic',
            description='Basic plan',
            price=Decimal('10.00'),
            duration_days=30
        )

    def test_status_pending_to_active(self):
        """Test transition from pending to active."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        self.assertEqual(sub.status, 'pending')
        
        sub.activate()
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'active')

    def test_status_active_to_cancelled(self):
        """Test transition from active to cancelled."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        sub.activate()
        self.assertEqual(sub.status, 'active')
        
        sub.cancel()
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'cancelled')

    def test_status_active_to_expired(self):
        """Test transition from active to expired."""
        sub = UserSubscription.objects.create(user=self.user, plan=self.plan)
        sub.activate()
        
        sub.status = 'expired'
        sub.save()
        sub.refresh_from_db()
        self.assertEqual(sub.status, 'expired')
