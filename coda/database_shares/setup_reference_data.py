#!/usr/bin/env python3
"""
Comprehensive script to create ALL needed reference data for loading the limited export.

This script analyzes the export file and creates all required reference data
(BudgetCategory, Department, Company, Task, etc.) that the export depends on.

Usage:
    cd coda
    poetry run python ../database_shares/setup_reference_data.py
"""

import json
import os
import sys
import uuid

# Change to coda directory
coda_dir = os.path.join(os.path.dirname(__file__), "..", "coda")
os.chdir(coda_dir)
sys.path.insert(0, coda_dir)

import django

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "coda_project.coda_settings.local_settings"
)
django.setup()

from accounts.models import CustomerUser, Department, TaskGroups
from finance.models import BudgetCategory, BudgetSubCategory, LoanProduct
from main.models import Assets, Company
from management.models import Task, TaskCategory


def find_all_reference_data(export_file):
    """Analyze export file and find all needed reference data"""
    with open(export_file) as f:
        data = json.load(f)

    category_ids = set()
    subcategory_ids = set()
    department_ids = set()
    company_ids = set()
    loan_product_ids = set()
    task_ids = set()
    user_ids = set()
    tasks_in_export = False  # Check if real tasks are in export

    for item in data:
        fields = item.get("fields", {})
        model = item.get("model", "")

        # Check if tasks are in export (real production tasks)
        if model == "management.task":
            tasks_in_export = True
            pk = item.get("pk")
            if pk:
                task_ids.add(pk)  # These are real tasks from export

        # Collect user IDs (for Task creation)
        if model == "accounts.customeruser":
            pk = item.get("pk")
            if pk:
                user_ids.add(pk)

        # Analyze all fields for FK references
        for field_name, value in fields.items():
            if not value:
                continue

            # Categories
            if field_name in ["category_id", "budget_category_id"]:
                category_ids.add(value)
            elif field_name == "category":
                if isinstance(value, int):
                    category_ids.add(value)
                elif isinstance(value, list) and len(value) > 1:
                    category_ids.add(value[1])

            # Subcategories
            if field_name == "subcategory_id":
                subcategory_ids.add(value)
            elif field_name == "subcategory":
                if isinstance(value, int):
                    subcategory_ids.add(value)
                elif isinstance(value, list) and len(value) > 1:
                    subcategory_ids.add(value[1])

            # Departments
            if field_name == "department_id":
                department_ids.add(value)
            elif field_name == "department":
                if isinstance(value, int):
                    department_ids.add(value)
                elif isinstance(value, list) and len(value) > 1:
                    department_ids.add(value[1])

            # Companies
            if field_name == "company_id":
                company_ids.add(value)
            elif field_name == "company":
                if isinstance(value, int):
                    company_ids.add(value)
                elif isinstance(value, list) and len(value) > 1:
                    company_ids.add(value[1])

            # Loan Products
            if field_name == "loan_product_id":
                loan_product_ids.add(value)
            elif field_name == "loan_product":
                if isinstance(value, int):
                    loan_product_ids.add(value)
                elif isinstance(value, list) and len(value) > 1:
                    loan_product_ids.add(value[1])

            # Tasks (from tasklinks)
            if model == "management.tasklinks":
                if field_name == "task_id":
                    task_ids.add(value)
                elif field_name == "task":
                    if isinstance(value, int):
                        task_ids.add(value)
                    elif isinstance(value, list) and len(value) > 1:
                        task_ids.add(value[1])

    # If tasks are in export, we don't need to create them
    # Only create tasks if they're NOT in export but are referenced by TaskLinks
    if not tasks_in_export:
        # Extract task IDs from TaskLinks
        for item in data:
            if item.get("model") == "management.tasklinks":
                fields = item.get("fields", {})
                if "task_id" in fields and fields["task_id"]:
                    task_ids.add(fields["task_id"])
                elif "task" in fields:
                    task_val = fields["task"]
                    if isinstance(task_val, int):
                        task_ids.add(task_val)
                    elif isinstance(task_val, list) and len(task_val) > 1:
                        task_ids.add(task_val[1])

    return {
        "categories": sorted(list(category_ids)),
        "subcategories": sorted(list(subcategory_ids)),
        "departments": sorted(list(department_ids)),
        "companies": sorted(list(company_ids)),
        "loan_products": sorted(list(loan_product_ids)),
        "tasks": sorted(list(task_ids)),
        "users": sorted(list(user_ids)),
        "tasks_in_export": tasks_in_export,  # Flag to know if we should create tasks
    }


