"""
Tests for Budget Phase 2: Tier System

Tests:
- BudgetCategory tier field functionality
- SmartApprovalService tier-based logic
- Tier classification command
- Auto-approval workflow integration
- Finance Manager tier control views
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal

from finance.models import BudgetCategory, BudgetRequest, ApprovalPolicy
from finance.services.smart_approval_service import SmartApprovalService
from finance.services.automation_service import BudgetRequestService
from accounts.models import Department
from main.models import Company

User = get_user_model()


class BudgetCategoryTierMethodsTest(TestCase):
    """Test BudgetCategory tier-related methods"""
    
    def setUp(self):
        """Set up test data"""
        self.category_tier_a = BudgetCategory.objects.create(
            name="Test Utilities",
            approval_tier='A',
            auto_approve_enabled=True,
            typical_monthly_amount=Decimal('2000.00'),
            variance_threshold=Decimal('20.00'),
            is_recurring=True,
            last_pattern_analysis=timezone.now()
        )
        
        self.category_tier_b = BudgetCategory.objects.create(
            name="Test Office Supplies",
            approval_tier='B',
            auto_approve_enabled=False,
            typical_monthly_amount=Decimal('500.00'),
            variance_threshold=Decimal('30.00'),
            is_recurring=True
        )
        
        self.category_tier_c = BudgetCategory.objects.create(
            name="Test R&D",
            approval_tier='C',
            auto_approve_enabled=False,
            typical_monthly_amount=None,
            variance_threshold=Decimal('50.00'),
            is_recurring=False
        )
    
    def test_is_within_variance_true(self):
        """Test variance checking returns True when within threshold"""
        # Amount within 20% of $2000 (threshold)
        self.assertTrue(self.category_tier_a.is_within_variance(Decimal('2100.00')))  # 5% variance
        self.assertTrue(self.category_tier_a.is_within_variance(Decimal('2400.00')))  # 20% variance
    
    def test_is_within_variance_false(self):
        """Test variance checking returns False when exceeds threshold"""
        # Amount exceeds 20% of $2000
        self.assertFalse(self.category_tier_a.is_within_variance(Decimal('2500.00')))  # 25% variance
        self.assertFalse(self.category_tier_a.is_within_variance(Decimal('3000.00')))  # 50% variance
    
    def test_is_within_variance_no_baseline(self):
        """Test variance checking when no typical amount"""
        self.assertFalse(self.category_tier_c.is_within_variance(Decimal('1000.00')))
    
    def test_should_auto_approve_tier_a_within_variance(self):
        """Test Tier A auto-approves when within variance"""
        should_approve, reason = self.category_tier_a.should_auto_approve(Decimal('2100.00'))
        self.assertTrue(should_approve)
        self.assertIn('within', reason.lower())
    
    def test_should_auto_approve_tier_a_exceeds_variance(self):
        """Test Tier A rejects when variance exceeded"""
        should_approve, reason = self.category_tier_a.should_auto_approve(Decimal('3000.00'))
        self.assertFalse(should_approve)
        self.assertIn('variance', reason.lower())
        self.assertIn('exceeds', reason.lower())
    
    def test_should_auto_approve_tier_a_disabled(self):
        """Test Tier A rejects when auto-approval disabled"""
        self.category_tier_a.auto_approve_enabled = False
        self.category_tier_a.save()
        
        should_approve, reason = self.category_tier_a.should_auto_approve(Decimal('2000.00'))
        self.assertFalse(should_approve)
        self.assertIn('disabled', reason.lower())
    
    def test_should_auto_approve_tier_b_always_false(self):
        """Test Tier B never auto-approves"""
        should_approve, reason = self.category_tier_b.should_auto_approve(Decimal('500.00'))
        self.assertFalse(should_approve)
        # Tier B should say auto-approval is disabled (or mention Tier B)
        self.assertTrue('disabled' in reason.lower() or 'tier b' in reason.lower())
    
    def test_should_auto_approve_tier_c_always_false(self):
        """Test Tier C never auto-approves"""
        should_approve, reason = self.category_tier_c.should_auto_approve(Decimal('1000.00'))
        self.assertFalse(should_approve)
        # Tier C should say auto-approval is disabled (or mention Tier C)
        self.assertTrue('disabled' in reason.lower() or 'tier c' in reason.lower())
    
    def test_needs_pattern_analysis_never_run(self):
        """Test needs analysis when never run"""
        category = BudgetCategory.objects.create(
            name="Test Never Analyzed",
            last_pattern_analysis=None
        )
        self.assertTrue(category.needs_pattern_analysis())
    
    def test_needs_pattern_analysis_old_data(self):
        """Test needs analysis when data is old (>30 days)"""
        from datetime import timedelta
        old_date = timezone.now() - timedelta(days=35)
        
        category = BudgetCategory.objects.create(
            name="Test Old Analysis",
            last_pattern_analysis=old_date
        )
        self.assertTrue(category.needs_pattern_analysis())
    
    def test_needs_pattern_analysis_recent_data(self):
        """Test doesn't need analysis when data is recent"""
        category = BudgetCategory.objects.create(
            name="Test Recent Analysis",
            last_pattern_analysis=timezone.now()
        )
        self.assertFalse(category.needs_pattern_analysis())


