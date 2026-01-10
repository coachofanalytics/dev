"""
Authorization & Access Control (RBAC) Security Tests.
Pillar 2: Authorization & Access Control

Tests:
- Role-based page access (investor, business, individual, staff, admin)
- Staff/admin-only pages rejection
- Object-level permissions (wallet, invoices, KYC docs, marketplace)
- IDOR (Insecure Direct Object Reference) checks
"""

import pytest
from decimal import Decimal
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from accounts.models import Staff, Role, Category, UserProfile
from payments.models import Wallet, Transaction, Invoice, SubscriptionPlan, UserSubscription
from marketplace.models import BusinessProfile, InvestmentOpportunity, JobOpportunity
from kyc.models import KYCDocument
from django.utils import timezone

User = get_user_model()


@pytest.mark.security
class TestRoleBasedAccessControl(TestCase):
    """
    Tests for role-based access control across the application.
    
    SECURITY REQUIREMENT: Users should only access pages appropriate to their role.
    """

    def setUp(self):
        # Create category types
        self.investor_category, _ = Category.objects.get_or_create(
            name='Investor', defaults={'slug': 'investor', 'is_active': True}
        )
        self.business_category, _ = Category.objects.get_or_create(
            name='Business', defaults={'slug': 'business', 'is_active': True}
        )
        self.individual_category, _ = Category.objects.get_or_create(
            name='Individual', defaults={'slug': 'individual', 'is_active': True}
        )
        
        # Create users with different roles
        self.investor_user = User.objects.create_user(
            username='investor_user', password='password123'
        )
        self.business_user = User.objects.create_user(
            username='business_user', password='password123'
        )
        self.individual_user = User.objects.create_user(
            username='individual_user', password='password123'
        )
        self.staff_user = User.objects.create_user(
            username='staff_user', password='password123', is_staff=True
        )
        self.admin_user = User.objects.create_superuser(
            username='admin_user', password='password123', email='admin@test.com'
        )
        
        # Set up profiles
        for user, category in [
            (self.investor_user, self.investor_category),
            (self.business_user, self.business_category),
            (self.individual_user, self.individual_category),
        ]:
            try:
                profile = user.profile
                profile.category = category
                profile.save()
            except UserProfile.DoesNotExist:
                UserProfile.objects.create(user=user, category=category)
        
        # Create staff role
        self.moderator_role = Role.objects.create(
            name='Moderator',
            can_moderate_content=True
        )
        Staff.objects.create(
            user=self.staff_user,
            role=self.moderator_role,
            employee_id='EMP001'
        )

    def test_admin_pages__regular_user__access_denied(self):
        """
        SECURITY TEST: Regular users should not access admin pages.
        
        Risk: Unauthorized admin access leads to full system compromise.
        """
        client = Client()
        client.force_login(self.individual_user)
        
        admin_urls = [
            '/admin/',
            '/admin/auth/user/',
            '/admin/payments/transaction/',
            '/admin/accounts/userprofile/',
        ]
        
        for url in admin_urls:
            response = client.get(url)
            self.assertIn(
                response.status_code, [302, 403],
                f"SECURITY VULNERABILITY: Regular user accessed admin page {url}"
            )
            
            if response.status_code == 302:
                self.assertIn('/admin/login', response.url)

    def test_staff_pages__non_staff_user__access_denied(self):
        """
        SECURITY TEST: Non-staff users should not access staff-only pages.
        
        Risk: Regular users accessing staff pages could view sensitive data.
        """
        client = Client()
        client.force_login(self.individual_user)
        
        staff_urls = [
            '/payments/staff/dashboard/',
            '/payments/staff/transactions/',
            '/payments/staff/fraud-alerts/',
            '/payments/staff/disputes/',
            '/kyc/staff/review/',
        ]
        
        for url in staff_urls:
            response = client.get(url)
            self.assertIn(
                response.status_code, [302, 403, 404],
                f"SECURITY VULNERABILITY: Non-staff user accessed staff page {url}"
            )

    def test_staff_pages__staff_user__access_granted(self):
        """
        SECURITY TEST: Staff users should access staff pages (positive test).
        """
        client = Client()
        client.force_login(self.staff_user)
        
        # These should be accessible to staff
        staff_urls = [
            '/kyc/staff/review/',
        ]
        
        for url in staff_urls:
            response = client.get(url)
            # Should not get 403 (but 404 is acceptable if route doesn't exist)
            if response.status_code == 403:
                pytest.fail(f"Staff user denied access to staff page {url}")


