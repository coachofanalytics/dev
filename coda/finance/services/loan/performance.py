"""
Loan performance service - tracks and analyzes loan performance metrics.
"""

import logging
from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.db.models import Q, Sum, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from ..core.base import BaseFinanceService, LoanServiceMixin
from ...models import LoanApplication, LoanProduct, Budget, Transaction

logger = logging.getLogger(__name__)


class LoanPerformanceService(BaseFinanceService, LoanServiceMixin):
    """
    Service for tracking and analyzing loan performance metrics.
    """
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_performance_metrics(self, company, department=None) -> Dict[str, Any]:
        """Get comprehensive loan performance metrics."""
        try:
            # Get loan portfolio overview
            portfolio_overview = self._get_portfolio_overview(company, department)
            
            # Get performance trends
            performance_trends = self._get_performance_trends(company, department)
            
            # Get risk metrics
            risk_metrics = self._get_risk_metrics(company, department)
            
            # Get profitability metrics
            profitability_metrics = self._get_profitability_metrics(company, department)
            
            return {
                'portfolio_overview': portfolio_overview,
                'performance_trends': performance_trends,
                'risk_metrics': risk_metrics,
                'profitability_metrics': profitability_metrics,
                'generated_at': timezone.now()
            }
        
        except Exception as e:
            self.log_error("Error getting loan performance metrics", e)
            return {
                'error': str(e),
                'generated_at': timezone.now()
            }
    
    def _get_portfolio_overview(self, company, department=None) -> Dict[str, Any]:
        """Get loan portfolio overview."""
        try:
            # Base query
            loan_query = LoanApplication.objects.filter(borrower__profile__department__company=company)
            
            if department:
                loan_query = loan_query.filter(borrower__profile__department=department)
            
            # Total portfolio metrics
            total_loans = loan_query.count()
            total_amount = loan_query.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            avg_loan_amount = loan_query.aggregate(Avg('amount'))['amount__avg'] or Decimal('0.00')
            
            # Status breakdown
            status_breakdown = loan_query.values('status').annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            )
            
            # Product breakdown
            product_breakdown = loan_query.values('loan_product__name').annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            )
            
            # Department breakdown
            department_breakdown = loan_query.values('borrower__profile__department__name').annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            )
            
            return {
                'total_loans': total_loans,
                'total_amount': total_amount,
                'avg_loan_amount': avg_loan_amount,
                'status_breakdown': list(status_breakdown),
                'product_breakdown': list(product_breakdown),
                'department_breakdown': list(department_breakdown)
            }
        
        except Exception as e:
            self.log_error("Error getting portfolio overview", e)
            return {
                'total_loans': 0,
                'total_amount': Decimal('0.00'),
                'avg_loan_amount': Decimal('0.00'),
                'status_breakdown': [],
                'product_breakdown': [],
                'department_breakdown': []
            }
    
    def _get_performance_trends(self, company, department=None) -> Dict[str, Any]:
        """Get loan performance trends over time."""
        try:
            # Base query
            loan_query = LoanApplication.objects.filter(borrower__profile__department__company=company)
            
            if department:
                loan_query = loan_query.filter(borrower__profile__department=department)
            
            # Monthly trends (last 12 months)
            monthly_trends = []
            for i in range(12):
                month_start = timezone.now().replace(day=1) - relativedelta(months=i)
                month_end = month_start + relativedelta(months=1) - timedelta(days=1)
                
                month_loans = loan_query.filter(
                    created_at__gte=month_start,
                    created_at__lte=month_end
                )
                
                monthly_trends.append({
                    'month': month_start.strftime('%Y-%m'),
                    'loan_count': month_loans.count(),
                    'total_amount': month_loans.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'),
                    'avg_amount': month_loans.aggregate(Avg('amount'))['amount__avg'] or Decimal('0.00')
                })
            
            # Approval rate trends
            approval_trends = []
            for i in range(6):  # Last 6 months
                month_start = timezone.now().replace(day=1) - relativedelta(months=i)
                month_end = month_start + relativedelta(months=1) - timedelta(days=1)
                
                month_loans = loan_query.filter(
                    created_at__gte=month_start,
                    created_at__lte=month_end
                )
                
                total_applications = month_loans.count()
                approved_applications = month_loans.filter(status='approved').count()
                
                approval_rate = (approved_applications / total_applications * 100) if total_applications > 0 else 0
                
                approval_trends.append({
                    'month': month_start.strftime('%Y-%m'),
                    'total_applications': total_applications,
                    'approved_applications': approved_applications,
                    'approval_rate': approval_rate
                })
            
            return {
                'monthly_trends': monthly_trends,
                'approval_trends': approval_trends
            }
        
        except Exception as e:
            self.log_error("Error getting performance trends", e)
            return {
                'monthly_trends': [],
                'approval_trends': []
            }
    
    def _get_risk_metrics(self, company, department=None) -> Dict[str, Any]:
        """Get loan risk metrics."""
        try:
            # Base query
            loan_query = LoanApplication.objects.filter(borrower__profile__department__company=company)
            
            if department:
                loan_query = loan_query.filter(borrower__profile__department=department)
            
            # Default rate (simplified)
            total_loans = loan_query.count()
            defaulted_loans = loan_query.filter(status='defaulted').count()
            default_rate = (defaulted_loans / total_loans * 100) if total_loans > 0 else 0
            
            # Delinquency rate (loans past due)
            current_date = timezone.now().date()
            delinquent_loans = loan_query.filter(
                status='active',
                due_date__lt=current_date
            ).count()
            delinquency_rate = (delinquent_loans / total_loans * 100) if total_loans > 0 else 0
            
            # Risk by loan amount
            risk_by_amount = loan_query.values('amount').annotate(
                count=Count('id'),
                default_count=Count('id', filter=Q(status='defaulted'))
            )
            
            # Risk by department
            risk_by_department = loan_query.values('borrower__profile__department__name').annotate(
                count=Count('id'),
                default_count=Count('id', filter=Q(status='defaulted'))
            )
            
            return {
                'default_rate': default_rate,
                'delinquency_rate': delinquency_rate,
                'total_loans': total_loans,
                'defaulted_loans': defaulted_loans,
                'delinquent_loans': delinquent_loans,
                'risk_by_amount': list(risk_by_amount),
                'risk_by_department': list(risk_by_department)
            }
        
        except Exception as e:
            self.log_error("Error getting risk metrics", e)
            return {
                'default_rate': 0,
                'delinquency_rate': 0,
                'total_loans': 0,
                'defaulted_loans': 0,
                'delinquent_loans': 0,
                'risk_by_amount': [],
                'risk_by_department': []
            }
    
    def _get_profitability_metrics(self, company, department=None) -> Dict[str, Any]:
        """Get loan profitability metrics."""
        try:
            # Base query
            loan_query = LoanApplication.objects.filter(borrower__profile__department__company=company)
            
            if department:
                loan_query = loan_query.filter(borrower__profile__department=department)
            
            # Total interest earned (simplified calculation)
            active_loans = loan_query.filter(status='active')
            total_principal = active_loans.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            
            # Assume average interest rate of 10% and average loan term of 12 months
            estimated_interest = total_principal * Decimal('0.10')
            
            # Total fees collected
            total_fees = active_loans.aggregate(Sum('processing_fee'))['processing_fee__sum'] or Decimal('0.00')
            
            # Total revenue
            total_revenue = estimated_interest + total_fees
            
            # Average revenue per loan
            avg_revenue_per_loan = total_revenue / active_loans.count() if active_loans.count() > 0 else Decimal('0.00')
            
            # Revenue by product
            revenue_by_product = active_loans.values('loan_product__name').annotate(
                count=Count('id'),
                total_principal=Sum('amount'),
                total_fees=Sum('processing_fee')
            )
            
            return {
                'total_revenue': total_revenue,
                'estimated_interest': estimated_interest,
                'total_fees': total_fees,
                'avg_revenue_per_loan': avg_revenue_per_loan,
                'active_loans_count': active_loans.count(),
                'revenue_by_product': list(revenue_by_product)
            }
        
        except Exception as e:
            self.log_error("Error getting profitability metrics", e)
            return {
                'total_revenue': Decimal('0.00'),
                'estimated_interest': Decimal('0.00'),
                'total_fees': Decimal('0.00'),
                'avg_revenue_per_loan': Decimal('0.00'),
                'active_loans_count': 0,
                'revenue_by_product': []
            }
    
    def get_loan_performance_report(self, company, department=None, start_date=None, end_date=None) -> Dict[str, Any]:
        """Generate comprehensive loan performance report."""
        try:
            # Set default date range if not provided
            if not start_date:
                start_date = timezone.now().date() - timedelta(days=90)
            if not end_date:
                end_date = timezone.now().date()
            
            # Base query with date filter
            loan_query = LoanApplication.objects.filter(
                borrower__profile__department__company=company,
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
            
            if department:
                loan_query = loan_query.filter(borrower__profile__department=department)
            
            # Generate report data
            report_data = {
                'report_period': {
                    'start_date': start_date,
                    'end_date': end_date
                },
                'summary': self._get_performance_metrics(company, department),
                'detailed_analysis': {
                    'loan_origination': self._analyze_loan_origination(loan_query),
                    'credit_quality': self._analyze_credit_quality(loan_query),
                    'collection_performance': self._analyze_collection_performance(loan_query)
                },
                'recommendations': self._generate_recommendations(company, department)
            }
            
            return report_data
        
        except Exception as e:
            self.log_error("Error generating loan performance report", e)
            return {
                'error': str(e),
                'report_period': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
    
    def _analyze_loan_origination(self, loan_query) -> Dict[str, Any]:
        """Analyze loan origination patterns."""
        try:
            # Origination volume
            total_originations = loan_query.count()
            total_origination_amount = loan_query.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
            
            # Origination by product
            origination_by_product = loan_query.values('loan_product__name').annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            )
            
            # Origination by department
            origination_by_department = loan_query.values('borrower__profile__department__name').annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            )
            
            return {
                'total_originations': total_originations,
                'total_origination_amount': total_origination_amount,
                'origination_by_product': list(origination_by_product),
                'origination_by_department': list(origination_by_department)
            }
        
        except Exception as e:
            self.log_error("Error analyzing loan origination", e)
            return {
                'total_originations': 0,
                'total_origination_amount': Decimal('0.00'),
                'origination_by_product': [],
                'origination_by_department': []
            }
    
    def _analyze_credit_quality(self, loan_query) -> Dict[str, Any]:
        """Analyze credit quality metrics."""
        try:
            # Credit quality by loan amount
            credit_quality_by_amount = loan_query.values('amount').annotate(
                count=Count('id'),
                approved_count=Count('id', filter=Q(status='approved')),
                rejected_count=Count('id', filter=Q(status='rejected'))
            )
            
            # Credit quality by department
            credit_quality_by_department = loan_query.values('borrower__profile__department__name').annotate(
                count=Count('id'),
                approved_count=Count('id', filter=Q(status='approved')),
                rejected_count=Count('id', filter=Q(status='rejected'))
            )
            
            return {
                'credit_quality_by_amount': list(credit_quality_by_amount),
                'credit_quality_by_department': list(credit_quality_by_department)
            }
        
        except Exception as e:
            self.log_error("Error analyzing credit quality", e)
            return {
                'credit_quality_by_amount': [],
                'credit_quality_by_department': []
            }
    
    def _analyze_collection_performance(self, loan_query) -> Dict[str, Any]:
        """Analyze collection performance."""
        try:
            # Collection performance by status
            collection_performance = loan_query.values('status').annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            )
            
            # Collection performance by department
            collection_by_department = loan_query.values('borrower__profile__department__name').annotate(
                count=Count('id'),
                total_amount=Sum('amount')
            )
            
            return {
                'collection_performance': list(collection_performance),
                'collection_by_department': list(collection_by_department)
            }
        
        except Exception as e:
            self.log_error("Error analyzing collection performance", e)
            return {
                'collection_performance': [],
                'collection_by_department': []
            }
    
    def _generate_recommendations(self, company, department=None) -> List[str]:
        """Generate recommendations based on performance analysis."""
        try:
            recommendations = []
            
            # Get performance metrics
            metrics = self._get_performance_metrics(company, department)
            
            # Check default rate
            if metrics.get('risk_metrics', {}).get('default_rate', 0) > 5:
                recommendations.append("High default rate detected. Consider tightening credit criteria.")
            
            # Check delinquency rate
            if metrics.get('risk_metrics', {}).get('delinquency_rate', 0) > 10:
                recommendations.append("High delinquency rate. Improve collection processes.")
            
            # Check approval rate
            approval_trends = metrics.get('performance_trends', {}).get('approval_trends', [])
            if approval_trends:
                latest_approval_rate = approval_trends[0].get('approval_rate', 0)
                if latest_approval_rate < 50:
                    recommendations.append("Low approval rate. Review credit criteria and consider relaxing standards.")
            
            # Check profitability
            profitability = metrics.get('profitability_metrics', {})
            if profitability.get('avg_revenue_per_loan', 0) < 100:
                recommendations.append("Low revenue per loan. Consider adjusting interest rates or fees.")
            
            if not recommendations:
                recommendations.append("Loan portfolio performance is within acceptable parameters.")
            
            return recommendations
        
        except Exception as e:
            self.log_error("Error generating recommendations", e)
            return ["Unable to generate recommendations due to system error"]



