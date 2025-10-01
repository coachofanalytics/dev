"""
Unified Budget Estimation Service

Phase 2: Consolidates BudgetEstimationService and EnhancedBudgetEstimationService
into a single, comprehensive service.

Replaces:
- BudgetEstimationService (basic transaction-based estimation)
- EnhancedBudgetEstimationService (multi-timeframe estimation)

Provides:
- All timeframes: weekly, monthly, quarterly, yearly, multi-year
- All estimation methods: average, trend, AI
- Backward compatibility with old service methods
- Website development cost estimation
"""

from decimal import Decimal
from typing import Dict, List, Any, Optional
from django.db.models import Q, Sum, Avg, Count, F
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import statistics

from ..models import Transaction, Inflow, Budget, BudgetCategory, Company, Department
from ..utils.calculation_utils import CalculationUtils
from ..utils.filter_utils import FilterUtils
from .base_service import BaseFinanceService

logger = logging.getLogger(__name__)


class UnifiedBudgetEstimationService(BaseFinanceService):
    """
    Unified service for all budget estimation needs.
    
    Consolidates functionality from:
    - BudgetEstimationService (basic estimation)
    - EnhancedBudgetEstimationService (multi-timeframe)
    
    Supports:
    - Multiple timeframes (weekly, monthly, quarterly, yearly, multi-year)
    - Multiple estimation methods (average, trend, ai)
    - Historical data analysis
    - Spending pattern recognition
    - Website development cost estimation
    - Investment planning
    """
    
    def __init__(self):
        super().__init__()
        self.calculation_utils = CalculationUtils()
        self.filter_utils = FilterUtils()
    
    # ==================================================================
    # CORE ESTIMATION METHOD (replaces all timeframe-specific methods)
    # ==================================================================
    
    def estimate_budget(
        self, 
        company: Company,
        department: Optional[Department] = None,
        timeframe: str = 'monthly',
        periods: int = 1,
        method: str = 'average'
    ) -> Dict[str, Any]:
        """
        Unified estimation method for all timeframes.
        
        Args:
            company: Company object
            department: Optional department for filtering
            timeframe: One of: 'weekly', 'monthly', 'quarterly', 'yearly', 'multi_year'
            periods: Number of periods to analyze (e.g., 3 months, 2 years)
            method: Estimation method - 'average', 'trend', 'ai'
        
        Returns:
            Dictionary with budget estimates by category
            
        Example:
            >>> service = UnifiedBudgetEstimationService()
            >>> result = service.estimate_budget(company, None, 'monthly', 3, 'average')
            >>> print(result['total_estimate'])
        """
        try:
            # Map timeframe to days for historical analysis
            timeframe_days = {
                'weekly': 7 * periods,
                'monthly': 30 * periods,
                'quarterly': 90 * periods,
                'yearly': 365 * periods,
                'multi_year': 365 * periods,
            }
            
            days = timeframe_days.get(timeframe, 30)
            
            # Get historical data
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            # Filter transactions
            transactions = self._get_transactions(company, department, start_date, end_date)
            
            # Analyze by category
            category_estimates = {}
            
            for category in BudgetCategory.objects.all():
                cat_transactions = transactions.filter(category=category)
                
                if cat_transactions.exists():
                    if method == 'average':
                        estimate = self._calculate_average_estimate(
                            cat_transactions, timeframe, periods, category
                        )
                    elif method == 'trend':
                        estimate = self._calculate_trend_estimate(
                            cat_transactions, timeframe, periods, category
                        )
                    elif method == 'ai':
                        estimate = self._calculate_ai_estimate(
                            cat_transactions, timeframe, periods, category
                        )
                    else:
                        estimate = self._calculate_average_estimate(
                            cat_transactions, timeframe, periods, category
                        )
                    
                    category_estimates[category.name] = estimate
            
            # Calculate total
            total_estimate = sum(est['amount'] for est in category_estimates.values())
            
            return {
                'timeframe': timeframe,
                'periods': periods,
                'method': method,
                'start_date': start_date,
                'end_date': end_date,
                'category_estimates': category_estimates,
                'total_estimate': total_estimate,
                'confidence_score': self._calculate_confidence(transactions, timeframe),
                'transaction_count': transactions.count(),
                'analysis_period_days': days,
            }
            
        except Exception as e:
            logger.error(f"Error in unified budget estimation: {e}", exc_info=True)
            return {
                'error': str(e),
                'timeframe': timeframe,
                'total_estimate': 0
            }
    
    # ==================================================================
    # BACKWARD COMPATIBILITY METHODS
    # (Support old service method calls without code changes)
    # ==================================================================
    
    def analyze_spending_patterns(self, company, department=None, months=3):
        """
        Backward compatible with BudgetEstimationService.analyze_spending_patterns()
        
        Analyzes spending patterns over specified months
        """
        return self.estimate_budget(company, department, 'monthly', months, 'average')
    
    def estimate_next_month_budget(self, company, department=None, method='average'):
        """
        Backward compatible with BudgetEstimationService.estimate_next_month_budget()
        
        Estimates budget for next month based on historical data
        """
        return self.estimate_budget(company, department, 'monthly', 1, method)
    
    def estimate_annual_budget(self, company, department=None):
        """
        Backward compatible with BudgetEstimationService.estimate_annual_budget()
        
        Estimates annual budget based on historical data
        """
        return self.estimate_budget(company, department, 'yearly', 1, 'average')
    
    def estimate_weekly_budget(self, company, department=None, weeks=4):
        """
        Backward compatible with EnhancedBudgetEstimationService.estimate_weekly_budget()
        
        Estimates weekly budget for specified number of weeks
        """
        return self.estimate_budget(company, department, 'weekly', weeks, 'average')
    
    def estimate_monthly_budget(self, company, department=None, months=3):
        """
        Backward compatible with EnhancedBudgetEstimationService.estimate_monthly_budget()
        
        Estimates monthly budget for specified number of months
        """
        return self.estimate_budget(company, department, 'monthly', months, 'average')
    
    def estimate_yearly_budget(self, company, department=None, years=1):
        """
        Backward compatible with EnhancedBudgetEstimationService.estimate_yearly_budget()
        
        Estimates yearly budget for specified number of years
        """
        return self.estimate_budget(company, department, 'yearly', years, 'average')
    
    # ==================================================================
    # SPECIALIZED ESTIMATION METHODS
    # ==================================================================
    
    def create_multi_year_plan(self, company, department=None, plan_years=2):
        """
        Create multi-year budget plan
        
        Args:
            company: Company object
            department: Optional department
            plan_years: Number of years (1, 2, or 5)
            
        Returns:
            Multi-year plan with yearly breakdowns
        """
        try:
            # Get base estimate for one year
            base_estimate = self.estimate_budget(
                company, department, 'yearly', 1, 'trend'
            )
            
            # Project forward for multiple years (with growth factor)
            growth_factor = 1.05  # 5% annual growth assumption
            
            yearly_projections = []
            for year in range(1, plan_years + 1):
                year_estimate = {}
                for cat_name, cat_data in base_estimate['category_estimates'].items():
                    projected_amount = cat_data['amount'] * (growth_factor ** (year - 1))
                    year_estimate[cat_name] = {
                        'amount': projected_amount,
                        'year': year,
                        'growth_factor': growth_factor ** (year - 1)
                    }
                
                total_year = sum(est['amount'] for est in year_estimate.values())
                yearly_projections.append({
                    'year': year,
                    'categories': year_estimate,
                    'total': total_year
                })
            
            total_multi_year = sum(proj['total'] for proj in yearly_projections)
            
            return {
                'plan_years': plan_years,
                'growth_factor': growth_factor,
                'yearly_projections': yearly_projections,
                'total_estimate': total_multi_year,
                'average_per_year': total_multi_year / plan_years,
                'base_year_estimate': base_estimate['total_estimate'],
            }
            
        except Exception as e:
            logger.error(f"Error creating multi-year plan: {e}", exc_info=True)
            return {'error': str(e)}
    
    def estimate_coda_development_cost(self, app_models_count, custom_tasks=None) -> Dict[str, Any]:
        """
        Estimate CODA website development cost
        
        Based on: requirements × hours × hourly_rate
        
        Args:
            app_models_count: Number of database models in the application
            custom_tasks: Optional custom task configuration
            
        Returns:
            Development cost estimation with breakdown
            
        Example:
            >>> result = service.estimate_coda_development_cost(5)
            >>> print(f"Total cost: ${result['total_cost']}")
        """
        try:
            # Default CODA development tasks
            default_tasks = {
                "createview": {"hour": 10, "quantity": 1, "unit_price": 30},
                "updateview": {"hour": 5, "quantity": 1, "unit_price": 30},
                "listview": {"hour": 3, "quantity": 1, "unit_price": 30},
                "detailview": {"hour": 3, "quantity": 1, "unit_price": 30},
                "deleteview": {"hour": 2, "quantity": 1, "unit_price": 30},
                "template": {"hour": 5, "quantity": 3, "unit_price": 30},
                "form": {"hour": 4, "quantity": 1, "unit_price": 30},
                "api": {"hour": 10, "quantity": 3, "unit_price": 30},
            }
            
            tasks = custom_tasks or default_tasks
            
            # Calculate cost per model
            one_model_cost = Decimal('0.00')
            task_breakdown = {}
            
            for task_name, task_config in tasks.items():
                quantity = task_config.get("quantity", 1)
                hours = task_config.get("hour", 1)
                unit_price = task_config.get("unit_price", 30)
                
                task_cost = Decimal(str(quantity)) * Decimal(str(hours)) * Decimal(str(unit_price))
                one_model_cost += task_cost
                
                task_breakdown[task_name] = {
                    'cost': float(task_cost),
                    'hours': hours,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_hours': hours * quantity
                }
            
            # Calculate total cost
            total_hours = sum(tb['total_hours'] for tb in task_breakdown.values())
            total_cost = one_model_cost * app_models_count
            
            return {
                'app_models_count': app_models_count,
                'cost_per_model': float(one_model_cost),
                'total_cost': float(total_cost),
                'total_hours': total_hours * app_models_count,
                'hours_per_model': total_hours,
                'task_breakdown': task_breakdown,
                'hourly_rate': tasks.get('createview', {}).get('unit_price', 30),
                'estimation_date': timezone.now().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error estimating CODA development cost: {e}", exc_info=True)
            return {'error': str(e)}
    
    def estimate_project_timeline(self, app_models_count, development_estimate=None) -> Dict[str, Any]:
        """
        Estimate project timeline based on development estimate
        
        Args:
            app_models_count: Number of models
            development_estimate: Output from estimate_coda_development_cost()
            
        Returns:
            Timeline estimation with milestones
        """
        try:
            if not development_estimate:
                development_estimate = self.estimate_coda_development_cost(app_models_count)
            
            total_hours = development_estimate.get('total_hours', 0)
            
            # Assumptions
            hours_per_day = 6  # Productive hours per day
            working_days_per_week = 5
            
            # Calculate timeline
            total_days = total_hours / hours_per_day
            total_weeks = total_days / working_days_per_week
            total_months = total_weeks / 4.33
            
            # Add buffer for testing, reviews, etc. (30%)
            buffered_days = total_days * 1.3
            buffered_weeks = buffered_days / working_days_per_week
            buffered_months = buffered_weeks / 4.33
            
            # Milestones
            milestones = {
                'design': {'percentage': 15, 'days': buffered_days * 0.15},
                'development': {'percentage': 50, 'days': buffered_days * 0.50},
                'testing': {'percentage': 20, 'days': buffered_days * 0.20},
                'deployment': {'percentage': 15, 'days': buffered_days * 0.15},
            }
            
            return {
                'total_hours': total_hours,
                'hours_per_day': hours_per_day,
                'total_days': round(total_days, 1),
                'total_weeks': round(total_weeks, 1),
                'total_months': round(total_months, 1),
                'buffered_days': round(buffered_days, 1),
                'buffered_weeks': round(buffered_weeks, 1),
                'buffered_months': round(buffered_months, 1),
                'milestones': milestones,
                'estimated_completion': (timezone.now() + timedelta(days=buffered_days)).date().isoformat(),
            }
            
        except Exception as e:
            logger.error(f"Error estimating project timeline: {e}", exc_info=True)
            return {'error': str(e)}
    
    # ==================================================================
    # INTERNAL HELPER METHODS
    # ==================================================================
    
    def _get_transactions(self, company, department, start_date, end_date):
        """
        Get filtered transactions for estimation
        
        Uses optimized query with select_related for performance
        
        Note: Transaction model doesn't have 'company' field, only 'department'
        """
        filters = Q(transaction_date__gte=start_date, transaction_date__lte=end_date)
        
        # Filter by department only (Transaction model doesn't have company field)
        if department:
            filters &= Q(department=department)
        
        return Transaction.objects.filter(filters).select_related(
            'category', 'department'
        )
    
    def _calculate_average_estimate(self, transactions, timeframe, periods, category):
        """
        Calculate average-based estimate
        
        Simple average of historical spending
        """
        total = Decimal('0.00')
        transaction_count = 0
        
        for txn in transactions:
            # Get amount (prefer USD if available)
            amount = txn.amount_usd if hasattr(txn, 'amount_usd') and txn.amount_usd else txn.amount
            
            # Get quantity (default to 1)
            quantity = txn.qty if hasattr(txn, 'qty') and txn.qty else Decimal('1.00')
            
            # Calculate total
            if amount:
                total += (Decimal(str(amount)) * Decimal(str(quantity)))
                transaction_count += 1
        
        # Average per period
        average = total / periods if periods > 0 else total
        
        return {
            'amount': float(average),
            'method': 'average',
            'confidence': self._get_confidence_for_count(transaction_count),
            'transaction_count': transaction_count,
            'category': category.name,
            'total_analyzed': float(total),
        }
    
    def _calculate_trend_estimate(self, transactions, timeframe, periods, category):
        """
        Calculate trend-based estimate
        
        Analyzes spending trend over time and projects forward
        """
        # Group by time periods
        transaction_list = transactions.order_by('transaction_date')
        
        if transaction_list.count() < 3:
            # Not enough data for trend, use average
            return self._calculate_average_estimate(transactions, timeframe, periods, category)
        
        # Calculate trend
        amounts = []
        for txn in transaction_list:
            amount = txn.amount_usd if hasattr(txn, 'amount_usd') and txn.amount_usd else txn.amount
            qty = txn.qty if hasattr(txn, 'qty') and txn.qty else Decimal('1.00')
            if amount:
                amounts.append(float(Decimal(str(amount)) * Decimal(str(qty))))
        
        if len(amounts) >= 3:
            # Simple trend: compare first half vs second half
            mid = len(amounts) // 2
            first_half_avg = sum(amounts[:mid]) / len(amounts[:mid])
            second_half_avg = sum(amounts[mid:]) / len(amounts[mid:])
            
            # Calculate growth rate
            if first_half_avg > 0:
                growth_rate = (second_half_avg - first_half_avg) / first_half_avg
            else:
                growth_rate = 0
            
            # Project forward
            current_avg = sum(amounts) / len(amounts)
            projected = current_avg * (1 + growth_rate)
            
            return {
                'amount': float(projected),
                'method': 'trend',
                'confidence': self._get_confidence_for_count(len(amounts)),
                'transaction_count': len(amounts),
                'category': category.name,
                'growth_rate': float(growth_rate),
                'trend': 'increasing' if growth_rate > 0.05 else 'decreasing' if growth_rate < -0.05 else 'stable',
            }
        
        # Fallback to average
        return self._calculate_average_estimate(transactions, timeframe, periods, category)
    
    def _calculate_ai_estimate(self, transactions, timeframe, periods, category):
        """
        Calculate AI-based estimate
        
        Uses AI suggestion service if available, otherwise falls back to trend
        """
        try:
            # Try to use AI suggestion service
            from .ai_budget_suggestion_service import AIBudgetSuggestionService
            
            ai_service = AIBudgetSuggestionService()
            # AI service integration would go here
            
            # For now, use trend as baseline
            return self._calculate_trend_estimate(transactions, timeframe, periods, category)
            
        except ImportError:
            # AI service not available, use trend
            logger.info("AI suggestion service not available, using trend estimation")
            return self._calculate_trend_estimate(transactions, timeframe, periods, category)
        except Exception as e:
            logger.warning(f"Error in AI estimation, falling back to trend: {e}")
            return self._calculate_trend_estimate(transactions, timeframe, periods, category)
    
    def _calculate_confidence(self, transactions, timeframe):
        """
        Calculate confidence score based on data availability
        
        More transactions = higher confidence
        """
        count = transactions.count()
        return self._get_confidence_for_count(count)
    
    def _get_confidence_for_count(self, count):
        """Get confidence score based on transaction count"""
        if count >= 50:
            return 0.95
        elif count >= 20:
            return 0.85
        elif count >= 10:
            return 0.75
        elif count >= 5:
            return 0.65
        else:
            return 0.50
    
    # ==================================================================
    # BUDGET MODEL INTEGRATION
    # ==================================================================
    
    def estimate_from_budget_history(self, company, department=None, timeframe='monthly'):
        """
        Estimate budget based on historical Budget model data
        
        Complements transaction-based estimation
        """
        try:
            # Get filter
            budget_filter = self.filter_utils.get_combined_filter(
                company=company, department=department
            )
            
            # Get historical budgets
            budgets = Budget.objects.filter(budget_filter).filter(
                is_active=True
            ).select_related('category', 'department')
            
            # Analyze by category
            category_estimates = {}
            
            for budget in budgets:
                if budget.category:
                    cat_name = budget.category.name
                    
                    if cat_name not in category_estimates:
                        category_estimates[cat_name] = {
                            'total': Decimal('0.00'),
                            'count': 0
                        }
                    
                    amount = budget.total_amount if hasattr(budget, 'total_amount') else Decimal('0.00')
                    category_estimates[cat_name]['total'] += amount
                    category_estimates[cat_name]['count'] += 1
            
            # Calculate averages
            for cat_name in category_estimates:
                total = category_estimates[cat_name]['total']
                count = category_estimates[cat_name]['count']
                category_estimates[cat_name]['average'] = float(total / count if count > 0 else 0)
                category_estimates[cat_name]['total'] = float(total)
            
            total_estimate = sum(est['total'] for est in category_estimates.values())
            
            return {
                'method': 'budget_history',
                'timeframe': timeframe,
                'category_estimates': category_estimates,
                'total_estimate': total_estimate,
                'budget_count': budgets.count(),
                'confidence': self._get_confidence_for_count(budgets.count()),
            }
            
        except Exception as e:
            logger.error(f"Error estimating from budget history: {e}", exc_info=True)
            return {'error': str(e)}

