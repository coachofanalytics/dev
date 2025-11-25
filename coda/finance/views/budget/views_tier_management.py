"""
Finance Manager Tier Management Views
Phase 2: Budget Category Tier Control Interface

Allows Finance Manager to:
- View tier classifications for all categories
- Enable/disable auto-approval per category
- Adjust variance thresholds
- View auto-approval logs
- Re-run tier classification analysis
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db.models import Q, Count, Sum
from decimal import Decimal
import logging

from finance.models import BudgetCategory, BudgetRequest, AutomationAuditLog
from finance.services.smart_approval_service import SmartApprovalService
from shared_core.models import Company

logger = logging.getLogger(__name__)


def is_finance_manager(user):
    """Check if user is Finance Manager (staff or superuser)"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_finance_manager)
def tier_management_dashboard(request, company_slug):
    """
    Finance Manager dashboard for managing budget category tiers.
    
    Features:
    - View all categories with tier classifications
    - Enable/disable auto-approval per category
    - Adjust variance thresholds
    - View tier statistics
    - Access to re-run analysis
    """
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Get all categories with tier data
        categories = BudgetCategory.objects.all().order_by('approval_tier', 'name')
        
        # Group by tier
        tier_a_categories = categories.filter(approval_tier='A')
        tier_b_categories = categories.filter(approval_tier='B')
        tier_c_categories = categories.filter(approval_tier='C')
        
        # Calculate statistics
        total_categories = categories.count()
        auto_approve_enabled_count = categories.filter(auto_approve_enabled=True).count()
        with_data_count = categories.exclude(typical_monthly_amount__isnull=True).count()
        
        # Get auto-approval statistics
        auto_approved_requests = BudgetRequest.objects.filter(
            status='approved',
            approved_by__isnull=False
        ).count()
        
        # Get audit logs for auto-approvals
        recent_auto_approvals = AutomationAuditLog.objects.filter(
            action='auto_approve_budget_request'
        ).order_by('-created_at')[:10]
        
        context = {
            'company': company,
            'categories': categories,
            'tier_a_categories': tier_a_categories,
            'tier_b_categories': tier_b_categories,
            'tier_c_categories': tier_c_categories,
            'total_categories': total_categories,
            'auto_approve_enabled_count': auto_approve_enabled_count,
            'with_data_count': with_data_count,
            'auto_approved_requests': auto_approved_requests,
            'recent_auto_approvals': recent_auto_approvals,
            'page_title': 'Tier Management Dashboard',
        }
        
        return render(request, 'finance/budgets/tier_management_dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error loading tier management dashboard: {str(e)}")
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return redirect('finance:unified-budget-dashboard', company_slug=company_slug)


@login_required
@user_passes_test(is_finance_manager)
@require_http_methods(["POST"])
def toggle_auto_approval(request, category_id):
    """
    Toggle auto-approval for a specific category.
    
    Only Tier A categories can have auto-approval enabled.
    """
    try:
        category = get_object_or_404(BudgetCategory, id=category_id)
        
        # Check if category is Tier A
        if category.approval_tier != 'A':
            return JsonResponse({
                'success': False,
                'error': f'Auto-approval only available for Tier A categories. {category.name} is Tier {category.approval_tier}.'
            }, status=400)
        
        # Check if category has baseline data
        if not category.typical_monthly_amount:
            return JsonResponse({
                'success': False,
                'error': f'Category {category.name} has no baseline data. Run tier analysis first.'
            }, status=400)
        
        # Toggle
        category.auto_approve_enabled = not category.auto_approve_enabled
        category.save()
        
        # Log action
        logger.info(f"Auto-approval {'enabled' if category.auto_approve_enabled else 'disabled'} for {category.name} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'enabled': category.auto_approve_enabled,
            'category': category.name,
            'message': f"Auto-approval {'enabled' if category.auto_approve_enabled else 'disabled'} for {category.name}"
        })
        
    except Exception as e:
        logger.error(f"Error toggling auto-approval: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@user_passes_test(is_finance_manager)
@require_http_methods(["POST"])
def update_variance_threshold(request, category_id):
    """
    Update variance threshold for a category.
    
    Variance threshold determines how much variation from typical amount is acceptable
    before triggering manual review.
    """
    try:
        category = get_object_or_404(BudgetCategory, id=category_id)
        
        # Get new threshold from POST data
        new_threshold = request.POST.get('variance_threshold')
        
        if not new_threshold:
            return JsonResponse({
                'success': False,
                'error': 'Variance threshold is required'
            }, status=400)
        
        try:
            threshold_decimal = Decimal(str(new_threshold))
            
            # Validate range (5% to 100%)
            if threshold_decimal < 5 or threshold_decimal > 100:
                return JsonResponse({
                    'success': False,
                    'error': 'Variance threshold must be between 5% and 100%'
                }, status=400)
            
            # Update
            old_threshold = category.variance_threshold
            category.variance_threshold = threshold_decimal
            category.save()
            
            # Log action
            logger.info(f"Variance threshold for {category.name} updated from {old_threshold}% to {threshold_decimal}% by {request.user.username}")
            
            return JsonResponse({
                'success': True,
                'category': category.name,
                'old_threshold': float(old_threshold),
                'new_threshold': float(threshold_decimal),
                'message': f"Variance threshold updated to {threshold_decimal}% for {category.name}"
            })
            
        except (ValueError, TypeError) as e:
            return JsonResponse({
                'success': False,
                'error': 'Invalid variance threshold value'
            }, status=400)
        
    except Exception as e:
        logger.error(f"Error updating variance threshold: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@user_passes_test(is_finance_manager)
def auto_approval_log(request, company_slug):
    """
    View log of all auto-approved budget requests.
    
    Shows:
    - Request details
    - Auto-approval reason
    - Tier and variance information
    - Date/time
    - Amount vs typical amount
    """
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Get filter parameters
        days_filter = request.GET.get('days', '30')  # Default: last 30 days
        tier_filter = request.GET.get('tier', '')  # Filter by tier
        
        # Calculate date threshold
        from datetime import timedelta
        try:
            days = int(days_filter)
            date_threshold = timezone.now() - timedelta(days=days)
        except (ValueError, TypeError):
            days = 30
            date_threshold = timezone.now() - timedelta(days=30)
        
        # Get auto-approved requests
        auto_approved = BudgetRequest.objects.filter(
            status='approved',
            approved_at__gte=date_threshold
        ).select_related('budget_category', 'requester', 'approved_by').order_by('-approved_at')
        
        # Filter by tier if specified
        if tier_filter:
            auto_approved = auto_approved.filter(budget_category__approval_tier=tier_filter)
        
        # Calculate summary statistics
        total_auto_approved = auto_approved.count()
        total_amount_auto_approved = auto_approved.aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        # Get tier breakdown
        tier_breakdown = {}
        for tier in ['A', 'B', 'C']:
            count = auto_approved.filter(budget_category__approval_tier=tier).count()
            amount = auto_approved.filter(budget_category__approval_tier=tier).aggregate(total=Sum('amount'))['total'] or Decimal('0')
            tier_breakdown[tier] = {'count': count, 'amount': amount}
        
        context = {
            'company': company,
            'auto_approved_requests': auto_approved,
            'total_auto_approved': total_auto_approved,
            'total_amount': total_amount_auto_approved,
            'tier_breakdown': tier_breakdown,
            'days_filter': days,
            'tier_filter': tier_filter,
            'page_title': 'Auto-Approval Log',
        }
        
        return render(request, 'finance/budgets/auto_approval_log.html', context)
        
    except Exception as e:
        logger.error(f"Error loading auto-approval log: {str(e)}")
        messages.error(request, f"Error loading log: {str(e)}")
        return redirect('finance:unified-budget-dashboard', company_slug=company_slug)


@login_required
@user_passes_test(is_finance_manager)
@require_http_methods(["POST"])
def run_tier_reclassification(request, company_slug):
    """
    Trigger re-run of tier classification analysis.
    
    This runs the classify_budget_category_tiers management command
    and updates all category tier data.
    """
    try:
        company = get_object_or_404(Company, slug=company_slug)
        
        # Import here to avoid circular dependency
        from django.core.management import call_command
        from io import StringIO
        
        # Capture command output
        out = StringIO()
        call_command('classify_budget_category_tiers', '--analyze', '--save', '--company', company_slug, stdout=out)
        output = out.getvalue()
        
        # Log action
        logger.info(f"Tier reclassification run by {request.user.username} for {company_slug}")
        
        messages.success(request, "Tier classification analysis completed successfully!")
        
        return JsonResponse({
            'success': True,
            'message': 'Tier classification updated',
            'output': output
        })
        
    except Exception as e:
        logger.error(f"Error running tier reclassification: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

