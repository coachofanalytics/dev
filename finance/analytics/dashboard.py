"""
Analytics Dashboard Service
Provides unified dashboard interface for all analytics data
"""

from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class AnalyticsDashboard:
    """Analytics dashboard service"""
    
    def __init__(self):
        self.logger = logger
    
    def get_dashboard_data(self, **kwargs):
        """Get comprehensive dashboard data"""
        try:
            # Get overview metrics
            overview_metrics = self._get_overview_metrics()
            
            # Get performance charts data
            performance_charts = self._get_performance_charts()
            
            # Get risk indicators
            risk_indicators = self._get_risk_indicators()
            
            # Get KCC insights
            kcc_insights = self._get_kcc_insights()
            
            # Get recent activity
            recent_activity = self._get_recent_activity()
            
            return {
                'status': 'success',
                'overview_metrics': overview_metrics,
                'performance_charts': performance_charts,
                'risk_indicators': risk_indicators,
                'kcc_insights': kcc_insights,
                'recent_activity': recent_activity,
            }
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {e}")
            return {
                'status': 'error',
                'message': f"Error getting dashboard data: {e}"
            }
    
    def _get_overview_metrics(self):
        """Get overview metrics for the dashboard"""
        try:
            from finance.models import LoanApplication
            from accounts.models import CustomerUser
            
            # Basic counts
            total_loans = LoanApplication.objects.count()
            total_users = CustomerUser.objects.count()
            kcc_members = CustomerUser.objects.filter(
                profile__is_karen_country_club_member=True
            ).count()
            
            # Financial metrics
            total_lent = LoanApplication.objects.filter(
                status__in=['approved', 'active', 'repaid']
            ).aggregate(total=Sum('amount_requested'))['total'] or Decimal('0.00')
            
            # Calculate approval rate
            approved_loans = LoanApplication.objects.filter(
                status__in=['approved', 'active', 'repaid']
            ).count()
            approval_rate = (approved_loans / total_loans * 100) if total_loans > 0 else 0
            
            return {
                'total_loans': total_loans,
                'total_users': total_users,
                'kcc_members': kcc_members,
                'total_lent': total_lent,
                'approval_rate': round(approval_rate, 2),
                'active_loans': LoanApplication.objects.filter(status='active').count(),
            }
            
        except Exception as e:
            self.logger.error(f"Error getting overview metrics: {e}")
            return {}
    
    def _get_performance_charts(self):
        """Get data for performance charts"""
        try:
            from finance.models import LoanApplication
            
            # Monthly trends (last 12 months)
            monthly_trends = self._get_monthly_trends()
            
            # Loan distribution by status
            status_distribution = self._get_status_distribution()
            
            # User type distribution
            user_type_distribution = self._get_user_type_distribution()
            
            return {
                'monthly_trends': monthly_trends,
                'status_distribution': status_distribution,
                'user_type_distribution': user_type_distribution,
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance charts: {e}")
            return {}
    
    def _get_monthly_trends(self):
        """Get monthly trends for the last 12 months"""
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
            self.logger.error(f"Error getting monthly trends: {e}")
            return []
    
    def _get_status_distribution(self):
        """Get loan distribution by status"""
        try:
            from finance.models import LoanApplication
            
            statuses = ['draft', 'submitted', 'under_review', 'pending_guarantor', 
                       'approved', 'active', 'overdue', 'repaid', 'rejected']
            
            distribution = []
            for status in statuses:
                count = LoanApplication.objects.filter(status=status).count()
                if count > 0:
                    distribution.append({
                        'status': status.replace('_', ' ').title(),
                        'count': count
                    })
            
            return distribution
            
        except Exception as e:
            self.logger.error(f"Error getting status distribution: {e}")
            return []
    
    def _get_user_type_distribution(self):
        """Get user type distribution"""
        try:
            from accounts.models import CustomerUser
            from finance.models import LoanApplication
            
            distribution = []
            
            # Staff users
            staff_count = CustomerUser.objects.filter(category=2).count()
            if staff_count > 0:
                distribution.append({
                    'user_type': 'Staff',
                    'count': staff_count
                })
            
            # KCC members
            kcc_count = CustomerUser.objects.filter(
                profile__is_karen_country_club_member=True
            ).count()
            if kcc_count > 0:
                distribution.append({
                    'user_type': 'KCC Members',
                    'count': kcc_count
                })
            
            # External users
            external_count = CustomerUser.objects.filter(
                ~Q(category=2),
                ~Q(profile__is_karen_country_club_member=True)
            ).count()
            if external_count > 0:
                distribution.append({
                    'user_type': 'External Users',
                    'count': external_count
                })
            
            return distribution
            
        except Exception as e:
            self.logger.error(f"Error getting user type distribution: {e}")
            return []
    
    def _get_risk_indicators(self):
        """Get risk indicators and alerts"""
        try:
            from finance.models import LoanApplication
            
            risk_indicators = []
            
            # Overdue loans
            overdue_count = LoanApplication.objects.filter(status='overdue').count()
            if overdue_count > 0:
                risk_indicators.append({
                    'type': 'overdue_loans',
                    'severity': 'high' if overdue_count > 5 else 'medium',
                    'message': f'{overdue_count} loans are overdue',
                    'count': overdue_count
                })
            
            # High-risk applications
            high_risk_count = LoanApplication.objects.filter(
                status='under_review',
                amount_requested__gt=Decimal('1000.00')
            ).count()
            if high_risk_count > 0:
                risk_indicators.append({
                    'type': 'high_risk_applications',
                    'severity': 'medium',
                    'message': f'{high_risk_count} high-value applications under review',
                    'count': high_risk_count
                })
            
            return risk_indicators
            
        except Exception as e:
            self.logger.error(f"Error getting risk indicators: {e}")
            return []
    
    def _get_kcc_insights(self):
        """Get KCC-specific insights"""
        try:
            from accounts.models import CustomerUser
            from finance.models import LoanApplication
            
            kcc_members = CustomerUser.objects.filter(
                profile__is_karen_country_club_member=True
            )
            
            if not kcc_members.exists():
                return {}
            
            # KCC loan performance
            kcc_loans = LoanApplication.objects.filter(
                borrower__profile__is_karen_country_club_member=True
            )
            
            insights = {
                'total_members': kcc_members.count(),
                'active_loans': kcc_loans.filter(status='active').count(),
                'total_lent_to_kcc': kcc_loans.filter(
                    status__in=['approved', 'active', 'repaid']
                ).aggregate(total=Sum('amount_requested'))['total'] or Decimal('0.00'),
                'average_loan_amount': kcc_loans.filter(
                    status__in=['approved', 'active', 'repaid']
                ).aggregate(avg=Avg('amount_requested'))['avg'] or Decimal('0.00'),
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error getting KCC insights: {e}")
            return {}
    
    def _get_recent_activity(self):
        """Get recent loan activity"""
        try:
            from finance.models import LoanApplication
            
            recent_loans = LoanApplication.objects.select_related('borrower').order_by(
                '-created_at'
            )[:10]
            
            activity = []
            for loan in recent_loans:
                activity.append({
                    'id': loan.id,
                    'borrower': loan.borrower.username,
                    'amount': loan.amount_requested,
                    'status': loan.status,
                    'created_at': loan.created_at.strftime('%Y-%m-%d %H:%M'),
                })
            
            return activity
            
        except Exception as e:
            self.logger.error(f"Error getting recent activity: {e}")
            return []
    
    def export_dashboard_data(self, **kwargs):
        """Export dashboard data for external use"""
        try:
            dashboard_data = self.get_dashboard_data(**kwargs)
            
            if dashboard_data['status'] == 'success':
                return {
                    'status': 'success',
                    'data': dashboard_data,
                    'export_timestamp': timezone.now().isoformat(),
                }
            else:
                return dashboard_data
                
        except Exception as e:
            self.logger.error(f"Error exporting dashboard data: {e}")
            return {
                'status': 'error',
                'message': f"Error exporting dashboard data: {e}"
            } 