"""
Management command to show team members ready for promotion.

Usage:
    python manage.py show_promotion_candidates
    python manage.py show_promotion_candidates --detailed
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import TeamProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Show team members ready for promotion to Junior Analyst (6,000+ points)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed information for each candidate',
        )
    
    def handle(self, *args, **options):
        detailed = options['detailed']
        
        self.stdout.write(self.style.SUCCESS('\n🎯 Promotion Candidates Report\n'))
        self.stdout.write('=' * 80 + '\n')
        
        # Get promotion candidates (6,000+ points, not manually assigned)
        candidates = User.objects.filter(
            team_profile__is_manually_assigned=False,
            team_profile__total_points__gte=6000,
            is_active=True,
            category=2  # Employee
        ).select_related('profile', 'team_profile').order_by('-team_profile__total_points')
        
        if not candidates:
            self.stdout.write(
                self.style.SUCCESS(
                    '✅ No promotion candidates at this time.\n'
                    'All trainees with 6,000+ points have been promoted.\n'
                )
            )
            return
        
        self.stdout.write(
            self.style.WARNING(
                f'Found {len(candidates)} member(s) ready for manual promotion:\n'
            )
        )
        
        # Display candidates
        for i, user in enumerate(candidates, 1):
            team_profile = user.team_profile
            points = team_profile.total_points
            
            self.stdout.write(f"\n{i}. {user.get_full_name()}")
            self.stdout.write('-' * 80)
            self.stdout.write(f"   Username: {user.username}")
            self.stdout.write(f"   Email: {user.email}")
            self.stdout.write(f"   Total Points: {points:,}")
            self.stdout.write(f"   Position: {user.profile.position or 'Not set'}")
            
            if detailed:
                # Show point breakdown
                self.stdout.write('\n   Point Breakdown:')
                
                # Education
                edu_points = {
                    1: 250, 2: 500, 3: 1000, 4: 1500, 5: 2000
                }.get(profile.education, 0)
                edu_name = {
                    1: 'High School', 2: 'Some College', 3: "Bachelor's",
                    4: "Master's", 5: 'Doctorate'
                }.get(profile.education, 'Unknown')
                self.stdout.write(f"     • Education: {edu_points:,} ({edu_name})")
                
                # Task history
                from management.models import TaskHistory
                task_pts = TaskHistory.objects.filter(
                    employee_id=user
                ).aggregate(total=Sum('point'))['total'] or 0
                task_count = TaskHistory.objects.filter(employee_id=user).count()
                self.stdout.write(f"     • Task History: {task_pts:,} ({task_count} tasks)")
                
                # Requirements
                from management.models import Requirement
                req_pts = Requirement.objects.filter(
                    assigned_to=user
                ).aggregate(total=Sum('duration'))['total'] or 0
                req_count = Requirement.objects.filter(assigned_to=user).count()
                self.stdout.write(f"     • Requirements: {req_pts:,} ({req_count} requirements)")
                
                # Training
                from management.models import Training
                trainings = Training.objects.filter(presenter=user)
                train_pts = 0
                for training in trainings:
                    multiplier = {1: 5, 2: 10, 3: 15, 4: 20, 5: 25}.get(training.level, 0)
                    train_pts += training.level * multiplier
                train_count = trainings.count()
                self.stdout.write(f"     • Training: {train_pts:,} ({train_count} trainings)")
                
                # Assessment
                from professional_services.models import ClientAssessment
                from django.db.models import Sum
                assessment = ClientAssessment.objects.filter(
                    email=user.email
                ).order_by('-rating_date').first()
                assess_pts = assessment.totalpoints if assessment else 0
                self.stdout.write(f"     • Assessment: {assess_pts:,}")
                
                # Days since points calculated
                if profile.total_points_calculated_at:
                    from django.utils import timezone
                    days_ago = (timezone.now() - profile.total_points_calculated_at).days
                    self.stdout.write(f"\n   Last calculated: {days_ago} days ago")
        
        # Instructions
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('\n📝 Next Steps:\n')
        self.stdout.write(
            '\n1. Review each candidate (check skills, projects, behavior)'
        )
        self.stdout.write(
            '\n2. To promote a candidate to Junior Analyst:'
        )
        self.stdout.write(
            '\n   python manage.py promote_team_member <username> junior_analyst'
        )
        self.stdout.write(
            '\n\n3. Or use Django Admin:'
        )
        self.stdout.write(
            '\n   - Go to Accounts → User Profiles'
        )
        self.stdout.write(
            '\n   - Find the user'
        )
        self.stdout.write(
            '\n   - Set: is_manually_assigned=True, team_category_manual=junior_analyst'
        )
        self.stdout.write('\n')

