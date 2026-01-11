"""
Diagnostic command to check employee cohort selection.

Helps debug why Group B (or other groups) returns 0 users.

Usage:
    poetry run python coda/manage.py diagnose_employee_cohorts
    poetry run python coda/manage.py diagnose_employee_cohorts --group B
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from management.models import EmployeeCareerState

User = get_user_model()


class Command(BaseCommand):
    help = "Diagnose employee cohort selection (groups and departments)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--group",
            type=str,
            choices=["A", "B", "C"],
            help="Filter by group (A, B, or C)",
        )

    def handle(self, *args, **options):
        group = options.get("group")

        self.stdout.write(
            self.style.SUCCESS(f"\n🔍 Employee Cohort Diagnostic Report 🔍\n")
        )

        # 1) Check EmployeeCareerState counts
        self.stdout.write(f"{'='*80}")
        self.stdout.write(f"1. EmployeeCareerState Counts by Group")
        self.stdout.write(f"{'='*80}\n")

        career_state_counts = (
            EmployeeCareerState.objects.values("group")
            .annotate(count=Count("id"))
            .order_by("group")
        )

        total_career_states = EmployeeCareerState.objects.count()
        self.stdout.write(f"Total EmployeeCareerState records: {total_career_states}\n")

        if career_state_counts:
            for item in career_state_counts:
                self.stdout.write(f"  Group {item['group']}: {item['count']} employees")
        else:
            self.stdout.write(
                self.style.WARNING("  ⚠️  No EmployeeCareerState records found!")
            )
            self.stdout.write("     Employees may not have groups assigned yet.")

        # 2) Check base employee queryset (from get_filtered_employees_queryset)
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(
            f"2. Base Employee Queryset (get_filtered_employees_queryset)"
        )
        self.stdout.write(f"{'='*80}\n")

        from management.services.employee_filter_service import \
            get_filtered_employees_queryset

        class MockRequest:
            def __init__(self):
                self.user = type("User", (), {"is_staff": True, "is_superuser": True})()
                self.GET = {}

        mock_request = MockRequest()
        base_employees = get_filtered_employees_queryset(
            mock_request, test_patterns=None, include_inactive=False
        )

        base_count = base_employees.count()
        self.stdout.write(
            f"Base employees (is_staff=True, is_active=True, has tasks with points>0): {base_count}"
        )

        if base_count == 0:
            self.stdout.write(
                self.style.WARNING(
                    "  ⚠️  No employees found in base queryset. "
                    "This may be because no employees have tasks with points > 0."
                )
            )

        # 3) Check employees with career_state
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"3. Employees with Career State")
        self.stdout.write(f"{'='*80}\n")

        employees_with_career_state = base_employees.filter(
            career_state__isnull=False
        ).select_related("career_state")

        with_career_state_count = employees_with_career_state.count()
        self.stdout.write(
            f"Employees with EmployeeCareerState: {with_career_state_count}"
        )

        if with_career_state_count < base_count:
            missing = base_count - with_career_state_count
            self.stdout.write(
                self.style.WARNING(
                    f"  ⚠️  {missing} employees do NOT have EmployeeCareerState records"
                )
            )

        # 4) Check employees by group (if group specified)
        if group:
            self.stdout.write(f"\n{'='*80}")
            self.stdout.write(f"4. Employees in Group {group}")
            self.stdout.write(f"{'='*80}\n")

            group_employees = base_employees.filter(
                career_state__group=group
            ).select_related("career_state")

            group_count = group_employees.count()
            self.stdout.write(f"Employees in Group {group}: {group_count}")

            if group_count == 0:
                self.stdout.write(
                    self.style.WARNING(f"  ⚠️  No employees found in Group {group}")
                )
                self.stdout.write("\nPossible reasons:")
                self.stdout.write(
                    "  1. No EmployeeCareerState records exist for Group {group}"
                )
                self.stdout.write(
                    "  2. Employees have EmployeeCareerState but with different group"
                )
                self.stdout.write("  3. Employees don't have tasks with points > 0")
                self.stdout.write("\nSolutions:")
                self.stdout.write(
                    f"  - Check: SELECT COUNT(*) FROM management_employeecareerstate WHERE group = '{group}';"
                )
                self.stdout.write("  - Use --department-id instead of --group")
                self.stdout.write(
                    "  - Seed EmployeeCareerState records via admin or employee groups UI"
                )
            else:
                self.stdout.write(f"\nSample employees in Group {group}:")
                for emp in group_employees[:10]:
                    self.stdout.write(
                        f"  - {emp.username} (ID: {emp.id}, "
                        f"career_state.group: {emp.career_state.group if emp.career_state else 'None'})"
                    )

        # 5) Check employees by department
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"5. Employees by Department")
        self.stdout.write(f"{'='*80}\n")

        # Check if User model has department_id field
        if hasattr(User, "department_id"):
            dept_counts = (
                base_employees.exclude(department_id__isnull=True)
                .values("department_id")
                .annotate(count=Count("id"))
                .order_by("-count")[:10]
            )

            if dept_counts:
                self.stdout.write("Top departments by employee count:")
                for item in dept_counts:
                    dept_id = item["department_id"]
                    count = item["count"]
                    self.stdout.write(f"  Department {dept_id}: {count} employees")
            else:
                self.stdout.write("  No employees with department_id found")
        else:
            self.stdout.write("  User model does not have department_id field")

        # 6) SQL queries for verification
        self.stdout.write(f"\n{'='*80}")
        self.stdout.write(f"6. Verification SQL Queries")
        self.stdout.write(f"{'='*80}\n")

        self.stdout.write("-- Count employees by group")
        self.stdout.write("SELECT group, COUNT(*) as count")
        self.stdout.write("FROM management_employeecareerstate")
        self.stdout.write("GROUP BY group")
        self.stdout.write("ORDER BY group;\n")

        self.stdout.write("-- Count employees with tasks (base queryset)")
        self.stdout.write("SELECT COUNT(DISTINCT employee_id) as employees_with_tasks")
        self.stdout.write("FROM management_task")
        self.stdout.write("WHERE point > 0 AND is_active = True;\n")

        self.stdout.write("-- Employees with career_state but no group")
        self.stdout.write("SELECT COUNT(*) as count")
        self.stdout.write("FROM accounts_customeruser u")
        self.stdout.write(
            "JOIN management_employeecareerstate ecs ON u.id = ecs.user_id"
        )
        self.stdout.write("WHERE u.is_staff = True AND u.is_active = True")
        self.stdout.write("  AND (ecs.group IS NULL OR ecs.group = '');\n")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Diagnostic complete!\n"))
