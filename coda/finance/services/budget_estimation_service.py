"""
Budget Estimation Service for CODA Finance System

Automated budget estimation based on historical transaction data including:
- Spending pattern analysis
- Budget estimation methods
- Category-based analysis
- Trend analysis
- Variance analysis
"""

from decimal import Decimal
from typing import Dict, List, Any, Optional
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta
import logging

from ..models import Transaction, Inflow, Budget, CodaBudget, BudgetCategory, Company, Department
from ..utils.calculation_utils import CalculationUtils
from ..utils.filter_utils import FilterUtils
from .base_service import BaseFinanceService

logger = logging.getLogger(__name__)


class BudgetEstimationService(BaseFinanceService):
    """Service for automated budget estimation based on historical data"""
    
    def __init__(self):
        super().__init__()
        self.calculation_utils = CalculationUtils()
        self.filter_utils = FilterUtils()
    
    def analyze_spending_patterns(self, company, department=None, months=3) -> Dict[str, Any]:
        """
        Analyze spending patterns over last N months
        
        Args:
            company: Company object
            department: Department object (optional)
            category: Category object (optional)
            months: Number of months to analyze
            
        Returns:
            Dictionary with spending pattern analysis
        """
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=months * 30)
            
            # Get transactions
            transaction_filter = self.filter_utils.get_combined_filter(
                company=company, department=department,
                start_date=start_date, end_date=end_date
            )
            
            transactions = Transaction.objects.filter(transaction_filter)
            
            # Analyze by category
            category_analysis = {}
            total_spent = Decimal('0.00')
            
            for transaction in transactions:
                if transaction.category:
                    cat_name = transaction.category.name
                    if cat_name not in category_analysis:
                        category_analysis[cat_name] = {
                            'total_spent': Decimal('0.00'),
                            'transaction_count': 0,
                            'average_per_transaction': Decimal('0.00'),
                            'max_transaction': Decimal('0.00'),
                            'min_transaction': Decimal('0.00')
                        }
                    
                    amount = transaction.amount * transaction.qty if transaction.amount and transaction.qty else Decimal('0.00')
                    category_analysis[cat_name]['total_spent'] += amount
                    category_analysis[cat_name]['transaction_count'] += 1
                    total_spent += amount
                    
                    # Track min/max
                    if amount > category_analysis[cat_name]['max_transaction']:
                        category_analysis[cat_name]['max_transaction'] = amount
                    if category_analysis[cat_name]['min_transaction'] == 0 or amount < category_analysis[cat_name]['min_transaction']:
                        category_analysis[cat_name]['min_transaction'] = amount
            
            # Calculate averages
            for cat_name, data in category_analysis.items():
                if data['transaction_count'] > 0:
                    data['average_per_transaction'] = data['total_spent'] / data['transaction_count']
                    data['percentage_of_total'] = (data['total_spent'] / total_spent * 100) if total_spent > 0 else 0
            
            return {
                'total_spent': total_spent,
                'category_analysis': category_analysis,
                'analysis_period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'months': months
                },
                'summary': {
                    'total_categories': len(category_analysis),
                    'average_per_category': total_spent / len(category_analysis) if category_analysis else Decimal('0.00'),
                    'most_spent_category': max(category_analysis.items(), key=lambda x: x[1]['total_spent'])[0] if category_analysis else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing spending patterns: {str(e)}")
            return {'error': str(e)}
    
    def estimate_next_month_budget(self, company, department=None, method='average') -> Dict[str, Any]:
        """
        Estimate budget for next month based on historical data
        
        Args:
            company: Company object
            department: Department object (optional)
            method: Estimation method ('average', 'trend', 'conservative', 'optimistic')
            
        Returns:
            Dictionary with budget estimates
        """
        try:
            analysis = self.analyze_spending_patterns(company, department, months=3)
            
            if 'error' in analysis:
                return analysis
            
            estimates = {}
            recommendations = []
            
            for cat_name, data in analysis['category_analysis'].items():
                if method == 'average':
                    # Use 3-month average
                    estimates[cat_name] = data['average_per_transaction'] * 4  # 4 weeks
                elif method == 'trend':
                    # 10% increase trend
                    estimates[cat_name] = data['total_spent'] * 1.1
                elif method == 'conservative':
                    # 10% decrease for conservative estimate
                    estimates[cat_name] = data['total_spent'] * 0.9
                elif method == 'optimistic':
                    # 20% increase for optimistic estimate
                    estimates[cat_name] = data['total_spent'] * 1.2
                else:
                    estimates[cat_name] = data['total_spent']
            
            # Generate recommendations
            total_estimate = sum(estimates.values())
            if total_estimate > analysis['total_spent']:
                recommendations.append(f"Budget estimate ({total_estimate}) is higher than recent spending ({analysis['total_spent']})")
            elif total_estimate < analysis['total_spent']:
                recommendations.append(f"Budget estimate ({total_estimate}) is lower than recent spending ({analysis['total_spent']})")
            else:
                recommendations.append("Budget estimate matches recent spending patterns")
            
            return {
                'estimates': estimates,
                'total_estimate': total_estimate,
                'method': method,
                'recommendations': recommendations,
                'based_on': analysis['analysis_period']
            }
            
        except Exception as e:
            logger.error(f"Error estimating next month budget: {str(e)}")
            return {'error': str(e)}
    
    def estimate_annual_budget(self, company, department=None, method='ytd_average') -> Dict[str, Any]:
        """
        Estimate annual budget based on historical data
        
        Args:
            company: Company object
            department: Department object (optional)
            method: Estimation method ('ytd_average', 'last_year', 'trend')
            
        Returns:
            Dictionary with annual budget estimates
        """
        try:
            current_year = datetime.now().year
            current_month = datetime.now().month
            
            # Get YTD data
            ytd_filter = self.filter_utils.get_financial_year_filter(current_year)
            if department:
                ytd_filter &= self.filter_utils.get_department_filter(department)
            
            ytd_transactions = Transaction.objects.filter(ytd_filter)
            
            # Calculate YTD totals by category
            ytd_analysis = self.calculation_utils.calculate_category_breakdown(
                ytd_transactions, 'amount', 'qty'
            )
            
            estimates = {}
            total_estimate = Decimal('0.00')
            
            for cat_name, ytd_total in ytd_analysis.items():
                if method == 'ytd_average':
                    # Project based on YTD average
                    monthly_average = ytd_total / current_month if current_month > 0 else Decimal('0.00')
                    estimates[cat_name] = monthly_average * 12
                elif method == 'last_year':
                    # Use last year's data
                    last_year_filter = self.filter_utils.get_financial_year_filter(current_year - 1)
                    if department:
                        last_year_filter &= self.filter_utils.get_department_filter(department)
                    
                    last_year_transactions = Transaction.objects.filter(last_year_filter)
                    last_year_analysis = self.calculation_utils.calculate_category_breakdown(
                        last_year_transactions, 'amount', 'qty'
                    )
                    estimates[cat_name] = last_year_analysis.get(cat_name, Decimal('0.00'))
                elif method == 'trend':
                    # Apply trend analysis
                    trend_data = self.calculation_utils.calculate_trend_analysis(
                        ytd_transactions, 'amount', 'qty', periods=6
                    )
                    trend_factor = 1 + (trend_data['trend_percentage'] / 100)
                    estimates[cat_name] = ytd_total * trend_factor
                else:
                    estimates[cat_name] = ytd_total
                
                total_estimate += estimates[cat_name]
            
            return {
                'estimates': estimates,
                'total_estimate': total_estimate,
                'method': method,
                'ytd_total': sum(ytd_analysis.values()),
                'year': current_year
            }
            
        except Exception as e:
            logger.error(f"Error estimating annual budget: {str(e)}")
            return {'error': str(e)}
    
    def get_budget_variance_analysis(self, company, department=None, category=None) -> Dict[str, Any]:
        """
        Get budget variance analysis comparing actual vs budget
        
        Args:
            company: Company object
            department: Department object (optional)
            category: Category object (optional)
            
        Returns:
            Dictionary with variance analysis
        """
        try:
            # Get actual transactions for current year
            current_year = datetime.now().year
            actual_filter = self.filter_utils.get_financial_year_filter(current_year)
            if department:
                actual_filter &= self.filter_utils.get_department_filter(department)
            if category:
                actual_filter &= self.filter_utils.get_category_filter(category)
            
            actual_transactions = Transaction.objects.filter(actual_filter)
            
            # Get budget data
            budget_filter = self.filter_utils.get_combined_filter(
                company=company, department=department, category=category
            )
            budgets = Budget.objects.filter(budget_filter)
            coda_budgets = CodaBudget.objects.filter(budget_filter)
            
            # Calculate actual totals
            actual_analysis = self.calculation_utils.calculate_category_breakdown(
                actual_transactions, 'amount', 'qty'
            )
            
            # Calculate budget totals
            budget_analysis = {}
            for budget in budgets:
                if budget.category:
                    cat_name = budget.category.name
                    if cat_name not in budget_analysis:
                        budget_analysis[cat_name] = Decimal('0.00')
                    budget_analysis[cat_name] += budget.unit_price * budget.qty if budget.unit_price and budget.qty else Decimal('0.00')
            
            for coda_budget in coda_budgets:
                if coda_budget.category:
                    cat_name = coda_budget.category.name
                    if cat_name not in budget_analysis:
                        budget_analysis[cat_name] = Decimal('0.00')
                    budget_analysis[cat_name] += coda_budget.amount
            
            # Calculate variance
            variance_analysis = {}
            for cat_name in set(list(actual_analysis.keys()) + list(budget_analysis.keys())):
                actual = actual_analysis.get(cat_name, Decimal('0.00'))
                budget = budget_analysis.get(cat_name, Decimal('0.00'))
                variance = actual - budget
                variance_percentage = (variance / budget * 100) if budget > 0 else 0
                
                variance_analysis[cat_name] = {
                    'actual': actual,
                    'budget': budget,
                    'variance': variance,
                    'variance_percentage': variance_percentage,
                    'status': 'over_budget' if variance > 0 else 'under_budget' if variance < 0 else 'on_budget'
                }
            
            return {
                'variance_analysis': variance_analysis,
                'summary': {
                    'total_actual': sum(actual_analysis.values()),
                    'total_budget': sum(budget_analysis.values()),
                    'total_variance': sum(actual_analysis.values()) - sum(budget_analysis.values()),
                    'over_budget_categories': len([v for v in variance_analysis.values() if v['status'] == 'over_budget']),
                    'under_budget_categories': len([v for v in variance_analysis.values() if v['status'] == 'under_budget'])
                }
            }
            
        except Exception as e:
            logger.error(f"Error in budget variance analysis: {str(e)}")
            return {'error': str(e)}
    
    def get_budget_recommendations(self, company, department=None) -> Dict[str, Any]:
        """
        Get budget recommendations based on analysis
        
        Args:
            company: Company object
            department: Department object (optional)
            
        Returns:
            Dictionary with budget recommendations
        """
        try:
            # Get spending analysis
            spending_analysis = self.analyze_spending_patterns(company, department, months=6)
            if 'error' in spending_analysis:
                return spending_analysis
            
            # Get variance analysis
            variance_analysis = self.get_budget_variance_analysis(company, department)
            if 'error' in variance_analysis:
                return variance_analysis
            
            recommendations = []
            
            # Spending pattern recommendations
            if spending_analysis['summary']['most_spent_category']:
                most_spent = spending_analysis['summary']['most_spent_category']
                recommendations.append(f"Focus budget allocation on {most_spent} category (highest spending)")
            
            # Variance recommendations
            over_budget_categories = [
                cat for cat, data in variance_analysis['variance_analysis'].items()
                if data['status'] == 'over_budget'
            ]
            
            if over_budget_categories:
                recommendations.append(f"Review spending in over-budget categories: {', '.join(over_budget_categories)}")
            
            under_budget_categories = [
                cat for cat, data in variance_analysis['variance_analysis'].items()
                if data['status'] == 'under_budget'
            ]
            
            if under_budget_categories:
                recommendations.append(f"Consider reallocating budget from under-budget categories: {', '.join(under_budget_categories)}")
            
            # Trend recommendations
            trend_analysis = self.calculation_utils.calculate_trend_analysis(
                Transaction.objects.filter(
                    self.filter_utils.get_combined_filter(company=company, department=department)
                ), 'amount', 'qty', periods=6
            )
            
            if trend_analysis['trend_direction'] == 'increasing':
                recommendations.append("Spending trend is increasing - consider higher budget allocation")
            elif trend_analysis['trend_direction'] == 'decreasing':
                recommendations.append("Spending trend is decreasing - consider lower budget allocation")
            
            return {
                'recommendations': recommendations,
                'spending_analysis': spending_analysis,
                'variance_analysis': variance_analysis,
                'trend_analysis': trend_analysis
            }
            
        except Exception as e:
            logger.error(f"Error generating budget recommendations: {str(e)}")
            return {'error': str(e)}

