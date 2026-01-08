"""
Regression Tests for Critical Business Paths

These tests verify that critical end-to-end business flows remain intact
after code changes. Tests are designed to FIND and REPORT issues.

Tested Flows:
- Complete user registration flow
- Wallet operation flows
- Subscription lifecycle flow
- Business opportunity flow
- Job application flow
- GDPR compliance flow
- KYC verification flow

Author: Fadhiri
Date: January 2026
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import timedelta

import accounts.models as accounts_models
import audit.signals as audit_signals
import payments.signals as payments_signals
from payments.models import Wallet, SubscriptionPlan, UserSubscription, Invoice, Transaction
from marketplace.models import BusinessProfile, InvestmentOpportunity, JobOpportunity, JobApplication
from gdpr.models import ConsentRecord, DataExportRequest, DataDeletionRequest
from kyc.models import KYCDocument, KYCVerificationLevel
from onboarding.models import OnboardingProgress, EmailVerificationToken


class UserRegistrationFlowRegressionTests(TestCase):
    """
    Regression tests for complete user registration flow.
    
    These tests verify the end-to-end registration process including:
    - User creation
    - Profile creation
    - Onboarding progress
    - Email verification token
    """
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        try:
            post_save.disconnect(accounts_models.create_user_profile, sender=User)
        except Exception:
            pass
        try:
            user_logged_in.disconnect(audit_signals.log_user_login)
        except Exception:
            pass
        try:
            user_logged_out.disconnect(audit_signals.log_user_logout)
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
            user_logged_in.connect(audit_signals.log_user_login)
        except Exception:
            pass
        try:
            user_logged_out.connect(audit_signals.log_user_logout)
        except Exception:
            pass
    
    def test_user_creation_flow(self):
        """
        REGRESSION TEST: User creation flow should work completely.
        
        Verifies: Full user creation including related objects.
        Reports: Broken user creation flow.
        """
        # Step 1: Create user
        user = User.objects.create_user(
            username='flow_user',
            email='flow@test.com',
            password='FlowPass123!',
            first_name='Flow',
            last_name='User'
        )
        
        self.assertIsNotNone(user.pk, "REGRESSION ISSUE: User not created")
        self.assertEqual(user.username, 'flow_user', "REGRESSION ISSUE: Username not saved")
        
        # Step 2: Create profile (manually since signal is disconnected)
        from accounts.models import UserProfile, Category
        category = Category.objects.create(
            name='Flow Category',
            slug='flow-category',
            description='Test category'
        )
        profile = UserProfile.objects.create(
            user=user,
            category=category
        )
        
        self.assertIsNotNone(profile.pk, "REGRESSION ISSUE: Profile not created")
        self.assertEqual(profile.user, user, "REGRESSION ISSUE: Profile not linked to user")
        
        # Step 3: Create onboarding progress
        onboarding = OnboardingProgress.objects.create(user=user)
        
        self.assertIsNotNone(onboarding.pk, "REGRESSION ISSUE: Onboarding progress not created")
        self.assertFalse(onboarding.email_verified, "REGRESSION ISSUE: Email should not be verified initially")
        
        # Step 4: Create verification token
        token = EmailVerificationToken.objects.create(user=user)
        
        self.assertIsNotNone(token.pk, "REGRESSION ISSUE: Verification token not created")
        self.assertTrue(token.is_valid(), "REGRESSION ISSUE: New token should be valid")
    
    def test_email_verification_flow(self):
        """
        REGRESSION TEST: Email verification flow should work.
        
        Verifies: Token creation, validation, and marking as used.
        Reports: Broken email verification.
        """
        user = User.objects.create_user(
            username='verify_user',
            email='verify@test.com',
            password='VerifyPass123!'
        )
        
        # Create token
        token = EmailVerificationToken.objects.create(user=user)
        self.assertTrue(token.is_valid(), "REGRESSION ISSUE: New token should be valid")
        
        # Verify token is valid
        token_value = token.token
        found_token = EmailVerificationToken.objects.filter(token=token_value).first()
        self.assertIsNotNone(found_token, "REGRESSION ISSUE: Token not retrievable")
        
        # Mark token as used
        found_token.mark_used()
        found_token.refresh_from_db()
        self.assertTrue(found_token.is_used, "REGRESSION ISSUE: Token not marked as used")
        self.assertFalse(found_token.is_valid(), "REGRESSION ISSUE: Used token still valid")


class WalletOperationsFlowRegressionTests(TestCase):
    """
    Regression tests for wallet operation flows.
    
    These tests verify:
    - Deposit flow
    - Payment flow
    - Balance tracking
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
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='wallet_flow_user',
            email='wallet_flow@test.com',
            password='WalletPass123!'
        )
        self.wallet = Wallet.objects.create(user=self.user, balance=Decimal('0'))
    
    def test_deposit_flow(self):
        """
        REGRESSION TEST: Deposit flow should work completely.
        
        Verifies: Wallet credit and transaction creation.
        Reports: Broken deposit flow.
        """
        initial_balance = self.wallet.balance
        deposit_amount = Decimal('100.00')
        
        # Step 1: Credit wallet
        result = self.wallet.credit(deposit_amount)
        self.assertTrue(result, "REGRESSION ISSUE: Wallet credit failed")
        
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            initial_balance + deposit_amount,
            "REGRESSION ISSUE: Balance not updated correctly after deposit"
        )
        
        # Step 2: Create transaction record
        transaction = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='deposit',
            amount=deposit_amount,
            payment_gateway='manual',
            status='completed'
        )
        
        self.assertIsNotNone(transaction.transaction_id, "REGRESSION ISSUE: Transaction ID not generated")
        self.assertEqual(transaction.status, 'completed', "REGRESSION ISSUE: Transaction status not set")
    
    def test_payment_flow(self):
        """
        REGRESSION TEST: Payment flow should work completely.
        
        Verifies: Wallet debit and transaction creation.
        Reports: Broken payment flow.
        """
        # Setup: Fund wallet first
        self.wallet.credit(Decimal('200.00'))
        self.wallet.refresh_from_db()
        initial_balance = self.wallet.balance
        
        payment_amount = Decimal('75.00')
        
        # Step 1: Check sufficient balance
        has_balance = self.wallet.has_sufficient_balance(payment_amount)
        self.assertTrue(has_balance, "REGRESSION ISSUE: Balance check failed incorrectly")
        
        # Step 2: Debit wallet
        result = self.wallet.debit(payment_amount)
        self.assertTrue(result, "REGRESSION ISSUE: Wallet debit failed")
        
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            initial_balance - payment_amount,
            "REGRESSION ISSUE: Balance not updated correctly after payment"
        )
        
        # Step 3: Create transaction record
        transaction = Transaction.objects.create(
            user=self.user,
            wallet=self.wallet,
            transaction_type='subscription_payment',
            amount=payment_amount,
            payment_gateway='wallet',
            status='completed'
        )
        
        self.assertEqual(transaction.status, 'completed', "REGRESSION ISSUE: Payment transaction not completed")
    
    def test_insufficient_balance_flow(self):
        """
        REGRESSION TEST: Insufficient balance should prevent payment.
        
        Verifies: Balance validation prevents overdraft.
        Reports: Overdraft allowed (financial risk).
        """
        initial_balance = self.wallet.balance  # Should be 0
        payment_amount = Decimal('100.00')
        
        # Check should fail
        has_balance = self.wallet.has_sufficient_balance(payment_amount)
        self.assertFalse(has_balance, "REGRESSION ISSUE: Insufficient balance check passed incorrectly")
        
        # Debit should fail
        result = self.wallet.debit(payment_amount)
        self.assertFalse(result, "REGRESSION ISSUE: Debit succeeded with insufficient balance")
        
        self.wallet.refresh_from_db()
        self.assertEqual(
            self.wallet.balance,
            initial_balance,
            "REGRESSION ISSUE: Balance changed despite failed debit"
        )


