"""
Regression Tests for Database Integrity and Migrations

These tests verify that database migrations and constraints remain intact
after code changes. Tests are designed to FIND and REPORT issues.

Tested Features:
- Migration file existence
- Database constraints
- Unique constraints
- Foreign key relationships
- Index existence
- Data integrity

Author: Fadhiri
Date: January 2026
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db import IntegrityError, connection
from django.apps import apps
from pathlib import Path
from decimal import Decimal

import accounts.models as accounts_models
import payments.signals as payments_signals


class MigrationExistenceRegressionTests(TestCase):
    """
    Regression tests for migration file existence.
    
    These tests verify that:
    - All core apps have migrations
    - Migration files follow naming conventions
    """
    
    def get_project_base(self):
        """Get project base directory."""
        resolved = Path(__file__).resolve()
        candidates = [resolved.parents[3], resolved.parents[2], resolved.parents[4] if len(resolved.parents) > 4 else resolved.parents[3]]
        for cand in candidates:
            if (cand / 'manage.py').exists() or (cand / 'pyproject.toml').exists() or (cand / 'requirements.txt').exists():
                return cand
        return resolved.parents[3]
    
    def test_accounts_migrations_exist(self):
        """
        REGRESSION TEST: accounts app should have migrations.
        
        Verifies: Migration files exist for accounts.
        Reports: Missing migrations for accounts app.
        """
        base = self.get_project_base()
        migrations_dir = base / 'accounts' / 'migrations'
        self.assertTrue(migrations_dir.exists(), "REGRESSION ISSUE: accounts migrations directory missing")
        
        py_files = list(migrations_dir.glob('[0-9]*_*.py'))
        self.assertTrue(len(py_files) > 0, "REGRESSION ISSUE: No migration files in accounts app")
    
    def test_payments_migrations_exist(self):
        """
        REGRESSION TEST: payments app should have migrations.
        
        Verifies: Migration files exist for payments.
        Reports: Missing migrations for payments app.
        """
        base = self.get_project_base()
        migrations_dir = base / 'payments' / 'migrations'
        self.assertTrue(migrations_dir.exists(), "REGRESSION ISSUE: payments migrations directory missing")
        
        py_files = list(migrations_dir.glob('[0-9]*_*.py'))
        self.assertTrue(len(py_files) > 0, "REGRESSION ISSUE: No migration files in payments app")
    
    def test_marketplace_migrations_exist(self):
        """
        REGRESSION TEST: marketplace app should have migrations.
        
        Verifies: Migration files exist for marketplace.
        Reports: Missing migrations for marketplace app.
        """
        base = self.get_project_base()
        migrations_dir = base / 'marketplace' / 'migrations'
        self.assertTrue(migrations_dir.exists(), "REGRESSION ISSUE: marketplace migrations directory missing")
        
        py_files = list(migrations_dir.glob('[0-9]*_*.py'))
        self.assertTrue(len(py_files) > 0, "REGRESSION ISSUE: No migration files in marketplace app")
    
    def test_kyc_migrations_exist(self):
        """
        REGRESSION TEST: kyc app should have migrations.
        
        Verifies: Migration files exist for kyc.
        Reports: Missing migrations for kyc app.
        """
        base = self.get_project_base()
        migrations_dir = base / 'kyc' / 'migrations'
        self.assertTrue(migrations_dir.exists(), "REGRESSION ISSUE: kyc migrations directory missing")
        
        py_files = list(migrations_dir.glob('[0-9]*_*.py'))
        self.assertTrue(len(py_files) > 0, "REGRESSION ISSUE: No migration files in kyc app")
    
    def test_gdpr_migrations_exist(self):
        """
        REGRESSION TEST: gdpr app should have migrations.
        
        Verifies: Migration files exist for gdpr.
        Reports: Missing migrations for gdpr app.
        """
        base = self.get_project_base()
        migrations_dir = base / 'gdpr' / 'migrations'
        self.assertTrue(migrations_dir.exists(), "REGRESSION ISSUE: gdpr migrations directory missing")
        
        py_files = list(migrations_dir.glob('[0-9]*_*.py'))
        self.assertTrue(len(py_files) > 0, "REGRESSION ISSUE: No migration files in gdpr app")
    
    def test_onboarding_migrations_exist(self):
        """
        REGRESSION TEST: onboarding app should have migrations.
        
        Verifies: Migration files exist for onboarding.
        Reports: Missing migrations for onboarding app.
        """
        base = self.get_project_base()
        migrations_dir = base / 'onboarding' / 'migrations'
        self.assertTrue(migrations_dir.exists(), "REGRESSION ISSUE: onboarding migrations directory missing")
        
        py_files = list(migrations_dir.glob('[0-9]*_*.py'))
        self.assertTrue(len(py_files) > 0, "REGRESSION ISSUE: No migration files in onboarding app")
    
    def test_audit_migrations_exist(self):
        """
        REGRESSION TEST: audit app should have migrations.
        
        Verifies: Migration files exist for audit.
        Reports: Missing migrations for audit app.
        """
        base = self.get_project_base()
        migrations_dir = base / 'audit' / 'migrations'
        self.assertTrue(migrations_dir.exists(), "REGRESSION ISSUE: audit migrations directory missing")
        
        py_files = list(migrations_dir.glob('[0-9]*_*.py'))
        self.assertTrue(len(py_files) > 0, "REGRESSION ISSUE: No migration files in audit app")


class UniqueConstraintRegressionTests(TestCase):
    """
    Regression tests for unique constraints.
    
    These tests verify that:
    - Unique constraints are enforced
    - Duplicate values are rejected
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    def test_user_username_unique(self):
        """
        REGRESSION TEST: Username uniqueness should be enforced.
        
        Verifies: User username unique constraint.
        Reports: Duplicate usernames allowed.
        """
        User.objects.create_user(username='unique_user', email='unique1@test.com', password='Pass123!')
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Duplicate usernames allowed"):
            User.objects.create_user(username='unique_user', email='unique2@test.com', password='Pass123!')
    
    def test_category_slug_unique(self):
        """
        REGRESSION TEST: Category slug uniqueness should be enforced.
        
        Verifies: Category slug unique constraint.
        Reports: Duplicate category slugs allowed.
        """
        from accounts.models import Category
        
        Category.objects.create(name='Category A', slug='unique-slug', description='Test')
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Duplicate category slugs allowed"):
            Category.objects.create(name='Category B', slug='unique-slug', description='Test')
    
    def test_subscription_plan_slug_unique(self):
        """
        REGRESSION TEST: Subscription plan slug uniqueness should be enforced.
        
        Verifies: SubscriptionPlan slug unique constraint.
        Reports: Duplicate plan slugs allowed.
        """
        from payments.models import SubscriptionPlan
        
        SubscriptionPlan.objects.create(
            name='Plan A', slug='unique-plan', description='Test', price=Decimal('9.99'), duration_days=30
        )
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Duplicate plan slugs allowed"):
            SubscriptionPlan.objects.create(
                name='Plan B', slug='unique-plan', description='Test', price=Decimal('19.99'), duration_days=30
            )
    
    def test_invoice_number_unique(self):
        """
        REGRESSION TEST: Invoice number uniqueness should be enforced.
        
        Verifies: Invoice invoice_number unique constraint.
        Reports: Duplicate invoice numbers allowed.
        """
        from payments.models import Invoice
        from django.utils import timezone
        
        user = User.objects.create_user(username='invoice_user', email='invoice@test.com', password='Pass123!')
        
        inv1 = Invoice.objects.create(
            user=user, amount=Decimal('100'), description='Test', due_date=timezone.now()
        )
        inv2 = Invoice.objects.create(
            user=user, amount=Decimal('200'), description='Test', due_date=timezone.now()
        )
        
        # Both invoices should have different invoice numbers
        self.assertNotEqual(
            inv1.invoice_number,
            inv2.invoice_number,
            "REGRESSION ISSUE: Invoice numbers are not unique"
        )


