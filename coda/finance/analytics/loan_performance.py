"""
Loan Performance Analytics Service
Provides comprehensive loan performance metrics and analysis
"""

from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class LoanPerformanceAnalytics:
    """Loan performance analytics service"""
    
    def __init__(self):
        self.logger = logger
    
    def get_performance_dashboard_data(self, **kwargs):
        """Get comprehensive loan performance dashboard data"""
        try:
            from finance.models import LoanApplication
            
            # Get all loans for analysis
            all_loans = LoanApplication.objects.all()
            
            # Summary metrics
            summary = {
                'total_applications': all_loans.count(),
                'approved_loans': all_loans.filter(status__in=['approved', 'active', 'repaid']).count(),
                'active_loans': all_loans.filter(status='active').count(),
                'under_review': all_loans.filter(status='under_review').count(),
                'rejected_loans': all_loans.filter(status='rejected').count(),
                'total_lent': all_loans.filter(status__in=['approved', 'active', 'repaid']).aggregate(
                    total=Sum('amount_requested'))['total'] or Decimal('0.00'),
                'total_outstanding': Decimal('0.00'),  # Will calculate manually
                'total_repaid': all_loans.filter(status='repaid').aggregate(
                    total=Sum('amount_requested'))['total'] or Decimal('0.00'),
            }
            
            # Calculate total outstanding manually to avoid computed property issues
            active_loans = all_loans.filter(status='active')
            total_outstanding = Decimal('0.00')
            for loan in active_loans:
                try:
                    total_outstanding += loan.balance_amount
                except:
                    continue
            summary['total_outstanding'] = total_outstanding
            
            # Calculate approval rate
            if summary['total_applications'] > 0:
                summary['approval_rate'] = (summary['approved_loans'] / summary['total_applications']) * 100
            else:
                summary['approval_rate'] = 0.0
            
            # Performance trends (last 12 months)
            trends = self._get_performance_trends()
            
            # Risk analysis
            risk_metrics = self._get_risk_metrics()
            
            # User type performance
            user_performance = self._get_user_type_performance()
            
            return {
                'status': 'success',
                'summary': summary,
                'trends': trends,
                'risk_metrics': risk_metrics,
                'user_performance': user_performance,
            }
            
        except Exception as e:
            self.logger.error(f"Error generating loan performance data: {e}")
            return {
                'status': 'error',
                'message': f"Error generating performance data: {e}"
            }
    
    def _get_performance_trends(self):
        """Get performance trends for the last 12 months"""
        try:
            from finance.models import LoanApplication
            
            trends = []
            current_date = timezone.now()
            
            for i in range(12):
                month_date = current_date.replace(day=1) - timezone.timedelta(days=30*i)
                month_start = month_date.replace(day=1)
                month_end = (month_start + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)
                
                month_loans = LoanApplication.objects.filter(
                    created_at__gte=month_start,
                    created_at__lte=month_end
                )
                
                month_data = {
                    'month': month_start.strftime('%B %Y'),
                    'applications': month_loans.count(),
                    'approved': month_loans.filter(status__in=['approved', 'active', 'repaid']).count(),
                    'amount': month_loans.filter(status__in=['approved', 'active', 'repaid']).aggregate(
                        total=Sum('amount_requested'))['total'] or Decimal('0.00'),
                }
                trends.append(month_data)
            
            return trends
            
        except Exception as e:
            self.logger.error(f"Error getting performance trends: {e}")
            return []
    
    def _get_risk_metrics(self):
        """Get risk analysis metrics"""
        try:
            from finance.models import LoanApplication
            
            all_loans = LoanApplication.objects.all()
            
            # Default rate
            total_approved = all_loans.filter(status__in=['approved', 'active', 'repaid']).count()
            defaulted_loans = all_loans.filter(status='defaulted').count()
            default_rate = (defaulted_loans / total_approved * 100) if total_approved > 0 else 0
            
            # Overdue analysis
            overdue_loans = all_loans.filter(status='overdue').count()
            overdue_rate = (overdue_loans / total_approved * 100) if total_approved > 0 else 0
            
            return {
                'default_rate': round(default_rate, 2),
                'overdue_rate': round(overdue_rate, 2),
                'total_defaulted': defaulted_loans,
                'total_overdue': overdue_loans,
            }
            
        except Exception as e:
            self.logger.error(f"Error getting risk metrics: {e}")
            return {}
    
    def _get_user_type_performance(self):
        """Get performance metrics by user type"""
        try:
            from finance.models import LoanApplication
            from accounts.models import CustomerUser
            
            user_performance = {}
            
            # Staff performance
            staff_loans = LoanApplication.objects.filter(borrower__category=2)
            if staff_loans.exists():
                user_performance['staff'] = {
                    'total_loans': staff_loans.count(),
                    'approved_loans': staff_loans.filter(status__in=['approved', 'active', 'repaid']).count(),
                    'total_amount': staff_loans.filter(status__in=['approved', 'active', 'repaid']).aggregate(
                        total=Sum('amount_requested'))['total'] or Decimal('0.00'),
                }
            
            # KCC member performance
            kcc_loans = LoanApplication.objects.filter(borrower__profile__is_karen_country_club_member=True)
            if kcc_loans.exists():
                user_performance['kcc_members'] = {
                    'total_loans': kcc_loans.count(),
                    'approved_loans': kcc_loans.filter(status__in=['approved', 'active', 'repaid']).count(),
                    'total_amount': kcc_loans.filter(status__in=['approved', 'active', 'repaid']).aggregate(
                        total=Sum('amount_requested'))['total'] or Decimal('0.00'),
                }
            
            # External users performance
            external_loans = LoanApplication.objects.filter(
                ~Q(borrower__category=2),
                ~Q(borrower__profile__is_karen_country_club_member=True)
            )
            if external_loans.exists():
                user_performance['external_users'] = {
                    'total_loans': external_loans.count(),
                    'approved_loans': external_loans.filter(status__in=['approved', 'active', 'repaid']).count(),
                    'total_amount': external_loans.filter(status__in=['approved', 'active', 'repaid']).aggregate(
                        total=Sum('amount_requested'))['total'] or Decimal('0.00'),
                }
            
            return user_performance
            
        except Exception as e:
            self.logger.error(f"Error getting user type performance: {e}")
            return {} 