@pytest.mark.security
class TestWalletIDOR(TestCase):
    """
    Tests for Insecure Direct Object Reference in wallet/payment endpoints.
    
    SECURITY REQUIREMENT: Users should only access their own wallet data.
    """

    def setUp(self):
        self.victim = User.objects.create_user(username='victim', password='password123')
        self.attacker = User.objects.create_user(username='attacker', password='password123')
        
        # Create wallets
        self.victim_wallet, _ = Wallet.objects.get_or_create(user=self.victim)
        self.attacker_wallet, _ = Wallet.objects.get_or_create(user=self.attacker)
        
        # Add funds to victim wallet
        self.victim_wallet.balance = Decimal('1000.00')
        self.victim_wallet.save()
        
        # Create a transaction for victim
        self.victim_transaction = Transaction.objects.create(
            user=self.victim,
            wallet=self.victim_wallet,
            transaction_type='deposit',
            amount=Decimal('500.00'),
            payment_gateway='test',
            status='completed'
        )

    def test_wallet_dashboard__cross_user__access_denied(self):
        """
        SECURITY TEST: User cannot access another user's wallet dashboard.
        
        Risk: IDOR allows viewing other users' financial data.
        """
        client = Client()
        client.force_login(self.attacker)
        
        # Try to access victim's wallet (if URL pattern allows ID)
        response = client.get(f'/payments/wallet/{self.victim_wallet.id}/')
        
        # Should be 404 (doesn't exist) or 403 (forbidden)
        if response.status_code == 200:
            content = response.content.decode('utf-8', errors='ignore')
            self.assertNotIn(
                str(self.victim_wallet.balance),
                content,
                "IDOR VULNERABILITY: Attacker can view victim's wallet balance"
            )

    def test_transaction_receipt__cross_user__access_denied(self):
        """
        SECURITY TEST: User cannot download another user's transaction receipt.
        
        Risk: Transaction receipts contain sensitive financial data.
        """
        client = Client()
        client.force_login(self.attacker)
        
        response = client.get(
            f'/payments/transactions/{self.victim_transaction.transaction_id}/receipt/'
        )
        
        self.assertIn(
            response.status_code, [403, 404],
            "IDOR VULNERABILITY: Attacker can access victim's transaction receipt"
        )

    def test_transaction_export__cross_user_data__not_leaked(self):
        """
        SECURITY TEST: Transaction export should not include other users' data.
        
        Risk: Data export leaking cross-user information.
        """
        client = Client()
        client.force_login(self.attacker)
        
        response = client.get('/payments/transactions/export/')
        
        if response.status_code == 200:
            content = response.content.decode('utf-8', errors='ignore')
            self.assertNotIn(
                str(self.victim_transaction.transaction_id),
                content,
                "DATA LEAK: Transaction export contains other user's transactions"
            )
            self.assertNotIn(
                self.victim.username,
                content,
                "DATA LEAK: Transaction export contains other user's username"
            )


@pytest.mark.security
class TestInvoiceIDOR(TestCase):
    """
    Tests for Insecure Direct Object Reference in invoice endpoints.
    
    SECURITY REQUIREMENT: Users should only access their own invoices.
    """

    def setUp(self):
        self.victim = User.objects.create_user(username='victim_inv', password='password123')
        self.attacker = User.objects.create_user(username='attacker_inv', password='password123')
        
        # Create subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan',
            price=Decimal('50.00'),
            duration_days=30,
            description='Test subscription plan'
        )
        
        # Create subscription for victim
        self.victim_subscription = UserSubscription.objects.create(
            user=self.victim,
            plan=self.plan,
            status='pending'
        )
        
        # Create invoice for victim
        self.victim_invoice = Invoice.objects.create(
            user=self.victim,
            subscription=self.victim_subscription,
            amount=Decimal('50.00'),
            due_date=timezone.now(),
            description='Test invoice'
        )

    def test_invoice_pdf__cross_user__access_denied(self):
        """
        SECURITY TEST: User cannot download another user's invoice PDF.
        
        Risk: Invoice PDFs contain billing and personal information.
        """
        client = Client()
        client.force_login(self.attacker)
        
        response = client.get(f'/payments/invoices/{self.victim_invoice.id}/pdf/')
        
        self.assertIn(
            response.status_code, [403, 404],
            "IDOR VULNERABILITY: Attacker can access victim's invoice PDF"
        )


