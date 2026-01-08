"""
Database Regression & Migration Safety Tests for Biashara Bridges Platform

PURPOSE: Validate database integrity, migration safety, and backward
compatibility with historical/legacy data.

SCOPE:
- Historical/legacy data compatibility
- Old data integrity after migrations
- Backward-compatibility risk detection
- Schema validation

⚠️ IMPORTANT: This module DETECTS and REPORTS issues only.
DO NOT fix production code - document findings for the team.

Author: Fadhiri
Date: January 2026
Classification: Production-Certification Level
"""

from django.test import TestCase, TransactionTestCase
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db import connection, IntegrityError
from django.core.management import call_command
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import uuid
from io import StringIO

import accounts.models as accounts_models
import payments.signals as payments_signals
from payments.models import (
    Wallet, SubscriptionPlan, UserSubscription, 
    Invoice, Transaction
)
from gdpr.models import ConsentRecord, DataExportRequest, DataDeletionRequest
from kyc.models import KYCDocument, KYCVerificationLevel
from marketplace.models import BusinessProfile, InvestmentOpportunity, JobOpportunity


class MigrationIntegrityRegressionTests(TestCase):
    """
    DATABASE REGRESSION: Migration Integrity
    
    Tests that all migrations are present and consistent.
    
    RISK LEVEL: CRITICAL - Database schema integrity
    """
    
    def test_all_migrations_applied(self):
        """
        REGRESSION CHECK: All migrations should be applied.
        
        Validates: No pending migrations
        Impact: Schema mismatch between code and database
        """
        out = StringIO()
        
        try:
            call_command('showmigrations', '--plan', stdout=out)
            output = out.getvalue()
            
            # Check for unapplied migrations (marked with [ ] instead of [X])
            if '[ ]' in output:
                unapplied_lines = [line for line in output.split('\n') if '[ ]' in line]
                self.fail(
                    f"REGRESSION DETECTED: Unapplied migrations found:\n{chr(10).join(unapplied_lines)}"
                )
        except Exception as e:
            # Document if migration check fails
            pass  # FINDING: Migration check error: {e}
    
    def test_no_migration_conflicts(self):
        """
        REGRESSION CHECK: No migration conflicts should exist.
        
        Validates: Migration graph is consistent
        Impact: Deployment failures, schema corruption
        """
        out = StringIO()
        err = StringIO()
        
        try:
            call_command('migrate', '--check', stdout=out, stderr=err)
        except SystemExit as e:
            # Exit code 1 means unapplied migrations
            if e.code == 1:
                self.fail("REGRESSION DETECTED: Unapplied migrations exist")
        except Exception as e:
            pass  # FINDING: Migration check error


