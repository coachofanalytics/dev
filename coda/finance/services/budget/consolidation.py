"""
Budget consolidation service for aggregating and analyzing budget data.
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.db.models import Q, Sum, Avg, Count, F, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from ..core.base import BaseFinanceService, BudgetServiceMixin
from ...models import Budget, BudgetCategory, BudgetSubCategory, Transaction

logger = logging.getLogger(__name__)


class BudgetConsolidationService(BaseFinanceService, BudgetServiceMixin):
    """
    Service for budget consolidation and analytics.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_budget_analytics(self, company, department=None) -> Dict[str, Any]:
        """Get comprehensive budget analytics for a company."""
        try:
            # Build base filter
            budget_filter = Q(company=company)
            if department:
                budget_filter &= Q(department=department)
            
            # Get basic statistics
            basic_stats = self._get_basic_statistics(budget_filter)
            
            # Get category breakdown
            category_breakdown = self._get_category_breakdown(budget_filter)
            
            # Get variance analysis
            variance_analysis = self._get_variance_analysis(budget_filter)
            
            # Get trend analysis
            trend_analysis = self._get_trend_analysis(company, department)
            
            # Get performance metrics
            performance_metrics = self._get_performance_metrics(budget_filter)
            
            return {
                'basic_statistics': basic_stats,
                'category_breakdown': category_breakdown,
                'variance_analysis': variance_analysis,
                'trend_analysis': trend_analysis,
                'performance_metrics': performance_metrics,
                'generated_at': timezone.now(),
            }
        
        except Exception as e:
            self.log_error("Error getting budget analytics", e)
            return {'error': str(e)}
    
    def consolidate_budgets(self, company, department=None, 
                          categories: List[int] = None) -> Dict[str, Any]:
        """Consolidate budgets for reporting and analysis."""
        try:
            # Build filter
            budget_filter = Q(company=company)
            if department:
                budget_filter &= Q(department=department)
            if categories:
                budget_filter &= Q(category_id__in=categories)
            
            # Get consolidated data
            consolidated_data = self._get_consolidated_data(budget_filter)
            
            # Calculate totals
            totals = self._calculate_consolidated_totals(consolidated_data)
            
            # Generate summary
            summary = self._generate_consolidation_summary(consolidated_data, totals)
            
            return {
                'consolidated_data': consolidated_data,
                'totals': totals,
                'summary': summary,
                'consolidated_at': timezone.now(),
            }
        
        except Exception as e:
            self.log_error("Error consolidating budgets", e)
            return {'error': str(e)}
    
    def get_budget_variance_report(self, company, department=None, 
                                 start_date=None, end_date=None) -> Dict[str, Any]:
        """Generate budget variance report."""
        try:
            # Set default date range
            if not end_date:
                end_date = timezone.now().date()
            if not start_date:
                start_date = end_date - timedelta(days=90)
            
            # Build filter
            budget_filter = Q(company=company)
            if department:
                budget_filter &= Q(department=department)
            budget_filter &= Q(start_date__gte=start_date, end_date__lte=end_date)
            
            # Get variance data
            variance_data = self._get_variance_data(budget_filter)
            
            # Calculate variance metrics
            variance_metrics = self._calculate_variance_metrics(variance_data)
            
            # Identify significant variances
            significant_variances = self._identify_significant_variances(variance_data)
            
            return {
                'variance_data': variance_data,
                'variance_metrics': variance_metrics,
                'significant_variances': significant_variances,
                'report_period': {
                    'start_date': start_date,
                    'end_date': end_date,
                },
                'generated_at': timezone.now(),
            }
        
        except Exception as e:
            self.log_error("Error generating budget variance report", e)
            return {'error': str(e)}
    
    def _get_basic_statistics(self, budget_filter) -> Dict[str, Any]:
        """Get basic budget statistics."""
        try:
            budgets = Budget.objects.filter(budget_filter)
            
            # Count statistics
            total_budgets = budgets.count()
            active_budgets = budgets.filter(status='Active').count()
            completed_budgets = budgets.filter(status='Completed').count()
            
            # Amount statistics
            total_estimated = budgets.aggregate(
                total=Sum(F('unit_price') * F('quantity') * Coalesce(F('cases'), 1), output_field=DecimalField())
            )['total'] or Decimal('0.00')
            
            total_actual = budgets.aggregate(
                total=Sum('actual_spent')
            )['total'] or Decimal('0.00')
            
            total_variance = total_actual - total_estimated
            
            # Calculate percentages
            variance_percentage = (total_variance / total_estimated * 100) if total_estimated > 0 else 0
            
            return {
                'total_budgets': total_budgets,
                'active_budgets': active_budgets,
                'completed_budgets': completed_budgets,
                'total_estimated': float(total_estimated),
                'total_actual': float(total_actual),
                'total_variance': float(total_variance),
                'variance_percentage': float(variance_percentage),
            }
        
        except Exception as e:
            self.log_error("Error getting basic statistics", e)
            return {}
    
    def _get_category_breakdown(self, budget_filter) -> List[Dict[str, Any]]:
        """Get budget breakdown by category."""
        try:
            categories = BudgetCategory.objects.all()
            breakdown = []
            
            for category in categories:
                cat_budgets = Budget.objects.filter(budget_filter, category=category)
                
                if cat_budgets.exists():
                    # Calculate category totals
                    cat_estimated = cat_budgets.aggregate(
                        total=Sum(F('unit_price') * F('quantity') * Coalesce(F('cases'), 1), output_field=DecimalField())
                    )['total'] or Decimal('0.00')
                    
                    cat_actual = cat_budgets.aggregate(
                        total=Sum('actual_spent')
                    )['total'] or Decimal('0.00')
                    
                    cat_variance = cat_actual - cat_estimated
                    
                    breakdown.append({
                        'category_id': category.id,
                        'category_name': category.name,
                        'budget_count': cat_budgets.count(),
                        'estimated_amount': float(cat_estimated),
                        'actual_amount': float(cat_actual),
                        'variance': float(cat_variance),
                        'variance_percentage': float((cat_variance / cat_estimated * 100) if cat_estimated > 0 else 0),
                    })
            
            return breakdown
        
        except Exception as e:
            self.log_error("Error getting category breakdown", e)
            return []
    
    def _get_variance_analysis(self, budget_filter) -> Dict[str, Any]:
        """Get variance analysis data."""
        try:
            budgets = Budget.objects.filter(budget_filter)
            
            # Calculate variance statistics
            favorable_variances = budgets.filter(variance__lt=0).count()
            unfavorable_variances = budgets.filter(variance__gt=0).count()
            no_variance = budgets.filter(variance=0).count()
            
            # Get variance amounts
            total_favorable = budgets.filter(variance__lt=0).aggregate(
                total=Sum('variance')
            )['total'] or Decimal('0.00')
            
            total_unfavorable = budgets.filter(variance__gt=0).aggregate(
                total=Sum('variance')
            )['total'] or Decimal('0.00')
            
            # Calculate average variance
            avg_variance = budgets.aggregate(avg=Avg('variance'))['avg'] or Decimal('0.00')
            
            return {
                'favorable_count': favorable_variances,
                'unfavorable_count': unfavorable_variances,
                'no_variance_count': no_variance,
                'total_favorable': float(abs(total_favorable)),
                'total_unfavorable': float(total_unfavorable),
                'net_variance': float(total_favorable + total_unfavorable),
                'average_variance': float(avg_variance),
            }
        
        except Exception as e:
            self.log_error("Error getting variance analysis", e)
            return {}
    
    def _get_trend_analysis(self, company, department=None) -> Dict[str, Any]:
        """Get budget trend analysis."""
        try:
            # Get monthly budget data for the last 12 months
            monthly_data = []
            end_date = timezone.now()
            
            for i in range(12):
                month_start = (end_date - relativedelta(months=i+1)).replace(day=1)
                month_end = (month_start + relativedelta(months=1)) - timedelta(days=1)
                
                # Build filter for this month
                month_filter = Q(company=company, start_date__gte=month_start, end_date__lte=month_end)
                if department:
                    month_filter &= Q(department=department)
                
                month_budgets = Budget.objects.filter(month_filter)
                
                month_estimated = month_budgets.aggregate(
                    total=Sum(F('unit_price') * F('quantity') * Coalesce(F('cases'), 1), output_field=DecimalField())
                )['total'] or Decimal('0.00')
                
                month_actual = month_budgets.aggregate(
                    total=Sum('actual_spent')
                )['total'] or Decimal('0.00')
                
                monthly_data.append({
                    'month': month_start.strftime('%Y-%m'),
                    'estimated': float(month_estimated),
                    'actual': float(month_actual),
                    'variance': float(month_actual - month_estimated),
                })
            
            # Calculate trend
            trend = self._calculate_budget_trend(monthly_data)
            
            return {
                'monthly_data': monthly_data,
                'trend': trend,
            }
        
        except Exception as e:
            self.log_error("Error getting trend analysis", e)
            return {}
    
    def _get_performance_metrics(self, budget_filter) -> Dict[str, Any]:
        """Get budget performance metrics."""
        try:
            budgets = Budget.objects.filter(budget_filter)
            
            # Calculate performance metrics
            on_budget_count = budgets.filter(variance__gte=-Decimal('0.05'), variance__lte=Decimal('0.05')).count()
            over_budget_count = budgets.filter(variance__gt=Decimal('0.05')).count()
            under_budget_count = budgets.filter(variance__lt=-Decimal('0.05')).count()
            
            total_budgets = budgets.count()
            
            # Calculate percentages
            on_budget_percentage = (on_budget_count / total_budgets * 100) if total_budgets > 0 else 0
            over_budget_percentage = (over_budget_count / total_budgets * 100) if total_budgets > 0 else 0
            under_budget_percentage = (under_budget_count / total_budgets * 100) if total_budgets > 0 else 0
            
            return {
                'on_budget_count': on_budget_count,
                'over_budget_count': over_budget_count,
                'under_budget_count': under_budget_count,
                'on_budget_percentage': float(on_budget_percentage),
                'over_budget_percentage': float(over_budget_percentage),
                'under_budget_percentage': float(under_budget_percentage),
                'total_budgets': total_budgets,
            }
        
        except Exception as e:
            self.log_error("Error getting performance metrics", e)
            return {}
    
    def _get_consolidated_data(self, budget_filter) -> List[Dict[str, Any]]:
        """Get consolidated budget data."""
        try:
            budgets = Budget.objects.filter(budget_filter).select_related(
                'category', 'subcategory', 'budget_lead'
            )
            
            consolidated = []
            for budget in budgets:
                consolidated.append({
                    'id': budget.id,
                    'item_name': budget.item_name,
                    'category': budget.category.name,
                    'subcategory': budget.subcategory.name,
                    'estimated_amount': float(budget.estimated_amount),
                    'actual_spent': float(budget.actual_spent),
                    'variance': float(budget.variance),
                    'variance_percentage': float(budget.variance_percentage),
                    'status': budget.status,
                    'budget_lead': budget.budget_lead.get_full_name() if budget.budget_lead else 'Unassigned',
                })
            
            return consolidated
        
        except Exception as e:
            self.log_error("Error getting consolidated data", e)
            return []
    
    def _calculate_consolidated_totals(self, consolidated_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate totals for consolidated data."""
        try:
            totals = {
                'total_estimated': sum(item['estimated_amount'] for item in consolidated_data),
                'total_actual': sum(item['actual_spent'] for item in consolidated_data),
                'total_variance': sum(item['variance'] for item in consolidated_data),
                'item_count': len(consolidated_data),
            }
            
            # Calculate variance percentage
            if totals['total_estimated'] > 0:
                totals['variance_percentage'] = (totals['total_variance'] / totals['total_estimated']) * 100
            else:
                totals['variance_percentage'] = 0
            
            return totals
        
        except Exception as e:
            self.log_error("Error calculating consolidated totals", e)
            return {}
    
    def _generate_consolidation_summary(self, consolidated_data: List[Dict[str, Any]], 
                                      totals: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary for consolidation."""
        try:
            # Count by status
            status_counts = {}
            for item in consolidated_data:
                status = item['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Identify top variances
            top_variances = sorted(consolidated_data, key=lambda x: abs(x['variance']), reverse=True)[:5]
            
            return {
                'status_counts': status_counts,
                'top_variances': top_variances,
                'summary_text': self._generate_summary_text(totals, status_counts),
            }
        
        except Exception as e:
            self.log_error("Error generating consolidation summary", e)
            return {}
    
    def _generate_summary_text(self, totals: Dict[str, Any], status_counts: Dict[str, int]) -> str:
        """Generate human-readable summary text."""
        try:
            variance_percentage = totals.get('variance_percentage', 0)
            
            if variance_percentage > 5:
                variance_desc = f"over budget by {variance_percentage:.1f}%"
            elif variance_percentage < -5:
                variance_desc = f"under budget by {abs(variance_percentage):.1f}%"
            else:
                variance_desc = "on budget"
            
            return f"Total of {totals.get('item_count', 0)} budget items, {variance_desc}."
        
        except Exception as e:
            self.log_error("Error generating summary text", e)
            return "Summary unavailable"
    
    def _get_variance_data(self, budget_filter) -> List[Dict[str, Any]]:
        """Get detailed variance data."""
        try:
            budgets = Budget.objects.filter(budget_filter).select_related(
                'category', 'subcategory'
            )
            
            variance_data = []
            for budget in budgets:
                variance_data.append({
                    'id': budget.id,
                    'item_name': budget.item_name,
                    'category': budget.category.name,
                    'subcategory': budget.subcategory.name,
                    'estimated_amount': float(budget.estimated_amount),
                    'actual_spent': float(budget.actual_spent),
                    'variance': float(budget.variance),
                    'variance_percentage': float(budget.variance_percentage),
                    'status': budget.status,
                })
            
            return variance_data
        
        except Exception as e:
            self.log_error("Error getting variance data", e)
            return []
    
    def _calculate_variance_metrics(self, variance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate variance metrics."""
        try:
            if not variance_data:
                return {}
            
            # Calculate statistics
            total_variance = sum(item['variance'] for item in variance_data)
            avg_variance = total_variance / len(variance_data)
            
            # Count by variance type
            favorable = len([item for item in variance_data if item['variance'] < 0])
            unfavorable = len([item for item in variance_data if item['variance'] > 0])
            on_target = len([item for item in variance_data if item['variance'] == 0])
            
            return {
                'total_variance': total_variance,
                'average_variance': avg_variance,
                'favorable_count': favorable,
                'unfavorable_count': unfavorable,
                'on_target_count': on_target,
                'total_items': len(variance_data),
            }
        
        except Exception as e:
            self.log_error("Error calculating variance metrics", e)
            return {}
    
    def _identify_significant_variances(self, variance_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify significant variances (above threshold)."""
        try:
            significant_threshold = 0.10  # 10% variance threshold
            
            significant = []
            for item in variance_data:
                if abs(item['variance_percentage']) > significant_threshold:
                    significant.append(item)
            
            # Sort by absolute variance percentage
            significant.sort(key=lambda x: abs(x['variance_percentage']), reverse=True)
            
            return significant
        
        except Exception as e:
            self.log_error("Error identifying significant variances", e)
            return []
    
    def _calculate_budget_trend(self, monthly_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate budget trend from monthly data."""
        try:
            if len(monthly_data) < 2:
                return {'trend': 'insufficient_data', 'direction': 'stable'}
            
            # Calculate trend direction
            recent_months = monthly_data[:3]  # Last 3 months
            older_months = monthly_data[3:6]  # Previous 3 months
            
            if recent_months and older_months:
                recent_avg = sum(month['variance'] for month in recent_months) / len(recent_months)
                older_avg = sum(month['variance'] for month in older_months) / len(older_months)
                
                if recent_avg > older_avg:
                    direction = 'improving'
                elif recent_avg < older_avg:
                    direction = 'worsening'
                else:
                    direction = 'stable'
            else:
                direction = 'stable'
            
            return {
                'trend': 'calculated',
                'direction': direction,
                'recent_average_variance': recent_avg if 'recent_avg' in locals() else 0,
                'older_average_variance': older_avg if 'older_avg' in locals() else 0,
            }
        
        except Exception as e:
            self.log_error("Error calculating budget trend", e)
            return {'trend': 'error', 'direction': 'unknown'}