def create_categories(category_ids):
    """Create all needed BudgetCategory records"""
    created_count = 0
    for cat_id in category_ids:
        cat, created = BudgetCategory.objects.get_or_create(
            pk=cat_id,
            defaults={
                "name": f"Category {cat_id}",
                "description": f"Default category {cat_id} for limited export",
            },
        )
        if created:
            created_count += 1
            print(f"  ✅ Created: BudgetCategory pk={cat_id}")
    return created_count


def create_subcategories(subcategory_ids):
    """Create all needed BudgetSubCategory records"""
    # Get or create default category
    cat1, _ = BudgetCategory.objects.get_or_create(
        pk=1, defaults={"name": "Default", "description": "Default category"}
    )

    created_count = 0
    for subcat_id in subcategory_ids:
        subcat, created = BudgetSubCategory.objects.get_or_create(
            pk=subcat_id,
            defaults={
                "name": f"Subcategory {subcat_id}",
                "category": cat1,
            },
        )
        if created:
            created_count += 1
            print(f"  ✅ Created: BudgetSubCategory pk={subcat_id}")
    return created_count


def create_departments(department_ids):
    """Create all needed Department records"""
    created_count = 0
    for dept_id in department_ids:
        dept, created = Department.objects.get_or_create(
            pk=dept_id,
            defaults={
                "name": f"Department {dept_id}",
                "slug": f"dept-{dept_id}-{uuid.uuid4().hex[:8]}",
                "description": f"Default department {dept_id} for limited export",
            },
        )
        if created:
            created_count += 1
            print(f"  ✅ Created: Department pk={dept_id}")
    return created_count


def create_companies(company_ids):
    """Create all needed Company records"""
    created_count = 0
    for comp_id in company_ids:
        comp, created = Company.objects.get_or_create(
            pk=comp_id,
            defaults={
                "name": f"Company {comp_id}",
                "description": f"Default company {comp_id} for limited export",
            },
        )
        if created:
            created_count += 1
            print(f"  ✅ Created: Company pk={comp_id}")
    return created_count


def create_loan_products(loan_product_ids):
    """Create all needed LoanProduct records"""
    created_count = 0
    for lp_id in loan_product_ids:
        lp, created = LoanProduct.objects.get_or_create(
            pk=lp_id,
            defaults={
                "name": f"Loan Product {lp_id}",
                "description": f"Default loan product {lp_id} for limited export",
                "min_amount": 1000.0,
                "max_amount": 100000.0,
                "interest_rate": 10.0,
                "term_months": 12,
                "fees": 0.0,
                "is_active": True,
            },
        )
        if created:
            created_count += 1
            print(f"  ✅ Created: LoanProduct pk={lp_id}")
    return created_count


def create_task_groups_and_categories():
    """Create default TaskGroups and TaskCategory (always needed)"""
    task_group, created = TaskGroups.objects.get_or_create(
        pk=1,
        defaults={
            "title": "Default Group",
            "description": "Default task group for limited export",
        },
    )
    if created:
        print(f"  ✅ Created: TaskGroups pk=1")

    task_category, created = TaskCategory.objects.get_or_create(
        pk=1,
        defaults={
            "title": "Default Category",
            "description": "Default task category for limited export",
        },
    )
    if created:
        print(f"  ✅ Created: TaskCategory pk=1")

    return task_group, task_category