class ForeignKeyConstraintRegressionTests(TestCase):
    """
    Regression tests for foreign key constraints.
    
    These tests verify that:
    - Foreign key relationships are enforced
    - Cascade and SET_NULL behaviors work correctly
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    def test_wallet_user_cascade_delete(self):
        """
        REGRESSION TEST: Wallet should be deleted when user is deleted.
        
        Verifies: CASCADE delete behavior.
        Reports: Orphan wallets after user deletion.
        """
        from payments.models import Wallet
        
        user = User.objects.create_user(username='cascade_user', email='cascade@test.com', password='Pass123!')
        Wallet.objects.create(user=user, balance=Decimal('100'))
        
        user_id = user.pk
        user.delete()
        
        # Wallet should be deleted
        self.assertFalse(
            Wallet.objects.filter(user_id=user_id).exists(),
            "REGRESSION ISSUE: Wallet not deleted when user deleted (orphan data)"
        )
    
    def test_userprofile_user_cascade_delete(self):
        """
        REGRESSION TEST: UserProfile should be deleted when user is deleted.
        
        Verifies: CASCADE delete behavior.
        Reports: Orphan profiles after user deletion.
        """
        from accounts.models import UserProfile
        
        user = User.objects.create_user(username='profile_cascade', email='profile_cascade@test.com', password='Pass123!')
        UserProfile.objects.create(user=user)
        
        user_id = user.pk
        user.delete()
        
        # Profile should be deleted
        self.assertFalse(
            UserProfile.objects.filter(user_id=user_id).exists(),
            "REGRESSION ISSUE: UserProfile not deleted when user deleted"
        )
    
    def test_subscription_plan_protect_delete(self):
        """
        REGRESSION TEST: SubscriptionPlan should be protected from deletion if subscriptions exist.
        
        Verifies: PROTECT delete behavior.
        Reports: Plans deleted while active subscriptions exist.
        """
        from payments.models import SubscriptionPlan, UserSubscription
        from django.db.models import ProtectedError
        
        user = User.objects.create_user(username='protect_user', email='protect@test.com', password='Pass123!')
        plan = SubscriptionPlan.objects.create(
            name='Protected Plan', slug='protected-plan', description='Test', price=Decimal('9.99'), duration_days=30
        )
        UserSubscription.objects.create(user=user, plan=plan)
        
        with self.assertRaises(ProtectedError, msg="REGRESSION ISSUE: Plan deleted with active subscriptions"):
            plan.delete()


class OneToOneConstraintRegressionTests(TestCase):
    """
    Regression tests for OneToOne constraints.
    
    These tests verify that:
    - OneToOne relationships are enforced
    - Duplicate relationships are rejected
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    def test_userprofile_onetoone(self):
        """
        REGRESSION TEST: Each user should have only one profile.
        
        Verifies: OneToOne constraint on UserProfile.
        Reports: Multiple profiles per user allowed.
        """
        from accounts.models import UserProfile
        
        user = User.objects.create_user(username='onetoone_user', email='onetoone@test.com', password='Pass123!')
        UserProfile.objects.create(user=user)
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Multiple profiles per user allowed"):
            UserProfile.objects.create(user=user)
    
    def test_wallet_onetoone(self):
        """
        REGRESSION TEST: Each user should have only one wallet.
        
        Verifies: OneToOne constraint on Wallet.
        Reports: Multiple wallets per user allowed.
        """
        from payments.models import Wallet
        
        user = User.objects.create_user(username='wallet_onetoone', email='wallet_onetoone@test.com', password='Pass123!')
        Wallet.objects.create(user=user)
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Multiple wallets per user allowed"):
            Wallet.objects.create(user=user)
    
    def test_business_profile_onetoone(self):
        """
        REGRESSION TEST: Each user should have only one business profile.
        
        Verifies: OneToOne constraint on BusinessProfile.
        Reports: Multiple business profiles per user allowed.
        """
        from marketplace.models import BusinessProfile
        
        user = User.objects.create_user(username='bizprof_onetoone', email='bizprof@test.com', password='Pass123!')
        BusinessProfile.objects.create(user=user, company_name='Company 1', industry='Tech')
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Multiple business profiles per user allowed"):
            BusinessProfile.objects.create(user=user, company_name='Company 2', industry='Finance')
    
    def test_kyc_level_onetoone(self):
        """
        REGRESSION TEST: Each user should have only one KYC level.
        
        Verifies: OneToOne constraint on KYCVerificationLevel.
        Reports: Multiple KYC levels per user allowed.
        """
        from kyc.models import KYCVerificationLevel
        
        user = User.objects.create_user(username='kyc_onetoone', email='kyc_onetoone@test.com', password='Pass123!')
        KYCVerificationLevel.objects.create(user=user)
        
        with self.assertRaises(IntegrityError, msg="REGRESSION ISSUE: Multiple KYC levels per user allowed"):
            KYCVerificationLevel.objects.create(user=user)


