"""
Management command to assign team members to manual categories using Django Groups.

Usage:
    python manage.py assign_manual_team_members
    python manage.py assign_manual_team_members --dry-run
    python manage.py assign_manual_team_members --category bog_leadership
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from accounts.models import TeamProfile, CustomerUser
from django.utils import timezone


class Command(BaseCommand):
    help = 'Assign team members to manual categories (BOG, Elite, Lead, Support, Analysts)'
    
    # Team assignments using Django Groups
    # Format: category_slug -> [(username, full_name, priority), ...]
    MANUAL_ASSIGNMENTS = {
        'BOG/Leadership': [
            # (username, full_name, priority)
            ('amanda_towe', 'Amanda Towe', 100),
            ('cmaghas', 'Chris Maghas', 90),
            ('tirimba_obonyo', 'Tirimba Obonyo', 80),
        ],
        'Elite Team': [
            ('coda-info', 'Chris Maghas', 100),
        ],
        'Lead Team': [
            ('edwin_kimtai', 'Edwin Kimtai', 100),
            ('emanuel_masakhwe', 'Emanuel Masakhwe', 90),
            ('george_ndahiro', 'George Ndahiro', 80),
        ],
        'Support Team': [
            ('hashim_kha', 'Hashim Kha', 100),
            ('christine_karagu', 'Christine Karagu', 90),
        ],
        'Senior Analysts': [
            ('sylvia_jelante', 'Sylvia Jelante', 100),
        ],
        'Junior Analysts': [
            ('phinehas_maina', 'Phinehas Maina', 100),
        ],
    }
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Only assign specific category (bog_leadership, elite, lead, etc.)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reassignment even if already assigned',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        category_filter = options['category']
        force = options['force']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))
        
        self.stdout.write(self.style.SUCCESS('🎯 Assigning Manual Team Categories\n'))
        self.stdout.write('=' * 70 + '\n')
        
        # Filter categories if specified
        categories_to_process = self.MANUAL_ASSIGNMENTS
        if category_filter:
            if category_filter in self.MANUAL_ASSIGNMENTS:
                categories_to_process = {category_filter: self.MANUAL_ASSIGNMENTS[category_filter]}
                self.stdout.write(f"Processing only: {category_filter}\n")
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Invalid category: {category_filter}")
                )
                return
        
        total_assigned = 0
        total_errors = 0
        
        for category_name, members in categories_to_process.items():
            self.stdout.write(f"\n📂 {category_name}:")
            self.stdout.write('-' * 70)
            
            # Get or create group
            group, _ = Group.objects.get_or_create(name=category_name)
            
            for username, full_name, priority in members:
                try:
                    # Find user
                    user = CustomerUser.objects.get(username=username)
                    
                    # Get or create TeamProfile
                    team_profile, created = TeamProfile.objects.get_or_create(user=user)
                    
                    # Check if already assigned
                    if user.groups.filter(name=category_name).exists() and not force:
                        self.stdout.write(
                            f"  ⏭️  {full_name:25} ({username:20}) - Already in {category_name}"
                        )
                        continue
                    
                    # Check if in different team group
                    current_team_groups = user.groups.filter(
                        name__in=self.MANUAL_ASSIGNMENTS.keys()
                    )
                    
                    if current_team_groups.exists() and not force:
                        current = current_team_groups.first().name
                        if current != category_name:
                            self.stdout.write(
                                self.style.WARNING(
                                    f"  ⚠️  {full_name:25} ({username:20}) - "
                                    f"Currently in '{current}' (use --force to reassign)"
                                )
                            )
                            continue
                    
                    # Make assignment
                    if not dry_run:
                        # Remove from all other team groups
                        user.groups.filter(
                            name__in=self.MANUAL_ASSIGNMENTS.keys()
                        ).delete()
                        
                        # Add to new group
                        user.groups.add(group)
                        
                        # Update TeamProfile
                        team_profile.is_manually_assigned = True
                        team_profile.priority = priority
                        team_profile.last_promoted = timezone.now()
                        team_profile.promotion_notes = f'Initial manual assignment to {category_name}'
                        team_profile.save()
                    
                    total_assigned += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✅ {full_name:25} ({username:20}) → {category_name:25} "
                            f"(priority: {priority})"
                        )
                    )
                    
                except CustomerUser.DoesNotExist:
                    total_errors += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ❌ {full_name:25} ({username:20}) - USER NOT FOUND"
                        )
                    )
                    self.stdout.write(
                        f"     ℹ️  Create user: python manage.py shell -c "
                        f"\"from accounts.models import CustomerUser; "
                        f"CustomerUser.objects.create_user(username='{username}', email='{username}@example.com')\""
                    )
                
                except Exception as e:
                    total_errors += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ❌ {full_name:25} ({username:20}) - ERROR: {str(e)}"
                        )
                    )
        
        # Summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write('\n📊 SUMMARY:')
        self.stdout.write(f"  ✅ Successfully assigned: {total_assigned}")
        self.stdout.write(f"  ❌ Errors: {total_errors}")
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    '\n⚠️  DRY RUN - No changes were made. '
                    'Run without --dry-run to apply changes.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Manual team assignment complete!'
                )
            )
            self.stdout.write(
                '\nNext steps:'
            )
            self.stdout.write(
                '  1. python manage.py recalculate_team_points (for future talents)'
            )
            self.stdout.write(
                '  2. Visit /members/team_profiles to verify assignments'
            )