def create_tasks(task_ids, user_ids):
    """Create all needed Task records"""
    # Get or create default TaskGroups and TaskCategory
    task_group, task_category = create_task_groups_and_categories()

    # Get a default user for task creation (Task.employee requires is_staff=True)
    # We need a user to create tasks, but users come from the fixture
    # Solution: Create a temporary user with a high PK that won't conflict
    default_user = None

    # First, try to find any existing user (in case fixture was partially loaded)
    try:
        default_user = CustomerUser.objects.get(username="coda_info")
        if not default_user.is_staff:
            default_user.is_staff = True
            default_user.save()
    except CustomerUser.DoesNotExist:
        # Try any existing staff user
        default_user = CustomerUser.objects.filter(is_staff=True).first()

    # If still no user, create a temporary system user with high PK to avoid conflicts
    # This user will be replaced when the fixture loads real users
    if not default_user:
        # Use a very high PK (99999) that won't conflict with fixture users
        temp_user_pk = 99999
        try:
            default_user = CustomerUser.objects.get(pk=temp_user_pk)
        except CustomerUser.DoesNotExist:
            default_user = CustomerUser.objects.create(
                pk=temp_user_pk,
                username=f"temp_system_{temp_user_pk}",
                email=f"temp_system_{temp_user_pk}@coda.co.ke",
                first_name="Temporary",
                last_name="System",
                is_staff=True,
                is_active=True,
            )
            print(f"  ⚠️  Created temporary user (pk={temp_user_pk}) for task creation")
            print(f"  💡 Real users will be loaded from fixture")

    created_count = 0
    for task_id in task_ids:
        task, created = Task.objects.get_or_create(
            pk=task_id,
            defaults={
                "group": "Group A",
                "groupname": task_group,
                "category": task_category,
                "employee": default_user,
                "activity_name": f"Task {task_id}",
                "description": f"Default task {task_id} for limited export",
                "point": 1.0,  # Required field
                "mxpoint": 10.0,
                "mxearning": 100.0,
                "duration": 1,
                "is_active": True,
                "featured": False,
                "is_client_project": False,
            },
        )
        if created:
            created_count += 1
            print(f"  ✅ Created: Task pk={task_id}")
    return created_count


def create_default_assets():
    """Create default Assets record"""
    asset, created = Assets.objects.get_or_create(
        pk=1,
        defaults={
            "name": "default",
            "category": "default",
            "description": "default",
            "image_url": "default",
        },
    )
    if created:
        print(f"  ✅ Created: Assets pk=1")
    return 1 if created else 0


def main():
    """Main function to create all reference data"""
    export_file = os.path.join(os.path.dirname(__file__), "limited_export_fixed.json")

    if not os.path.exists(export_file):
        print(f"❌ Error: Export file not found: {export_file}")
        print("   Please ensure limited_export_fixed.json exists in database_shares/")
        sys.exit(1)

    print("🔍 Analyzing export file for required reference data...")
    ref_data = find_all_reference_data(export_file)

    print(f"\n📊 Found required reference data:")
    print(f"  - BudgetCategory: {len(ref_data['categories'])} IDs")
    print(f"  - BudgetSubCategory: {len(ref_data['subcategories'])} IDs")
    print(f"  - Department: {len(ref_data['departments'])} IDs")
    print(f"  - Company: {len(ref_data['companies'])} IDs")
    print(f"  - LoanProduct: {len(ref_data['loan_products'])} IDs")
    print(f"  - Task: {len(ref_data['tasks'])} IDs")

    print("\n🔧 Creating reference data...\n")

    total_created = 0

    # Always create TaskGroups and TaskCategory (needed for tasks)
    print("Creating TaskGroups and TaskCategory...")
    create_task_groups_and_categories()
    total_created += 2  # Count as created even if they already exist

    if ref_data["categories"]:
        print("Creating BudgetCategory records...")
        total_created += create_categories(ref_data["categories"])

    if ref_data["subcategories"]:
        print("Creating BudgetSubCategory records...")
        total_created += create_subcategories(ref_data["subcategories"])

    if ref_data["departments"]:
        print("Creating Department records...")
        total_created += create_departments(ref_data["departments"])

    if ref_data["companies"]:
        print("Creating Company records...")
        total_created += create_companies(ref_data["companies"])

    if ref_data["loan_products"]:
        print("Creating LoanProduct records...")
        total_created += create_loan_products(ref_data["loan_products"])

    if ref_data["tasks"]:
        if ref_data.get("tasks_in_export", False):
            print("⚠️  Tasks are in export - skipping task creation")
            print("   Real production tasks will be loaded from fixture")
        else:
            print("Creating Task records...")
            print("   (Tasks not in export - creating placeholder tasks)")
            total_created += create_tasks(ref_data["tasks"], ref_data["users"])

    print("Creating default Assets...")
    total_created += create_default_assets()

    print(f"\n✅ Successfully created {total_created} reference data records!")
    print("\n📝 Next steps:")
    print("  1. Run migrations (if needed): poetry run python manage.py migrate")
    print(
        "  2. Load the fixture: poetry run python manage.py loaddata ../database_shares/limited_export_fixed.json"
    )
    print(
        "\n💡 Note: If you encounter duplicate key errors, some data may already exist."
    )
    print("   You can either:")
    print("   - Clear the database and start fresh")
    print("   - Use --verbosity=0 to suppress duplicate warnings")


if __name__ == "__main__":
    main()
