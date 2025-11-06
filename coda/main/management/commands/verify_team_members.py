"""
Management command to verify all required team members exist.

Usage:
    python manage.py verify_team_members
    python manage.py verify_team_members --create-missing
"""

from django.core.management.base import BaseCommand
from accounts.models import UserProfile, CustomerUser


class Command(BaseCommand):
    help = 'Verify all required team members exist in the system'
    
    # All required team members (using Group names)
    REQUIRED_MEMBERS = {
        'BOG/Leadership': [
            ('amanda_towe', 'Amanda', 'Towe', 'amanda.towe@example.com'),
            ('cmaghas', 'Chris', 'Maghas', 'cmaghas@example.com'),
            ('tirimba_obonyo', 'Tirimba', 'Obonyo', 'tirimba.obonyo@example.com'),
        ],
        'Elite Team': [
            ('coda-info', 'Chris', 'Maghas', 'coda-info@example.com'),
        ],
        'Lead Team': [
            ('edwin_kimtai', 'Edwin', 'Kimtai', 'edwin.kimtai@example.com'),
            ('emanuel_masakhwe', 'Emanuel', 'Masakhwe', 'emanuel.masakhwe@example.com'),
            ('george_ndahiro', 'George', 'Ndahiro', 'george.ndahiro@example.com'),
        ],
        'Support Team': [
            ('hashim_kha', 'Hashim', 'Kha', 'hashim.kha@example.com'),
            ('christine_karagu', 'Christine', 'Karagu', 'christine.karagu@example.com'),
        ],
        'Senior Analysts': [
            ('sylvia_jelante', 'Sylvia', 'Jelante', 'sylvia.jelante@example.com'),
        ],
        'Junior Analysts': [
            ('phinehas_maina', 'Phinehas', 'Maina', 'phinehas.maina@example.com'),
        ],
        'Future Talents': [
            ('bonie_luke', 'Bonie', 'Luke', 'bonie.luke@example.com'),
            ('brenda_nasimiyu', 'Brenda', 'Nasimiyu', 'brenda.nasimiyu@example.com'),
            ('angel', 'Angel', '', 'angel@example.com'),
            ('eugene', 'Eugene', '', 'eugene@example.com'),
        ],
    }
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-missing',
            action='store_true',
            help='Create missing user accounts',
        )
    
    def handle(self, *args, **options):
        create_missing = options['create_missing']
        
        self.stdout.write(self.style.SUCCESS('\n🔍 Verifying Team Members\n'))
        self.stdout.write('=' * 80 + '\n')
        
        total_required = 0
        total_found = 0
        total_missing = 0
        total_no_profile = 0
        missing_users = []
        users_without_profile = []
        
        for category, members in self.REQUIRED_MEMBERS.items():
            self.stdout.write(f"\n📂 {category.upper().replace('_', ' ')}:")
            self.stdout.write('-' * 80)
            
            for username, first_name, last_name, email in members:
                total_required += 1
                full_name = f"{first_name} {last_name}".strip()
                
                try:
                    # Check if user exists
                    user = CustomerUser.objects.get(username=username)
                    
                    # Check if profile exists
                    try:
                        profile = user.profile
                        total_found += 1
                        
                        # Show status
                        status = []
                        if user.is_active:
                            status.append('✅ Active')
                        else:
                            status.append('⚠️ Inactive')
                        
                        # Check team assignment
                        try:
                            team_profile = user.team_profile
                            category = team_profile.category or 'Not assigned'
                            if team_profile.is_manually_assigned:
                                status.append(f'📌 Manual: {category}')
                            else:
                                status.append(f'📊 Points: {team_profile.total_points:,}')
                        except:
                            status.append('⚠️ No TeamProfile')
                        
                        self.stdout.write(
                            f"  ✅ {full_name:25} ({username:20}) - {' | '.join(status)}"
                        )
                        
                    except UserProfile.DoesNotExist:
                        total_no_profile += 1
                        users_without_profile.append((username, full_name, category))
                        self.stdout.write(
                            self.style.WARNING(
                                f"  ⚠️  {full_name:25} ({username:20}) - User exists but NO PROFILE"
                            )
                        )
                
                except CustomerUser.DoesNotExist:
                    total_missing += 1
                    missing_users.append((username, first_name, last_name, email, category))
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ❌ {full_name:25} ({username:20}) - USER NOT FOUND"
                        )
                    )
        
        # Summary
        self.stdout.write('\n' + '=' * 80)
        self.stdout.write('\n📊 SUMMARY:')
        self.stdout.write(f"  Total Required: {total_required}")
        self.stdout.write(
            self.style.SUCCESS(f"  ✅ Found with Profile: {total_found}")
        )
        self.stdout.write(
            self.style.WARNING(f"  ⚠️  User exists, no profile: {total_no_profile}")
        )
        self.stdout.write(
            self.style.ERROR(f"  ❌ Missing Users: {total_missing}")
        )
        
        # Show missing users
        if missing_users:
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write('\n❌ MISSING USERS:')
            for username, first_name, last_name, email, category in missing_users:
                self.stdout.write(
                    f"  • {first_name} {last_name} ({username}) - {category}"
                )
            
            if create_missing:
                self.stdout.write('\n📝 Creating missing users...\n')
                for username, first_name, last_name, email, category in missing_users:
                    user = CustomerUser.objects.create_user(
                        username=username,
                        email=email,
                        first_name=first_name,
                        last_name=last_name,
                        category=2,  # Employee
                        is_active=True,
                    )
                    # Profile is auto-created via signal
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✅ Created: {first_name} {last_name} ({username})"
                        )
                    )
            else:
                self.stdout.write(
                    '\nTo create missing users, run:\n'
                    '  python manage.py verify_team_members --create-missing\n'
                )
        
        # Show users without profile
        if users_without_profile:
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write('\n⚠️  USERS WITHOUT PROFILE:')
            for username, full_name, category in users_without_profile:
                self.stdout.write(
                    f"  • {full_name} ({username}) - {category}"
                )
            self.stdout.write(
                '\nProfiles should auto-create via signal. '
                'If not, create manually in Django admin.\n'
            )
        
        # Next steps
        if total_found == total_required:
            self.stdout.write(
                self.style.SUCCESS(
                    '\n✅ All team members verified! Ready to assign categories.\n'
                )
            )
            self.stdout.write(
                'Next step:\n'
                '  python manage.py assign_manual_team_members\n'
            )
        else:
            self.stdout.write(
                '\n⚠️  Some team members are missing. '
                'Create them before proceeding.\n'
            )

