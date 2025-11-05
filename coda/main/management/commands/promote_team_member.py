"""
Management command to promote a team member to a manual category.

Usage:
    python manage.py promote_team_member <username> <category>
    python manage.py promote_team_member phinehas_maina junior_analyst
    python manage.py promote_team_member edwin_kimtai lead --priority 100
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Group
from accounts.models import TeamProfile, CustomerUser
from django.utils import timezone
from main.services.team_service import TeamService


class Command(BaseCommand):
    help = 'Promote a team member to a manual category'
    
    VALID_CATEGORIES = [
        'BOG/Leadership',
        'Elite Team',
        'Lead Team',
        'Support Team',
        'Senior Analysts',
        'Junior Analysts',
    ]
    
    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            type=str,
            help='Username of team member to promote',
        )
        parser.add_argument(
            'category',
            type=str,
            choices=self.VALID_CATEGORIES,
            help='Category to promote to',
        )
        parser.add_argument(
            '--priority',
            type=int,
            default=50,
            help='Display priority (higher = displayed first, default: 50)',
        )
        parser.add_argument(
            '--notes',
            type=str,
            default='',
            help='Promotion notes (reason, who approved, etc.)',
        )
    
    def handle(self, *args, **options):
        username = options['username']
        category = options['category']
        priority = options['priority']
        notes = options['notes']
        
        self.stdout.write(self.style.SUCCESS(f'\n🎯 Promoting Team Member\n'))
        self.stdout.write('=' * 70 + '\n')
        
        try:
            # Find user
            user = CustomerUser.objects.get(username=username)
            team_profile, created = TeamProfile.objects.get_or_create(user=user)
            
            # Show current state
            self.stdout.write(f"Member: {user.get_full_name()}")
            self.stdout.write(f"Username: {username}")
            self.stdout.write(f"Email: {user.email}")
            self.stdout.write(f"Current Points: {team_profile.total_points:,}")
            
            # Get current category
            current_category = team_profile.category or 'Not assigned'
            assignment_type = 'manual' if team_profile.is_manually_assigned else 'points-based'
            
            self.stdout.write(
                f"Current Assignment: {current_category} ({assignment_type})"
            )
            
            self.stdout.write('-' * 70)
            
            # Confirm promotion
            self.stdout.write(
                self.style.WARNING(
                    f"\nPromoting to: {category} (priority: {priority})"
                )
            )
            
            if notes:
                self.stdout.write(f"Notes: {notes}")
            else:
                notes = f'Promoted to {category} via management command'
            
            # Ask for confirmation
            confirm = input('\nProceed with promotion? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write(
                    self.style.WARNING('\nPromotion cancelled.')
                )
                return
            
            # Make the promotion using TeamService
            TeamService.assign_to_category(
                user,
                category,
                priority=priority,
                is_manual=True,
                notes=notes
            )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Successfully promoted {user.get_full_name()} to {category}!'
                )
            )
            
            # Next steps
            self.stdout.write('\n📝 Next Steps:')
            self.stdout.write(
                f'\n1. Verify on team page: /members/team_profiles'
            )
            self.stdout.write(
                f'\n2. Update their position/description if needed'
            )
            self.stdout.write(
                f'\n3. Notify the team member'
            )
            self.stdout.write('\n')
            
        except CustomerUser.DoesNotExist:
            raise CommandError(
                f'User with username "{username}" not found.\n'
                f'Check username spelling or create user first.'
            )
        except Exception as e:
            raise CommandError(f'Error promoting user: {str(e)}')