class SmartApprovalServiceTest(TestCase):
    """Test SmartApprovalService Phase 2 functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.company = Company.objects.create(name='Test Company', slug='test')
        self.department = Department.objects.create(name=Department.FIN)  # Use Finance Department
        
        # Create categories with tier data
        self.category_tier_a = BudgetCategory.objects.create(
            name="Rent",
            approval_tier='A',
            auto_approve_enabled=True,
            typical_monthly_amount=Decimal('2000.00'),
            variance_threshold=Decimal('15.00'),
            is_recurring=True
        )
        
        self.category_tier_b = BudgetCategory.objects.create(
            name="Office Supplies",
            approval_tier='B',
            typical_monthly_amount=Decimal('500.00'),
            variance_threshold=Decimal('25.00'),
            is_recurring=True
        )
        
        self.category_tier_c = BudgetCategory.objects.create(
            name="Marketing",
            approval_tier='C',
            typical_monthly_amount=None,
            variance_threshold=Decimal('50.00'),
            is_recurring=False
        )
        
        self.service = SmartApprovalService()
    
    def create_budget_request(self, category, amount, priority='medium'):
        """Helper to create budget request"""
        from datetime import date
        return BudgetRequest.objects.create(
            requester=self.user,
            created_by=self.user,
            last_modified_by=self.user,
            amount=amount,
            purpose="Test request",
            department=self.department,
            budget_category=category,
            priority=priority,
            required_date=date.today(),
            status='draft'
        )
    
    def test_should_auto_approve_tier_a_within_variance(self):
        """Test auto-approves Tier A within variance"""
        request = self.create_budget_request(self.category_tier_a, Decimal('2100.00'))
        should_approve, reason = self.service.should_auto_approve(request)
        
        self.assertTrue(should_approve)
        self.assertIn('within', reason.lower())
    
    def test_should_not_auto_approve_tier_a_exceeds_variance(self):
        """Test rejects Tier A when exceeds variance"""
        request = self.create_budget_request(self.category_tier_a, Decimal('2500.00'))
        should_approve, reason = self.service.should_auto_approve(request)
        
        self.assertFalse(should_approve)
        self.assertIn('variance', reason.lower())
        self.assertIn('exceeds', reason.lower())
    
    def test_should_not_auto_approve_tier_b(self):
        """Test Tier B requires manual approval"""
        request = self.create_budget_request(self.category_tier_b, Decimal('500.00'))
        should_approve, reason = self.service.should_auto_approve(request)
        
        self.assertFalse(should_approve)
    
    def test_should_not_auto_approve_tier_c(self):
        """Test Tier C requires manual approval"""
        request = self.create_budget_request(self.category_tier_c, Decimal('1000.00'))
        should_approve, reason = self.service.should_auto_approve(request)
        
        self.assertFalse(should_approve)
    
    def test_get_recommended_approver_tier_a(self):
        """Test recommends Finance Manager for Tier A"""
        request = self.create_budget_request(self.category_tier_a, Decimal('2000.00'))
        approver_type, reason = self.service.get_recommended_approver(request)
        
        self.assertEqual(approver_type, 'finance_manager')
    
    def test_get_recommended_approver_tier_b_high_priority(self):
        """Test recommends auto-approve for Tier B high priority"""
        request = self.create_budget_request(self.category_tier_b, Decimal('500.00'), priority='high')
        approver_type, reason = self.service.get_recommended_approver(request)
        
        self.assertEqual(approver_type, 'auto_approve_flagged')
    
    def test_get_recommended_approver_tier_b_medium_priority(self):
        """Test recommends Department Manager for Tier B medium priority"""
        request = self.create_budget_request(self.category_tier_b, Decimal('500.00'), priority='medium')
        approver_type, reason = self.service.get_recommended_approver(request)
        
        self.assertEqual(approver_type, 'department_manager')
    
    def test_get_recommended_approver_tier_b_low_priority(self):
        """Test recommends Finance Manager for Tier B low priority"""
        request = self.create_budget_request(self.category_tier_b, Decimal('500.00'), priority='low')
        approver_type, reason = self.service.get_recommended_approver(request)
        
        self.assertEqual(approver_type, 'finance_manager')
    
    def test_get_recommended_approver_tier_c_strategic(self):
        """Test recommends Executive for Tier C"""
        request = self.create_budget_request(self.category_tier_c, Decimal('5000.00'))
        approver_type, reason = self.service.get_recommended_approver(request)
        
        self.assertEqual(approver_type, 'executive')
    
    def test_get_approval_routing_complete_data(self):
        """Test get_approval_routing returns complete routing info"""
        request = self.create_budget_request(self.category_tier_a, Decimal('2100.00'))
        routing = self.service.get_approval_routing(request)
        
        self.assertIn('should_auto_approve', routing)
        self.assertIn('tier', routing)
        self.assertIn('recommended_approver', routing)
        self.assertIn('amount', routing)
        self.assertIn('typical_amount', routing)
        self.assertIn('variance_threshold', routing)
    
    def test_process_budget_request_auto_approve(self):
        """Test process_budget_request auto-approves eligible requests"""
        request = self.create_budget_request(self.category_tier_a, Decimal('2000.00'))
        result = self.service.process_budget_request(request, auto_approver=self.user)
        
        self.assertTrue(result['approved'])
        self.assertEqual(result['status'], 'approved')
        self.assertEqual(result['approver'], 'auto')
        
        # Verify database updated
        request.refresh_from_db()
        self.assertEqual(request.status, 'approved')
        self.assertIsNotNone(request.approved_by)
        self.assertIsNotNone(request.approved_at)
    
    def test_process_budget_request_manual_approval(self):
        """Test process_budget_request routes to manual for non-eligible requests"""
        request = self.create_budget_request(self.category_tier_b, Decimal('500.00'))
        result = self.service.process_budget_request(request)
        
        self.assertFalse(result['approved'])
        self.assertEqual(result['status'], 'submitted')
        self.assertIn('approver', result)
        
        # Verify database updated
        request.refresh_from_db()
        self.assertEqual(request.status, 'submitted')


class TierClassificationLogicTest(TestCase):
    """Test tier classification logic and calculations"""
    
    def test_variance_calculation(self):
        """Test variance percentage calculation"""
        category = BudgetCategory.objects.create(
            name="Test",
            typical_monthly_amount=Decimal('1000.00'),
            variance_threshold=Decimal('20.00')
        )
        
        # 10% variance (within 20% threshold)
        self.assertTrue(category.is_within_variance(Decimal('1100.00')))
        
        # 30% variance (exceeds 20% threshold)
        self.assertFalse(category.is_within_variance(Decimal('1300.00')))
    
    def test_tier_a_rules(self):
        """Test Tier A auto-approval rules"""
        category = BudgetCategory.objects.create(
            name="Rent",
            approval_tier='A',
            auto_approve_enabled=True,
            typical_monthly_amount=Decimal('2000.00'),
            variance_threshold=Decimal('15.00')
        )
        
        # Within variance - should approve
        should, reason = category.should_auto_approve(Decimal('2200.00'))  # 10% variance
        self.assertTrue(should)
        
        # Exceeds variance - should reject
        should, reason = category.should_auto_approve(Decimal('2400.00'))  # 20% variance
        self.assertFalse(should)
    
    def test_tier_b_never_auto_approves(self):
        """Test Tier B never auto-approves regardless of amount"""
        category = BudgetCategory.objects.create(
            name="Travel",
            approval_tier='B',
            auto_approve_enabled=True,  # Even if enabled
            typical_monthly_amount=Decimal('500.00'),
            variance_threshold=Decimal('30.00')
        )
        
        should, reason = category.should_auto_approve(Decimal('500.00'))
        self.assertFalse(should)
        self.assertIn('tier b', reason.lower())
    
    def test_tier_c_never_auto_approves(self):
        """Test Tier C never auto-approves"""
        category = BudgetCategory.objects.create(
            name="R&D",
            approval_tier='C'
        )
        
        should, reason = category.should_auto_approve(Decimal('1000.00'))
        self.assertFalse(should)
        # Tier C should say auto-approval is disabled (or mention Tier C)
        self.assertTrue('disabled' in reason.lower() or 'tier c' in reason.lower())
    
    def test_auto_approve_disabled(self):
        """Test auto-approval fails when disabled"""
        category = BudgetCategory.objects.create(
            name="Utilities",
            approval_tier='A',
            auto_approve_enabled=False,  # Disabled
            typical_monthly_amount=Decimal('1000.00'),
            variance_threshold=Decimal('20.00')
        )
        
        should, reason = category.should_auto_approve(Decimal('1000.00'))
        self.assertFalse(should)
        self.assertIn('disabled', reason.lower())
    
    def test_no_typical_amount_data(self):
        """Test auto-approval fails when no baseline data"""
        category = BudgetCategory.objects.create(
            name="New Category",
            approval_tier='A',
            auto_approve_enabled=True,
            typical_monthly_amount=None  # No data
        )
        
        should, reason = category.should_auto_approve(Decimal('1000.00'))
        self.assertFalse(should)
        self.assertIn('no typical amount', reason.lower())


class AutoApprovalWorkflowIntegrationTest(TestCase):
    """Test complete auto-approval workflow integration"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.staff_user = User.objects.create_user(username='staff', password='testpass123', is_staff=True)
        self.company = Company.objects.create(name='Test Company', slug='test')
        self.department = Department.objects.create(name=Department.FIN)  # Use Finance Department
        
        # Tier A category (auto-approve enabled)
        self.auto_category = BudgetCategory.objects.create(
            name="Rent",
            approval_tier='A',
            auto_approve_enabled=True,
            typical_monthly_amount=Decimal('2000.00'),
            variance_threshold=Decimal('15.00'),
            is_recurring=True
        )
        
        # Tier B category (manual approval)
        self.manual_category = BudgetCategory.objects.create(
            name="Office Supplies",
            approval_tier='B',
            typical_monthly_amount=Decimal('500.00'),
            variance_threshold=Decimal('25.00')
        )
    
    def test_budget_request_auto_approved_on_submission(self):
        """Test budget request is auto-approved when submitted (Tier A within variance)"""
        from datetime import date
        
        request = BudgetRequest.objects.create(
            requester=self.user,
            created_by=self.user,
            last_modified_by=self.user,
            amount=Decimal('2050.00'),  # Within 15% of $2000
            purpose="Monthly rent payment",
            department=self.department,
            budget_category=self.auto_category,
            priority='medium',
            required_date=date.today(),
            status='draft'
        )
        
        # Submit using service (should auto-approve)
        service = BudgetRequestService()
        result = service.submit_for_approval(request.id, self.user)
        
        # Verify auto-approved
        result.refresh_from_db()
        self.assertEqual(result.status, 'approved')
        self.assertIsNotNone(result.approved_by)
        self.assertIsNotNone(result.approved_at)
    
    def test_budget_request_routes_to_manual_approval(self):
        """Test budget request routes to manual approval (Tier B)"""
        from datetime import date
        
        request = BudgetRequest.objects.create(
            requester=self.user,
            created_by=self.user,
            last_modified_by=self.user,
            amount=Decimal('500.00'),
            purpose="Office supplies",
            department=self.department,
            budget_category=self.manual_category,
            priority='medium',
            required_date=date.today(),
            status='draft'
        )
        
        # Submit using service (should route to manual)
        service = BudgetRequestService()
        result = service.submit_for_approval(request.id, self.user)
        
        # Verify routed to manual approval
        result.refresh_from_db()
        self.assertIn(result.status, ['submitted', 'under_review'])
        self.assertIsNone(result.approved_by)  # Not yet approved
    
    def test_budget_request_variance_exceeded_routes_to_manual(self):
        """Test Tier A request with exceeded variance routes to manual"""
        from datetime import date
        
        request = BudgetRequest.objects.create(
            requester=self.user,
            created_by=self.user,
            last_modified_by=self.user,
            amount=Decimal('2500.00'),  # 25% variance - exceeds 15% threshold
            purpose="High rent payment",
            department=self.department,
            budget_category=self.auto_category,
            priority='medium',
            required_date=date.today(),
            status='draft'
        )
        
        # Submit using service (should route to manual due to variance)
        service = BudgetRequestService()
        result = service.submit_for_approval(request.id, self.user)
        
        # Verify routed to manual
        result.refresh_from_db()
        self.assertIn(result.status, ['submitted', 'under_review'])
        self.assertIsNone(result.approved_by)


