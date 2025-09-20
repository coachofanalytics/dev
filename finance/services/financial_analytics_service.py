"""
Financial Analytics Service
Provides comprehensive financial analytics and reporting capabilities
"""

from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q
from core.services.base import ModelService
import logging

logger = logging.getLogger(__name__)

class FinancialAnalyticsService(ModelService):
    """Service for financial analytics and reporting - FOLLOWING OUR ARCHITECTURE"""
    
    def __init__(self):
        super().__init__()
    
    def get_system_overview(self):
        """Get comprehensive system overview metrics"""
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
                'status': 'success',
                'overview': {
                    'total_loans': total_loans,
                    'total_users': total_users,
                    'kcc_members': kcc_members,
                    'total_lent': total_lent,
                    'approval_rate': round(approval_rate, 2),
                    'active_loans': LoanApplication.objects.filter(status='active').count(),
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system overview: {e}")
            return {
                'status': 'error',
                'message': f"Error getting system overview: {e}"
            }
    
    def get_user_performance_analytics(self, user):
        """Get performance analytics for a specific user"""
        try:
            from finance.models import LoanApplication
            
            user_loans = LoanApplication.objects.filter(borrower=user)
            
            if not user_loans.exists():
                return {
                    'status': 'success',
                    'message': 'No loan history found for this user',
                    'data': {}
                }
            
            analytics = {
                'total_loans': user_loans.count(),
                'approved_loans': user_loans.filter(status__in=['approved', 'active', 'repaid']).count(),
                'active_loans': user_loans.filter(status='active').count(),
                'total_borrowed': user_loans.filter(status__in=['approved', 'active', 'repaid']).aggregate(
                    total=Sum('amount_requested'))['total'] or Decimal('0.00'),
                'average_loan_amount': user_loans.filter(status__in=['approved', 'active', 'repaid']).aggregate(
                    avg=Avg('amount_requested'))['avg'] or Decimal('0.00'),
                'payment_history': self._get_user_payment_history(user),
                'loan_timeline': self._get_user_loan_timeline(user_loans),
            }
            
            return {
                'status': 'success',
                'data': analytics
            }
            
        except Exception as e:
            self.logger.error(f"Error getting user performance analytics: {e}")
            return {
                'status': 'error',
                'message': f"Error getting user analytics: {e}"
            }
    
    def get_kcc_performance_analytics(self):
        """Get KCC-specific performance analytics"""
        try:
            from finance.models import LoanApplication
            from accounts.models import CustomerUser
            
            # Get KCC members
            kcc_members = CustomerUser.objects.filter(
                profile__is_karen_country_club_member=True
            )
            
            if not kcc_members.exists():
                return {
                    'status': 'success',
                    'message': 'No KCC members found',
                    'data': {}
                }
            
            # KCC member segmentation
            segmentation = self._get_kcc_segmentation(kcc_members)
            
            # KCC loan performance
            loan_performance = self._get_kcc_loan_performance()
            
            # Optimization opportunities
            optimization_opportunities = self._get_kcc_optimization_opportunities()
            
            # Performance trends
            performance_trends = self._get_kcc_performance_trends()
            
            return {
                'status': 'success',
                'data': {
                    'total_kcc_members': kcc_members.count(),
                    'segmentation': segmentation,
                    'loan_performance': loan_performance,
                    'optimization_opportunities': optimization_opportunities,
                    'performance_trends': performance_trends,
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting KCC performance analytics: {e}")
            return {
                'status': 'error',
                'message': f"Error getting KCC analytics: {e}"
            }
    
    def get_staff_performance_analytics(self):
        """Get staff-specific performance analytics"""
        try:
            from finance.models import LoanApplication
            from accounts.models import CustomerUser
            
            staff_users = CustomerUser.objects.filter(category=2)
            
            if not staff_users.exists():
                return {
                    'status': 'success',
                    'message': 'No staff users found',
                    'data': {}
                }
            
            staff_loans = LoanApplication.objects.filter(borrower__category=2)
            
            analytics = {
                'total_staff': staff_users.count(),
                'total_loans': staff_loans.count(),
                'approved_loans': staff_loans.filter(status__in=['approved', 'active', 'repaid']).count(),
                'total_amount': staff_loans.filter(status__in=['approved', 'active', 'repaid']).aggregate(
                    total=Sum('amount_requested'))['total'] or Decimal('0.00'),
                'average_loan_amount': staff_loans.filter(status__in=['approved', 'active', 'repaid']).aggregate(
                    avg=Avg('amount_requested'))['avg'] or Decimal('0.00'),
                'performance_by_department': self._get_staff_performance_by_department(),
            }
            
            return {
                'status': 'success',
                'data': analytics
            }
            
        except Exception as e:
            self.logger.error(f"Error getting staff performance analytics: {e}")
            return {
                'status': 'error',
                'message': f"Error getting staff analytics: {e}"
            }
    
    def get_monthly_trends(self, months=12):
        """Get monthly performance trends"""
        try:
            from finance.models import LoanApplication
            
            trends = []
            current_date = timezone.now()
            
            for i in range(months):
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
            
            return {
                'status': 'success',
                'data': trends
            }
            
        except Exception as e:
            self.logger.error(f"Error getting monthly trends: {e}")
            return {
                'status': 'error',
                'message': f"Error getting monthly trends: {e}"
            }
    
    def generate_performance_report(self, user=None, report_type='comprehensive'):
        """Generate comprehensive performance report"""
        try:
            if report_type == 'comprehensive':
                return self._generate_comprehensive_report(user)
            elif report_type == 'kcc':
                return self.get_kcc_performance_analytics()
            elif report_type == 'staff':
                return self.get_staff_performance_analytics()
            elif report_type == 'user' and user:
                return self.get_user_performance_analytics(user)
            else:
                return {
                    'status': 'error',
                    'message': f"Invalid report type: {report_type}"
                }
                
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return {
                'status': 'error',
                'message': f"Error generating report: {e}"
            }
    
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
    
    # Private helper methods
    
    def _get_user_payment_history(self, user):
        """Get user's payment history"""
        try:
            from finance.models import Payment
            
            payments = Payment.objects.filter(loan__borrower=user).order_by('-payment_date')
            
            history = []
            for payment in payments[:10]:  # Last 10 payments
                history.append({
                    'date': payment.payment_date.strftime('%Y-%m-%d'),
                    'amount': payment.amount,
                    'method': payment.payment_method,
                    'status': payment.status,
                })
            
            return history
            
        except Exception as e:
            self.logger.error(f"Error getting user payment history: {e}")
            return []
    
    def _get_user_loan_timeline(self, user_loans):
        """Get user's loan timeline"""
        try:
            timeline = []
            for loan in user_loans.order_by('-created_at')[:10]:
                timeline.append({
                    'date': loan.created_at.strftime('%Y-%m-%d'),
                    'amount': loan.amount_requested,
                    'status': loan.status,
                    'type': 'application' if loan.status in ['draft', 'submitted'] else 'loan',
                })
            
            return timeline
            
        except Exception as e:
            self.logger.error(f"Error getting user loan timeline: {e}")
            return []
    
    def _get_kcc_segmentation(self, kcc_members):
        """Get KCC member segmentation using RFM analysis"""
        try:
            from finance.models import LoanApplication
            
            segmentation = {
                'platinum': [],
                'gold': [],
                'silver': [],
                'bronze': [],
                'new': []
            }
            
            for member in kcc_members:
                # Get member's loan history
                loans = LoanApplication.objects.filter(borrower=member)
                
                if not loans.exists():
                    segmentation['new'].append({
                        'member_id': member.id,
                        'username': member.username,
                        'email': member.email,
                        'score': 0
                    })
                    continue
                
                # Calculate RFM score
                rfm_score = self._calculate_rfm_score(member, loans)
                
                # Assign to segment based on score
                if rfm_score >= 80:
                    segment = 'platinum'
                elif rfm_score >= 60:
                    segment = 'gold'
                elif rfm_score >= 40:
                    segment = 'silver'
                elif rfm_score >= 20:
                    segment = 'bronze'
                else:
                    segment = 'new'
                
                segmentation[segment].append({
                    'member_id': member.id,
                    'username': member.username,
                    'email': member.email,
                    'score': rfm_score
                })
            
            return segmentation
            
        except Exception as e:
            self.logger.error(f"Error getting KCC segmentation: {e}")
            return {}
    
    def _calculate_rfm_score(self, member, loans):
        """Calculate RFM (Recency, Frequency, Monetary) score for a member"""
        try:
            current_date = timezone.now()
            
            # Recency: Days since last loan
            last_loan = loans.order_by('-created_at').first()
            if last_loan:
                recency_days = (current_date - last_loan.created_at).days
                recency_score = max(0, 100 - (recency_days * 2))  # Higher score for recent activity
            else:
                recency_score = 0
            
            # Frequency: Number of loans
            frequency = loans.count()
            frequency_score = min(100, frequency * 20)  # Higher score for more loans
            
            # Monetary: Total amount borrowed
            total_amount = loans.aggregate(total=Sum('amount_requested'))['total'] or Decimal('0.00')
            monetary_score = min(100, float(total_amount) / 1000 * 100)  # Higher score for larger amounts
            
            # Calculate weighted RFM score
            rfm_score = (recency_score * 0.4) + (frequency_score * 0.3) + (monetary_score * 0.3)
            
            return round(rfm_score, 2)
            
        except Exception as e:
            self.logger.error(f"Error calculating RFM score for {member.username}: {e}")
            return 0
    
    def _get_kcc_loan_performance(self):
        """Get KCC loan performance metrics"""
        try:
            from finance.models import LoanApplication
            
            kcc_loans = LoanApplication.objects.filter(
                borrower__profile__is_karen_country_club_member=True
            )
            
            if not kcc_loans.exists():
                return {}
            
            performance = {
                'total_loans': kcc_loans.count(),
                'approved_loans': kcc_loans.filter(status__in=['approved', 'active', 'repaid']).count(),
                'active_loans': kcc_loans.filter(status='active').count(),
                'repaid_loans': kcc_loans.filter(status='repaid').count(),
                'total_amount': kcc_loans.filter(status__in=['approved', 'active', 'repaid']).aggregate(
                    total=Sum('amount_requested'))['total'] or Decimal('0.00'),
                'average_loan_amount': kcc_loans.filter(status__in=['approved', 'active', 'repaid']).aggregate(
                    avg=Avg('amount_requested'))['avg'] or Decimal('0.00'),
                'approval_rate': 0,
            }
            
            # Calculate approval rate
            if performance['total_loans'] > 0:
                performance['approval_rate'] = (performance['approved_loans'] / performance['total_loans']) * 100
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Error getting KCC loan performance: {e}")
            return {}
    
    def _get_kcc_optimization_opportunities(self):
        """Get KCC optimization opportunities"""
        try:
            opportunities = []
            
            # Opportunity 1: Increase loan limits for high-performing members
            opportunities.append({
                'type': 'loan_limit_increase',
                'title': 'Increase Loan Limits for High-Performing Members',
                'description': 'Members with high RFM scores could qualify for higher loan amounts',
                'priority': 'high',
                'potential_impact': 'Increase loan volume and member satisfaction'
            })
            
            # Opportunity 2: Reduce interest rates for platinum/gold members
            opportunities.append({
                'type': 'interest_rate_reduction',
                'title': 'Reduce Interest Rates for Premium Members',
                'description': 'Offer lower interest rates to platinum and gold tier members',
                'priority': 'medium',
                'potential_impact': 'Improve member retention and loyalty'
            })
            
            # Opportunity 3: Faster approval process for trusted members
            opportunities.append({
                'type': 'faster_approval',
                'title': 'Expedited Approval for Trusted Members',
                'description': 'Streamline approval process for members with excellent payment history',
                'priority': 'medium',
                'potential_impact': 'Improve member experience and reduce processing time'
            })
            
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Error getting KCC optimization opportunities: {e}")
            return []
    
    def _get_kcc_performance_trends(self):
        """Get KCC performance trends over time"""
        try:
            from finance.models import LoanApplication
            
            trends = []
            current_date = timezone.now()
            
            # Last 6 months
            for i in range(6):
                month_date = current_date.replace(day=1) - timezone.timedelta(days=30*i)
                month_start = month_date.replace(day=1)
                month_end = (month_start + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)
                
                month_loans = LoanApplication.objects.filter(
                    borrower__profile__is_karen_country_club_member=True,
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
            self.logger.error(f"Error getting KCC performance trends: {e}")
            return []
    
    def _get_staff_performance_by_department(self):
        """Get staff performance broken down by department"""
        try:
            from management.models import Department
            
            departments = Department.objects.all()
            performance = {}
            
            for dept in departments:
                staff_count = dept.employees.count()
                if staff_count > 0:
                    performance[dept.name] = {
                        'staff_count': staff_count,
                        'loans_count': 0,  # Would need to implement loan tracking by department
                        'total_amount': Decimal('0.00'),
                    }
            
            return performance
            
        except Exception as e:
            self.logger.error(f"Error getting staff performance by department: {e}")
            return {}
    
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
                'monthly_trends': monthly_trends.get('data', []) if monthly_trends.get('status') == 'success' else [],
                'status_distribution': status_distribution,
                'user_type_distribution': user_type_distribution,
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance charts: {e}")
            return {}
    
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
    
    def _generate_comprehensive_report(self, user=None):
        """Generate comprehensive performance report"""
        try:
            report = {
                'system_overview': self.get_system_overview(),
                'monthly_trends': self.get_monthly_trends(),
                'kcc_analytics': self.get_kcc_performance_analytics(),
                'staff_analytics': self.get_staff_performance_analytics(),
            }
            
            if user:
                report['user_analytics'] = self.get_user_performance_analytics(user)
            
            return {
                'status': 'success',
                'data': report,
                'generated_at': timezone.now().isoformat(),
            }
            
        except Exception as e:
            self.logger.error(f"Error generating comprehensive report: {e}")
            return {
                'status': 'error',
                'message': f"Error generating comprehensive report: {e}"
            } 