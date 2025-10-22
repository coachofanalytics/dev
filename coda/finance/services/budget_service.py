"""
Budget Service

Centralized business logic for budget operations.
Handles calculations, projections, variance analysis, and data retrieval.
"""

from decimal import Decimal
from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q, F, Avg
from django.db.models.functions import Coalesce
from django.utils import timezone

from finance.models import (
    Transaction, Budget, BudgetCategory, BudgetSubCategory,
    BudgetEstimateProjection
)


class BudgetService:
    """
    Centralized budget business logic service.
    
    This service layer separates business logic from views/models,
    making the code more testable, reusable, and maintainable.
    """
    
    # =========================================================================
    # ACTUAL SPENDING (from Transactions)
    # =========================================================================
    
    @staticmethod
    def get_actual_spending(company=None, category=None, department=None, 
                           start_date=None, end_date=None):
        """
        Get actual spending from transactions.
        
        Args:
            company: Company object (optional)
            category: BudgetCategory object (optional)
            department: Department object (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            
        Returns:
            Decimal: Total actual spending
        """
        filters = Q(category__isnull=False)  # Only categorized transactions
        
        if category:
            filters &= Q(category=category)
        if department:
            filters &= Q(department=department)
        if start_date:
            filters &= Q(transaction_date__gte=start_date)
        if end_date:
            filters &= Q(transaction_date__lte=end_date)
        
        result = Transaction.objects.filter(filters).aggregate(
            total=Sum('amount')
        )
        
        return result['total'] or Decimal('0.00')
    
    @staticmethod
    def get_spending_by_category(company=None, start_date=None, end_date=None):
        """
        Get spending breakdown by category.
        
        Returns:
            dict: {category_id: {'name': str, 'total': Decimal, 'count': int}}
        """
        filters = Q(category__isnull=False)
        
        if start_date:
            filters &= Q(transaction_date__gte=start_date)
        if end_date:
            filters &= Q(transaction_date__lte=end_date)
        
        spending = Transaction.objects.filter(filters).values(
            'category__id', 'category__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        return {
            item['category__id']: {
                'name': item['category__name'],
                'total': item['total'],
                'count': item['count']
            }
            for item in spending
        }
    
    @staticmethod
    def get_spending_by_department(company=None, start_date=None, end_date=None):
        """
        Get spending breakdown by department.
        
        Returns:
            dict: {dept_id: {'name': str, 'total': Decimal, 'count': int}}
        """
        filters = Q(category__isnull=False)
        
        if start_date:
            filters &= Q(transaction_date__gte=start_date)
        if end_date:
            filters &= Q(transaction_date__lte=end_date)
        
        spending = Transaction.objects.filter(filters).values(
            'department__id', 'department__name'
        ).annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('-total')
        
        return {
            item['department__id']: {
                'name': item['department__name'] or 'No Department',
                'total': item['total'],
                'count': item['count']
            }
            for item in spending
        }
    
    # =========================================================================
    # MONTHLY AVERAGES & TRENDS
    # =========================================================================
    
    @staticmethod
    def calculate_monthly_average(company=None, category=None, department=None, 
                                  months=6):
        """
        Calculate monthly average spending from transactions.
        
        Args:
            company: Company object (optional)
            category: BudgetCategory object (optional)
            department: Department object (optional)
            months: Number of months to analyze (default: 6)
            
        Returns:
            Decimal: Monthly average spending
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*30)
        
        total = BudgetService.get_actual_spending(
            company, category, department, start_date, end_date
        )
        
        return total / months if total > 0 else Decimal('0.00')
    
    @staticmethod
    def get_spending_trend(category=None, months=12):
        """
        Get spending trend over time.
        
        Returns:
            list: [{month, year, total, count}, ...]
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*30)
        
        filters = Q(
            category__isnull=False,
            transaction_date__gte=start_date
        )
        
        if category:
            filters &= Q(category=category)
        
        # Group by month/year
        from django.db.models.functions import TruncMonth
        
        trend = Transaction.objects.filter(filters).annotate(
            month=TruncMonth('transaction_date')
        ).values('month').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('month')
        
        return list(trend)
    
    # =========================================================================
    # BUDGET PROJECTIONS
    # =========================================================================
    
    @staticmethod
    def generate_budget_projection(company, category, months_ahead=12, 
                                   growth_factor=1.10):
        """
        Generate budget projection for a category based on transaction history.
        
        Args:
            company: Company object
            category: BudgetCategory object
            months_ahead: Number of months to project (default: 12)
            growth_factor: Growth multiplier (default: 1.10 for 10% growth)
            
        Returns:
            dict: {
                'historical_monthly': Decimal,
                'projected_monthly': Decimal,
                'total_annual': Decimal,
                'confidence': float,
                'transaction_count': int
            }
        """
        # Calculate historical average
        monthly_avg = BudgetService.calculate_monthly_average(
            company=company,
            category=category,
            months=6
        )
        
        # Apply growth factor
        projected_monthly = monthly_avg * Decimal(str(growth_factor))
        
        # Get transaction count for confidence
        transaction_count = Transaction.objects.filter(
            category=category
        ).count()
        
        # Calculate confidence based on data availability
        if transaction_count >= 50:
            confidence = 95.0
        elif transaction_count >= 20:
            confidence = 85.0
        elif transaction_count >= 10:
            confidence = 70.0
        else:
            confidence = 50.0
        
        return {
            'historical_monthly': monthly_avg,
            'projected_monthly': projected_monthly,
            'total_annual': projected_monthly * months_ahead,
            'confidence': confidence,
            'transaction_count': transaction_count
        }
    
    # =========================================================================
    # VARIANCE ANALYSIS
    # =========================================================================
    
    @staticmethod
    def calculate_variance(budget):
        """
        Calculate budget variance (actual vs planned).
        
        Args:
            budget: Budget object
            
        Returns:
            dict: {
                'budgeted': Decimal,
                'actual': Decimal,
                'variance': Decimal,
                'variance_pct': Decimal,
                'status': str ('under'|'over'|'on_track')
            }
        """
        # Get actual spending for this budget's period and category
        actual = BudgetService.get_actual_spending(
            company=budget.company,
            category=budget.category,
            department=budget.department,
            start_date=budget.start_date,
            end_date=budget.end_date
        )
        
        budgeted = budget.total_amount
        variance = actual - budgeted
        
        if budgeted > 0:
            variance_pct = (variance / budgeted) * 100
        else:
            variance_pct = Decimal('0.00')
        
        # Determine status
        if abs(variance_pct) <= 5:
            status = 'on_track'
        elif variance > 0:
            status = 'over'
        else:
            status = 'under'
        
        # Update budget record
        budget.actual_spent = actual
        budget.variance = variance
        budget.variance_percentage = variance_pct
        budget.save(update_fields=['actual_spent', 'variance', 'variance_percentage'])
        
        return {
            'budgeted': budgeted,
            'actual': actual,
            'variance': variance,
            'variance_pct': variance_pct,
            'status': status
        }
    
    @staticmethod
    def get_budget_health_summary(company):
        """
        Get overall budget health summary for a company.
        
        Returns:
            dict: {
                'total_budgets': int,
                'over_budget': int,
                'under_budget': int,
                'on_track': int,
                'total_variance': Decimal
            }
        """
        budgets = Budget.objects.filter(
            company=company,
            is_active=True,
            status='active'
        )
        
        over = under = on_track = 0
        total_variance = Decimal('0.00')
        
        for budget in budgets:
            variance_data = BudgetService.calculate_variance(budget)
            total_variance += variance_data['variance']
            
            if variance_data['status'] == 'over':
                over += 1
            elif variance_data['status'] == 'under':
                under += 1
            else:
                on_track += 1
        
        return {
            'total_budgets': budgets.count(),
            'over_budget': over,
            'under_budget': under,
            'on_track': on_track,
            'total_variance': total_variance
        }
    
    # =========================================================================
    # DASHBOARD DATA
    # =========================================================================
    
    @staticmethod
    def get_dashboard_data(company, department=None):
        """
        Get comprehensive dashboard data combining budgets and transactions.
        
        Returns:
            dict: {
                'transactions': {...},
                'budgets': {...},
                'variance': {...},
                'projections': {...}
            }
        """
        # Transaction data (actual spending)
        transactions_total = BudgetService.get_actual_spending(
            company=company,
            department=department
        )
        
        transactions_count = Transaction.objects.filter(
            category__isnull=False
        ).count()
        
        monthly_avg = transactions_total / 12 if transactions_total > 0 else Decimal('0.00')
        
        # Budget data (planned spending)
        budget_filters = Q(company=company, is_active=True)
        if department:
            budget_filters &= Q(department=department)
        
        budgets = Budget.objects.filter(budget_filters)
        budget_total = budgets.aggregate(
            total=Sum(
                F('unit_price') * F('quantity') * Coalesce(F('cases'), 1),
                output_field=models.DecimalField()
            )
        )['total'] or Decimal('0.00')
        
        # Category breakdown
        category_spending = BudgetService.get_spending_by_category(
            company=company
        )
        
        # Department breakdown
        dept_spending = BudgetService.get_spending_by_department(
            company=company
        )
        
        return {
            'transactions': {
                'total': transactions_total,
                'count': transactions_count,
                'monthly_avg': monthly_avg,
                'by_category': category_spending
            },
            'budgets': {
                'total': budget_total,
                'count': budgets.count(),
                'active': budgets.filter(status='active').count()
            },
            'departments': dept_spending,
            'data_quality': f"{transactions_count} transactions, ${transactions_total:,.2f} total"
        }
    
    # =========================================================================
    # BUDGET TEMPLATES
    # =========================================================================
    
    @staticmethod
    def clone_template(template_id, start_date, end_date, budget_lead, 
                      description_suffix=""):
        """
        Clone a budget template for a new period.
        
        Args:
            template_id: ID of template budget
            start_date: Start date for new budget
            end_date: End date for new budget
            budget_lead: User to assign as budget lead
            description_suffix: Additional description text
            
        Returns:
            Budget: New budget created from template
        """
        template = Budget.objects.get(id=template_id, status='template')
        
        new_budget = Budget.objects.create(
            company=template.company,
            department=template.department,
            budget_lead=budget_lead,
            category=template.category,
            subcategory=template.subcategory,
            item_name=template.item_name,
            quantity=template.quantity,
            unit_price=template.unit_price,
            cases=template.cases,
            description=f"{template.description} {description_suffix}".strip(),
            start_date=start_date,
            end_date=end_date,
            status='draft',
            is_active=True,
            budget_type=template.budget_type,
            timeframe=template.timeframe
        )
        
        return new_budget


# Import models after class definition to avoid circular imports
from django.db import models

