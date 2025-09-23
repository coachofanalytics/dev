#!/usr/bin/env python3
"""
STAFF TO EMPLOYEE MIGRATION SCRIPT
==================================

This script transitions all current staff members from their current categories
(Student, Applicant, Consultant) to the new Employee category.

Usage:
    python manage.py shell < STAFF_TO_EMPLOYEE_MIGRATION.py

Or run interactively:
    python manage.py shell
    >>> exec(open('docs/deployment/STAFF_TO_EMPLOYEE_MIGRATION.py').read())
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from accounts.models import CustomerUser
from accounts.choices import UserCategory, EmployeeSubCategoryChoices
from django.utils import timezone

def migrate_staff_to_employees():
    """
    Migrate all staff members to Employee category
    """
    print("="*60)
    print("STAFF TO EMPLOYEE MIGRATION")
    print("="*60)
    
    # Get all staff members
    staff_members = CustomerUser.objects.filter(is_staff=True, is_active=True)
    total_staff = staff_members.count()
    
    print(f"Found {total_staff} staff members to migrate")
    print()
    
    # Migration mapping
    migration_map = {
        # Students -> Full-time Employees (most common)
        (UserCategory.STUDENT, None): (UserCategory.EMPLOYEE, EmployeeSubCategoryChoices.FULL_TIME),
        (UserCategory.STUDENT, 1): (UserCategory.EMPLOYEE, EmployeeSubCategoryChoices.FULL_TIME),  # Data Analytics
        (UserCategory.STUDENT, 2): (UserCategory.EMPLOYEE, EmployeeSubCategoryChoices.FULL_TIME),  # Programming
        (UserCategory.STUDENT, 3): (UserCategory.EMPLOYEE, EmployeeSubCategoryChoices.FULL_TIME),  # Other
        
        # Applicants -> Full-time Employees
        (UserCategory.APPLICANT, ApplicantSubCategoryChoices.FULL_TIME): (UserCategory.EMPLOYEE, EmployeeSubCategoryChoices.FULL_TIME),
        (UserCategory.APPLICANT, ApplicantSubCategoryChoices.CONTRACT): (UserCategory.EMPLOYEE, EmployeeSubCategoryChoices.CONTRACT),
        (UserCategory.APPLICANT, ApplicantSubCategoryChoices.INTERNSHIP): (UserCategory.EMPLOYEE, EmployeeSubCategoryChoices.INTERN),
        
        # Consultants -> Managers (assuming they're senior)
        (UserCategory.CONSULTANT, None): (UserCategory.EMPLOYEE, EmployeeSubCategoryChoices.MANAGER),
        (UserCategory.CONSULTANT, 1): (UserCategory.EMPLOYEE, EmployeeSubCategoryChoices.MANAGER),  # Technical
        (UserCategory.CONSULTANT, 2): (UserCategory.EMPLOYEE, EmployeeSubCategoryChoices.MANAGER),  # Business
        (UserCategory.CONSULTANT, 3): (UserCategory.EMPLOYEE, EmployeeSubCategoryChoices.MANAGER),  # Career
        (UserCategory.CONSULTANT, 4): (UserCategory.EMPLOYEE, EmployeeSubCategoryChoices.MANAGER),  # Project
    }
    
    migrated_count = 0
    skipped_count = 0
    
    print("MIGRATION DETAILS:")
    print("-" * 40)
    
    for user in staff_members:
        current_category = user.category
        current_subcategory = user.sub_category
        current_status = user.employment_status
        
        # Determine new category and subcategory
        migration_key = (current_category, current_subcategory)
        if migration_key in migration_map:
            new_category, new_subcategory = migration_map[migration_key]
            
            # Perform migration
            user.category = new_category
            user.sub_category = new_subcategory
            user.save()
            
            new_status = user.employment_status
            
            print(f"✅ {user.username}")
            print(f"   {user.first_name} {user.last_name}")
            print(f"   {current_status} → {new_status}")
            print(f"   Category: {current_category} → {new_category}")
            print(f"   Subcategory: {current_subcategory} → {new_subcategory}")
            print()
            
            migrated_count += 1
        else:
            print(f"⚠️  {user.username} - SKIPPED")
            print(f"   {user.first_name} {user.last_name}")
            print(f"   Unknown category combination: {current_category}, {current_subcategory}")
            print(f"   Current status: {current_status}")
            print()
            
            skipped_count += 1
    
    print("="*60)
    print("MIGRATION SUMMARY")
    print("="*60)
    print(f"Total staff members: {total_staff}")
    print(f"Successfully migrated: {migrated_count}")
    print(f"Skipped (manual review needed): {skipped_count}")
    print()
    
    if skipped_count > 0:
        print("⚠️  MANUAL REVIEW REQUIRED:")
        print("Some staff members were skipped due to unknown category combinations.")
        print("Please review these users manually in the admin panel.")
        print()
    
    print("✅ Migration completed!")
    return migrated_count, skipped_count

def verify_migration():
    """
    Verify the migration results
    """
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    # Check employee count
    employees = CustomerUser.objects.filter(category=UserCategory.EMPLOYEE, is_active=True)
    print(f"Total employees: {employees.count()}")
    
    # Check staff count
    staff = CustomerUser.objects.filter(is_staff=True, is_active=True)
    print(f"Total staff: {staff.count()}")
    
    # Category breakdown
    print("\nCategory breakdown:")
    for category_id, category_name in UserCategory.choices:
        count = CustomerUser.objects.filter(category=category_id, is_staff=True, is_active=True).count()
        print(f"  {category_name}: {count}")
    
    # Employee subcategory breakdown
    print("\nEmployee subcategory breakdown:")
    for subcategory_id, subcategory_name in EmployeeSubCategoryChoices.choices:
        count = CustomerUser.objects.filter(
            category=UserCategory.EMPLOYEE, 
            sub_category=subcategory_id, 
            is_active=True
        ).count()
        print(f"  {subcategory_name}: {count}")

if __name__ == "__main__":
    try:
        migrated, skipped = migrate_staff_to_employees()
        verify_migration()
        
        print("\n🎉 STAFF TO EMPLOYEE MIGRATION COMPLETED!")
        print(f"✅ {migrated} staff members migrated to Employee category")
        if skipped > 0:
            print(f"⚠️  {skipped} staff members need manual review")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("Migration failed. Please check the error and try again.")
        sys.exit(1)