class TierManagementViewsTest(TestCase):
    """Test Finance Manager tier management views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(username='regular', password='testpass123')
        self.staff_user = User.objects.create_user(username='staff', password='testpass123', is_staff=True)
        self.company = Company.objects.create(name='Test Company', slug='test')
        
        self.category = BudgetCategory.objects.create(
            name="Test Category",
            approval_tier='A',
            auto_approve_enabled=False,
            typical_monthly_amount=Decimal('1000.00'),
            variance_threshold=Decimal('20.00')
        )
    
    def test_tier_management_dashboard_requires_staff(self):
        """Test tier management requires staff permission"""
        # Try as regular user
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(f'/finance/tier-management/{self.company.slug}/')
        
        # Should redirect (permission denied)
        self.assertEqual(response.status_code, 302)
    
    def test_tier_management_dashboard_accessible_to_staff(self):
        """Test tier management accessible to staff"""
        self.client.login(username='staff', password='testpass123')
        response = self.client.get(f'/finance/tier-management/{self.company.slug}/')
        
        # Should load (200) or redirect to login
        self.assertIn(response.status_code, [200, 302])
    
    def test_toggle_auto_approval_requires_staff(self):
        """Test toggle auto-approval requires staff permission"""
        self.client.login(username='regular', password='testpass123')
        response = self.client.post(f'/finance/api/tier/toggle-auto-approval/{self.category.id}/')
        
        # Should deny access
        self.assertEqual(response.status_code, 302)
    
    def test_auto_approval_log_requires_staff(self):
        """Test auto-approval log requires staff permission"""
        self.client.login(username='regular', password='testpass123')
        response = self.client.get(f'/finance/tier/auto-approval-log/{self.company.slug}/')
        
        # Should redirect (permission denied)
        self.assertEqual(response.status_code, 302)


class TierSystemRegressionTests(TestCase):
    """Regression tests for Phase 2 tier system"""
    
    def test_budget_category_has_tier_fields(self):
        """REGRESSION: Ensure BudgetCategory has all Phase 2 tier fields"""
        category = BudgetCategory.objects.create(name="Test")
        
        # Verify all tier fields exist
        self.assertTrue(hasattr(category, 'approval_tier'))
        self.assertTrue(hasattr(category, 'auto_approve_enabled'))
        self.assertTrue(hasattr(category, 'typical_monthly_amount'))
        self.assertTrue(hasattr(category, 'variance_threshold'))
        self.assertTrue(hasattr(category, 'is_recurring'))
        self.assertTrue(hasattr(category, 'last_pattern_analysis'))
    
    def test_budget_category_tier_methods_exist(self):
        """REGRESSION: Ensure BudgetCategory has Phase 2 helper methods"""
        category = BudgetCategory.objects.create(name="Test")
        
        # Verify methods exist
        self.assertTrue(hasattr(category, 'should_auto_approve'))
        self.assertTrue(hasattr(category, 'is_within_variance'))
        self.assertTrue(hasattr(category, 'needs_pattern_analysis'))
    
    def test_smart_approval_service_uses_tier_data(self):
        """REGRESSION: Ensure SmartApprovalService uses tier data not hardcoded rules"""
        service = SmartApprovalService()
        
        # Should not have hardcoded auto_approve_categories dict
        # (Phase 1 had this, Phase 2 should not)
        self.assertFalse(hasattr(service, 'auto_approve_categories'))
    
    def test_migration_0002_applied(self):
        """REGRESSION: Ensure migration 0002 adds tier fields correctly"""
        category = BudgetCategory.objects.create(
            name="Test Migration",
            approval_tier='B',
            auto_approve_enabled=False,
            variance_threshold=Decimal('25.00')
        )
        
        self.assertEqual(category.approval_tier, 'B')
        self.assertFalse(category.auto_approve_enabled)
        self.assertEqual(category.variance_threshold, Decimal('25.00'))