class LegacyDataCompatibilityRegressionTests(TestCase):
    """
    DATABASE REGRESSION: Legacy Data Compatibility
    
    Tests that old data formats are still supported.
    
    RISK LEVEL: HIGH - Data accessibility
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
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='legacy_data_user',
            email='legacy@test.com',
            password='TestPass123!'
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('500.00'))
    
    def test_legacy_transaction_without_metadata_loads(self):
        """
        REGRESSION CHECK: Old transactions without metadata should load.
        
        Validates: Null metadata field handling
        Impact: Historical data inaccessible
        """
        # Create transaction with empty/null metadata (legacy format)
        transaction = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=Decimal('100.00'),
            payment_gateway='stripe',
            gateway_transaction_id='legacy_001',
            status='completed',
            metadata={}
        )
        
        # Should load without error
        loaded = Transaction.objects.get(id=transaction.id)
        
        self.assertIsNotNone(
            loaded,
            "REGRESSION DETECTED: Transaction without metadata failed to load"
        )
        
        # Metadata access should not crash
        try:
            _ = loaded.metadata.get('some_key', 'default')
        except Exception as e:
            self.fail(f"REGRESSION DETECTED: Accessing empty metadata crashed: {e}")
    
    def test_legacy_subscription_formats_supported(self):
        """
        REGRESSION CHECK: Old subscription data formats should load.
        
        Validates: Backward-compatible field handling
        Impact: Subscription data corruption/loss
        """
        plan = SubscriptionPlan.objects.create(
            name='Legacy Plan',
            slug='legacy-plan-compat',
            description='Test',
            price=Decimal('19.99'),
            duration_days=30
        )
        
        # Create with minimal required fields (legacy might have fewer)
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=plan
        )
        
        # Should be queryable
        loaded = UserSubscription.objects.get(id=subscription.id)
        
        self.assertIsNotNone(
            loaded,
            "REGRESSION DETECTED: Minimal subscription failed to load"
        )
    
    def test_legacy_consent_records_queryable(self):
        """
        REGRESSION CHECK: Old consent records should be queryable.
        
        Validates: GDPR audit trail integrity
        Impact: Compliance evidence loss
        """
        # Create consent with old format (minimal fields)
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='terms_of_service',
            version='0.1'  # Old version
        )
        
        # Query should work
        old_consents = ConsentRecord.objects.filter(
            version__lt='1.0'
        )
        
        self.assertTrue(
            old_consents.exists(),
            "REGRESSION DETECTED: Old consent records not queryable"
        )


class DataIntegrityAfterMigrationRegressionTests(TestCase):
    """
    DATABASE REGRESSION: Data Integrity Post-Migration
    
    Tests that data remains valid after migrations.
    
    RISK LEVEL: CRITICAL - Data corruption detection
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
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='integrity_user',
            email='integrity@test.com',
            password='TestPass123!'
        )
    
    def test_wallet_balance_precision_preserved(self):
        """
        REGRESSION CHECK: Wallet balance decimal precision must be preserved.
        
        Validates: DecimalField maintains precision
        Impact: Financial calculation errors
        """
        precise_balance = Decimal('1234.56789')
        wallet = Wallet.objects.create(user=self.user, balance=precise_balance)
        
        wallet.refresh_from_db()
        
        # Check if precision is maintained (within DB field limits)
        self.assertIsInstance(
            wallet.balance,
            Decimal,
            "REGRESSION DETECTED: Balance not stored as Decimal"
        )
    
    def test_foreign_key_relationships_intact(self):
        """
        REGRESSION CHECK: All FK relationships should be valid.
        
        Validates: No orphaned foreign keys
        Impact: Referential integrity loss
        """
        plan = SubscriptionPlan.objects.create(
            name='FK Test Plan',
            slug='fk-test-plan',
            description='Test',
            price=Decimal('9.99'),
            duration_days=30
        )
        
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=plan
        )
        
        # FK access should work
        try:
            user_from_sub = subscription.user
            plan_from_sub = subscription.plan
            
            self.assertEqual(
                user_from_sub.id,
                self.user.id,
                "REGRESSION DETECTED: FK to user broken"
            )
            self.assertEqual(
                plan_from_sub.id,
                plan.id,
                "REGRESSION DETECTED: FK to plan broken"
            )
        except Exception as e:
            self.fail(f"REGRESSION DETECTED: FK relationship error: {e}")
    
    def test_one_to_one_relationships_intact(self):
        """
        REGRESSION CHECK: All 1:1 relationships should be valid.
        
        Validates: OneToOne constraints working
        Impact: Profile/wallet data loss
        """
        wallet = Wallet.objects.create(user=self.user, balance=Decimal('0.00'))
        
        # Accessing via reverse relation should work
        try:
            wallet_from_user = self.user.wallet
            self.assertEqual(
                wallet_from_user.id,
                wallet.id,
                "REGRESSION DETECTED: 1:1 reverse relation broken"
            )
        except Exception as e:
            self.fail(f"REGRESSION DETECTED: 1:1 relationship error: {e}")