@pytest.mark.security
class TestKYCDocumentIDOR(TestCase):
    """
    Tests for Insecure Direct Object Reference in KYC document endpoints.
    
    SECURITY REQUIREMENT: Users should only access their own KYC documents.
    """

    def setUp(self):
        self.victim = User.objects.create_user(username='victim_kyc', password='password123')
        self.attacker = User.objects.create_user(username='attacker_kyc', password='password123')
        
        # Create KYC document for victim
        self.victim_doc = KYCDocument.objects.create(
            user=self.victim,
            document_type='national_id',
            document_file='kyc/test_document.pdf',
            status='pending'
        )

    def test_kyc_document_detail__cross_user__access_denied(self):
        """
        SECURITY TEST: User cannot view another user's KYC document.
        
        Risk: KYC documents contain sensitive identity information.
        """
        client = Client()
        client.force_login(self.attacker)
        
        response = client.get(f'/kyc/document/{self.victim_doc.id}/')
        
        self.assertIn(
            response.status_code, [403, 404],
            "IDOR VULNERABILITY: Attacker can view victim's KYC document"
        )

    def test_kyc_document_delete__cross_user__access_denied(self):
        """
        SECURITY TEST: User cannot delete another user's KYC document.
        
        Risk: Unauthorized deletion of KYC documents.
        """
        client = Client()
        client.force_login(self.attacker)
        
        response = client.post(f'/kyc/document/{self.victim_doc.id}/delete/')
        
        self.assertIn(
            response.status_code, [403, 404],
            "IDOR VULNERABILITY: Attacker can delete victim's KYC document"
        )
        
        # Verify document still exists
        self.victim_doc.refresh_from_db()
        self.assertIsNotNone(self.victim_doc.id)


@pytest.mark.security
class TestMarketplaceIDOR(TestCase):
    """
    Tests for Insecure Direct Object Reference in marketplace endpoints.
    
    SECURITY REQUIREMENT: Users should only modify their own listings.
    """

    def setUp(self):
        # Create business category
        self.business_category, _ = Category.objects.get_or_create(
            name='Business', defaults={'slug': 'business', 'is_active': True}
        )
        
        self.victim = User.objects.create_user(username='victim_market', password='password123')
        self.attacker = User.objects.create_user(username='attacker_market', password='password123')
        
        # Create business profile for victim (using correct model fields)
        self.victim_business = BusinessProfile.objects.create(
            user=self.victim,
            company_name='Victim Company',
            industry='Technology',
            company_size='10-50',
            investment_seeking=Decimal('100000.00'),
            equity_offered=Decimal('10.00'),
            funding_stage='seed'
        )
        
        # Create investment opportunity for victim (business is ForeignKey to User)
        self.victim_opportunity = InvestmentOpportunity.objects.create(
            business=self.victim,
            title='Victim Opportunity',
            description='Test opportunity',
            amount_seeking=Decimal('100000.00'),
            minimum_investment=Decimal('1000.00'),
            equity_percentage=Decimal('10.00'),
            industry='Technology',
            status='open'
        )

    def test_business_profile_update__cross_user__access_denied(self):
        """
        SECURITY TEST: User cannot modify another user's business profile.
        
        Risk: Unauthorized modification of business listings.
        """
        client = Client()
        client.force_login(self.attacker)
        
        response = client.post('/marketplace/business/update/', {
            'company_name': 'Attacker Modified Name',
            'industry': 'Fraud',
        })
        
        # Verify victim's business was not modified
        self.victim_business.refresh_from_db()
        self.assertNotEqual(
            self.victim_business.company_name,
            'Attacker Modified Name',
            "IDOR VULNERABILITY: Attacker modified victim's business profile"
        )


@pytest.mark.security 
class TestDisputeIDOR(TestCase):
    """
    Tests for Insecure Direct Object Reference in dispute endpoints.
    
    SECURITY REQUIREMENT: Users should only access their own disputes.
    """

    def setUp(self):
        self.victim = User.objects.create_user(username='victim_dispute', password='password123')
        self.attacker = User.objects.create_user(username='attacker_dispute', password='password123')
        
        # Create wallet and transaction for victim
        self.victim_wallet, _ = Wallet.objects.get_or_create(user=self.victim)
        self.victim_transaction = Transaction.objects.create(
            user=self.victim,
            wallet=self.victim_wallet,
            transaction_type='deposit',
            amount=Decimal('100.00'),
            payment_gateway='test',
            status='completed'
        )

    def test_create_dispute__cross_user_transaction__access_denied(self):
        """
        SECURITY TEST: User cannot create dispute for another user's transaction.
        
        Risk: Malicious dispute creation for fraud.
        """
        client = Client()
        client.force_login(self.attacker)
        
        response = client.post(
            f'/payments/disputes/create/{self.victim_transaction.transaction_id}/',
            {'reason': 'Fraudulent dispute'}
        )
        
        self.assertIn(
            response.status_code, [403, 404],
            "IDOR VULNERABILITY: Attacker can create dispute for victim's transaction"
        )


