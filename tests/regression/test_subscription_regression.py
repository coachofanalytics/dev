"""
Regression Tests for Subscription Lifecycle

These tests verify that existing subscription functionality remains intact
after code changes. Tests are designed to FIND and REPORT issues.

Tested Features:
- Subscription plan creation
- Subscription activation
- Subscription renewal
- Subscription cancellation
- Subscription expiration
- Payment method handling

Author: Fadhiri
Date: January 2026
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta

import accounts.models as accounts_models
from payments.models import (
    Wallet, SubscriptionPlan, UserSubscription, 
    Invoice, Transaction
)


class SubscriptionPlanRegressionTests(TestCase):
    """
    Regression tests for subscription plan model.
    
    These tests verify that:
    - Plans can be created with required fields
    - Price validation works
    - Slug uniqueness is enforced
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def test_plan_creation_with_required_fields(self):
        """
        REGRESSION TEST: Plan should be created with all required fields.
        
        Verifies: Basic plan creation works.
        Reports: Issues with required field handling.
        """
        plan = SubscriptionPlan.objects.create(
            name='Basic Plan',
            slug='basic-plan',
            description='Basic subscription plan',
            price=Decimal('9.99'),
            duration_days=30,
            features=['Feature 1', 'Feature 2']
        )
        
        self.assertIsNotNone(plan.pk, "REGRESSION ISSUE: Plan not created")
        self.assertEqual(plan.name, 'Basic Plan', "REGRESSION ISSUE: Plan name not saved")
        self.assertEqual(plan.price, Decimal('9.99'), "REGRESSION ISSUE: Price not saved correctly")
    
    def test_plan_slug_unique(self):
        """
        REGRESSION TEST: Plan slugs should be unique.
        
        Verifies: Unique constraint on slug field.
        Reports: Duplicate slugs allowed.
        """
        from django.db import IntegrityError
        
        SubscriptionPlan.objects.create(
            name='Plan A',
            slug='same-slug',
            description='First plan',
            price=Decimal('9.99'),
            duration_days=30
        )
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Duplicate plan slugs allowed"):
            SubscriptionPlan.objects.create(
                name='Plan B',
                slug='same-slug',
                description='Second plan',
                price=Decimal('19.99'),
                duration_days=30
            )
    
    def test_plan_is_active_by_default(self):
        """
        REGRESSION TEST: New plans should be active by default.
        
        Verifies: is_active default value.
        Reports: Plans created inactive.
        """
        plan = SubscriptionPlan.objects.create(
            name='Active Plan',
            slug='active-plan',
            description='Test plan',
            price=Decimal('9.99'),
            duration_days=30
        )
        
        self.assertTrue(plan.is_active, "REGRESSION ISSUE: Plan not active by default")
    
    def test_plan_price_minimum_value(self):
        """
        REGRESSION TEST: Plan price should not be negative.
        
        Verifies: MinValueValidator on price field.
        Reports: Negative prices allowed.
        """
        plan = SubscriptionPlan(
            name='Negative Plan',
            slug='negative-plan',
            description='Test plan',
            price=Decimal('-9.99'),
            duration_days=30
        )
        
        with self.assertRaises(ValidationError, msg="REGRESSION ISSUE: Negative price allowed"):
            plan.full_clean()
    
    def test_plan_duration_days_default(self):
        """
        REGRESSION TEST: Plan duration should default to 30 days.
        
        Verifies: Default duration_days value.
        Reports: Incorrect default duration.
        """
        plan = SubscriptionPlan.objects.create(
            name='Duration Test Plan',
            slug='duration-test',
            description='Test plan',
            price=Decimal('9.99')
        )
        
        self.assertEqual(plan.duration_days, 30, "REGRESSION ISSUE: Default duration not 30 days")
    
    def test_plan_features_as_json(self):
        """
        REGRESSION TEST: Features should be stored as JSON list.
        
        Verifies: JSONField stores features correctly.
        Reports: Issues with JSON field handling.
        """
        features = ['Feature A', 'Feature B', 'Feature C']
        plan = SubscriptionPlan.objects.create(
            name='Features Plan',
            slug='features-plan',
            description='Test plan',
            price=Decimal('9.99'),
            duration_days=30,
            features=features
        )
        
        plan.refresh_from_db()
        self.assertEqual(plan.features, features, "REGRESSION ISSUE: Features not stored correctly")


