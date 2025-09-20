"""
KCC Dashboard Admin Interface
Provides high-level overview and analytics for KCC operations
"""

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.html import format_html
from django.db.models import Count, Sum, Q, Avg
from django.utils import timezone
from django.urls import path, reverse
from django.shortcuts import render
from django.http import JsonResponse
from decimal import Decimal
from datetime import date, timedelta
import json

from accounts.models import UserProfile
from finance.models import LoanApplication, LoanPayment

class KCCDashboardAdminSite(AdminSite):
    """Custom admin site for KCC Dashboard"""
    site_header = "KCC Management Dashboard"
    site_title = "KCC Dashboard"
    index_title = "Karen Country Club Management"

class KCCDashboardAdmin(admin.ModelAdmin):
    """KCC Dashboard with analytics and reporting"""
    
    change_list_template = 'admin/kcc_dashboard_change_list.html'
    
    def get_urls(self):
        """Add custom dashboard URLs"""
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_site.admin_view(self.kcc_dashboard_view), name='kcc_dashboard'),
            path('analytics/', self.admin_site.admin_view(self.kcc_analytics_view), name='kcc_analytics'),
            path('reports/', self.admin_site.admin_view(self.kcc_reports_view), name='kcc_reports'),
            path('api/kcc-stats/', self.admin_site.admin_view(self.kcc_stats_api), name='kcc_stats_api'),
        ]
        return custom_urls + urls
    
    def kcc_dashboard_view(self, request):
        """Main KCC dashboard view"""
        context = self.get_dashboard_context()
        return render(request, 'admin/kcc_dashboard.html', context)
    
    def kcc_analytics_view(self, request):
        """KCC analytics view"""
        context = self.get_analytics_context()
        return render(request, 'admin/kcc_analytics.html', context)
    
    def kcc_reports_view(self, request):
        """KCC reports view"""
        context = self.get_reports_context()
        return render(request, 'admin/kcc_reports.html', context)
    
    def kcc_stats_api(self, request):
        """API endpoint for KCC statistics"""
        stats = self.get_kcc_statistics()
        return JsonResponse(stats)
    
    def get_dashboard_context(self):
        """Get context data for dashboard"""
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        
        # KCC membership statistics
        total_kcc_members = UserProfile.objects.filter(
            is_karen_country_club_member=True
        ).count()
        
        active_kcc_members = UserProfile.objects.filter(
            is_karen_country_club_member=True,
            kcc_membership_expiry__gte=today
        ).count()
        
        expired_memberships = UserProfile.objects.filter(
            is_karen_country_club_member=True,
            kcc_membership_expiry__lt=today
        ).count()
        
        new_members_this_month = UserProfile.objects.filter(
            is_karen_country_club_member=True,
            kcc_membership_date__gte=thirty_days_ago
        ).count()
        
        # Tier distribution
        tier_distribution = {}
        for profile in UserProfile.objects.filter(is_karen_country_club_member=True):
            tier = profile.kcc_performance_tier or 'new'
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        # Loan statistics for KCC members
        kcc_user_ids = UserProfile.objects.filter(
            is_karen_country_club_member=True
        ).values_list('user_id', flat=True)
        
        kcc_loans = LoanApplication.objects.filter(borrower_id__in=kcc_user_ids)
        total_kcc_loans = kcc_loans.count()
        active_kcc_loans = kcc_loans.filter(status='active').count()
        total_kcc_borrowed = kcc_loans.filter(
            status__in=['repaid', 'active']
        ).aggregate(Sum('amount_requested'))['amount_requested__sum'] or Decimal('0.00')
        
        # Recent activity
        recent_loans = kcc_loans.order_by('-created_at')[:5]
        recent_members = UserProfile.objects.filter(
            is_karen_country_club_member=True
        ).order_by('-kcc_membership_date')[:5]
        
        context = {
            'total_kcc_members': total_kcc_members,
            'active_kcc_members': active_kcc_members,
            'expired_memberships': expired_memberships,
            'new_members_this_month': new_members_this_month,
            'tier_distribution': tier_distribution,
            'total_kcc_loans': total_kcc_loans,
            'active_kcc_loans': active_kcc_loans,
            'total_kcc_borrowed': total_kcc_borrowed,
            'recent_loans': recent_loans,
            'recent_members': recent_members,
            'today': today,
            'thirty_days_ago': thirty_days_ago,
        }
        
        return context
    
    def get_analytics_context(self):
        """Get context data for analytics"""
        today = date.today()
        
        # Time series data for the last 12 months
        monthly_data = []
        for i in range(12):
            month_date = today - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            # New KCC members this month
            new_members = UserProfile.objects.filter(
                is_karen_country_club_member=True,
                kcc_membership_date__gte=month_start,
                kcc_membership_date__lte=month_end
            ).count()
            
            # KCC loans this month
            month_loans = LoanApplication.objects.filter(
                borrower__profile__is_karen_country_club_member=True,
                created_at__gte=month_start,
                created_at__lte=month_end
            )
            month_loan_count = month_loans.count()
            month_loan_amount = month_loans.aggregate(
                Sum('amount_requested')
            )['amount_requested__sum'] or Decimal('0.00')
            
            monthly_data.append({
                'month': month_start.strftime('%Y-%m'),
                'new_members': new_members,
                'loan_count': month_loan_count,
                'loan_amount': float(month_loan_amount)
            })
        
        # Tier progression analysis
        tier_progression = {}
        for profile in UserProfile.objects.filter(is_karen_country_club_member=True):
            tier = profile.kcc_performance_tier or 'new'
            if tier not in tier_progression:
                tier_progression[tier] = {
                    'count': 0,
                    'avg_loans': 0,
                    'avg_amount': Decimal('0.00'),
                    'upgrade_potential': 0
                }
            
            tier_progression[tier]['count'] += 1
            
            # Calculate average loans and amount for this tier
            user_loans = LoanApplication.objects.filter(borrower=profile.user)
            tier_progression[tier]['avg_loans'] += user_loans.count()
            
            user_total = user_loans.filter(
                status__in=['repaid', 'active']
            ).aggregate(Sum('amount_requested'))['amount_requested__sum'] or Decimal('0.00')
            tier_progression[tier]['avg_amount'] += user_total
        
        # Calculate averages
        for tier_data in tier_progression.values():
            if tier_data['count'] > 0:
                tier_data['avg_loans'] = tier_data['avg_loans'] / tier_data['count']
                tier_data['avg_amount'] = tier_data['avg_amount'] / tier_data['count']
        
        # Performance metrics
        performance_metrics = {
            'avg_loan_amount': float(total_kcc_borrowed / total_kcc_loans if total_kcc_loans > 0 else 0),
            'loan_approval_rate': 0,  # Would need to calculate from loan statuses
            'avg_repayment_time': 0,   # Would need to calculate from payment history
            'member_satisfaction': 0   # Would need to implement feedback system
        }
        
        context = {
            'monthly_data': monthly_data,
            'tier_progression': tier_progression,
            'performance_metrics': performance_metrics,
        }
        
        return context
    
    def get_reports_context(self):
        """Get context data for reports"""
        today = date.today()
        
        # Generate various reports
        reports = {
            'membership_report': self.generate_membership_report(),
            'loan_report': self.generate_loan_report(),
            'performance_report': self.generate_performance_report(),
            'financial_report': self.generate_financial_report(),
        }
        
        context = {
            'reports': reports,
            'today': today,
        }
        
        return context
    
    def generate_membership_report(self):
        """Generate KCC membership report"""
        today = date.today()
        
        # Total members by tier
        tier_counts = {}
        for profile in UserProfile.objects.filter(is_karen_country_club_member=True):
            tier = profile.kcc_performance_tier or 'new'
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        # Membership growth
        growth_data = []
        for i in range(6):
            month_date = today - timedelta(days=30*i)
            month_start = month_date.replace(day=1)
            month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            new_members = UserProfile.objects.filter(
                is_karen_country_club_member=True,
                kcc_membership_date__gte=month_start,
                kcc_membership_date__lte=month_end
            ).count()
            
            growth_data.append({
                'month': month_start.strftime('%Y-%m'),
                'new_members': new_members
            })
        
        return {
            'total_members': UserProfile.objects.filter(is_karen_country_club_member=True).count(),
            'tier_distribution': tier_counts,
            'growth_trend': growth_data,
            'expired_memberships': UserProfile.objects.filter(
                is_karen_country_club_member=True,
                kcc_membership_expiry__lt=today
            ).count()
        }
    
    def generate_loan_report(self):
        """Generate KCC loan report"""
        kcc_user_ids = UserProfile.objects.filter(
            is_karen_country_club_member=True
        ).values_list('user_id', flat=True)
        
        kcc_loans = LoanApplication.objects.filter(borrower_id__in=kcc_user_ids)
        
        # Loan statistics
        total_loans = kcc_loans.count()
        active_loans = kcc_loans.filter(status='active').count()
        repaid_loans = kcc_loans.filter(status='repaid').count()
        rejected_loans = kcc_loans.filter(status='rejected').count()
        
        # Amount statistics
        total_requested = kcc_loans.aggregate(
            Sum('amount_requested')
        )['amount_requested__sum'] or Decimal('0.00')
        
        total_approved = kcc_loans.filter(
            status__in=['approved', 'active', 'repaid']
        ).aggregate(Sum('amount_requested'))['amount_requested__sum'] or Decimal('0.00')
        
        # Average loan amounts by tier
        tier_loan_amounts = {}
        for profile in UserProfile.objects.filter(is_karen_country_club_member=True):
            tier = profile.kcc_performance_tier or 'new'
            user_loans = LoanApplication.objects.filter(borrower=profile.user)
            user_total = user_loans.aggregate(
                Sum('amount_requested')
            )['amount_requested__sum'] or Decimal('0.00')
            
            if tier not in tier_loan_amounts:
                tier_loan_amounts[tier] = []
            tier_loan_amounts[tier].append(float(user_total))
        
        # Calculate averages
        tier_averages = {}
        for tier, amounts in tier_loan_amounts.items():
            tier_averages[tier] = sum(amounts) / len(amounts) if amounts else 0
        
        return {
            'total_loans': total_loans,
            'active_loans': active_loans,
            'repaid_loans': repaid_loans,
            'rejected_loans': rejected_loans,
            'total_requested': float(total_requested),
            'total_approved': float(total_approved),
            'approval_rate': (total_approved / total_requested * 100) if total_requested > 0 else 0,
            'tier_averages': tier_averages
        }
    
    def generate_performance_report(self):
        """Generate KCC performance report"""
        # This would analyze loan repayment performance, tier progression, etc.
        return {
            'message': 'Performance report generation not yet implemented'
        }
    
    def generate_financial_report(self):
        """Generate KCC financial report"""
        # This would analyze revenue, costs, profitability of KCC loans
        return {
            'message': 'Financial report generation not yet implemented'
        }
    
    def get_kcc_statistics(self):
        """Get KCC statistics for API"""
        today = date.today()
        
        # Basic counts
        total_members = UserProfile.objects.filter(is_karen_country_club_member=True).count()
        active_members = UserProfile.objects.filter(
            is_karen_country_club_member=True,
            kcc_membership_expiry__gte=today
        ).count()
        
        # Tier distribution
        tier_distribution = {}
        for profile in UserProfile.objects.filter(is_karen_country_club_member=True):
            tier = profile.kcc_performance_tier or 'new'
            tier_distribution[tier] = tier_distribution.get(tier, 0) + 1
        
        # Loan statistics
        kcc_user_ids = UserProfile.objects.filter(
            is_karen_country_club_member=True
        ).values_list('user_id', flat=True)
        
        kcc_loans = LoanApplication.objects.filter(borrower_id__in=kcc_user_ids)
        total_loans = kcc_loans.count()
        total_amount = kcc_loans.aggregate(
            Sum('amount_requested')
        )['amount_requested__sum'] or Decimal('0.00')
        
        return {
            'total_members': total_members,
            'active_members': active_members,
            'tier_distribution': tier_distribution,
            'total_loans': total_loans,
            'total_amount': float(total_amount),
            'last_updated': timezone.now().isoformat()
        }

# Create and register the KCC dashboard admin site
kcc_admin_site = KCCDashboardAdminSite(name='kcc_admin')

# Register models with the KCC admin site
kcc_admin_site.register(UserProfile, KCCDashboardAdmin)

# Also register with the main admin site for integration
admin.site.register(UserProfile, KCCDashboardAdmin) 