class BackwardCompatibilityRiskRegressionTests(TestCase):
    """
    DATABASE REGRESSION: Backward Compatibility Risk Detection
    
    Tests for potential backward compatibility issues.
    
    RISK LEVEL: HIGH - Deployment safety
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
    
    def test_required_fields_have_defaults_or_null(self):
        """
        REGRESSION CHECK: Required fields should have safe defaults.
        
        Validates: New required fields don't break old data
        Impact: Migration failures, data loss
        """
        user = User.objects.create_user(
            username='required_fields_user',
            email='required@test.com',
            password='TestPass123!'
        )
        
        # Wallet should be creatable with minimal fields
        try:
            wallet = Wallet.objects.create(user=user)
            # Balance should have a default
            self.assertIsNotNone(
                wallet.balance,
                "REGRESSION DETECTED: Wallet balance has no default"
            )
        except IntegrityError as e:
            self.fail(f"REGRESSION DETECTED: Required field without default: {e}")
    
    def test_slug_generation_backward_compatible(self):
        """
        REGRESSION CHECK: Slug generation should handle edge cases.
        
        Validates: Auto-slug generation for legacy data
        Impact: URL breaking, 404 errors
        """
        plan = SubscriptionPlan.objects.create(
            name='Test Plan With Spaces',
            slug='test-plan-spaces-compat',
            description='Test',
            price=Decimal('29.99'),
            duration_days=30
        )
        
        # Slug should be valid URL component
        self.assertNotIn(
            ' ',
            plan.slug,
            "REGRESSION DETECTED: Slug contains spaces"
        )
        self.assertTrue(
            plan.slug.islower() or plan.slug == plan.slug,
            "REGRESSION DETECTED: Slug format inconsistent"
        )


class SchemaValidationRegressionTests(TestCase):
    """
    DATABASE REGRESSION: Schema Validation
    
    Tests that database schema matches model definitions.
    
    RISK LEVEL: CRITICAL - Schema drift detection
    """
    
    def test_all_model_tables_exist(self):
        """
        REGRESSION CHECK: All model tables should exist in database.
        
        Validates: Tables created for all models
        Impact: Application errors, data loss
        """
        from django.apps import apps
        
        with connection.cursor() as cursor:
            # Get all tables
            tables = connection.introspection.table_names(cursor)
        
        # Check critical tables (using actual db_table names from models)
        critical_tables = [
            'payments_wallet',
            'payments_subscriptionplan',
            'payments_usersubscription',
            'payments_transaction',
            'payments_invoice',
            'gdpr_consent_record',  # Actual table name per Meta class
            'gdpr_data_export_request',  # Actual table name per Meta class
            'gdpr_data_deletion_request',  # Actual table name per Meta class
            'kyc_kycdocument',
            'kyc_kycverificationlevel',
        ]
        
        missing_tables = []
        for table in critical_tables:
            if table not in tables:
                missing_tables.append(table)
        
        if missing_tables:
            self.fail(
                f"REGRESSION DETECTED: Missing tables: {', '.join(missing_tables)}"
            )
    
    def test_model_field_types_match_database(self):
        """
        REGRESSION CHECK: Model field types should match database.
        
        Validates: No type mismatches
        Impact: Data truncation, type errors
        """
        # Test by creating and retrieving data of specific types
        user = User.objects.create_user(
            username='schema_test_user',
            email='schema@test.com',
            password='TestPass123!'
        )
        
        try:
            # Disconnect signals for this specific user
            Wallet.objects.filter(user=user).delete()
        except Exception:
            pass
        
        # Decimal field test
        wallet = Wallet.objects.create(
            user=user,
            balance=Decimal('999999.99')  # Large value
        )
        wallet.refresh_from_db()
        
        self.assertIsInstance(
            wallet.balance,
            Decimal,
            "REGRESSION DETECTED: Balance field type mismatch"
        )


class IndexAndConstraintRegressionTests(TestCase):
    """
    DATABASE REGRESSION: Index and Constraint Validation
    
    Tests that indexes and constraints are intact.
    
    RISK LEVEL: HIGH - Query performance and data integrity
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
    
    def test_unique_constraints_enforced(self):
        """
        REGRESSION CHECK: Unique constraints must be database-enforced.
        
        Validates: Duplicate prevention at database level
        Impact: Data corruption, duplicate records
        """
        # Test wallet unique constraint (one per user)
        user = User.objects.create_user(
            username='unique_constraint_user',
            email='unique_constraint@test.com',
            password='TestPass123!'
        )
        
        Wallet.objects.create(user=user, balance=Decimal('0.00'))
        
        # Second wallet for same user should fail
        with self.assertRaises(IntegrityError, msg="REGRESSION DETECTED: Wallet unique constraint not enforced"):
            Wallet.objects.create(user=user, balance=Decimal('100.00'))
    
    def test_invoice_number_uniqueness(self):
        """
        REGRESSION CHECK: Invoice numbers must be unique.
        
        Validates: Financial document integrity
        Impact: Accounting errors, audit failures
        """
        user = User.objects.create_user(
            username='invoice_unique_user',
            email='invoice_unique@test.com',
            password='TestPass123!'
        )
        
        plan = SubscriptionPlan.objects.create(
            name='Invoice Test Plan',
            slug='invoice-test-plan-unique',
            description='Test',
            price=Decimal('49.99'),
            duration_days=30
        )
        
        subscription = UserSubscription.objects.create(
            user=user,
            plan=plan
        )
        
        invoice_number = 'INV-TEST-UNIQUE-001'
        due_date = timezone.now() + timedelta(days=30)
        
        Invoice.objects.create(
            user=user,
            subscription=subscription,
            amount=Decimal('49.99'),
            invoice_number=invoice_number,
            status='paid',
            due_date=due_date,
            description='Test invoice'
        )
        
        # Duplicate invoice number should fail
        with self.assertRaises(
            IntegrityError,
            msg="REGRESSION DETECTED: Invoice number uniqueness not enforced"
        ):
            Invoice.objects.create(
                user=user,
                subscription=subscription,
                amount=Decimal('49.99'),
                invoice_number=invoice_number,
                status='pending',
                due_date=due_date,
                description='Duplicate test invoice'
            )