class SubscriptionLifecycleFlowRegressionTests(TestCase):
    """
    Regression tests for subscription lifecycle flow.
    
    These tests verify:
    - Subscription creation
    - Activation
    - Renewal
    - Cancellation
    - Expiration
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
            username='sub_flow_user',
            email='sub_flow@test.com',
            password='SubPass123!'
        )
        self.plan = SubscriptionPlan.objects.create(
            name='Flow Plan',
            slug='flow-plan',
            description='Test plan',
            price=Decimal('29.99'),
            duration_days=30
        )
    
    def test_subscription_creation_to_activation_flow(self):
        """
        REGRESSION TEST: Subscription creation and activation flow.
        
        Verifies: Complete subscription setup process.
        Reports: Broken subscription flow.
        """
        # Step 1: Create subscription (pending)
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan
        )
        
        self.assertEqual(subscription.status, 'pending', "REGRESSION ISSUE: New subscription not pending")
        self.assertIsNone(subscription.start_date, "REGRESSION ISSUE: Start date set before activation")
        
        # Step 2: Activate subscription
        subscription.activate()
        subscription.refresh_from_db()
        
        self.assertEqual(subscription.status, 'active', "REGRESSION ISSUE: Subscription not activated")
        self.assertIsNotNone(subscription.start_date, "REGRESSION ISSUE: Start date not set")
        self.assertIsNotNone(subscription.end_date, "REGRESSION ISSUE: End date not set")
        
        # Step 3: Verify validity
        self.assertTrue(subscription.is_valid(), "REGRESSION ISSUE: Active subscription not valid")
        self.assertGreater(subscription.days_remaining(), 0, "REGRESSION ISSUE: No days remaining")
    
    def test_subscription_cancellation_flow(self):
        """
        REGRESSION TEST: Subscription cancellation flow.
        
        Verifies: Complete cancellation process.
        Reports: Broken cancellation flow.
        """
        # Setup: Create and activate subscription
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan
        )
        subscription.activate()
        
        # Verify auto_renew is True initially
        self.assertTrue(subscription.auto_renew, "REGRESSION ISSUE: auto_renew not True by default")
        
        # Cancel subscription
        subscription.cancel()
        subscription.refresh_from_db()
        
        self.assertEqual(subscription.status, 'cancelled', "REGRESSION ISSUE: Subscription not cancelled")
        self.assertFalse(subscription.auto_renew, "REGRESSION ISSUE: auto_renew not disabled on cancel")
    
    def test_subscription_expiration_detection(self):
        """
        REGRESSION TEST: Subscription expiration detection.
        
        Verifies: Expired subscriptions are detected correctly.
        Reports: Expired subscriptions still marked valid.
        """
        subscription = UserSubscription.objects.create(
            user=self.user,
            plan=self.plan
        )
        subscription.activate()
        
        # Manually set end_date to past
        subscription.end_date = timezone.now() - timedelta(days=1)
        subscription.save()
        
        self.assertFalse(subscription.is_valid(), "REGRESSION ISSUE: Expired subscription marked valid")
        self.assertEqual(subscription.days_remaining(), 0, "REGRESSION ISSUE: Days remaining for expired subscription")


class BusinessOpportunityFlowRegressionTests(TestCase):
    """
    Regression tests for business opportunity flow.
    
    These tests verify:
    - Business profile creation
    - Investment opportunity posting
    - Opportunity viewing and tracking
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
        self.business_user = User.objects.create_user(
            username='business_flow',
            email='business_flow@test.com',
            password='BusinessPass123!'
        )
    
    def test_business_profile_to_opportunity_flow(self):
        """
        REGRESSION TEST: Business profile to opportunity posting flow.
        
        Verifies: Complete business opportunity creation process.
        Reports: Broken business flow.
        """
        # Step 1: Create business profile
        profile = BusinessProfile.objects.create(
            user=self.business_user,
            company_name='Flow Business Inc',
            industry='Technology',
            company_size='11-50',
            funding_stage='seed'
        )
        
        self.assertIsNotNone(profile.pk, "REGRESSION ISSUE: Business profile not created")
        
        # Step 2: Create investment opportunity
        opportunity = InvestmentOpportunity.objects.create(
            business=self.business_user,
            title='Series A Investment Round',
            description='Seeking investment for expansion',
            amount_seeking=Decimal('1000000'),
            minimum_investment=Decimal('50000'),
            equity_percentage=Decimal('15'),
            industry='Technology',
            stage='seed'
        )
        
        self.assertIsNotNone(opportunity.pk, "REGRESSION ISSUE: Investment opportunity not created")
        self.assertIsNotNone(opportunity.slug, "REGRESSION ISSUE: Slug not auto-generated")
        self.assertEqual(opportunity.status, 'open', "REGRESSION ISSUE: Default status not 'open'")
        
        # Step 3: Track views
        initial_views = opportunity.views
        opportunity.increment_views()
        opportunity.refresh_from_db()
        
        self.assertEqual(
            opportunity.views,
            initial_views + 1,
            "REGRESSION ISSUE: View tracking not working"
        )


