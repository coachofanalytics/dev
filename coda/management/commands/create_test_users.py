"""
Django management command to create test users for each category and subcategory
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.choices import (
    UserCategory, ApplicantSubCategoryChoices, StudentSubCategoryChoices,
    ConsultantSubCategoryChoices, InvestorSubCategoryChoices, ExplorerSubCategoryChoices
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test users for each category and subcategory'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-existing',
            action='store_true',
            help='Delete existing test users before creating new ones',
        )

    def handle(self, *args, **options):
        if options['delete_existing']:
            self.delete_existing_test_users()

        self.create_test_users()
        self.stdout.write(
            self.style.SUCCESS('Successfully created test users for all categories and subcategories')
        )

    def delete_existing_test_users(self):
        """Delete existing test users"""
        test_users = User.objects.filter(username__startswith='test_')
        count = test_users.count()
        test_users.delete()
        self.stdout.write(f'Deleted {count} existing test users')

    def create_test_users(self):
        """Create test users for each category and subcategory"""
        
        # 1. ADMIN/STAFF Users
        self.create_admin_user()
        self.create_staff_user()
        
        # 2. APPLICANT Users
        self.create_applicant_users()
        
        # 3. STUDENT Users
        self.create_student_users()
        
        # 4. CONSULTANT Users
        self.create_consultant_users()
        
        # 5. INVESTOR Users
        self.create_investor_users()
        
        # 6. EXPLORER Users
        self.create_explorer_users()

    def create_admin_user(self):
        """Create admin test user"""
        user, created = User.objects.get_or_create(
            username='test_admin',
            defaults={
                'email': 'admin@test.com',
                'first_name': 'Test',
                'last_name': 'Admin',
                'category': UserCategory.STUDENT,  # Staff category
                'is_admin': True,
                'is_staff': True,
                'is_superuser': True,
                'email_verified': True,
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write('Created test admin user')

    def create_staff_user(self):
        """Create staff test user"""
        user, created = User.objects.get_or_create(
            username='test_staff',
            defaults={
                'email': 'staff@test.com',
                'first_name': 'Test',
                'last_name': 'Staff',
                'category': UserCategory.STUDENT,  # Staff category
                'is_staff': True,
                'email_verified': True,
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write('Created test staff user')

    def create_applicant_users(self):
        """Create applicant test users"""
        applicants = [
            ('test_applicant_fulltime', 'Full Time Applicant', ApplicantSubCategoryChoices.FULL_TIME),
            ('test_applicant_contract', 'Contract Applicant', ApplicantSubCategoryChoices.CONTRACT),
            ('test_applicant_internship', 'Internship Applicant', ApplicantSubCategoryChoices.INTERNSHIP),
        ]
        
        for username, name, subcategory in applicants:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@test.com',
                    'first_name': name.split()[0],
                    'last_name': name.split()[1],
                    'category': UserCategory.APPLICANT,
                    'sub_category': subcategory,
                    'email_verified': True,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(f'Created {username}')

    def create_student_users(self):
        """Create student test users"""
        students = [
            ('test_student_data', 'Data Analytics Student', StudentSubCategoryChoices.DATA_ANALYTICS),
            ('test_student_programming', 'Programming Student', StudentSubCategoryChoices.PROGRAMMING),
            ('test_student_other', 'Other Student', StudentSubCategoryChoices.OTHER),
        ]
        
        for username, name, subcategory in students:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@test.com',
                    'first_name': name.split()[0],
                    'last_name': name.split()[1],
                    'category': UserCategory.STUDENT,
                    'sub_category': subcategory,
                    'email_verified': True,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(f'Created {username}')

    def create_consultant_users(self):
        """Create consultant test users"""
        consultants = [
            ('test_consultant_technical', 'Technical Consultant', ConsultantSubCategoryChoices.TECHNICAL),
            ('test_consultant_business', 'Business Consultant', ConsultantSubCategoryChoices.BUSINESS),
            ('test_consultant_career', 'Career Consultant', ConsultantSubCategoryChoices.CAREER),
            ('test_consultant_project', 'Project Consultant', ConsultantSubCategoryChoices.PROJECT),
        ]
        
        for username, name, subcategory in consultants:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@test.com',
                    'first_name': name.split()[0],
                    'last_name': name.split()[1],
                    'category': UserCategory.CONSULTANT,
                    'sub_category': subcategory,
                    'email_verified': True,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(f'Created {username}')

    def create_investor_users(self):
        """Create investor test users"""
        investors = [
            ('test_investor_angel', 'Angel Investor', InvestorSubCategoryChoices.ANGEL),
            ('test_investor_vc', 'VC Investor', InvestorSubCategoryChoices.VC),
            ('test_investor_private', 'Private Investor', InvestorSubCategoryChoices.PRIVATE),
            ('test_investor_individual', 'Individual Investor', InvestorSubCategoryChoices.INDIVIDUAL),
        ]
        
        for username, name, subcategory in investors:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@test.com',
                    'first_name': name.split()[0],
                    'last_name': name.split()[1],
                    'category': UserCategory.INVESTOR,
                    'sub_category': subcategory,
                    'email_verified': True,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(f'Created {username}')

    def create_explorer_users(self):
        """Create explorer test users"""
        explorers = [
            ('test_explorer_research', 'Research Explorer', ExplorerSubCategoryChoices.RESEARCH),
            ('test_explorer_networking', 'Networking Explorer', ExplorerSubCategoryChoices.NETWORKING),
            ('test_explorer_learning', 'Learning Explorer', ExplorerSubCategoryChoices.LEARNING),
            ('test_explorer_partnership', 'Partnership Explorer', ExplorerSubCategoryChoices.PARTNERSHIP),
        ]
        
        for username, name, subcategory in explorers:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@test.com',
                    'first_name': name.split()[0],
                    'last_name': name.split()[1],
                    'category': UserCategory.EXPLORER,
                    'sub_category': subcategory,
                    'email_verified': True,
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                self.stdout.write(f'Created {username}')