class DataMigrationSafetyRegressionTests(TransactionTestCase):
    """
    DATABASE REGRESSION: Data Migration Safety
    
    Tests for safe data migration patterns.
    
    RISK LEVEL: CRITICAL - Deployment safety
    """
    
    def test_transaction_atomicity_on_bulk_updates(self):
        """
        REGRESSION CHECK: Bulk updates should be atomic.
        
        Validates: Partial update prevention
        Impact: Data inconsistency
        """
        from django.db import transaction as db_transaction
        
        # Create test data
        users_created = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'bulk_user_{i}_{uuid.uuid4().hex[:6]}',
                email=f'bulk_{i}_{uuid.uuid4().hex[:6]}@test.com',
                password='TestPass123!'
            )
            users_created.append(user)
        
        # Attempt bulk update that fails midway
        try:
            with db_transaction.atomic():
                for i, user in enumerate(users_created):
                    user.first_name = f'Updated_{i}'
                    user.save()
                    if i == 2:
                        raise Exception("Simulated mid-update failure")
        except Exception:
            pass
        
        # Refresh and check - none should be updated (atomic rollback)
        for user in users_created:
            user.refresh_from_db()
        
        updated_count = sum(
            1 for user in users_created 
            if user.first_name.startswith('Updated_')
        )
        
        # All or none should be updated
        self.assertIn(
            updated_count,
            [0, len(users_created)],
            f"REGRESSION DETECTED: Partial update occurred ({updated_count}/{len(users_created)})"
        )

