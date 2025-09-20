"""
Django management command for KCC administrative tasks
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from datetime import date, timedelta

from accounts.models import UserProfile
from finance.models import LoanApplication


class Command(BaseCommand):
    help = 'Manage Karen Country Club operations and members'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=[
                'list_members', 'add_member', 'remove_member', 'renew_memberships',
                'recalculate_tiers', 'generate_report', 'cleanup_expired'
            ],
            help='Action to perform'
        )
        parser.add_argument(
            '--username',
            type=str,
            help='Username for member operations'
        )
        parser.add_argument(
            '--membership-number',
            type=str,
            help='KCC membership number'
        )
        parser.add_argument(
            '--expiry-days',
            type=int,
            default=365,
            help='Membership expiry in days (default: 365)'
        )
        parser.add_argument(
            '--output',
            type=str,
            choices=['console', 'csv', 'json'],
            default='console',
            help='Output format for reports'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'list_members':
            self.list_kcc_members(options)
        elif action == 'add_member':
            self.add_kcc_member(options)
        elif action == 'remove_member':
            self.remove_kcc_member(options)
        elif action == 'renew_memberships':
            self.renew_memberships(options)
        elif action == 'recalculate_tiers':
            self.recalculate_tiers(options)
        elif action == 'generate_report':
            self.generate_report(options)
        elif action == 'cleanup_expired':
            self.cleanup_expired_memberships(options)
    
    def list_kcc_members(self, options):
        """List all KCC members with their details"""
        self.stdout.write(self.style.SUCCESS('Listing KCC Members...'))
        
        members = UserProfile.objects.filter(
            is_karen_country_club_member=True
        ).select_related('user').order_by('kcc_membership_date')
        
        if not members:
            self.stdout.write(self.style.WARNING('No KCC members found'))
            return
        
        # Header
        self.stdout.write(
            f"{'Username':<15} {'Name':<25} {'Tier':<10} {'Member Since':<15} "
            f"{'Expiry':<15} {'Status':<10}"
        )
        self.stdout.write('-' * 90)
        
        for member in members:
            # Get tier
            tier = member.kcc_performance_tier or 'new'
            
            # Check if expired
            if member.kcc_membership_expiry and member.kcc_membership_expiry < date.today():
                status = 'EXPIRED'
            else:
                status = 'ACTIVE'
            
            # Format dates
            member_since = member.kcc_membership_date.strftime('%Y-%m-%d') if member.kcc_membership_date else 'N/A'
            expiry = member.kcc_membership_expiry.strftime('%Y-%m-%d') if member.kcc_membership_expiry else 'N/A'
            
            self.stdout.write(
                f"{member.user.username:<15} "
                f"{member.user.get_full_name() or 'N/A':<25} "
                f"{tier.upper():<10} "
                f"{member_since:<15} "
                f"{expiry:<15} "
                f"{status:<10}"
            )
        
        self.stdout.write(f'\nTotal KCC Members: {members.count()}')
    
    def add_kcc_member(self, options):
        """Add a new KCC member"""
        username = options.get('username')
        membership_number = options.get('membership_number')
        
        if not username:
            raise CommandError('Username is required for adding KCC member')
        
        try:
            profile = UserProfile.objects.get(user__username=username)
            
            if profile.is_karen_country_club_member:
                self.stdout.write(
                    self.style.WARNING(f'User {username} is already a KCC member')
                )
                return
            
            # Add KCC membership
            profile.is_karen_country_club_member = True
            profile.kcc_membership_date = date.today()
            profile.kcc_membership_expiry = date.today() + timedelta(days=options['expiry_days'])
            
            if membership_number:
                profile.kcc_membership_number = membership_number
            
            profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully added {username} as KCC member. '
                    f'Expires: {profile.kcc_membership_expiry}'
                )
            )
            
        except UserProfile.DoesNotExist:
            raise CommandError(f'User profile not found for username: {username}')
    
    def remove_kcc_member(self, options):
        """Remove KCC membership from a user"""
        username = options.get('username')
        
        if not username:
            raise CommandError('Username is required for removing KCC member')
        
        try:
            profile = UserProfile.objects.get(user__username=username)
            
            if not profile.is_karen_country_club_member:
                self.stdout.write(
                    self.style.WARNING(f'User {username} is not a KCC member')
                )
                return
            
            # Remove KCC membership
            profile.is_karen_country_club_member = False
            profile.kcc_membership_number = None
            profile.kcc_membership_expiry = None
            profile.kcc_membership_date = None
            profile.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully removed KCC membership from {username}')
            )
            
        except UserProfile.DoesNotExist:
            raise CommandError(f'User profile not found for username: {username}')
    
    def renew_memberships(self, options):
        """Renew expired KCC memberships"""
        self.stdout.write(self.style.SUCCESS('Renewing expired KCC memberships...'))
        
        expired_members = UserProfile.objects.filter(
            is_karen_country_club_member=True,
            kcc_membership_expiry__lt=date.today()
        )
        
        if not expired_members:
            self.stdout.write(self.style.WARNING('No expired memberships found'))
            return
        
        renewed_count = 0
        new_expiry = date.today() + timedelta(days=options['expiry_days'])
        
        for member in expired_members:
            member.kcc_membership_expiry = new_expiry
            member.save()
            renewed_count += 1
            
            self.stdout.write(
                f'Renewed membership for {member.user.username} until {new_expiry}'
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully renewed {renewed_count} memberships')
        )
    
    def recalculate_tiers(self, options):
        """Recalculate KCC performance tiers for all members"""
        self.stdout.write(self.style.SUCCESS('Recalculating KCC performance tiers...'))
        
        kcc_members = UserProfile.objects.filter(is_karen_country_club_member=True)
        
        if not kcc_members:
            self.stdout.write(self.style.WARNING('No KCC members found'))
            return
        
        updated_count = 0
        
        for member in kcc_members:
            try:
                # Force recalculation by accessing the property
                old_tier = getattr(member, '_cached_kcc_performance_tier', None)
                new_tier = member.kcc_performance_tier
                
                if old_tier != new_tier:
                    updated_count += 1
                    self.stdout.write(
                        f'{member.user.username}: {old_tier or "N/A"} → {new_tier}'
                    )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error calculating tier for {member.user.username}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully recalculated tiers for {updated_count} members')
        )
    
    def generate_report(self, options):
        """Generate KCC report"""
        self.stdout.write(self.style.SUCCESS('Generating KCC Report...'))
        
        today = date.today()
        
        # Membership statistics
        total_members = UserProfile.objects.filter(is_karen_country_club_member=True).count()
        active_members = UserProfile.objects.filter(
            is_karen_country_club_member=True,
            kcc_membership_expiry__gte=today
        ).count()
        expired_members = total_members - active_members
        
        # Tier distribution
        tier_distribution = {}
        for member in UserProfile.objects.filter(is_karen_country_club_member=True):
            tier = member.kcc_performance_tier or 'new'
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
        
        # Generate report
        report = f"""