@pytest.mark.security
class TestVerticalPrivilegeEscalation(TestCase):
    """
    Tests for vertical privilege escalation attempts.
    
    SECURITY REQUIREMENT: Users cannot escalate their privileges.
    """

    def setUp(self):
        self.regular_user = User.objects.create_user(
            username='regular_priv', password='password123'
        )
        self.staff_user = User.objects.create_user(
            username='staff_priv', password='password123', is_staff=True
        )

    def test_regular_user__staff_resolve_dispute__access_denied(self):
        """
        SECURITY TEST: Regular user cannot resolve disputes (staff action).
        
        Risk: Privilege escalation to perform staff actions.
        """
        client = Client()
        client.force_login(self.regular_user)
        
        response = client.post('/payments/staff/disputes/1/resolve/', {
            'resolution': 'approved'
        })
        
        self.assertIn(
            response.status_code, [302, 403, 404],
            "PRIVILEGE ESCALATION: Regular user can resolve disputes"
        )

    def test_regular_user__staff_fraud_alert_resolve__access_denied(self):
        """
        SECURITY TEST: Regular user cannot resolve fraud alerts.
        
        Risk: Malicious clearing of fraud alerts.
        """
        client = Client()
        client.force_login(self.regular_user)
        
        response = client.post('/payments/staff/fraud-alerts/1/resolve/', {
            'action': 'dismiss'
        })
        
        self.assertIn(
            response.status_code, [302, 403, 404],
            "PRIVILEGE ESCALATION: Regular user can resolve fraud alerts"
        )

    def test_staff_user__superuser_actions__access_denied(self):
        """
        SECURITY TEST: Staff user cannot perform superuser actions.
        
        Risk: Staff escalating to full admin.
        """
        client = Client()
        client.force_login(self.staff_user)
        
        # Try to add a new superuser via admin
        response = client.post('/admin/auth/user/add/', {
            'username': 'hacked_admin',
            'password1': 'HackedPassword123!',
            'password2': 'HackedPassword123!',
            'is_superuser': True,
        })
        
        # Verify no superuser was created
        self.assertFalse(
            User.objects.filter(username='hacked_admin', is_superuser=True).exists(),
            "PRIVILEGE ESCALATION: Staff user created superuser account"
        )


@pytest.mark.security
class TestHorizontalPrivilegeEscalation(TestCase):
    """
    Tests for horizontal privilege escalation (accessing peer's resources).
    
    SECURITY REQUIREMENT: Users cannot access other users' resources at same privilege level.
    """

    def setUp(self):
        self.user1 = User.objects.create_user(username='peer1', password='password123')
        self.user2 = User.objects.create_user(username='peer2', password='password123')
        
        Wallet.objects.get_or_create(user=self.user1)
        Wallet.objects.get_or_create(user=self.user2)

    def test_profile_edit__other_user__access_denied(self):
        """
        SECURITY TEST: User cannot edit another user's profile.
        
        Risk: Account takeover or data modification.
        """
        client = Client()
        client.force_login(self.user1)
        
        # Try to access user2's profile edit (if URL allows direct access)
        response = client.get(f'/accounts/profile/{self.user2.username}/edit/')
        
        # Should be 404 (doesn't exist) or 403 (forbidden)
        if response.status_code == 200:
            pytest.fail("HORIZONTAL PRIVILEGE ESCALATION: Can access other user's profile edit")

    def test_subscription_cancel__other_user__access_denied(self):
        """
        SECURITY TEST: User cannot cancel another user's subscription.
        
        Risk: Malicious service disruption.
        """
        plan = SubscriptionPlan.objects.create(
            name='Test Plan',
            slug='test-plan-hpe',
            price=Decimal('50.00'),
            duration_days=30,
            description='Test'
        )
        
        user2_subscription = UserSubscription.objects.create(
            user=self.user2,
            plan=plan,
            status='active'
        )
        
        client = Client()
        client.force_login(self.user1)
        
        response = client.post(f'/payments/subscriptions/{user2_subscription.id}/cancel/')
        
        self.assertIn(
            response.status_code, [403, 404],
            "HORIZONTAL PRIVILEGE ESCALATION: User can cancel other user's subscription"
        )
        
        # Verify subscription is still active
        user2_subscription.refresh_from_db()
        self.assertEqual(user2_subscription.status, 'active')
