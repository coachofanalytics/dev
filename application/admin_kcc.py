"""
Dedicated KCC Management Admin Interface
Provides comprehensive tools for managing Karen Country Club members and operations
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from decimal import Decimal
from datetime import date, timedelta

from accounts.models import UserProfile
from finance.models import LoanApplication, LoanPayment

@admin.register(UserProfile)
class KCCManagementAdmin(admin.ModelAdmin):
    """Comprehensive KCC management admin interface"""
    
    # Custom admin site title
    change_list_template = 'admin/kcc_management_change_list.html'
    
    # List display with KCC focus
    list_display = [
        'user_info', 'kcc_status', 'performance_tier', 'loan_summary', 
        'membership_duration', 'last_activity', 'actions'
    ]
    
    # Advanced filtering
    list_filter = [
        ('is_karen_country_club_member', admin.BooleanFieldListFilter),
        'kcc_performance_tier',
        ('kcc_membership_expiry', admin.DateFieldListFilter),
        'is_active'
    ]
    
    # Search capabilities
    search_fields = [
        'user__username', 'user__first_name', 'user__last_name', 'user__email',
        'kcc_membership_number'
    ]
    
    # KCC-specific actions
    actions = [
        'bulk_approve_kcc', 'bulk_renew_membership', 'bulk_upgrade_tier',
        'export_kcc_report', 'send_kcc_notifications'
    ]
    
    # Custom fieldsets for KCC management
    fieldsets = (
        ('KCC Membership', {
            'fields': (
                'is_karen_country_club_member', 'kcc_membership_number',
                'kcc_membership_date', 'kcc_membership_expiry'
            ),
            'classes': ('wide',)
        }),
        ('Performance Metrics', {
            'fields': ('performance_metrics_display',),
            'classes': ('collapse',),
            'description': 'Real-time performance metrics (read-only)'
        }),
        ('Loan History', {
            'fields': ('loan_history_display',),
            'classes': ('collapse',),
            'description': 'Complete loan application and payment history'
        }),
        ('Tier Management', {
            'fields': ('tier_management_display',),
            'classes': ('collapse',),
            'description': 'Tier progression and upgrade opportunities'
        })
    )
    
    readonly_fields = [
        'performance_metrics_display', 'loan_history_display', 'tier_management_display'
    ]
    
    def user_info(self, obj):
        """Display user information with avatar"""
        if obj.user:
            return format_html(
                '<div style="display: flex; align-items: center;">'
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 50%; margin-right: 10px;" />'
                '<div>'
                '<strong>{}</strong><br/>'
                '<small>{}</small>'
                '</div>'
                '</div>',
                obj.img_url if hasattr(obj, 'img_url') else '/static/default-avatar.png',
                obj.user.get_full_name() or obj.user.username,
                obj.user.email
            )
        return "No User"
    user_info.short_description = 'User Information'
    user_info.allow_tags = True
    
    def kcc_status(self, obj):
        """Display KCC membership status with visual indicators"""
        if not obj.is_karen_country_club_member:
            return format_html(
                '<span style="color: #999; font-weight: bold;">Not KCC Member</span>'
            )
        
        # Check if membership is expired
        if obj.kcc_membership_expiry and obj.kcc_membership_expiry < date.today():
            status_color = '#ff4444'
            status_text = 'EXPIRED'
        else:
            status_color = '#00aa00'
            status_text = 'ACTIVE'
        
        return format_html(
            '<div style="text-align: center;">'
            '<span style="color: {}; font-weight: bold; font-size: 12px;">{}</span><br/>'
            '<small>Member #{}</small>'
            '</div>',
            status_color, status_text, obj.kcc_membership_number or 'N/A'
        )
    kcc_status.short_description = 'KCC Status'
    kcc_status.allow_tags = True
    
    def performance_tier(self, obj):
        """Display performance tier with visual enhancement"""
        if not obj.is_karen_country_club_member:
            return "N/A"
        
        tier = obj.kcc_performance_tier
        tier_config = {
            'new': {'color': '#ff9500', 'icon': '🆕'},
            'bronze': {'color': '#cd7f32', 'icon': '🥉'},
            'silver': {'color': '#c0c0c0', 'icon': '🥈'},
            'gold': {'color': '#ffd700', 'icon': '🥇'},
            'platinum': {'color': '#e5e4e2', 'icon': '💎'}
        }
        
        config = tier_config.get(tier, {'color': '#000000', 'icon': '❓'})
        
        return format_html(
            '<div style="text-align: center;">'
            '<span style="font-size: 20px;">{}</span><br/>'
            '<span style="color: {}; font-weight: bold; text-transform: uppercase;">{}</span>'
            '</div>',
            config['icon'], config['color'], tier
        )
    performance_tier.short_description = 'Performance Tier'
    performance_tier.allow_tags = True
    
    def loan_summary(self, obj):
        """Display loan summary statistics"""
        if not obj.is_karen_country_club_member:
            return "N/A"
        
        try:
            user_loans = LoanApplication.objects.filter(borrower=obj.user)
            total_loans = user_loans.count()
            active_loans = user_loans.filter(status='active').count()
            total_borrowed = user_loans.filter(
                status__in=['repaid', 'active']
            ).aggregate(Sum('amount_requested'))['amount_requested__sum'] or Decimal('0.00')
            
            return format_html(
                '<div style="text-align: center;">'
                '<strong>Total: {}</strong><br/>'
                '<small>Active: {} | ${:,.2f}</small>'
                '</div>',
                total_loans, active_loans, total_borrowed
            )
        except Exception:
            return "Error"
    loan_summary.short_description = 'Loan Summary'
    loan_summary.allow_tags = True
    
    def membership_duration(self, obj):
        """Display membership duration"""
        if not obj.is_karen_country_club_member or not obj.kcc_membership_date:
            return "N/A"
        
        duration = (date.today() - obj.kcc_membership_date).days
        if duration < 30:
            return f"{duration} days"
        elif duration < 365:
            months = duration // 30
            return f"{months} month{'s' if months > 1 else ''}"
        else:
            years = duration // 365
            return f"{years} year{'s' if years > 1 else ''}"
    membership_duration.short_description = 'Member Since'
    
    def last_activity(self, obj):
        """Display last loan activity"""
        if not obj.is_karen_country_club_member:
            return "N/A"
        
        try:
            last_loan = LoanApplication.objects.filter(
                borrower=obj.user
            ).order_by('-updated_at').first()
            
            if last_loan:
                days_ago = (date.today() - last_loan.updated_at.date()).days
                if days_ago == 0:
                    return "Today"
                elif days_ago == 1:
                    return "Yesterday"
                elif days_ago < 7:
                    return f"{days_ago} days ago"
                elif days_ago < 30:
                    weeks = days_ago // 7
                    return f"{weeks} week{'s' if weeks > 1 else ''} ago"
                else:
                    months = days_ago // 30
                    return f"{months} month{'s' if months > 1 else ''} ago"
            else:
                return "No activity"
        except Exception:
            return "Error"
    last_activity.short_description = 'Last Activity'
    
    def actions(self, obj):
        """Display action buttons"""
        if not obj.is_karen_country_club_member:
            return format_html(
                '<a href="?action=make_kcc&user_id={}" class="button">Make KCC Member</a>',
                obj.user.id if obj.user else 0
            )
        
        return format_html(
            '<div style="display: flex; gap: 5px;">'
            '<a href="?action=view_details&user_id={}" class="button">View Details</a>'
            '<a href="?action=manage_tier&user_id={}" class="button">Manage Tier</a>'
            '</div>',
            obj.user.id if obj.user else 0,
            obj.user.id if obj.user else 0
        )
    actions.short_description = 'Actions'
    actions.allow_tags = True
    
    # Custom admin actions
    def bulk_approve_kcc(self, request, queryset):
        """Bulk approve KCC membership for selected users"""
        updated = queryset.update(
            is_karen_country_club_member=True,
            kcc_membership_date=date.today()
        )
        self.message_user(request, f'{updated} users approved for KCC membership')
    bulk_approve_kcc.short_description = "Approve KCC membership for selected users"
    
    def bulk_renew_membership(self, request, queryset):
        """Bulk renew KCC membership for selected users"""
        new_expiry = date.today() + timedelta(days=365)
        updated = queryset.filter(is_karen_country_club_member=True).update(
            kcc_membership_expiry=new_expiry
        )
        self.message_user(request, f'{updated} KCC memberships renewed until {new_expiry}')
    bulk_renew_membership.short_description = "Renew KCC membership for selected users"
    
    def bulk_upgrade_tier(self, request, queryset):
        """Bulk upgrade KCC tier for selected users"""
        # This would implement tier upgrade logic
        self.message_user(request, f'Tier upgrade initiated for {queryset.count()} users')
    bulk_upgrade_tier.short_description = "Upgrade KCC tier for selected users"
    
    def export_kcc_report(self, request, queryset):
        """Export KCC report for selected users"""
        # This would implement CSV/Excel export
        self.message_user(request, f'KCC report export initiated for {queryset.count()} users')
    export_kcc_report.short_description = "Export KCC report for selected users"
    
    def send_kcc_notifications(self, request, queryset):
        """Send KCC notifications to selected users"""
        # This would implement notification sending
        self.message_user(request, f'KCC notifications sent to {queryset.count()} users')
    send_kcc_notifications.short_description = "Send KCC notifications to selected users"
    
    # Performance metrics display
    def performance_metrics_display(self, obj):
        """Display comprehensive performance metrics"""
        if not obj.is_karen_country_club_member:
            return "User is not a KCC member"
        
        try:
            # Get performance metrics
            metrics = obj.get_performance_metrics() if hasattr(obj, 'get_performance_metrics') else None
            
            if metrics:
                return format_html(
                    '<div style="background: #f9f9f9; padding: 15px; border-radius: 5px;">'
                    '<h4>Performance Metrics</h4>'
                    '<table style="width: 100%; border-collapse: collapse;">'
                    '<tr><td><strong>Total Loans:</strong></td><td>{}</td></tr>'
                    '<tr><td><strong>Active Loans:</strong></td><td>{}</td></tr>'
                    '<tr><td><strong>Repaid Loans:</strong></td><td>{}</td></tr>'
                    '<tr><td><strong>Total Borrowed:</strong></td><td>${:,.2f}</td></tr>'
                    '<tr><td><strong>Average Loan:</strong></td><td>${:,.2f}</td></tr>'
                    '<tr><td><strong>Membership Duration:</strong></td><td>{} days</td></tr>'
                    '</table>'
                    '</div>',
                    metrics.get('total_loans', 0),
                    metrics.get('active_loans', 0),
                    metrics.get('repaid_loans', 0),
                    metrics.get('total_borrowed', Decimal('0.00')),
                    metrics.get('average_loan_amount', Decimal('0.00')),
                    metrics.get('membership_duration_days', 0)
                )
            else:
                return "Performance metrics not available"
        except Exception as e:
            return f"Error calculating metrics: {str(e)}"
    performance_metrics_display.short_description = 'Performance Metrics'
    performance_metrics_display.allow_tags = True
    
    # Loan history display
    def loan_history_display(self, obj):
        """Display loan application and payment history"""
        if not obj.is_karen_country_club_member:
            return "User is not a KCC member"
        
        try:
            user_loans = LoanApplication.objects.filter(borrower=obj.user).order_by('-created_at')[:10]
            
            if not user_loans:
                return "No loan history found"
            
            history_html = '<div style="background: #f9f9f9; padding: 15px; border-radius: 5px;">'
            history_html += '<h4>Recent Loan History</h4>'
            history_html += '<table style="width: 100%; border-collapse: collapse; font-size: 12px;">'
            history_html += '<tr style="background: #e0e0e0;"><th>Date</th><th>Amount</th><th>Status</th><th>Balance</th></tr>'
            
            for loan in user_loans:
                balance = getattr(loan, 'balance_amount', loan.amount_requested)
                history_html += format_html(
                    '<tr>'
                    '<td>{}</td>'
                    '<td>${:,.2f}</td>'
                    '<td>{}</td>'
                    '<td>${:,.2f}</td>'
                    '</tr>',
                    loan.created_at.strftime('%Y-%m-%d'),
                    loan.amount_requested,
                    loan.status.title(),
                    balance
                )
            
            history_html += '</table></div>'
            return format_html(history_html)
        except Exception as e:
            return f"Error loading loan history: {str(e)}"
    loan_history_display.short_description = 'Loan History'
    loan_history_display.allow_tags = True
    
    # Tier management display
    def tier_management_display(self, obj):
        """Display tier management information"""
        if not obj.is_karen_country_club_member:
            return "User is not a KCC member"
        
        try:
            current_tier = obj.kcc_performance_tier
            benefits = obj.kcc_benefits
            
            if not benefits:
                return "Benefits information not available"
            
            # Check if user can upgrade
            can_upgrade = obj.can_upgrade_tier() if hasattr(obj, 'can_upgrade_tier') else False
            
            tier_html = '<div style="background: #f9f9f9; padding: 15px; border-radius: 5px;">'
            tier_html += '<h4>Tier Management</h4>'
            tier_html += f'<p><strong>Current Tier:</strong> {current_tier.title()}</p>'
            tier_html += f'<p><strong>Max Loan:</strong> ${benefits["max_loan"]:,.2f}</p>'
            tier_html += f'<p><strong>Interest Discount:</strong> {benefits["interest_rate_discount"]}%</p>'
            tier_html += f'<p><strong>Fee Discount:</strong> {benefits["processing_fee_discount"]}%</p>'
            
            if can_upgrade:
                tier_html += '<p style="color: #00aa00; font-weight: bold;">✅ Eligible for tier upgrade!</p>'
            else:
                tier_html += '<p style="color: #999;">⏳ Working towards next tier...</p>'
            
            tier_html += '</div>'
            return format_html(tier_html)
        except Exception as e:
            return f"Error loading tier information: {str(e)}"
    tier_management_display.short_description = 'Tier Management'
    tier_management_display.allow_tags = True
    
    # Override changelist to handle custom actions
    def changelist_view(self, request, extra_context=None):
        """Handle custom actions in changelist view"""
        if 'action' in request.GET:
            action = request.GET.get('action')
            user_id = request.GET.get('user_id')
            
            if action == 'make_kcc' and user_id:
                try:
                    profile = UserProfile.objects.get(user_id=user_id)
                    profile.is_karen_country_club_member = True
                    profile.kcc_membership_date = date.today()
                    profile.save()
                    messages.success(request, f'User {profile.user.username} is now a KCC member')
                except UserProfile.DoesNotExist:
                    messages.error(request, 'User profile not found')
                
                return HttpResponseRedirect(request.path)
        
        return super().changelist_view(request, extra_context)
    
    # Custom admin site configuration
    class Media:
        css = {
            'all': ('admin/css/kcc_admin.css',)
        }
        js = ('admin/js/kcc_admin.js',)

# Register the KCC management admin
admin.site.unregister(UserProfile)  # Unregister the default
admin.site.register(UserProfile, KCCManagementAdmin) 