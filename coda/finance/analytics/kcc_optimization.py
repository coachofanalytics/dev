"""
KCC Optimization Analytics Service
Provides specialized analytics for KCC member optimization
"""

from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

class KCCOptimizationAnalytics:
    """KCC optimization analytics service"""
    
    def __init__(self):
        self.logger = logger
    
    def generate_kcc_optimization_report(self, **kwargs):
        """Generate comprehensive KCC optimization report"""
        try:
            from finance.models import LoanApplication
            from shared_core.users import CustomerUser
            
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
            optimization_opportunities = self._get_optimization_opportunities()
            
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
            self.logger.error(f"Error generating KCC optimization report: {e}")
            return {
                'status': 'error',
                'message': f"Error generating KCC report: {e}"
            }
    
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
    
    def _get_optimization_opportunities(self):
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
            self.logger.error(f"Error getting optimization opportunities: {e}")
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