class JobApplicationFlowRegressionTests(TestCase):
    """
    Regression tests for job application flow.
    
    These tests verify:
    - Job posting
    - Application submission
    - Status tracking
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
        self.employer = User.objects.create_user(
            username='employer_flow',
            email='employer_flow@test.com',
            password='EmployerPass123!'
        )
        self.applicant = User.objects.create_user(
            username='applicant_flow',
            email='applicant_flow@test.com',
            password='ApplicantPass123!'
        )
    
    def test_job_posting_to_application_flow(self):
        """
        REGRESSION TEST: Job posting to application flow.
        
        Verifies: Complete job application process.
        Reports: Broken job application flow.
        """
        # Step 1: Create job posting
        job = JobOpportunity.objects.create(
            business=self.employer,
            title='Senior Software Engineer',
            description='Join our growing team',
            requirements='5+ years Python experience',
            responsibilities='Lead development of core features',
            location='New York, NY',
            job_type='full_time',
            experience_level='senior'
        )
        
        self.assertIsNotNone(job.pk, "REGRESSION ISSUE: Job not created")
        self.assertIsNotNone(job.slug, "REGRESSION ISSUE: Job slug not generated")
        self.assertEqual(job.status, 'open', "REGRESSION ISSUE: Job not open by default")
        
        # Step 2: Submit application
        application = JobApplication.objects.create(
            job=job,
            applicant=self.applicant,
            cover_letter='I am very interested in this position...',
            resume='resumes/applicant_resume.pdf'
        )
        
        self.assertIsNotNone(application.pk, "REGRESSION ISSUE: Application not created")
        self.assertEqual(application.status, 'pending', "REGRESSION ISSUE: Application not pending")
        
        # Step 3: Update application status
        application.status = 'reviewing'
        application.save()
        application.refresh_from_db()
        
        self.assertEqual(application.status, 'reviewing', "REGRESSION ISSUE: Status update failed")


class GDPRComplianceFlowRegressionTests(TestCase):
    """
    Regression tests for GDPR compliance flow.
    
    These tests verify:
    - Consent management
    - Data export requests
    - Data deletion requests
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
            username='gdpr_flow',
            email='gdpr_flow@test.com',
            password='GDPRPass123!'
        )
    
    def test_consent_management_flow(self):
        """
        REGRESSION TEST: Consent management flow.
        
        Verifies: Complete consent lifecycle.
        Reports: Broken consent management.
        """
        # Step 1: Create consent record
        consent = ConsentRecord.objects.create(
            user=self.user,
            consent_type='privacy_policy',
            version='1.0'
        )
        
        self.assertFalse(consent.is_given, "REGRESSION ISSUE: Consent given by default")
        
        # Step 2: Give consent
        consent.give_consent(ip_address='192.168.1.1', user_agent='TestBrowser')
        consent.refresh_from_db()
        
        self.assertTrue(consent.is_given, "REGRESSION ISSUE: Consent not given")
        self.assertIsNotNone(consent.given_at, "REGRESSION ISSUE: given_at not set")
        
        # Step 3: Withdraw consent
        consent.withdraw_consent()
        consent.refresh_from_db()
        
        self.assertFalse(consent.is_given, "REGRESSION ISSUE: Consent not withdrawn")
        self.assertIsNotNone(consent.withdrawn_at, "REGRESSION ISSUE: withdrawn_at not set")
    
    def test_data_export_request_flow(self):
        """
        REGRESSION TEST: Data export request flow.
        
        Verifies: Complete export request lifecycle.
        Reports: Broken export request handling.
        """
        # Step 1: Create export request
        request = DataExportRequest.objects.create(
            user=self.user,
            export_format='json'
        )
        
        self.assertEqual(request.status, 'pending', "REGRESSION ISSUE: Request not pending")
        
        # Step 2: Mark as processing
        request.mark_processing()
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'processing', "REGRESSION ISSUE: Request not processing")
        
        # Step 3: Mark as completed
        request.mark_completed('/exports/data.json', 1024)
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'completed', "REGRESSION ISSUE: Request not completed")
        self.assertIsNotNone(request.expires_at, "REGRESSION ISSUE: Expiry not set")
    
    def test_data_deletion_request_flow(self):
        """
        REGRESSION TEST: Data deletion request flow with grace period.
        
        Verifies: Complete deletion request lifecycle.
        Reports: Broken deletion request handling.
        """
        # Step 1: Create deletion request
        request = DataDeletionRequest.objects.create(
            user=self.user,
            reason='No longer using service'
        )
        
        self.assertEqual(request.status, 'pending', "REGRESSION ISSUE: Request not pending")
        self.assertEqual(request.username, 'gdpr_flow', "REGRESSION ISSUE: Username not captured")
        
        # Step 2: Start grace period
        request.start_grace_period()
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'grace_period', "REGRESSION ISSUE: Grace period not started")
        self.assertIsNotNone(request.grace_period_end, "REGRESSION ISSUE: Grace period end not set")
        self.assertTrue(request.is_in_grace_period, "REGRESSION ISSUE: Not in grace period")
        
        # Step 3: Cancel request (user changed mind)
        request.cancel_request()
        request.refresh_from_db()
        
        self.assertEqual(request.status, 'cancelled', "REGRESSION ISSUE: Request not cancelled")