class UserSubscriptionCreationRegressionTests(TestCase):
    """
    Regression tests for user subscription creation.
    
    These tests verify that:
    - Subscriptions can be created
    - User-Plan relationship works
    - Default status is pending
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='sub_user',
            email='sub@test.com',
            password='SubPass123!'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            description='Test subscription plan',
            price=Decimal('29.99'),
            duration_days=30
        )
    
    def test_subscription_creation(self):
        """
        REGRESSION TEST: Subscription should be created successfully.
        
        Verifies: Basic subscription creation.
        Reports: Subscription creation failures.
        """
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan
        )
        
        self.assertIsNotNone(subscription.pk, "REGRESSION ISSUE: Subscription not created")
        self.assertEqual(subscription.user, self.user, "REGRESSION ISSUE: User not linked")
        self.assertEqual(subscription.plan, self.plan, "REGRESSION ISSUE: Plan not linked")
    
    def test_subscription_default_status_pending(self):
        """
        REGRESSION TEST: New subscription should have pending status.
        
        Verifies: Default status value.
        Reports: Incorrect default status.
        """
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan
        )
        
        self.assertEqual(
            subscription.status, 
            'pending',
            "REGRESSION ISSUE: Default status not 'pending'"
        )
    
    def test_subscription_auto_renew_default_true(self):
        """
        REGRESSION TEST: Auto-renew should default to True.
        
        Verifies: auto_renew default value.
        Reports: Auto-renew not enabled by default.
        """
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan
        )
        
        self.assertTrue(subscription.auto_renew, "REGRESSION ISSUE: auto_renew not True by default")
    
    def test_subscription_default_payment_method_wallet(self):
        """
        REGRESSION TEST: Default payment method should be wallet.
        
        Verifies: payment_method default value.
        Reports: Incorrect default payment method.
        """
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan
        )
        
        self.assertEqual(
            subscription.payment_method,
            'wallet',
            "REGRESSION ISSUE: Default payment method not 'wallet'"
        )


class UserSubscriptionActivationRegressionTests(TestCase):
    """
    Regression tests for subscription activation.
    
    These tests verify that:
    - activate() sets correct status
    - Start and end dates are set
    - Duration is calculated correctly
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='activate_user',
            email='activate@test.com',
            password='ActivatePass123!'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Activation Plan',
            slug='activation-plan',
            description='Test plan',
            price=Decimal('29.99'),
            duration_days=30
        )
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan
        )
    
    def test_activate_sets_status_active(self):
        """
        REGRESSION TEST: activate() should set status to 'active'.
        
        Verifies: Status changes correctly.
        Reports: Activation not setting correct status.
        """
        self.subscription.activate()
        self.subscription.refresh_from_db()
        
        self.assertEqual(
            self.subscription.status,
            'active',
            "REGRESSION ISSUE: activate() did not set status to 'active'"
        )
    
    def test_activate_sets_start_date(self):
        """
        REGRESSION TEST: activate() should set start_date.
        
        Verifies: Start date is populated.
        Reports: Missing start date after activation.
        """
        self.subscription.activate()
        self.subscription.refresh_from_db()
        
        self.assertIsNotNone(
            self.subscription.start_date,
            "REGRESSION ISSUE: activate() did not set start_date"
        )
    
    def test_activate_sets_end_date(self):
        """
        REGRESSION TEST: activate() should set end_date based on plan duration.
        
        Verifies: End date is calculated correctly.
        Reports: Incorrect end date calculation.
        """
        self.subscription.activate()
        self.subscription.refresh_from_db()
        
        self.assertIsNotNone(
            self.subscription.end_date,
            "REGRESSION ISSUE: activate() did not set end_date"
        )
        
        # Check end date is approximately 30 days from start
        expected_end = self.subscription.start_date + timedelta(days=30)
        self.assertEqual(
            self.subscription.end_date.date(),
            expected_end.date(),
            "REGRESSION ISSUE: End date not calculated correctly"
        )