class DataValidationConstraintRegressionTests(TestCase):
    """
    Regression tests for data validation constraints.
    
    These tests verify that:
    - Field validators work correctly
    - Invalid data is rejected
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.disconnect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        try:
            post_save.connect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.create_user_wallet, sender=User)
        except Exception:
            pass
        try:
            post_save.connect(payments_signals.save_user_wallet, sender=User)
        except Exception:
            pass
    
    def test_wallet_balance_min_value(self):
        """
        REGRESSION TEST: Wallet balance should not be negative.
        
        Verifies: MinValueValidator on wallet balance.
        Reports: Negative balances allowed.
        """
        from payments.models import Wallet
        from django.core.exceptions import ValidationError
        
        user = User.objects.create_user(username='balance_min', email='balance_min@test.com', password='Pass123!')
        wallet = Wallet(user=user, balance=Decimal('-100'))
        
        with self.assertRaises(ValidationError, msg="REGRESSION ISSUE: Negative wallet balance allowed"):
            wallet.full_clean()
    
    def test_subscription_plan_price_min_value(self):
        """
        REGRESSION TEST: Subscription plan price should not be negative.
        
        Verifies: MinValueValidator on plan price.
        Reports: Negative prices allowed.
        """
        from payments.models import SubscriptionPlan
        from django.core.exceptions import ValidationError
        
        plan = SubscriptionPlan(
            name='Negative Plan', slug='neg-plan', description='Test', 
            price=Decimal('-9.99'), duration_days=30
        )
        
        with self.assertRaises(ValidationError, msg="REGRESSION ISSUE: Negative plan price allowed"):
            plan.full_clean()
    
    def test_equity_percentage_max_value(self):
        """
        REGRESSION TEST: Equity percentage should not exceed 100%.
        
        Verifies: MaxValueValidator on equity fields.
        Reports: Equity over 100% allowed.
        """
        from marketplace.models import BusinessProfile
        from django.core.exceptions import ValidationError
        
        user = User.objects.create_user(username='equity_max', email='equity_max@test.com', password='Pass123!')
        profile = BusinessProfile(
            user=user, company_name='Test', industry='Tech',
            equity_offered=Decimal('150')  # Over 100%
        )
        
        with self.assertRaises(ValidationError, msg="REGRESSION ISSUE: Equity over 100% allowed"):
            profile.full_clean()