class KYCVerificationFlowRegressionTests(TestCase):
    """
    Regression tests for KYC verification flow.
    
    These tests verify:
    - Document upload
    - Document verification
    - Level updates
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
            username='kyc_flow',
            email='kyc_flow@test.com',
            password='KYCPass123!'
        )
        self.staff_user = User.objects.create_user(
            username='kyc_staff_flow',
            email='kyc_staff_flow@test.com',
            password='StaffPass123!',
            is_staff=True
        )
    
    def test_document_upload_to_verification_flow(self):
        """
        REGRESSION TEST: Document upload to verification flow.
        
        Verifies: Complete KYC document lifecycle.
        Reports: Broken KYC flow.
        """
        # Step 1: Upload document
        doc = KYCDocument.objects.create(
            user=self.user,
            document_type='national_id',
            document_file='kyc_documents/id_doc.pdf'
        )
        
        self.assertEqual(doc.status, 'pending', "REGRESSION ISSUE: Document not pending")
        self.assertTrue(doc.requires_review, "REGRESSION ISSUE: Document not requiring review")
        
        # Step 2: Mark under review
        doc.mark_under_review(self.staff_user)
        doc.refresh_from_db()
        
        self.assertEqual(doc.status, 'under_review', "REGRESSION ISSUE: Document not under review")
        
        # Step 3: Approve document
        doc.approve(self.staff_user, 'Document verified successfully')
        doc.refresh_from_db()
        
        self.assertEqual(doc.status, 'approved', "REGRESSION ISSUE: Document not approved")
        self.assertTrue(doc.is_verified, "REGRESSION ISSUE: Document not marked verified")
    
    def test_verification_level_progression_flow(self):
        """
        REGRESSION TEST: KYC verification level progression.
        
        Verifies: Level updates based on verifications.
        Reports: Broken level progression.
        """
        # Step 1: Create verification level (basic by default)
        level = KYCVerificationLevel.objects.create(user=self.user)
        
        self.assertEqual(level.level, 'basic', "REGRESSION ISSUE: Default level not basic")
        self.assertFalse(level.can_invest, "REGRESSION ISSUE: can_invest True for basic")
        
        # Step 2: Update to standard (email + identity)
        level.email_verified = True
        level.identity_verified = True
        level.update_level()
        level.refresh_from_db()
        
        self.assertEqual(level.level, 'standard', "REGRESSION ISSUE: Level not updated to standard")
        self.assertEqual(level.transaction_limit_daily, Decimal('1000'), "REGRESSION ISSUE: Standard limit incorrect")
        
        # Step 3: Update to enhanced
        level.phone_verified = True
        level.address_verified = True
        level.update_level()
        level.refresh_from_db()
        
        self.assertEqual(level.level, 'enhanced', "REGRESSION ISSUE: Level not updated to enhanced")
        self.assertTrue(level.can_invest, "REGRESSION ISSUE: can_invest not enabled for enhanced")
        
        # Step 4: Update to premium
        level.business_verified = True
        level.update_level()
        level.refresh_from_db()
        
        self.assertEqual(level.level, 'premium', "REGRESSION ISSUE: Level not updated to premium")
        self.assertTrue(level.can_receive_investment, "REGRESSION ISSUE: can_receive_investment not enabled")

