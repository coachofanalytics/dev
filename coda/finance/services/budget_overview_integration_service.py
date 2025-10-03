"""
Budget Overview Integration Service for CODA Finance System

Provides comprehensive integration of salary data into the main budget overview
dashboard, including historical trending, department comparisons, and real-time
updates for the complete salary-budget integration system.

Features:
- Salary totals integration into main budget overview
- Historical trending and analytics
- Department comparisons and breakdowns
- Real-time budget calculations
- Performance metrics and KPIs

Created: October 2025
Phase: Final Budget Integration
"""

import logging
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from django.db.models import Q, Sum, Avg, Count
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models.functions import TruncMonth, TruncYear

from finance.models import Budget, BudgetEstimateProjection, BudgetCategory, BudgetSubCategory
from management.models import TaskHistory
from accounts.models import Department
from management.services.employee_compliance_service import EmployeeComplianceService
from finance.services.integrated_budget_service import IntegratedBudgetService

User = get_user_model()
logger = logging.getLogger(__name__)


class BudgetOverviewIntegrationService:
    """
    Service for integrating salary data into the main budget overview dashboard.
    
    Provides comprehensive budget analysis including salary integration,
    historical trending, and department comparisons.
    """
    
    def __init__(self):
        self.compliance_service = EmployeeComplianceService()
        self.integrated_service = IntegratedBudgetService()
        self.logger = logging.getLogger(__name__)
    
    def get_comprehensive_budget_overview(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Get comprehensive budget overview including salary integration.
        
        Returns complete budget analysis with:
        - Salary totals from compliant employees
        - Other budget items and projections
        - Historical comparisons
        - Department breakdowns
        - Performance metrics
        """
        try:
            self.logger.info(f"Generating comprehensive budget overview for {target_month}/{target_year}")
            
            # Get salary data
            salary_data = self._get_salary_integration_data(target_month, target_year)
            
            # Get budget items data
            budget_items_data = self._get_budget_items_data(target_month, target_year)
            
            # Get historical data for trending
            historical_data = self._get_historical_trending_data(target_month, target_year)
            
            # Get department comparisons
            department_data = self._get_department_comparisons(target_month, target_year)
            
            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(target_month, target_year)
            
            # Calculate totals and summaries
            totals = self._calculate_comprehensive_totals(salary_data, budget_items_data)
            
            return {
                'period': f"{target_month}/{target_year}",
                'generated_at': timezone.now(),
                'totals': totals,
                'salary_data': salary_data,
                'budget_items_data': budget_items_data,
                'historical_data': historical_data,
                'department_data': department_data,
                'performance_metrics': performance_metrics,
                'summary': {
                    'total_budget': totals['grand_total'],
                    'salary_percentage': (totals['total_salaries'] / totals['grand_total'] * 100) if totals['grand_total'] > 0 else 0,
                    'budget_items_percentage': (totals['total_budget_items'] / totals['grand_total'] * 100) if totals['grand_total'] > 0 else 0,
                    'compliant_employees': salary_data['compliant_count'],
                    'total_employees': salary_data['total_employees'],
                    'compliance_rate': (salary_data['compliant_count'] / salary_data['total_employees'] * 100) if salary_data['total_employees'] > 0 else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive budget overview: {e}")
            return {'error': str(e)}
    
    def get_historical_trending_analysis(self, months_back: int = 12) -> Dict[str, Any]:
        """
        Get historical trending analysis for budget and salary data.
        
        Returns trending data for the specified number of months back,
        including growth rates, patterns, and forecasts.
        """
        try:
            self.logger.info(f"Generating historical trending analysis for {months_back} months")
            
            # Get current date
            current_date = timezone.now().date()
            current_month = current_date.month
            current_year = current_date.year
            
            # Generate date range
            trending_data = []
            for i in range(months_back):
                # Calculate target month/year (going backwards)
                target_month = current_month - i
                target_year = current_year
                
                # Handle year rollover
                while target_month <= 0:
                    target_month += 12
                    target_year -= 1
                
                # Get data for this month
                month_data = self._get_monthly_trending_data(target_month, target_year)
                month_data['month'] = target_month
                month_data['year'] = target_year
                month_data['period'] = f"{target_month}/{target_year}"
                
                trending_data.append(month_data)
            
            # Reverse to get chronological order (oldest first)
            trending_data.reverse()
            
            # Calculate growth rates and patterns
            growth_analysis = self._calculate_growth_analysis(trending_data)
            
            # Generate forecasts
            forecast_data = self._generate_forecasts(trending_data)
            
            return {
                'trending_data': trending_data,
                'growth_analysis': growth_analysis,
                'forecast_data': forecast_data,
                'analysis_period': f"{months_back} months",
                'generated_at': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating historical trending analysis: {e}")
            return {'error': str(e)}
    
    def get_department_budget_analysis(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Get comprehensive department budget analysis.
        
        Returns detailed breakdown by department including:
        - Salary costs per department
        - Budget allocations per department
        - Compliance rates per department
        - Performance comparisons
        """
        try:
            self.logger.info(f"Generating department budget analysis for {target_month}/{target_year}")
            
            # Get all departments
            departments = Department.objects.all()
            
            department_analysis = []
            total_salaries = Decimal('0.00')
            total_budgets = Decimal('0.00')
            
            for department in departments:
                # Get department-specific data
                dept_data = self._get_department_specific_data(department, target_month, target_year)
                
                if dept_data['employee_count'] > 0:  # Only include departments with employees
                    department_analysis.append(dept_data)
                    total_salaries += dept_data['total_salary']
                    total_budgets += dept_data['total_budget']
            
            # Calculate department rankings and comparisons
            rankings = self._calculate_department_rankings(department_analysis)
            
            # Calculate department efficiency metrics
            efficiency_metrics = self._calculate_department_efficiency(department_analysis)
            
            return {
                'period': f"{target_month}/{target_year}",
                'departments': department_analysis,
                'rankings': rankings,
                'efficiency_metrics': efficiency_metrics,
                'totals': {
                    'total_salaries': total_salaries,
                    'total_budgets': total_budgets,
                    'department_count': len(department_analysis)
                },
                'generated_at': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating department budget analysis: {e}")
            return {'error': str(e)}
    
    def get_budget_performance_kpis(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """
        Get key performance indicators for budget management.
        
        Returns comprehensive KPIs including:
        - Budget vs actual spending
        - Salary efficiency metrics
        - Compliance performance
        - Cost per employee metrics
        - Budget utilization rates
        """
        try:
            self.logger.info(f"Generating budget performance KPIs for {target_month}/{target_year}")
            
            # Get comprehensive overview data
            overview_data = self.get_comprehensive_budget_overview(target_month, target_year)
            
            if 'error' in overview_data:
                return overview_data
            
            # Extract key metrics
            totals = overview_data['totals']
            salary_data = overview_data['salary_data']
            performance_metrics = overview_data['performance_metrics']
            
            # Calculate KPIs
            kpis = {
                'budget_efficiency': {
                    'total_budget': float(totals['grand_total']),
                    'salary_ratio': float(totals['total_salaries'] / totals['grand_total']) if totals['grand_total'] > 0 else 0,
                    'operational_ratio': float(totals['total_budget_items'] / totals['grand_total']) if totals['grand_total'] > 0 else 0
                },
                'salary_performance': {
                    'total_salary_cost': float(totals['total_salaries']),
                    'average_salary_per_employee': float(totals['total_salaries'] / salary_data['compliant_count']) if salary_data['compliant_count'] > 0 else 0,
                    'salary_per_compliant_employee': float(totals['total_salaries'] / salary_data['compliant_count']) if salary_data['compliant_count'] > 0 else 0,
                    'cost_per_percentage_compliance': float(totals['total_salaries'] / performance_metrics['average_compliance_rate']) if performance_metrics['average_compliance_rate'] > 0 else 0
                },
                'compliance_performance': {
                    'overall_compliance_rate': performance_metrics['average_compliance_rate'],
                    'compliant_employee_count': salary_data['compliant_count'],
                    'total_employee_count': salary_data['total_employees'],
                    'compliance_cost_efficiency': float(totals['total_salaries'] / salary_data['compliant_count']) if salary_data['compliant_count'] > 0 else 0
                },
                'budget_utilization': {
                    'budget_items_count': overview_data['budget_items_data']['item_count'],
                    'average_budget_item_value': float(totals['total_budget_items'] / overview_data['budget_items_data']['item_count']) if overview_data['budget_items_data']['item_count'] > 0 else 0,
                    'budget_item_efficiency': performance_metrics.get('budget_item_efficiency', 0)
                },
                'operational_metrics': {
                    'employees_per_department': performance_metrics.get('employees_per_department', 0),
                    'budget_approval_rate': performance_metrics.get('approval_rate', 0),
                    'salary_processing_time': performance_metrics.get('processing_time', 0)
                }
            }
            
            # Calculate performance scores
            performance_scores = self._calculate_performance_scores(kpis)
            
            return {
                'period': f"{target_month}/{target_year}",
                'kpis': kpis,
                'performance_scores': performance_scores,
                'generated_at': timezone.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating budget performance KPIs: {e}")
            return {'error': str(e)}
    
    def _get_salary_integration_data(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """Get salary data for integration into budget overview."""
        try:
            salary_data = self.integrated_service.get_salary_dashboard_data(target_month, target_year)
            
            if 'error' in salary_data:
                return {
                    'total_amount': Decimal('0.00'),
                    'compliant_count': 0,
                    'non_compliant_count': 0,
                    'total_employees': 0,
                    'employees': []
                }
            
            return salary_data['salary_data']
            
        except Exception as e:
            self.logger.error(f"Error getting salary integration data: {e}")
            return {
                'total_amount': Decimal('0.00'),
                'compliant_count': 0,
                'non_compliant_count': 0,
                'total_employees': 0,
                'employees': []
            }
    
    def _get_budget_items_data(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """Get budget items data for integration."""
        try:
            # Get budget projections directly since the method name is different
            budget_projections = BudgetEstimateProjection.objects.filter(
                status='submitted',
                total_estimate__gt=0
            )
            
            total_amount = sum(proj.total_estimate for proj in budget_projections)
            budget_items = {
                'item_count': budget_projections.count(),
                'total_amount': total_amount,
                'items': list(budget_projections.values('id', 'company__name', 'department__name', 'total_estimate'))
            }
            
            return budget_items
            
        except Exception as e:
            self.logger.error(f"Error getting budget items data: {e}")
            return {
                'item_count': 0,
                'total_amount': Decimal('0.00'),
                'items': []
            }
    
    def _get_historical_trending_data(self, target_month: int, target_year: int) -> List[Dict[str, Any]]:
        """Get historical trending data for comparison."""
        # Get data for previous months for comparison
        historical_data = []
        
        for months_back in [1, 2, 3, 6, 12]:
            compare_month = target_month - months_back
            compare_year = target_year
            
            while compare_month <= 0:
                compare_month += 12
                compare_year -= 1
            
            month_data = self._get_monthly_trending_data(compare_month, compare_year)
            month_data['months_back'] = months_back
            historical_data.append(month_data)
        
        return historical_data
    
    def _get_monthly_trending_data(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """Get monthly trending data for a specific month."""
        try:
            # Get salary data
            salary_data = self._get_salary_integration_data(target_month, target_year)
            
            # Get budget items data
            budget_items_data = self._get_budget_items_data(target_month, target_year)
            
            return {
                'total_salary': salary_data['total_amount'],
                'total_budget_items': budget_items_data['total_amount'],
                'grand_total': salary_data['total_amount'] + budget_items_data['total_amount'],
                'compliant_employees': salary_data['compliant_count'],
                'total_employees': salary_data['total_employees'],
                'compliance_rate': (salary_data['compliant_count'] / salary_data['total_employees'] * 100) if salary_data['total_employees'] > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error getting monthly trending data: {e}")
            return {
                'total_salary': Decimal('0.00'),
                'total_budget_items': Decimal('0.00'),
                'grand_total': Decimal('0.00'),
                'compliant_employees': 0,
                'total_employees': 0,
                'compliance_rate': 0
            }
    
    def _get_department_comparisons(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """Get department comparison data."""
        try:
            departments = Department.objects.all()
            
            department_data = []
            for department in departments:
                # Get department-specific compliance and salary data
                dept_compliance = self.compliance_service.get_department_compliance_report(department.name, target_month, target_year)
                
                department_data.append({
                    'department_name': department.name,
                    'employee_count': dept_compliance.get('total_employees', 0),
                    'compliant_count': dept_compliance.get('compliant_count', 0),
                    'compliance_rate': dept_compliance.get('compliance_rate', 0),
                    'total_salary': dept_compliance.get('total_salary', Decimal('0.00'))
                })
            
            return {
                'departments': department_data,
                'department_count': len(department_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting department comparisons: {e}")
            return {'departments': [], 'department_count': 0}
    
    def _calculate_performance_metrics(self, target_month: int, target_year: int) -> Dict[str, Any]:
        """Calculate performance metrics for the budget overview."""
        try:
            # Get compliance summary
            compliance_summary = self.compliance_service.get_compliance_summary()
            
            # Get salary data
            salary_data = self._get_salary_integration_data(target_month, target_year)
            
            return {
                'average_compliance_rate': compliance_summary.get('average_compliance_rate', 0),
                'total_compliance_rate': (salary_data['compliant_count'] / salary_data['total_employees'] * 100) if salary_data['total_employees'] > 0 else 0,
                'salary_efficiency': float(salary_data['total_amount'] / salary_data['compliant_count']) if salary_data['compliant_count'] > 0 else 0,
                'employees_per_department': salary_data['total_employees'] / Department.objects.count() if Department.objects.count() > 0 else 0,
                'budget_item_efficiency': 0,  # Would be calculated based on actual vs projected
                'approval_rate': 100,  # Would be calculated based on approval success rate
                'processing_time': 0  # Would be calculated based on processing metrics
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating performance metrics: {e}")
            return {
                'average_compliance_rate': 0,
                'total_compliance_rate': 0,
                'salary_efficiency': 0,
                'employees_per_department': 0,
                'budget_item_efficiency': 0,
                'approval_rate': 0,
                'processing_time': 0
            }
    
    def _calculate_comprehensive_totals(self, salary_data: Dict[str, Any], budget_items_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive totals for the budget overview."""
        total_salaries = salary_data.get('total_amount', Decimal('0.00'))
        total_budget_items = budget_items_data.get('total_amount', Decimal('0.00'))
        grand_total = total_salaries + total_budget_items
        
        return {
            'total_salaries': total_salaries,
            'total_budget_items': total_budget_items,
            'grand_total': grand_total
        }
    
    def _get_department_specific_data(self, department: Department, target_month: int, target_year: int) -> Dict[str, Any]:
        """Get department-specific data for analysis."""
        try:
            # Get department compliance data
            dept_compliance = self.compliance_service.get_department_compliance_report(department.name, target_month, target_year)
            
            # Get department budget data
            dept_budgets = BudgetEstimateProjection.objects.filter(
                department=department,
                status='submitted',
                total_estimate__gt=0
            ).aggregate(
                total_budget=Sum('total_estimate'),
                item_count=Count('id')
            )
            
            return {
                'department_id': department.id,
                'department_name': department.name,
                'employee_count': dept_compliance.get('total_employees', 0),
                'compliant_count': dept_compliance.get('compliant_count', 0),
                'compliance_rate': dept_compliance.get('compliance_rate', 0),
                'total_salary': dept_compliance.get('total_salary', Decimal('0.00')),
                'total_budget': dept_budgets.get('total_budget', Decimal('0.00')) or Decimal('0.00'),
                'budget_item_count': dept_budgets.get('item_count', 0)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting department specific data: {e}")
            return {
                'department_id': department.id,
                'department_name': department.name,
                'employee_count': 0,
                'compliant_count': 0,
                'compliance_rate': 0,
                'total_salary': Decimal('0.00'),
                'total_budget': Decimal('0.00'),
                'budget_item_count': 0
            }
    
    def _calculate_department_rankings(self, department_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate department rankings and comparisons."""
        try:
            # Sort departments by different criteria
            by_compliance = sorted(department_analysis, key=lambda x: x['compliance_rate'], reverse=True)
            by_salary = sorted(department_analysis, key=lambda x: x['total_salary'], reverse=True)
            by_efficiency = sorted(department_analysis, key=lambda x: x['total_salary'] / x['employee_count'] if x['employee_count'] > 0 else 0, reverse=True)
            
            return {
                'by_compliance': [{'department': d['department_name'], 'rate': d['compliance_rate']} for d in by_compliance[:5]],
                'by_salary': [{'department': d['department_name'], 'amount': float(d['total_salary'])} for d in by_salary[:5]],
                'by_efficiency': [{'department': d['department_name'], 'efficiency': float(d['total_salary'] / d['employee_count']) if d['employee_count'] > 0 else 0} for d in by_efficiency[:5]]
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating department rankings: {e}")
            return {'by_compliance': [], 'by_salary': [], 'by_efficiency': []}
    
    def _calculate_department_efficiency(self, department_analysis: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate department efficiency metrics."""
        try:
            total_salary = sum(float(d['total_salary']) for d in department_analysis)
            total_employees = sum(d['employee_count'] for d in department_analysis)
            total_compliant = sum(d['compliant_count'] for d in department_analysis)
            
            return {
                'average_salary_per_employee': total_salary / total_employees if total_employees > 0 else 0,
                'average_compliance_rate': (total_compliant / total_employees * 100) if total_employees > 0 else 0,
                'salary_efficiency_score': total_salary / total_compliant if total_compliant > 0 else 0,
                'department_count': len(department_analysis)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating department efficiency: {e}")
            return {
                'average_salary_per_employee': 0,
                'average_compliance_rate': 0,
                'salary_efficiency_score': 0,
                'department_count': 0
            }
    
    def _calculate_growth_analysis(self, trending_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate growth analysis from trending data."""
        try:
            if len(trending_data) < 2:
                return {'error': 'Insufficient data for growth analysis'}
            
            # Calculate month-over-month growth
            current = trending_data[-1]
            previous = trending_data[-2]
            
            salary_growth = ((current['total_salary'] - previous['total_salary']) / previous['total_salary'] * 100) if previous['total_salary'] > 0 else 0
            budget_growth = ((current['total_budget_items'] - previous['total_budget_items']) / previous['total_budget_items'] * 100) if previous['total_budget_items'] > 0 else 0
            compliance_growth = current['compliance_rate'] - previous['compliance_rate']
            
            # Calculate overall trends
            first_month = trending_data[0]
            last_month = trending_data[-1]
            
            overall_salary_growth = ((last_month['total_salary'] - first_month['total_salary']) / first_month['total_salary'] * 100) if first_month['total_salary'] > 0 else 0
            overall_budget_growth = ((last_month['total_budget_items'] - first_month['total_budget_items']) / first_month['total_budget_items'] * 100) if first_month['total_budget_items'] > 0 else 0
            overall_compliance_change = last_month['compliance_rate'] - first_month['compliance_rate']
            
            return {
                'month_over_month': {
                    'salary_growth': round(salary_growth, 2),
                    'budget_growth': round(budget_growth, 2),
                    'compliance_change': round(compliance_growth, 2)
                },
                'overall_trend': {
                    'salary_growth': round(overall_salary_growth, 2),
                    'budget_growth': round(overall_budget_growth, 2),
                    'compliance_change': round(overall_compliance_change, 2)
                },
                'period_months': len(trending_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating growth analysis: {e}")
            return {'error': str(e)}
    
    def _generate_forecasts(self, trending_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate forecasts based on trending data."""
        try:
            if len(trending_data) < 3:
                return {'error': 'Insufficient data for forecasting'}
            
            # Simple linear regression for forecasting
            # In a real implementation, this would use more sophisticated forecasting models
            
            recent_data = trending_data[-3:]  # Use last 3 months for trend
            
            # Calculate average growth rates
            salary_growth_rates = []
            budget_growth_rates = []
            compliance_changes = []
            
            for i in range(1, len(recent_data)):
                prev = recent_data[i-1]
                curr = recent_data[i]
                
                if prev['total_salary'] > 0:
                    salary_growth_rates.append((curr['total_salary'] - prev['total_salary']) / prev['total_salary'])
                if prev['total_budget_items'] > 0:
                    budget_growth_rates.append((curr['total_budget_items'] - prev['total_budget_items']) / prev['total_budget_items'])
                compliance_changes.append(curr['compliance_rate'] - prev['compliance_rate'])
            
            avg_salary_growth = sum(salary_growth_rates) / len(salary_growth_rates) if salary_growth_rates else 0
            avg_budget_growth = sum(budget_growth_rates) / len(budget_growth_rates) if budget_growth_rates else 0
            avg_compliance_change = sum(compliance_changes) / len(compliance_changes) if compliance_changes else 0
            
            # Generate 3-month forecast
            last_month = recent_data[-1]
            
            forecast = {
                'next_month': {
                    'total_salary': float(last_month['total_salary'] * (1 + avg_salary_growth)),
                    'total_budget_items': float(last_month['total_budget_items'] * (1 + avg_budget_growth)),
                    'compliance_rate': last_month['compliance_rate'] + avg_compliance_change
                },
                'two_months': {
                    'total_salary': float(last_month['total_salary'] * (1 + avg_salary_growth) ** 2),
                    'total_budget_items': float(last_month['total_budget_items'] * (1 + avg_budget_growth) ** 2),
                    'compliance_rate': last_month['compliance_rate'] + (avg_compliance_change * 2)
                },
                'three_months': {
                    'total_salary': float(last_month['total_salary'] * (1 + avg_salary_growth) ** 3),
                    'total_budget_items': float(last_month['total_budget_items'] * (1 + avg_budget_growth) ** 3),
                    'compliance_rate': last_month['compliance_rate'] + (avg_compliance_change * 3)
                }
            }
            
            return {
                'forecast': forecast,
                'growth_rates': {
                    'salary_growth_rate': round(avg_salary_growth * 100, 2),
                    'budget_growth_rate': round(avg_budget_growth * 100, 2),
                    'compliance_change_rate': round(avg_compliance_change, 2)
                },
                'confidence': 'medium',  # Would be calculated based on data consistency
                'forecast_period': '3 months'
            }
            
        except Exception as e:
            self.logger.error(f"Error generating forecasts: {e}")
            return {'error': str(e)}
    
    def _calculate_performance_scores(self, kpis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate performance scores based on KPIs."""
        try:
            # Calculate performance scores (0-100 scale)
            scores = {
                'budget_efficiency_score': min(100, max(0, (1 - kpis['budget_efficiency']['salary_ratio']) * 100)),
                'salary_performance_score': min(100, max(0, (kpis['compliance_performance']['overall_compliance_rate'] / 33) * 100)),
                'compliance_score': kpis['compliance_performance']['overall_compliance_rate'],
                'cost_efficiency_score': min(100, max(0, 100 - (kpis['salary_performance']['average_salary_per_employee'] / 1000))),
                'overall_score': 0
            }
            
            # Calculate overall score as weighted average
            weights = {
                'budget_efficiency_score': 0.25,
                'salary_performance_score': 0.25,
                'compliance_score': 0.25,
                'cost_efficiency_score': 0.25
            }
            
            overall_score = sum(scores[key] * weights[key] for key in weights.keys())
            scores['overall_score'] = round(overall_score, 2)
            
            # Add performance grade
            if scores['overall_score'] >= 90:
                scores['grade'] = 'A'
            elif scores['overall_score'] >= 80:
                scores['grade'] = 'B'
            elif scores['overall_score'] >= 70:
                scores['grade'] = 'C'
            elif scores['overall_score'] >= 60:
                scores['grade'] = 'D'
            else:
                scores['grade'] = 'F'
            
            return scores
            
        except Exception as e:
            self.logger.error(f"Error calculating performance scores: {e}")
            return {
                'budget_efficiency_score': 0,
                'salary_performance_score': 0,
                'compliance_score': 0,
                'cost_efficiency_score': 0,
                'overall_score': 0,
                'grade': 'F'
            }