class UserSubscriptionCancellationRegressionTests(TestCase):
    """
    Regression tests for subscription cancellation.
    
    These tests verify that:
    - cancel() sets correct status
    - Auto-renew is disabled on cancellation
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='cancel_user',
            email='cancel@test.com',
            password='CancelPass123!'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Cancel Plan',
            slug='cancel-plan',
            description='Test plan',
            price=Decimal('29.99'),
            duration_days=30
        )
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan
        )
        self.subscription.activate()
    
    def test_cancel_sets_status_cancelled(self):
        """
        REGRESSION TEST: cancel() should set status to 'cancelled'.
        
        Verifies: Status changes correctly.
        Reports: Cancellation not setting correct status.
        """
        self.subscription.cancel()
        self.subscription.refresh_from_db()
        
        self.assertEqual(
            self.subscription.status,
            'cancelled',
            "REGRESSION ISSUE: cancel() did not set status to 'cancelled'"
        )
    
    def test_cancel_disables_auto_renew(self):
        """
        REGRESSION TEST: cancel() should disable auto-renew.
        
        Verifies: auto_renew is set to False.
        Reports: Auto-renew not disabled on cancellation.
        """
        self.subscription.cancel()
        self.subscription.refresh_from_db()
        
        self.assertFalse(
            self.subscription.auto_renew,
            "REGRESSION ISSUE: cancel() did not disable auto_renew"
        )


class UserSubscriptionValidityRegressionTests(TestCase):
    """
    Regression tests for subscription validity checking.
    
    These tests verify that:
    - is_valid() returns correct results
    - days_remaining() calculates correctly
    - needs_renewal_notification property works
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='validity_user',
            email='validity@test.com',
            password='ValidityPass123!'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Validity Plan',
            slug='validity-plan',
            description='Test plan',
            price=Decimal('29.99'),
            duration_days=30
        )
        self.subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan
        )
    
    def test_is_valid_returns_false_for_pending(self):
        """
        REGRESSION TEST: is_valid() should return False for pending subscription.
        
        Verifies: Pending subscriptions are not valid.
        Reports: Pending subscriptions marked as valid.
        """
        self.assertFalse(
            self.subscription.is_valid(),
            "REGRESSION ISSUE: Pending subscription marked as valid"
        )
    
    def test_is_valid_returns_true_for_active(self):
        """
        REGRESSION TEST: is_valid() should return True for active subscription.
        
        Verifies: Active subscriptions are valid.
        Reports: Active subscriptions marked as invalid.
        """
        self.subscription.activate()
        
        self.assertTrue(
            self.subscription.is_valid(),
            "REGRESSION ISSUE: Active subscription marked as invalid"
        )
    
    def test_is_valid_returns_false_for_expired(self):
        """
        REGRESSION TEST: is_valid() should return False for expired subscription.
        
        Verifies: Expired subscriptions are not valid.
        Reports: Expired subscriptions marked as valid (financial risk).
        """
        self.subscription.activate()
        # Manually set end_date to past
        self.subscription.end_date = timezone.now() - timedelta(days=1)
        self.subscription.save()
        
        self.assertFalse(
            self.subscription.is_valid(),
            "REGRESSION ISSUE: Expired subscription marked as valid (FINANCIAL RISK)"
        )
    
    def test_days_remaining_for_active(self):
        """
        REGRESSION TEST: days_remaining() should return positive days for active subscription.
        
        Verifies: Days calculation is correct.
        Reports: Incorrect days calculation.
        """
        self.subscription.activate()
        days = self.subscription.days_remaining()
        
        self.assertGreater(
            days,
            0,
            "REGRESSION ISSUE: days_remaining() not returning positive value for active subscription"
        )
        self.assertLessEqual(
            days,
            30,
            "REGRESSION ISSUE: days_remaining() exceeds plan duration"
        )
    
    def test_days_remaining_for_inactive(self):
        """
        REGRESSION TEST: days_remaining() should return 0 for inactive subscription.
        
        Verifies: Days return 0 when not active.
        Reports: Non-zero days for inactive subscription.
        """
        days = self.subscription.days_remaining()
        
        self.assertEqual(
            days,
            0,
            "REGRESSION ISSUE: days_remaining() not returning 0 for pending subscription"
        )
    
    def test_needs_renewal_notification_false_for_new_subscription(self):
        """
        REGRESSION TEST: needs_renewal_notification should be False for new subscription.
        
        Verifies: Notification not triggered for new subscriptions.
        Reports: Premature renewal notifications.
        """
        self.subscription.activate()
        
        self.assertFalse(
            self.subscription.needs_renewal_notification,
            "REGRESSION ISSUE: Renewal notification triggered for new subscription"
        )
    
    def test_needs_renewal_notification_true_when_expiring_soon(self):
        """
        REGRESSION TEST: needs_renewal_notification should be True when expiring within 7 days.
        
        Verifies: Notification triggered at correct time.
        Reports: Missing renewal notifications.
        """
        self.subscription.activate()
        # Set end_date to 5 days from now
        self.subscription.end_date = timezone.now() + timedelta(days=5)
        self.subscription.save()
        
        self.assertTrue(
            self.subscription.needs_renewal_notification,
            "REGRESSION ISSUE: Renewal notification not triggered for expiring subscription"
        )


