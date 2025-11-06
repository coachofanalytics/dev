"""
Management command to recalculate points for future talent team members.

Usage:
    python manage.py recalculate_team_points
    python manage.py recalculate_team_points --all  # Include manually assigned
    python manage.py recalculate_team_points --dry-run
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from accounts.models import TeamProfile
from django.utils import timezone
from django.db.models import Sum
from main.services.team_service import TeamService


class Command(BaseCommand):
    help = 'Recalculate points for future talent team members (non-manually assigned)'
    
    # Point calculation constants
    EDUCATION_MULTIPLIERS = {
        1: 250,    # High School
        2: 500,    # Some College
        3: 1000,   # Bachelor's
        4: 1500,   # Master's
        5: 2000,   # Doctorate
    }
    
    TRAINING_MULTIPLIERS = {
        1: 5,
        2: 10,
        3: 15,
        4: 20,
        5: 25,
    }
    
    POINT_THRESHOLDS = {
        'senior_trainee': (5000, 6000),
        'junior_trainee': (4000, 5000),
        'elementary': (0, 4000),
        'ready_for_promotion': (6000, 999999),
    }
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Calculate points for all members (including manually assigned)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be calculated without saving',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed point breakdown',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        include_all = options['all']
        verbose = options['verbose']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))
        
        self.stdout.write(self.style.SUCCESS('📊 Recalculating Team Points\n'))
        self.stdout.write('=' * 80 + '\n')
        
        # Get profiles to calculate
        if include_all:
            profiles = TeamProfile.objects.filter(
                user__category=2,  # Employee category
                user__is_active=True
            ).select_related('user')
            self.stdout.write('Calculating for: ALL team members\n')
        else:
            profiles = TeamProfile.objects.filter(
                is_manually_assigned=False,
                user__category=2,
                user__is_active=True
            ).select_related('user')
            self.stdout.write('Calculating for: FUTURE TALENTS only (non-manually assigned)\n')
        
        self.stdout.write(f"Total profiles to process: {profiles.count()}\n")
        self.stdout.write('-' * 80 + '\n')
        
        total_updated = 0
        promotion_ready = []
        category_counts = {
            'senior_trainee': 0,
            'junior_trainee': 0,
            'elementary': 0,
            'ready_for_promotion': 0,
        }
        
        for team_profile in profiles:
            user = team_profile.user
            
            # Calculate points using TeamService
            old_points = team_profile.total_points
            new_points = TeamService.calculate_total_points(user)
            
            # Determine category
            category = self._get_category_from_points(new_points)
            category_counts[category] += 1
            
            # Save if not dry run
            if not dry_run:
                team_profile.total_points = new_points
                team_profile.save()
                
                # Auto-categorize if not manual
                if not team_profile.is_manually_assigned:
                    TeamService.auto_categorize_by_points(user)
            
            total_updated += 1
            
            # Track promotion candidates
            if new_points >= 6000 and not team_profile.is_manually_assigned:
                promotion_ready.append((team_profile, new_points))
            
            # Display
            change_indicator = ''
            if new_points > old_points:
                change_indicator = f'(↑ +{new_points - old_points:,})'
            elif new_points < old_points:
                change_indicator = f'(↓ -{old_points - new_points:,})'
            else:
                change_indicator = '(no change)'
            
            assignment_type = '📌 Manual' if team_profile.is_manually_assigned else '📊 Points'
            
            self.stdout.write(
                f"  {assignment_type} "
                f"{user.get_full_name():30} "
                f"{new_points:6,} pts {change_indicator:20} → {category:20}"
            )
        
        # Summary
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('\n📊 SUMMARY:')
        self.stdout.write(f"  ✅ Profiles updated: {total_updated}")
        self.stdout.write('\n📂 Category Breakdown:')
        self.stdout.write(f"  🎯 Ready for Promotion (≥6,000): {category_counts['ready_for_promotion']}")
        self.stdout.write(f"  🌟 Senior Trainee (5,000-6,000): {category_counts['senior_trainee']}")
        self.stdout.write(f"  📚 Junior Trainee (4,000-5,000): {category_counts['junior_trainee']}")
        self.stdout.write(f"  🌱 Elementary (<4,000): {category_counts['elementary']}")
        
        # Show promotion candidates
        if promotion_ready:
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  {len(promotion_ready)} members ready for manual promotion to Junior Analyst:\n'
                )
            )
            for team_profile, points in promotion_ready:
                self.stdout.write(
                    f"  🎯 {team_profile.user.get_full_name():30} "
                    f"{points:6,} points ({team_profile.user.username})"
                )
            self.stdout.write(
                '\nTo promote, run:\n'
                '  python manage.py show_promotion_candidates\n'
                '  python manage.py promote_team_member <username> junior_analyst\n'
            )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  DRY RUN - No changes were made. '
                    'Run without --dry-run to save.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Point calculation complete!'
                )
            )
    
    def _get_category_from_points(self, points):
        """Determine category from point total"""
        if points >= 6000:
            return 'ready_for_promotion'
        elif points >= 5000:
            return 'Senior Trainee'
        elif points >= 4000:
            return 'Junior Trainee'
        else:
            return 'Elementary'

