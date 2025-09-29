"""
Enhanced Budget Estimation Service

Provides comprehensive budget estimation capabilities including:
- Transaction-based estimation for accurate weekly/monthly/yearly planning
- Multi-year planning (1-year, 2-year, 5-year plans)
- Investment planning and funding analysis
- CODA development cost estimation
- Trend analysis and AI predictions
"""

from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Q, Sum, Avg, Count, Max, Min
from django.utils import timezone
from datetime import datetime, timedelta
import logging
import statistics

from ..models import Transaction, Inflow, Budget, CodaBudget, BudgetCategory, Company, Department
from ..utils.calculation_utils import CalculationUtils
from ..utils.filter_utils import FilterUtils
from .base_service import BaseFinanceService

logger = logging.getLogger(__name__)


class EnhancedBudgetEstimationService(BaseFinanceService):
    """
    Enhanced service for comprehensive budget estimation and planning
    
    Supports:
    - Transaction-based estimation
    - Multi-timeframe planning
    - Investment analysis
    - CODA development estimation
    - Trend analysis
    """
    
    def __init__(self):
        super().__init__()
        self.calculation_utils = CalculationUtils()
        self.filter_utils = FilterUtils()
    
    def estimate_weekly_budget(self, company, department=None, weeks=4) -> Dict[str, Any]:
        """
        Estimate weekly budget based on historical transaction data
        
        Args:
            company: Company instance
            department: Department instance (optional)
            weeks: Number of weeks to analyze (default: 4)
        
        Returns:
            Dict containing weekly budget estimates by category
        """
        try:
            # Get historical data for the specified number of weeks
            end_date = timezone.now()
            start_date = end_date - timedelta(weeks=weeks)
            
            # Filter transactions
            transactions = Transaction.objects.filter(
                company=company,
                transaction_date__gte=start_date,
                transaction_date__lte=end_date
            )
            
            if department:
                transactions = transactions.filter(department=department)
            
            # Group by category and calculate weekly averages
            category_data = {}
            for transaction in transactions:
                category = transaction.category
                if not category:
                    continue
                
                category_name = category.name
                if category_name not in category_data:
                    category_data[category_name] = {
                        'total_amount': Decimal('0.00'),
                        'transaction_count': 0,
                        'weekly_average': Decimal('0.00'),
                        'subcategories': {}
                    }
                
                # Calculate total amount for this transaction
                amount = (transaction.amount or Decimal('0.00')) * (transaction.qty or Decimal('1.00'))
                category_data[category_name]['total_amount'] += amount
                category_data[category_name]['transaction_count'] += 1
                
                # Track subcategories
                if transaction.subcategory:
                    subcat_name = transaction.subcategory.name
                    if subcat_name not in category_data[category_name]['subcategories']:
                        category_data[category_name]['subcategories'][subcat_name] = Decimal('0.00')
                    category_data[category_name]['subcategories'][subcat_name] += amount
            
            # Calculate weekly averages
            for category_name, data in category_data.items():
                data['weekly_average'] = data['total_amount'] / weeks
                data['confidence'] = min(100, (data['transaction_count'] / weeks) * 25)  # Confidence based on data frequency
            
            return {
                'timeframe': 'weekly',
                'analysis_period_weeks': weeks,
                'categories': category_data,
                'total_weekly_estimate': sum(data['weekly_average'] for data in category_data.values()),
                'generated_at': timezone.now(),
                'method': 'transaction_based'
            }
            
        except Exception as e:
            self.logger.error(f"Error estimating weekly budget: {str(e)}")
            return {'error': str(e)}
    
    def estimate_monthly_budget(self, company, department=None, months=3) -> Dict[str, Any]:
        """
        Estimate monthly budget based on historical transaction data
        
        Args:
            company: Company instance
            department: Department instance (optional)
            months: Number of months to analyze (default: 3)
        
        Returns:
            Dict containing monthly budget estimates by category
        """
        try:
            # Get historical data for the specified number of months
            end_date = timezone.now()
            start_date = end_date - timedelta(days=months * 30)
            
            # Filter transactions
            transactions = Transaction.objects.filter(
                company=company,
                transaction_date__gte=start_date,
                transaction_date__lte=end_date
            )
            
            if department:
                transactions = transactions.filter(department=department)
            
            # Group by category and calculate monthly averages
            category_data = {}
            monthly_totals = {}
            
            for transaction in transactions:
                category = transaction.category
                if not category:
                    continue
                
                category_name = category.name
                if category_name not in category_data:
                    category_data[category_name] = {
                        'total_amount': Decimal('0.00'),
                        'transaction_count': 0,
                        'monthly_average': Decimal('0.00'),
                        'monthly_breakdown': {},
                        'subcategories': {},
                        'trend': 'stable'
                    }
                
                # Calculate total amount for this transaction
                amount = (transaction.amount or Decimal('0.00')) * (transaction.qty or Decimal('1.00'))
                category_data[category_name]['total_amount'] += amount
                category_data[category_name]['transaction_count'] += 1
                
                # Track monthly breakdown
                month_key = transaction.transaction_date.strftime('%Y-%m')
                if month_key not in category_data[category_name]['monthly_breakdown']:
                    category_data[category_name]['monthly_breakdown'][month_key] = Decimal('0.00')
                category_data[category_name]['monthly_breakdown'][month_key] += amount
                
                # Track subcategories
                if transaction.subcategory:
                    subcat_name = transaction.subcategory.name
                    if subcat_name not in category_data[category_name]['subcategories']:
                        category_data[category_name]['subcategories'][subcat_name] = Decimal('0.00')
                    category_data[category_name]['subcategories'][subcat_name] += amount
            
            # Calculate monthly averages and trends
            for category_name, data in category_data.items():
                data['monthly_average'] = data['total_amount'] / months
                
                # Calculate trend
                monthly_values = list(data['monthly_breakdown'].values())
                if len(monthly_values) >= 2:
                    if monthly_values[-1] > monthly_values[-2]:
                        data['trend'] = 'increasing'
                    elif monthly_values[-1] < monthly_values[-2]:
                        data['trend'] = 'decreasing'
                    else:
                        data['trend'] = 'stable'
                
                # Calculate confidence based on data consistency
                if len(monthly_values) >= 2:
                    variance = statistics.variance([float(v) for v in monthly_values])
                    data['confidence'] = max(50, 100 - (variance / float(data['monthly_average']) * 100))
                else:
                    data['confidence'] = 50
            
            return {
                'timeframe': 'monthly',
                'analysis_period_months': months,
                'categories': category_data,
                'total_monthly_estimate': sum(data['monthly_average'] for data in category_data.values()),
                'generated_at': timezone.now(),
                'method': 'transaction_based'
            }
            
        except Exception as e:
            self.logger.error(f"Error estimating monthly budget: {str(e)}")
            return {'error': str(e)}
    
    def estimate_yearly_budget(self, company, department=None, years=1) -> Dict[str, Any]:
        """
        Estimate yearly budget based on historical transaction data
        
        Args:
            company: Company instance
            department: Department instance (optional)
            years: Number of years to analyze (default: 1)
        
        Returns:
            Dict containing yearly budget estimates by category
        """
        try:
            # Get historical data for the specified number of years
            end_date = timezone.now()
            start_date = end_date - timedelta(days=years * 365)
            
            # Filter transactions
            transactions = Transaction.objects.filter(
                company=company,
                transaction_date__gte=start_date,
                transaction_date__lte=end_date
            )
            
            if department:
                transactions = transactions.filter(department=department)
            
            # Group by category and calculate yearly estimates
            category_data = {}
            yearly_breakdown = {}
            
            for transaction in transactions:
                category = transaction.category
                if not category:
                    continue
                
                category_name = category.name
                if category_name not in category_data:
                    category_data[category_name] = {
                        'total_amount': Decimal('0.00'),
                        'transaction_count': 0,
                        'yearly_estimate': Decimal('0.00'),
                        'yearly_breakdown': {},
                        'subcategories': {},
                        'growth_rate': 0.0,
                        'seasonality': {}
                    }
                
                # Calculate total amount for this transaction
                amount = (transaction.amount or Decimal('0.00')) * (transaction.qty or Decimal('1.00'))
                category_data[category_name]['total_amount'] += amount
                category_data[category_name]['transaction_count'] += 1
                
                # Track yearly breakdown
                year = transaction.transaction_date.year
                if year not in category_data[category_name]['yearly_breakdown']:
                    category_data[category_name]['yearly_breakdown'][year] = Decimal('0.00')
                category_data[category_name]['yearly_breakdown'][year] += amount
                
                # Track monthly seasonality
                month = transaction.transaction_date.month
                if month not in category_data[category_name]['seasonality']:
                    category_data[category_name]['seasonality'][month] = Decimal('0.00')
                category_data[category_name]['seasonality'][month] += amount
                
                # Track subcategories
                if transaction.subcategory:
                    subcat_name = transaction.subcategory.name
                    if subcat_name not in category_data[category_name]['subcategories']:
                        category_data[category_name]['subcategories'][subcat_name] = Decimal('0.00')
                    category_data[category_name]['subcategories'][subcat_name] += amount
            
            # Calculate yearly estimates and growth rates
            for category_name, data in category_data.items():
                data['yearly_estimate'] = data['total_amount'] / years
                
                # Calculate growth rate
                yearly_values = list(data['yearly_breakdown'].values())
                if len(yearly_values) >= 2:
                    growth_rate = ((yearly_values[-1] - yearly_values[-2]) / yearly_values[-2]) * 100
                    data['growth_rate'] = round(growth_rate, 2)
                
                # Calculate confidence based on data consistency and growth stability
                if len(yearly_values) >= 2:
                    variance = statistics.variance([float(v) for v in yearly_values])
                    growth_stability = 100 - abs(data['growth_rate'])
                    data['confidence'] = max(60, (100 - (variance / float(data['yearly_estimate']) * 100)) * 0.7 + growth_stability * 0.3)
                else:
                    data['confidence'] = 60
            
            return {
                'timeframe': 'yearly',
                'analysis_period_years': years,
                'categories': category_data,
                'total_yearly_estimate': sum(data['yearly_estimate'] for data in category_data.values()),
                'generated_at': timezone.now(),
                'method': 'transaction_based'
            }
            
        except Exception as e:
            self.logger.error(f"Error estimating yearly budget: {str(e)}")
            return {'error': str(e)}
    
    def create_multi_year_plan(self, company, department=None, plan_years=5) -> Dict[str, Any]:
        """
        Create multi-year budget plan (1-year, 2-year, 5-year)
        
        Args:
            company: Company instance
            department: Department instance (optional)
            plan_years: Number of years for the plan (1, 2, or 5)
        
        Returns:
            Dict containing multi-year budget plan
        """
        try:
            # Get historical data for trend analysis
            historical_data = self.estimate_yearly_budget(company, department, years=min(3, plan_years))
            
            if 'error' in historical_data:
                return historical_data
            
            # Create multi-year projections
            multi_year_plan = {
                'plan_years': plan_years,
                'company': company.name,
                'department': department.name if department else 'All Departments',
                'years': {},
                'total_investment_required': Decimal('0.00'),
                'funding_recommendations': [],
                'risk_assessment': {},
                'generated_at': timezone.now()
            }
            
            # Project budgets for each year
            for year in range(plan_years):
                current_year = timezone.now().year + year
                year_data = {
                    'year': current_year,
                    'categories': {},
                    'total_estimated': Decimal('0.00'),
                    'investment_required': Decimal('0.00'),
                    'operational_budget': Decimal('0.00')
                }
                
                # Project each category
                for category_name, category_data in historical_data['categories'].items():
                    # Apply growth rate to project future budgets
                    growth_rate = category_data.get('growth_rate', 0) / 100
                    projected_amount = category_data['yearly_estimate'] * (1 + growth_rate) ** year
                    
                    year_data['categories'][category_name] = {
                        'estimated_amount': round(projected_amount, 2),
                        'growth_rate': category_data.get('growth_rate', 0),
                        'confidence': max(50, category_data.get('confidence', 60) - (year * 10)),
                        'subcategories': category_data.get('subcategories', {}),
                        'seasonality': category_data.get('seasonality', {})
                    }
                    
                    year_data['total_estimated'] += projected_amount
                
                # Identify investment opportunities
                investment_categories = ['Infrastructure', 'Technology', 'Equipment', 'Software']
                for category_name in investment_categories:
                    if category_name in year_data['categories']:
                        year_data['investment_required'] += year_data['categories'][category_name]['estimated_amount']
                        year_data['operational_budget'] = year_data['total_estimated'] - year_data['investment_required']
                
                multi_year_plan['years'][current_year] = year_data
                multi_year_plan['total_investment_required'] += year_data['investment_required']
            
            # Generate funding recommendations
            multi_year_plan['funding_recommendations'] = self._generate_funding_recommendations(
                multi_year_plan['total_investment_required']
            )
            
            # Risk assessment
            multi_year_plan['risk_assessment'] = self._assess_plan_risks(multi_year_plan)
            
            return multi_year_plan
            
        except Exception as e:
            self.logger.error(f"Error creating multi-year plan: {str(e)}")
            return {'error': str(e)}
    
    def estimate_coda_development_cost(self, app_models_count, custom_tasks=None) -> Dict[str, Any]:
        """
        Estimate CODA development cost using the existing coda_budget_estimation logic
        
        Args:
            app_models_count: Number of models in the application
            custom_tasks: Custom task configuration (optional)
        
        Returns:
            Dict containing development cost estimation
        """
        try:
            # Default CODA development tasks (from coda_budget_estimation)
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
            one_model_calculation = 0
            task_breakdown = {}
            
            for task_name, task_config in tasks.items():
                task_cost = (
                    task_config.get("quantity", 1) *
                    task_config.get("hour", 1) *
                    task_config.get("unit_price", 30)
                )
                one_model_calculation += task_cost
                task_breakdown[task_name] = {
                    'cost': task_cost,
                    'hours': task_config.get("hour", 1),
                    'quantity': task_config.get("quantity", 1),
                    'unit_price': task_config.get("unit_price", 30)
                }
            
            # Calculate total cost
            total_cost = one_model_calculation * app_models_count
            
            return {
                'app_models_count': app_models_count,
                'cost_per_model': one_model_calculation,
                'total_estimated_cost': total_cost,
                'task_breakdown': task_breakdown,
                'estimated_hours': sum(task['hours'] * task['quantity'] for task in task_breakdown.values()) * app_models_count,
                'method': 'coda_development_estimation',
                'generated_at': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error estimating CODA development cost: {str(e)}")
            return {'error': str(e)}
    
    def _generate_funding_recommendations(self, total_investment) -> List[Dict[str, Any]]:
        """Generate funding recommendations based on investment amount"""
        recommendations = []
        
        if total_investment < 10000:
            recommendations.append({
                'source': 'Internal Cash Flow',
                'amount': total_investment,
                'percentage': 100,
                'description': 'Small investment can be funded from internal cash flow'
            })
        elif total_investment < 50000:
            recommendations.append({
                'source': 'Internal Cash Flow',
                'amount': total_investment * 0.6,
                'percentage': 60,
                'description': 'Primary funding from internal cash flow'
            })
            recommendations.append({
                'source': 'Short-term Loan',
                'amount': total_investment * 0.4,
                'percentage': 40,
                'description': 'Supplement with short-term loan'
            })
        else:
            recommendations.append({
                'source': 'Internal Cash Flow',
                'amount': total_investment * 0.3,
                'percentage': 30,
                'description': 'Partial funding from internal cash flow'
            })
            recommendations.append({
                'source': 'Long-term Loan',
                'amount': total_investment * 0.5,
                'percentage': 50,
                'description': 'Primary funding from long-term loan'
            })
            recommendations.append({
                'source': 'Investment/Equity',
                'amount': total_investment * 0.2,
                'percentage': 20,
                'description': 'Consider seeking external investment'
            })
        
        return recommendations
    
    def _assess_plan_risks(self, multi_year_plan) -> Dict[str, Any]:
        """Assess risks for the multi-year plan"""
        risks = {
            'low_risk': [],
            'medium_risk': [],
            'high_risk': [],
            'mitigation_strategies': []
        }
        
        # Analyze confidence levels
        low_confidence_categories = []
        for year_data in multi_year_plan['years'].values():
            for category_name, category_data in year_data['categories'].items():
                if category_data.get('confidence', 60) < 70:
                    low_confidence_categories.append(category_name)
        
        if low_confidence_categories:
            risks['medium_risk'].append({
                'risk': 'Low confidence in budget estimates',
                'categories': low_confidence_categories,
                'impact': 'Budget overruns possible'
            })
            risks['mitigation_strategies'].append(
                'Increase data collection and analysis for low-confidence categories'
            )
        
        # Analyze growth rates
        high_growth_categories = []
        for year_data in multi_year_plan['years'].values():
            for category_name, category_data in year_data['categories'].items():
                if category_data.get('growth_rate', 0) > 20:
                    high_growth_categories.append(category_name)
        
        if high_growth_categories:
            risks['high_risk'].append({
                'risk': 'High growth rate projections',
                'categories': high_growth_categories,
                'impact': 'Unrealistic budget expectations'
            })
            risks['mitigation_strategies'].append(
                'Review and validate high growth rate assumptions'
            )
        
        return risks
    
    def analyze_investment_opportunities(self, company, department=None) -> Dict[str, Any]:
        """
        Analyze investment opportunities for the company
        
        Args:
            company: Company instance
            department: Department instance (optional)
        
        Returns:
            Dict containing investment analysis and recommendations
        """
        try:
            # Get historical data for analysis
            historical_data = self.estimate_yearly_budget(company, department, years=2)
            
            if 'error' in historical_data:
                return historical_data
            
            # Analyze investment opportunities
            investment_opportunities = []
            total_investment_potential = Decimal('0.00')
            
            # Identify high-growth categories as investment opportunities
            for category_name, category_data in historical_data['categories'].items():
                growth_rate = category_data.get('growth_rate', 0)
                yearly_estimate = category_data.get('yearly_estimate', Decimal('0.00'))
                
                if growth_rate > 10:  # High growth categories
                    investment_opportunities.append({
                        'category': category_name,
                        'current_spending': yearly_estimate,
                        'growth_rate': growth_rate,
                        'investment_potential': yearly_estimate * (growth_rate / 100),
                        'roi_estimate': min(50, growth_rate * 2),  # Conservative ROI estimate
                        'payback_period': max(12, 24 - growth_rate),  # Months
                        'risk_level': 'medium' if growth_rate < 25 else 'high',
                        'recommendation': 'Consider increasing investment' if growth_rate > 15 else 'Monitor growth'
                    })
                    total_investment_potential += yearly_estimate * (growth_rate / 100)
            
            # Generate funding recommendations
            funding_recommendations = self._generate_funding_recommendations(total_investment_potential)
            
            # Risk assessment
            risk_assessment = {
                'overall_risk': 'low',
                'high_risk_opportunities': [opp for opp in investment_opportunities if opp['risk_level'] == 'high'],
                'medium_risk_opportunities': [opp for opp in investment_opportunities if opp['risk_level'] == 'medium'],
                'mitigation_strategies': [
                    'Diversify investment across multiple categories',
                    'Start with low-risk, high-ROI opportunities',
                    'Monitor market conditions regularly',
                    'Maintain cash reserves for unexpected opportunities'
                ]
            }
            
            # Calculate overall risk level
            if len(risk_assessment['high_risk_opportunities']) > 2:
                risk_assessment['overall_risk'] = 'high'
            elif len(risk_assessment['medium_risk_opportunities']) > 3:
                risk_assessment['overall_risk'] = 'medium'
            
            return {
                'company': company.name,
                'department': department.name if department else 'All Departments',
                'investment_opportunities': investment_opportunities,
                'total_investment_potential': total_investment_potential,
                'funding_recommendations': funding_recommendations,
                'risk_assessment': risk_assessment,
                'analysis_date': timezone.now(),
                'method': 'growth_analysis'
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing investment opportunities: {str(e)}")
            return {'error': str(e)}
    
    def get_funding_recommendations(self, company, department=None, investment_amount=None) -> Dict[str, Any]:
        """
        Get funding recommendations for investment planning
        
        Args:
            company: Company instance
            department: Department instance (optional)
            investment_amount: Specific investment amount (optional)
        
        Returns:
            Dict containing funding recommendations
        """
        try:
            # If no investment amount provided, get from investment analysis
            if not investment_amount:
                investment_analysis = self.analyze_investment_opportunities(company, department)
                if 'error' in investment_analysis:
                    return investment_analysis
                investment_amount = investment_analysis.get('total_investment_potential', Decimal('0.00'))
            
            # Generate funding recommendations
            funding_recommendations = self._generate_funding_recommendations(investment_amount)
            
            # Add additional analysis
            total_investment = investment_amount
            internal_cash_flow = sum(rec['amount'] for rec in funding_recommendations if 'Internal' in rec['source'])
            external_funding = sum(rec['amount'] for rec in funding_recommendations if 'Internal' not in rec['source'])
            
            return {
                'company': company.name,
                'department': department.name if department else 'All Departments',
                'total_investment_required': total_investment,
                'funding_recommendations': funding_recommendations,
                'internal_cash_flow_percentage': (internal_cash_flow / total_investment * 100) if total_investment > 0 else 0,
                'external_funding_percentage': (external_funding / total_investment * 100) if total_investment > 0 else 0,
                'recommended_approach': self._get_recommended_funding_approach(investment_amount),
                'risk_assessment': self._assess_funding_risks(investment_amount),
                'generated_at': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting funding recommendations: {str(e)}")
            return {'error': str(e)}
    
    def _get_recommended_funding_approach(self, investment_amount) -> str:
        """Get recommended funding approach based on investment amount"""
        if investment_amount < 10000:
            return "Internal cash flow - Small investment can be funded internally"
        elif investment_amount < 50000:
            return "Mixed approach - Primary internal funding with short-term loan support"
        elif investment_amount < 200000:
            return "External funding - Consider long-term loan or equity investment"
        else:
            return "Strategic funding - Multiple funding sources including equity and debt"
    
    def _assess_funding_risks(self, investment_amount) -> Dict[str, Any]:
        """Assess funding risks based on investment amount"""
        risks = {
            'low_risk': [],
            'medium_risk': [],
            'high_risk': [],
            'mitigation_strategies': []
        }
        
        if investment_amount < 10000:
            risks['low_risk'].append("Small investment amount - low financial risk")
            risks['mitigation_strategies'].append("Monitor cash flow to ensure sufficient liquidity")
        elif investment_amount < 50000:
            risks['medium_risk'].append("Moderate investment - requires careful planning")
            risks['mitigation_strategies'].append("Prepare detailed financial projections")
            risks['mitigation_strategies'].append("Consider phased implementation")
        else:
            risks['high_risk'].append("Large investment - significant financial commitment")
            risks['high_risk'].append("Requires external funding - dependency on lenders/investors")
            risks['mitigation_strategies'].append("Conduct thorough due diligence")
            risks['mitigation_strategies'].append("Prepare comprehensive business plan")
            risks['mitigation_strategies'].append("Consider insurance and risk management")
        
        return risks
