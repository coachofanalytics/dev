"""
Smart Approval Service for Budget Requests
Phase 2: Data-driven approval automation using BudgetCategory tier system

Uses real transaction data analysis to determine auto-approval.
Replaces hardcoded rules with data-driven tier classifications.
"""

from decimal import Decimal
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class SmartApprovalService:
    """
    Phase 2: Data-driven smart approval service
    
    Uses BudgetCategory tier fields populated by transaction analysis:
    - approval_tier (A/B/C)
    - auto_approve_enabled (Finance Manager control)
    - typical_monthly_amount (from data)
    - variance_threshold (from data)
    - is_recurring (from pattern detection)
    """
    
    def should_auto_approve(self, budget_request):
        """
        Determine if a budget request should be auto-approved using tier system.
        
        Phase 2: Uses data-driven tier classification
        
        Returns: (should_auto_approve: bool, reason: str)
        """
        category = budget_request.budget_category
        
        if not category:
            return False, "No category specified - requires manual approval"
        
        # Use category's built-in auto-approval logic
        should_approve, reason = category.should_auto_approve(budget_request.amount)
        
        if should_approve:
            logger.info(f"Auto-approval recommended for request {budget_request.id}: {reason}")
            return True, reason
        else:
            # Check tier-based routing for manual approval
            routing_reason = self._get_routing_reason(budget_request, category)
            logger.info(f"Manual approval required for request {budget_request.id}: {routing_reason}")
            return False, routing_reason
    
    def _get_routing_reason(self, budget_request, category):
        """
        Determine routing reason for manual approval based on tier.
        """
        tier = category.approval_tier
        amount = budget_request.amount
        priority = budget_request.priority
        
        if tier == 'A':
            # Tier A but not auto-approved (likely variance exceeded or disabled)
            if not category.auto_approve_enabled:
                return f"Tier A (Known/Recurring) - Auto-approval disabled by Finance Manager"
            elif not category.typical_monthly_amount:
                return f"Tier A (Known/Recurring) - No baseline data, requires manual review"
            else:
                variance = abs(amount - category.typical_monthly_amount) / category.typical_monthly_amount * 100
                return f"Tier A (Known/Recurring) - Amount variance {variance:.1f}% exceeds threshold {category.variance_threshold}%"
        
        elif tier == 'B':
            # Tier B: Variable/Operational - Priority-based routing
            if priority in ['urgent', 'high']:
                return f"Tier B (Variable/Operational) - HIGH priority, recommend fast-track approval"
            elif priority == 'medium':
                return f"Tier B (Variable/Operational) - MEDIUM priority, route to Department Manager"
            else:
                return f"Tier B (Variable/Operational) - LOW priority, requires justification"
        
        else:  # Tier C
            # Tier C: Strategic/Discretionary
            return f"Tier C (Strategic/Discretionary) - Requires assessment and manual approval"
    
    def get_recommended_approver(self, budget_request):
        """
        Get recommended approver based on tier and priority.
        
        Returns: (approver_type: str, reason: str)
        """
        category = budget_request.budget_category
        
        if not category:
            return 'staff', "No category - default to staff approval"
        
        tier = category.approval_tier
        priority = budget_request.priority
        
        # Tier A: Finance Manager oversight
        if tier == 'A':
            return 'finance_manager', "Tier A requires Finance Manager oversight"
        
        # Tier B: Priority-based routing
        elif tier == 'B':
            if priority in ['urgent', 'high']:
                return 'auto_approve_flagged', "High priority operational expense - auto-approve with notification"
            elif priority == 'medium':
                return 'department_manager', "Medium priority - Department Manager approval"
            else:
                return 'finance_manager', "Low priority - Finance Manager approval required"
        
        # Tier C: Strategic assessment
        else:
            if priority in ['urgent', 'high']:
                return 'senior_manager', "High priority strategic - Senior Manager"
            else:
                return 'executive', "Strategic expense - Executive approval required"
    
    def get_approval_routing(self, budget_request):
        """
        Get complete approval routing information.
        
        Returns dict with:
        - should_auto_approve: bool
        - auto_approve_reason: str
        - recommended_approver: str
        - routing_reason: str
        - tier: str
        - priority: str
        """
        category = budget_request.budget_category
        
        should_approve, auto_reason = self.should_auto_approve(budget_request)
        approver_type, approver_reason = self.get_recommended_approver(budget_request)
        
        return {
            'should_auto_approve': should_approve,
            'auto_approve_reason': auto_reason,
            'recommended_approver': approver_type if not should_approve else 'auto',
            'routing_reason': approver_reason if not should_approve else auto_reason,
            'tier': category.approval_tier if category else 'C',
            'priority': budget_request.priority,
            'category_name': category.name if category else 'Unknown',
            'amount': budget_request.amount,
            'typical_amount': category.typical_monthly_amount if category else None,
            'variance_threshold': category.variance_threshold if category else None,
        }
    
    def process_budget_request(self, budget_request, auto_approver=None):
        """
        Process a budget request with smart routing.
        
        Args:
            budget_request: The BudgetRequest object
            auto_approver: User to set as approver for auto-approvals (typically system user)
        
        Returns:
            dict with:
            - approved: bool
            - status: str
            - reason: str
            - approver: str (type)
        """
        should_approve, reason = self.should_auto_approve(budget_request)
        
        if should_approve:
            # Auto-approve
            budget_request.status = 'approved'
            budget_request.approved_by = auto_approver or budget_request.requester
            budget_request.approved_at = timezone.now()
            budget_request.save()
            
            logger.info(f"✅ AUTO-APPROVED Request #{budget_request.id}: {reason}")
            
            return {
                'approved': True,
                'status': 'approved',
                'reason': reason,
                'approver': 'auto',
            }
        else:
            # Route for manual approval
            approver_type, approver_reason = self.get_recommended_approver(budget_request)
            
            budget_request.status = 'submitted'  # Or 'under_review' depending on workflow
            # Note: current_approver would be set here based on approver_type
            budget_request.save()
            
            logger.info(f"📋 MANUAL APPROVAL REQUIRED Request #{budget_request.id}: {approver_reason}")
            
            return {
                'approved': False,
                'status': 'submitted',
                'reason': reason,
                'approver': approver_type,
                'routing_reason': approver_reason,
            }