KCC MANAGEMENT REPORT
Generated: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

MEMBERSHIP OVERVIEW
==================
Total KCC Members: {total_members}
Active Members: {active_members}
Expired Memberships: {expired_members}

TIER DISTRIBUTION
=================
"""
        
        for tier, count in sorted(tier_distribution.items()):
            percentage = (count / total_members * 100) if total_members > 0 else 0
            report += f"{tier.title()}: {count} ({percentage:.1f}%)\n"
        
        report += f"""
LOAN STATISTICS
===============
Total KCC Loans: {total_loans}
Total Amount Borrowed: ${total_amount:,.2f}
Average Loan Amount: ${(total_amount / total_loans):,.2f if total_loans > 0 else 0.00}

RECENT ACTIVITY
===============
"""
        
        # Recent loans
        recent_loans = kcc_loans.order_by('-created_at')[:5]
        for loan in recent_loans:
            report += f"- {loan.borrower.username}: ${loan.amount_requested:,.2f} ({loan.status})\n"
        
        # Recent members
        recent_members = UserProfile.objects.filter(
            is_karen_country_club_member=True
        ).order_by('-kcc_membership_date')[:5]
        
        report += "\nRecent KCC Members:\n"
        for member in recent_members:
            report += f"- {member.user.username} (since {member.kcc_membership_date})\n"
        
        # Output report
        if options['output'] == 'console':
            self.stdout.write(report)
        elif options['output'] == 'csv':
            # Generate CSV format
            self.stdout.write('CSV output not yet implemented')
        elif options['output'] == 'json':
            # Generate JSON format
            self.stdout.write('JSON output not yet implemented')
    
    def cleanup_expired_memberships(self, options):
        """Clean up expired KCC memberships"""
        self.stdout.write(self.style.SUCCESS('Cleaning up expired KCC memberships...'))
        
        expired_members = UserProfile.objects.filter(
            is_karen_country_club_member=True,
            kcc_membership_expiry__lt=date.today()
        )
        
        if not expired_members:
            self.stdout.write(self.style.WARNING('No expired memberships found'))
            return
        
        # Ask for confirmation
        self.stdout.write(f'Found {expired_members.count()} expired memberships')
        confirm = input('Do you want to remove expired memberships? (yes/no): ')
        
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.WARNING('Operation cancelled'))
            return
        
        # Remove expired memberships
        for member in expired_members:
            self.stdout.write(f'Removing expired membership: {member.user.username}')
            member.is_karen_country_club_member = False
            member.kcc_membership_number = None
            member.kcc_membership_expiry = None
            member.kcc_membership_date = None
            member.save()
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleaned up {expired_members.count()} expired memberships')
        ) 