"""
Additional tab data functions for unified budget dashboard
"""

from django.db.models import Sum, Count, Avg
from finance.models import BudgetRequest, BudgetEstimateProjection


def _get_requests_tab_data(company, department, user):
    """
    Get data for Requests tab - Budget Request Management
    """
    try:
        # Get budget requests
        requests = BudgetRequest.objects.all().order_by('-request_date')
        
        if department:
            requests = requests.filter(department=department)
        
        # Status counts
        total_requests = requests.count()
        pending_requests = requests.filter(status__in=['submitted', 'under_review']).count()
        approved_requests = requests.filter(status='approved').count()
        rejected_requests = requests.filter(status='rejected').count()
        
        return {
            'budget_requests': requests[:20],  # Latest 20
            'total_requests': total_requests,
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'rejected_requests': rejected_requests,
        }
    
    except Exception as e:
        return {
            'budget_requests': [],
            'total_requests': 0,
            'pending_requests': 0,
            'approved_requests': 0,
            'rejected_requests': 0,
            'error': str(e)
        }


def _get_projections_tab_data(company, department):
    """
    Get data for Projections tab - Budget Projections & Forecasting
    """
    try:
        # Get projections
        projections = BudgetEstimateProjection.objects.select_related(
            'budget', 'budget__category'
        ).order_by('-projected_amount')
        
        if department:
            projections = projections.filter(budget__department=department)
        
        # Calculate totals
        projection_stats = projections.aggregate(
            total=Sum('projected_amount'),
            avg_confidence=Avg('confidence_score'),
            count=Count('id')
        )
        
        total_amount = projection_stats['total'] or 0
        monthly_average = total_amount / 12 if total_amount > 0 else 0
        
        # Calculate totals for historical and projected
        total_historical = 0
        total_projected_monthly = 0
        
        for proj in projections:
            # Calculate historical monthly from budget data
            if proj.budget.unit_price:
                historical_monthly = proj.budget.unit_price / 1.10  # Remove growth factor
                total_historical += historical_monthly
                total_projected_monthly += proj.budget.unit_price
                
                # Add to projection object for display
                proj.historical_monthly = historical_monthly
                proj.projected_monthly = proj.budget.unit_price
        
        return {
            'projections_data': {
                'total_projections': projection_stats['count'],
                'total_amount': total_amount,
                'monthly_average': monthly_average,
                'avg_confidence': projection_stats['avg_confidence'] or 0,
                'projections': projections[:15],  # Top 15
                'total_historical': total_historical,
                'total_projected_monthly': total_projected_monthly,
            }
        }
    
    except Exception as e:
        return {
            'projections_data': None,
            'error': str(e)
        }