class InvoiceGenerationRegressionTests(TestCase):
    """
    Regression tests for invoice generation.
    
    These tests verify that:
    - Invoice numbers are auto-generated
    - Invoice numbers are unique
    - Mark as paid functionality works
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='invoice_user',
            email='invoice@test.com',
            password='InvoicePass123!'
        )
    
    def test_invoice_number_auto_generated(self):
        """
        REGRESSION TEST: Invoice number should be auto-generated.
        
        Verifies: Invoice number is created on save.
        Reports: Missing invoice number generation.
        """
        invoice = Invoice.objects.create(
            user=self.user,
            amount=Decimal('99.99'),
            description='Test invoice',
            due_date=timezone.now() + timedelta(days=30)
        )
        
        self.assertIsNotNone(invoice.invoice_number, "REGRESSION ISSUE: Invoice number not generated")
        self.assertTrue(
            invoice.invoice_number.startswith('INV-'),
            "REGRESSION ISSUE: Invoice number format incorrect"
        )
    
    def test_invoice_number_unique(self):
        """
        REGRESSION TEST: Invoice numbers should be unique.
        
        Verifies: Unique constraint on invoice_number.
        Reports: Duplicate invoice numbers allowed.
        """
        invoice1 = Invoice.objects.create(
            user=self.user,
            amount=Decimal('99.99'),
            description='Invoice 1',
            due_date=timezone.now() + timedelta(days=30)
        )
        invoice2 = Invoice.objects.create(
            user=self.user,
            amount=Decimal('49.99'),
            description='Invoice 2',
            due_date=timezone.now() + timedelta(days=30)
        )
        
        self.assertNotEqual(
            invoice1.invoice_number,
            invoice2.invoice_number,
            "REGRESSION ISSUE: Duplicate invoice numbers generated"
        )
    
    def test_invoice_mark_as_paid(self):
        """
        REGRESSION TEST: mark_as_paid() should update status and paid_date.
        
        Verifies: Payment marking functionality.
        Reports: Issues with payment marking.
        """
        invoice = Invoice.objects.create(
            user=self.user,
            amount=Decimal('99.99'),
            description='Test invoice',
            due_date=timezone.now() + timedelta(days=30)
        )
        
        invoice.mark_as_paid()
        invoice.refresh_from_db()
        
        self.assertEqual(invoice.status, 'paid', "REGRESSION ISSUE: Status not set to 'paid'")
        self.assertIsNotNone(invoice.paid_date, "REGRESSION ISSUE: paid_date not set")
    
    def test_invoice_is_overdue_for_past_due_date(self):
        """
        REGRESSION TEST: is_overdue() should return True for past due invoices.
        
        Verifies: Overdue detection.
        Reports: Overdue invoices not detected.
        """
        invoice = Invoice.objects.create(
            user=self.user,
            amount=Decimal('99.99'),
            description='Overdue invoice',
            due_date=timezone.now() - timedelta(days=1)
        )
        
        self.assertTrue(
            invoice.is_overdue(),
            "REGRESSION ISSUE: Overdue invoice not detected"
        )
    
    def test_invoice_not_overdue_when_paid(self):
        """
        REGRESSION TEST: is_overdue() should return False for paid invoices.
        
        Verifies: Paid invoices are not marked overdue.
        Reports: Paid invoices marked as overdue.
        """
        invoice = Invoice.objects.create(
            user=self.user,
            amount=Decimal('99.99'),
            description='Paid invoice',
            due_date=timezone.now() - timedelta(days=1)
        )
        invoice.mark_as_paid()
        
        self.assertFalse(
            invoice.is_overdue(),
            "REGRESSION ISSUE: Paid invoice marked as overdue"
        )

