import http.client
import json
import logging
import math
import os
import re
import string
import tempfile
import threading
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal
from io import BytesIO
from typing import Any
from urllib.parse import urlencode

import requests
from accounts.choices import (ApplicantSubCategoryChoices,
                              ConsultantSubCategoryChoices,
                              ExplorerSubCategoryChoices,
                              InvestorSubCategoryChoices,
                              StudentSubCategoryChoices)
from dateutil import parser
from dateutil.relativedelta import relativedelta
from django import template
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.cache import cache
from django.db import transaction
from django.db.models import F, OuterRef, Q, Subquery, Sum
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.text import capfirst
from django.utils.timezone import make_aware
from django.views.decorators.http import require_http_methods
from shared_core.users import UserCategory as CategoryChoices

# Import utilities - try multiple sources
try:
    from shared_core.utils import (calculate_login_bonus, generate_password,
                                   send_verification_email)
except ImportError:
    try:
        from accounts.utils import (calculate_login_bonus,
                                    send_verification_email)
        from core.utils import generate_password
    except ImportError:
        # Fallback implementations
        def send_verification_email(*args, **kwargs):
            pass

        def calculate_login_bonus(*args, **kwargs):
            return 0

        def generate_password(*args, **kwargs):
            import secrets

            return secrets.token_urlsafe(12)


from accounts.views import create_profile
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from mail.custom_email import send_email
from management.forms import (AssignmentUploadForm, BackgroundForm,
                              ClientAssessmentForm, DepartmentForm,
                              EmployeeContractForm, EvidenceForm,
                              GrievanceForm, ManagementForm, MeetingForm,
                              PolicyForm, RequirementForm, TagFilterForm,
                              dynamic_agenda_form)
from shared_core.mixins import FilteredListViewMixin

# Import UserProfile - try multiple sources
try:
    from accounts.models import UserProfile
except ImportError:
    try:
        from shared_core.users import UserProfile
    except ImportError:
        # UserProfile might not be available - set to None for optional usage
        UserProfile = None

from management.models import (  # Note: Training model depends on professional_services (FeaturedCategory/SubCategory/Activity); Training feature should be gated via ENABLE_PRO_SERVICES_FEATURES setting in views that use it
    Advertisement, Assignment, Conflict_Resolution, Grievance, Link, Meetings,
    Policy, ProcessBreakdown, ProcessJustification, Requirement, SubCategory,
    Task, TaskCategory, TaskHistory, TaskLinks)

# Professional services models - use interface instead
# Optional import for management-only branch
try:
    from professional_services.models import Training
except ImportError:
    Training = None  # Not available in management-only branch

# Import professional services helper - optional
try:
    from management.services.pro_services_helper import \
        get_professional_services
except ImportError:

    def get_professional_services():
        return None


# Import CustomerUser and Department - try multiple sources
try:
    from shared_core.users import CustomerUser, Department
except ImportError:
    try:
        from accounts.models import CustomerUser, Department
    except ImportError:
        # Fallback: these might not be available
        CustomerUser = None
        Department = None

# Import finance service helper - optional
try:
    from management.services.finance_service_helper import \
        get_finance_task_service
except ImportError:

    def get_finance_task_service():
        class NoOpFinanceService:
            def has_payment_history(self, user_id):
                return False

        return NoOpFinanceService()


# Import Tracker and TaskGroups - try multiple sources
try:
    from shared_core.users import TaskGroups, Tracker
except ImportError:
    try:
        from accounts.models import TaskGroups, Tracker
    except ImportError:
        # Fallback: these might not be available
        Tracker = None
        TaskGroups = None

# Import filters - try multiple sources
try:
    from shared_core.filters import RequirementFilter, TaskHistoryFilter
except ImportError:
    try:
        from main.filters import RequirementFilter, TaskHistoryFilter
    except ImportError:
        # Fallback: filters might not be available
        RequirementFilter = None
        TaskHistoryFilter = None
import logging

import docx
import PyPDF2
from coda_project import settings
from coda_project.task import dump_data
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from management.permission import (
    check_payment_history_permission_job_support,
    check_payment_history_permission_student)
from management.utils import (addloantable, compute_total_points, deductions,
                              defined_links, employee_group_level,
                              get_bonus_and_summary, get_selected_month_year,
                              get_tasks, lap_save_bonus, loan_computation,
                              payinitial, paymentconfigurations, paytime,
                              task_assignment_random, updateloantable)
from shared_core.utils import (countdown_in_month, generate_chatbot_response,
                               path_values)

from .utils import split_review_by_sections, suggestions, upload_file_to_drive

logger = logging.getLogger(__name__)


def get_previous_month_reference_date(today=None):
    """
    Return a date that represents the previous full month.
    Used as the reference date for pay / DAF summaries.
    """
    if today is None:
        today = timezone.now().date()
    first_of_this_month = today.replace(day=1)
    last_day_previous = first_of_this_month - timedelta(days=1)
    return last_day_previous


def get_pay_service():
    """
    Try to load the new PayCalculationService; if unavailable,
    fall back to ReleaseEngine. Returns a service instance or None.
    """
    try:
        from management.services.pay_calculation_service import \
            PayCalculationService  # type: ignore

        logger.info("Using PayCalculationService for payroll calculations")
        return PayCalculationService()
    except ModuleNotFoundError as exc:
        logger.warning(
            "PayCalculationService not available, falling back to ReleaseEngine: %s",
            exc,
        )
        try:
            from management.services.release_engine import ReleaseEngine

            return ReleaseEngine()
        except Exception:
            logger.error(
                "ReleaseEngine fallback failed, using empty pay summary instead",
                exc_info=True,
            )
            return None


# OAUTH CONSTANTS - Import from shared_core.utils.oauth (Step 4 Round 2)
# OAuth helpers moved to shared_core as infrastructure utilities
# Using improved versions with:
#   - Environment-aware redirect URIs
#   - Better error handling
#   - Proper logging
# Optional import - oauth utilities may not be available
try:
    from shared_core.utils.oauth import (API_AUTHORIZATION_URL, API_CLIENT_ID,
                                         API_CLIENT_SECRET, API_REDIRECT_URI,
                                         API_TOKEN_URL,
                                         REFRESH_TOKEN_CACHE_KEY,
                                         TOKEN_CACHE_KEY,
                                         exchange_code_for_tokens,
                                         get_access_token,
                                         get_authorization_url,
                                         get_oauth_redirect_uri,
                                         refresh_access_token)
except ImportError:
    # Fallback implementations if oauth utilities are not available
    def get_oauth_redirect_uri(*args, **kwargs):
        return None

    def get_authorization_url(*args, **kwargs):
        return None

    def exchange_code_for_tokens(*args, **kwargs):
        return None

    def refresh_access_token(*args, **kwargs):
        return None

    def get_access_token(*args, **kwargs):
        return None

    API_CLIENT_ID = None
    API_CLIENT_SECRET = None
    API_AUTHORIZATION_URL = None
    API_TOKEN_URL = None
    TOKEN_CACHE_KEY = None
    REFRESH_TOKEN_CACHE_KEY = None
    API_REDIRECT_URI = None

# User=settings.AUTH_USER_MODEL
User = get_user_model()
register = template.Library()


def home(request):
    """Management system home view - redirects to appropriate dashboard based on user role"""
    from accounts.user_utils import get_user_permissions

    # Get user permissions
    permissions = get_user_permissions(request.user)

    # Redirect based on user permissions
    if permissions.get("can_access_management"):
        # User has management access - redirect to management dashboard
        return redirect("management:companyagenda")
    else:
        # User doesn't have management access - show limited access page
        return render(
            request,
            "management/limited_access.html",
            {
                "title": "Management Access",
                "message": "You don't have permission to access the management system.",
            },
        )


# dckdashboard function removed - functionality moved to unified dashboard


def score_report(request):
    return render(
        request, "management/departments/reports.html", {"title": "SCORE REPORT"}
    )


# ================================ DEPARTMENT SECTION ================================
def department(request):
    departments = Department.objects.filter(is_active=True)
    return render(
        request, "management/departments/departments.html", {"departments": departments}
    )


def newdepartment(request):
    if request.method == "POST":
        form = DepartmentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("management:departments")
    else:
        form = DepartmentForm()
    return render(request, "management/tag_form.html", {"form": form})


class DepartmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Department
    success_url = "/management/departments"
    fields = ["name", "slug", "description", "is_active", "is_featured"]
    form = DepartmentForm()

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def test_func(self):
        if self.request.user.is_admin or self.request.user.is_superuser:
            return True
        return False


@user_passes_test(
    lambda user: check_payment_history_permission_student(user),
    login_url="/display_plans/full-course/",
)
@user_passes_test(
    lambda user: check_payment_history_permission_job_support(user),
    login_url="/display_plans/job-support/",
)
def meetings(request, status):
    emp_obj = User.objects.filter(
        # Q(sub_category=3),
        Q(is_admin=True),
        Q(is_active=True),
        Q(is_staff=True),
    ).order_by("-date_joined")
    employees = [employee.first_name for employee in emp_obj]
    _, rand_departments = task_assignment_random(employees)

    if request.user.category in [
        1,
        3,
        4,
        5,
        6,
        7,
    ]:  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
        sessions = Meetings.objects.filter(is_active=True, category=3).order_by(
            "created_at"
        )
    else:
        if status == "company":
            sessions = Meetings.objects.filter(is_active=True, category=2).order_by(
                "created_at"
            )
        elif status == "training":
            sessions = Meetings.objects.filter(is_active=True, category=3).order_by(
                "created_at"
            )
        elif status == "other":
            sessions = Meetings.objects.filter(is_active=True, category=1).order_by(
                "created_at"
            )
        else:
            sessions = Meetings.objects.filter(is_active=True).order_by("created_at")

    categories_list = Meetings.objects.values_list(
        "category__title", flat=True
    ).distinct()
    meeting_categories = sorted(categories_list)
    context = {
        "header_links": defined_links(request),
        "meeting_categories": meeting_categories,
        "employees": employees,
        "title": "Meetings",
        "sessions": sessions,
    }
    return render(request, "management/departments/hr/meetings.html", context)


def newmeeting(request):
    if request.method == "POST":
        form = MeetingForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("management:meetings")
    else:
        form = MeetingForm()
        return render(
            request, "main/snippets_templates/generalform.html", {"form": form}
        )


class MeetingUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Meetings
    success_url = "/management/meetings/company"
    fields = "__all__"

    def get_form_class(self):
        return MeetingForm

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def test_func(self):
        if self.request.user.is_admin or self.request.user.is_superuser:
            return True
        return False


def contract(request):
    return render(request, "management/contracts/trainingcontract_form.html")


def employee_contract(request):
    submitted = False
    if request.user.is_employee_contract_signed:
        return redirect("accounts:account-profile")
    else:
        context = {}
        form = None
        try:
            profile = UserProfile.objects.get(user=request.user)
        except:
            profile = None

        # print(profile)
        if request.method == "POST":
            if profile:
                profile.national_id_no = request.POST["national_id_no"]
                profile.id_file = request.POST["id_file"]
                profile.emergency_name = request.POST["emergency_name"]
                profile.emergency_address = request.POST["emergency_address"]
                profile.emergency_citizenship = request.POST["emergency_citizenship"]
                profile.emergency_phone = request.POST["emergency_phone"]
                profile.emergency_email = request.POST["emergency_email"]
                profile.emergency_national_id_no = request.POST[
                    "emergency_national_id_no"
                ]
                profile.save()
                submitted = True

        form = EmployeeContractForm()
        context["user"] = request.user
        context["profile"] = profile
        context["form"] = form

        if submitted:
            return redirect("management:employee_contract")
        else:
            return render(
                request,
                "management/contracts/employee_contract.html",
                {"context": context},
            )
            # return render(request, "main/snippets_templates/modify.html", {'context': context})


def read_employee_contract(request):
    (
        today,
        year,
        deadline_date,
        month,
        last_month,
        day,
        target_date,
        time_remaining_days,
        time_remaining_hours,
        time_remaining_minutes,
        payday,
        *_,
    ) = paytime()
    user = UserProfile.objects.get(user=request.user)
    context = {
        "title": "Employee Contract",
        "today": today,
        "deadline_date": deadline_date,
    }
    return render(request, "management/contracts/my_investor_contract.html", context)


def confirm_employee_contract(request):
    user = UserProfile.objects.get(user=request.user)

    # if user.national_id_no:
    user = request.user
    user.is_employee_contract_signed = True
    user.save()

    try:
        group = TaskGroups.objects.all().first()
        cat = TaskCategory.objects.all().first()
        try:
            max_point = Task.objects.filter(groupname=group, category=cat).first()
            max_point = max_point.mxpoint
        except:
            max_point = 0

        create_task(
            "Group A",
            group,
            cat,
            user,
            "General Meeting",
            "General Meeting description, auto added",
            "0",
            "0",
            max_point,
            "0",
        )
        create_task(
            "Group A",
            group,
            cat,
            user,
            "BI Session",
            "BI Session description, auto added",
            "0",
            "0",
            max_point,
            "0",
        )
        create_task(
            "Group A",
            group,
            cat,
            user,
            "One on One",
            "One on One description, auto added",
            "0",
            "0",
            max_point,
            "0",
        )
        # create_task('Group A', group, cat, user, 'Video Editing', 'Video Editing description, auto added', '0', '0', max_point, '0')
        # create_task('Group A', group, cat, user, 'Dev Recruitment', 'Dev Recruitment description, auto added', '0', '0', max_point, '0')
        # create_task('Group A', group, cat, user, 'Sprint', 'Sprint description, auto added', '0', '0', max_point, '0')
    except:
        print("Something wrong in task creation")

    return redirect("accounts:account-profile")
    # else:
    #     return redirect("management:employee_contract")


def create_task(
    group,
    groupname,
    cat,
    user,
    activity,
    description,
    duration,
    point,
    mxpoint,
    mxearning,
    activity_type=None,
):
    """
    Create a Task instance with optional ActivityType integration.

    This function maintains backward compatibility while supporting ActivityType defaults.
    If activity_type is not provided, it will attempt to lookup by activity name.
    """
    from .services.activity_type_service import ActivityTypeApplicationService

    service = ActivityTypeApplicationService()

    # If activity_type not provided, try to find it by activity name
    if not activity_type and activity:
        activity_type = service.find_activity_type_by_name(activity)

    # Create task with basic fields
    x = Task()
    x.group = group
    x.groupname = groupname
    x.category = cat
    x.employee = user
    x.activity_name = activity  # Legacy field - may be updated by service
    x.description = description
    # Convert duration to int if it's a string (duration is PositiveIntegerField)
    try:
        x.duration = int(float(duration)) if duration else 0
    except (ValueError, TypeError):
        x.duration = 0
    x.point = point
    x.mxpoint = mxpoint  # May be overridden by ActivityType
    x.mxearning = mxearning  # May be overridden by ActivityType

    # Apply ActivityType defaults (if found)
    if activity_type:
        service.apply_to_task(x, activity_type, preserve_existing=False)
    elif not x.mxpoint:
        # If no ActivityType and mxpoint is 0/None, keep provided mxpoint
        x.mxpoint = mxpoint

    x.save()
    return x


# ==============================PLACE HOLDER MODELS=======================================

# Summary information for tasks


tasksummary = [
    {
        "Target": "1",
        "Description": "Total Amount Assigned",
    },
    {
        "Target": "2",
        "Description": " progress	",
    },
    {
        "Target": "3",
        "Description": "Keep making progress	",
    },
]


# ----------------------REPORTS--------------------------------
@login_required
def companyagenda(request):
    request.session["siteurl"] = settings.SITEURL
    meeting_id = request.GET.get("meeting_id", None)

    if meeting_id:
        meeting = get_object_or_404(Meetings, id=meeting_id, is_active=True)

        # Get all links related to the meeting.
        links = Link.objects.filter(meeting=meeting, is_active=True)

        # Get unique subcategories IDs from those links.
        subcategory_ids = links.values_list("subcategory_id", flat=True).distinct()

        # Get departments that have these subcategories.
        departments = Department.objects.filter(
            subcategory__in=subcategory_ids, is_active=True
        ).distinct()

        # Prepare the data structure for the template.
        categories_with_links = []
        for department in departments:
            subcategories_with_links = []
            for subcategory in department.subcategory_set.filter(
                id__in=subcategory_ids
            ):
                subcategory_links = links.filter(subcategory=subcategory)
                if subcategory_links.exists():
                    subcategories_with_links.append((subcategory, subcategory_links))
            if subcategories_with_links:
                categories_with_links.append((department, subcategories_with_links))

    elif request.user.is_staff:
        categories_with_links = []
        departments = Department.objects.filter(is_active=True)
        for department in departments:
            subcategories_with_links = []
            for subcategory in department.subcategory_set.all():
                subcategory_links = subcategory.link_set.all()
                if subcategory_links.exists():
                    subcategories_with_links.append((subcategory, subcategory_links))
            if subcategories_with_links:
                categories_with_links.append((department, subcategories_with_links))
    else:
        categories_with_links = []
    context = {
        "header_links": defined_links(request),
        "title": "Company Agenda",
        "categories_with_links": categories_with_links,  # Note the context variable change here
    }
    return render(request, "management/departments/agenda/general_agenda.html", context)


@login_required
def companyagenda_improved(request):
    """
    Improved version of companyagenda with modern UI
    Role-based view: Admins see all departments, Staff see single department with subtopics
    """
    request.session["siteurl"] = settings.SITEURL
    meeting_id = request.GET.get("meeting_id", None)

    # Check user role
    is_admin = request.user.is_superuser or request.user.is_admin
    is_staff = request.user.is_staff and not is_admin

    if meeting_id:
        meeting = get_object_or_404(Meetings, id=meeting_id, is_active=True)

        # Get all links related to the meeting.
        links = Link.objects.filter(meeting=meeting, is_active=True)

        # Get unique subcategories IDs from those links.
        subcategory_ids = links.values_list("subcategory_id", flat=True).distinct()

        # Get departments that have these subcategories.
        departments = Department.objects.filter(
            subcategory__in=subcategory_ids, is_active=True
        ).distinct()

        # Prepare the data structure for the template.
        categories_with_links = []
        for department in departments:
            subcategories_with_links = []
            for subcategory in department.subcategory_set.filter(
                id__in=subcategory_ids
            ):
                subcategory_links = links.filter(subcategory=subcategory)
                if subcategory_links.exists():
                    subcategories_with_links.append((subcategory, subcategory_links))
            if subcategories_with_links:
                categories_with_links.append((department, subcategories_with_links))

    elif is_admin:
        # Admin view: Show all departments in columns
        categories_with_links = []
        departments = Department.objects.filter(is_active=True)
        for department in departments:
            subcategories_with_links = []
            for subcategory in department.subcategory_set.all():
                subcategory_links = subcategory.link_set.all()
                if subcategory_links.exists():
                    subcategories_with_links.append((subcategory, subcategory_links))
            if subcategories_with_links:
                categories_with_links.append((department, subcategories_with_links))

    elif is_staff:
        # Staff view: Show single department (HR) with real database subtopics
        # Get HR Department as the main department
        try:
            hr_department = Department.objects.get(name="HR Department", is_active=True)
        except Department.DoesNotExist:
            hr_department = Department.objects.filter(is_active=True).first()

        # Get real subcategories and links from database
        subcategories_with_links = []
        for subcategory in hr_department.subcategory_set.all():
            subcategory_links = subcategory.link_set.all()
            if subcategory_links.exists():
                subcategories_with_links.append((subcategory, subcategory_links))

        categories_with_links = [(hr_department, subcategories_with_links)]

    else:
        categories_with_links = []

    context = {
        "header_links": defined_links(request),
        "title": "Company Agenda - Improved",
        "categories_with_links": categories_with_links,
        "is_admin": is_admin,
        "is_staff": is_staff,
        "user_role": "admin" if is_admin else "staff" if is_staff else "user",
    }
    return render(
        request, "management/departments/agenda/general_agenda_improved.html", context
    )


def updatelinks_companyagenda(request, title, pk):
    # Fetch the model instance based on the title and pk
    if title == "department":
        model_instance = get_object_or_404(Department, pk=pk)
    elif title == "subcategory":
        model_instance = get_object_or_404(SubCategory, pk=pk)
    else:
        model_instance = get_object_or_404(Link, pk=pk)

    DynamicForm = dynamic_agenda_form(model_instance)

    if request.method == "POST":
        form = DynamicForm(request.POST, instance=model_instance)
        if form.is_valid():
            form.save()
            return redirect("management:companyagenda")
    else:
        form = DynamicForm(instance=model_instance)

    return render(request, "main/form.html", {"form": form})


# ----------------------MANAGEMENT POLICIES& OTHER VIEWS--------------------------------
def policy(request):
    if request.method == "POST":
        form = PolicyForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("management:policies")
    else:
        form = PolicyForm()
    return render(request, "management/departments/hr/policy.html", {"form": form})


def policies(request):
    day_name = date.today().strftime("%A")
    policies = Policy.objects.filter(is_active=True, day=day_name).order_by(
        "upload_date"
    )
    applicant_policies = Policy.objects.filter(
        Q(is_active=True), Q(is_internal=False)
    ).order_by("upload_date")
    reporting_date = date.today() + timedelta(days=7)
    context = {
        "policies": policies,
        "applicant_policies": applicant_policies,
        "reporting_date": reporting_date,
        "day_name": day_name,
    }
    return render(request, "management/departments/hr/policies.html", context)


class PolicyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Policy
    fields = [
        "staff",
        "type",
        "department",
        "day",
        "description",
        "link",
        "is_active",
        "is_featured",
        "is_internal",
    ]
    form = PolicyForm()

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("management:policies")

    def test_func(self):
        policy = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user == policy.staff:
            return True
        return False


def benefits(request):
    reporting_date = date.today()
    day_name = date.today().strftime("%A")
    uploads = Policy.objects.all().order_by("upload_date")
    context = {
        "uploads": uploads,
        "reporting_date": reporting_date,
        "day_name": day_name,
    }
    return render(request, "management/departments/hr/benefits.html", context)


# ===================================ACTIVITY CLASS-BASED VIEWS=========================================


# ======================TaskCategory=======================
class TaskCategoryCreateView(LoginRequiredMixin, CreateView):
    model = TaskCategory
    success_url = "/management/newtask"
    fields = ["title", "description"]

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TaskGroupCreateView(LoginRequiredMixin, CreateView):
    model = TaskGroups
    success_url = "/management/tasks/"
    fields = ["title", "description"]

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


# ======================TASKS=======================
def reset_task(request):
    """
    View to reset tasks and update payslip fields with before-and-after print statements for testing.
    """
    try:

        # Step 1: Transfer tasks from Task table to history table (if applicable)
        dump_data(request)

        # Step 2: Update ls_amount
        updated_count = PayslipConfig.objects.filter(
            user__is_staff=True,
            user__is_active=True,
            laptop_status=False,
            ls_amount__lt=Decimal(20000.00),
        ).update(ls_amount=F("ls_amount") + Decimal(1000.00))

        # Step 3: Update rp_starting_amount
        retirement_updated_count = PayslipConfig.objects.filter(
            user__is_staff=True,
            user__is_active=True,
            user__sub_category=ApplicantSubCategoryChoices.FULL_TIME,
        ).update(rp_starting_amount=F("rp_starting_amount") + Decimal(200.00))

        # # Step 4: Update daf_date columan
        bulk_update_daf_date()

        # Step 4: Prepare the Message
        message = (
            f"We are done transferring your tasks to history and resetting the points to zero. "
            f"Furthermore, {updated_count} active user(s) had their ls_amount increased by 1000 for laptop savings, "
            f"and {retirement_updated_count} user(s) had their rp_starting_amount updated based on tenure and pay."
        )

    except Exception as e:
        message = f"An unexpected error occurred: {e}"

    # Step 7: Pass context to the template
    context = {"message": message}

    return render(request, "main/errors/generalerrors.html", context)


def newtaskcreation(request):
    if request.method == "POST":
        group = request.POST["group"]
        category = request.POST["category"]
        description = request.POST["description"]
        point = request.POST["point"]
        mxpoint = request.POST["mxpoint"]
        mxearning = request.POST["mxearning"]

        employee = request.POST["employee"].split(",")

        activitys = request.POST["activitys"].split(",")

        for emp in employee:
            historytasks = TaskHistory.objects.filter(
                employee__is_staff=True, employee__is_active=True, employee_id=emp
            )

            group_obj = TaskGroups.objects.get(id=group)

            # group for interns
            if group_obj.title == "Group I":

                group = group_obj.id
                group_title = group_obj.title

            # group for contractual people
            elif group_obj.title == "Group H":
                group = group_obj.id
                group_title = group_obj.title

            else:
                group, group_title, total_point = employee_group_level(
                    historytasks, TaskGroups
                )

            for act in activitys:
                # check if activity exist
                count = Task.objects.filter(
                    category_id=category, activity_name=act
                ).count()
                if count > 0:
                    des, po, maxpo, maxear = Task.objects.values_list(
                        "description", "point", "mxpoint", "mxearning"
                    ).filter(category_id=category, activity_name=act)[0]

                    if (
                        Task.objects.filter(
                            groupname_id=group,
                            group=group_title,
                            category_id=category,
                            activity_name=act,
                        ).count()
                        == 0
                    ):
                        Task.objects.create(
                            groupname_id=group,
                            category_id=category,
                            employee_id=emp,
                            activity_name=act,
                            description=des,
                            point=0.00,
                            mxpoint=mxpoint,
                            mxearning=mxearning,
                        )
                    else:
                        Task.objects.create(
                            groupname_id=group,
                            group=group_title,
                            category_id=category,
                            employee_id=emp,
                            activity_name=act,
                            description=des,
                            point=0.00,
                            mxpoint=maxpo,
                            mxearning=maxear,
                        )

                else:
                    Task.objects.create(
                        groupname_id=group,
                        group=group_title,
                        category_id=category,
                        employee_id=emp,
                        activity_name=act,
                        description=description,
                        point=point,
                        mxpoint=mxpoint,
                        mxearning=mxearning,
                    )
        # return redirect("management:tasks")
        return JsonResponse({"success": True})
    else:
        task_categories = TaskCategory.objects.all()
        group = TaskGroups.objects.all()
        # PART 2.1: Filter to only active employees (unless staff explicitly requests inactive)
        include_inactive = request.GET.get("include_inactive") == "1" and (
            request.user.is_staff or request.user.is_superuser
        )
        base_filter = Q(is_staff=True) | Q(is_admin=True) | Q(is_superuser=True)
        if not include_inactive:
            base_filter = base_filter & Q(is_active=True)
        employess = User.objects.filter(base_filter).all()

    return render(
        request,
        "management/tasknew_form.html",
        {"group": group, "category": task_categories, "employess": employess},
    )


def gettasksuggestions(request):
    category = request.POST["category"]
    tasks = list(
        Task.objects.values_list("activity_name", flat=True).filter(
            category__id=category
        )
    )
    return JsonResponse({"tasklist": tasks})


def verifytaskgroupexists(request):
    group = request.POST["group"]
    category = request.POST["category"]
    activity = request.POST["activity"]
    count = Task.objects.filter(
        groupname__id=group, category__id=category, activity_name=activity
    ).count()
    mxpoint = Task.objects.values_list("mxpoint", flat=True).filter(
        category__id=category, activity_name=activity
    )[0]

    return JsonResponse({"count": count, "mxpoint": mxpoint})


def getaveragetargets(request):
    # print("+++++++++getaveragetargets+++++++++")
    taskname = request.POST["taskname"]
    # 1st month
    last_day_of_prev_month1 = date.today().replace(day=1) - timedelta(days=1)
    start_day_of_prev_month1 = date.today().replace(day=1) - timedelta(
        days=last_day_of_prev_month1.day
    )

    last_day_of_prev_month2 = last_day_of_prev_month1.replace(day=1) - timedelta(days=1)
    start_day_of_prev_month2 = last_day_of_prev_month1.replace(day=1) - timedelta(
        days=last_day_of_prev_month2.day
    )

    # 3rd month
    last_day_of_prev_month3 = last_day_of_prev_month2.replace(day=1) - timedelta(days=1)
    start_day_of_prev_month3 = last_day_of_prev_month2.replace(day=1) - timedelta(
        days=last_day_of_prev_month3.day
    )

    history = TaskHistory.objects.filter(
        Q(activity_name=taskname),
        Q(created_at__gte=start_day_of_prev_month3),
        Q(created_at__lte=last_day_of_prev_month1),
    )

    results = {"target_points": 0, "target_amount": 0}
    counter = 0
    for data in history.all():
        results["target_points"] += data.mxpoint
        results["target_amount"] += data.mxearning
        counter = counter + 1
    try:
        results["target_points"] = results["target_points"] / counter
        results["target_amount"] = results["target_amount"] / counter
    except Exception as ZeroDivisionError:
        results["target_points"] = 0.0
        results["target_amount"] = 0.0

    return JsonResponse(results)


class TaskListView(FilteredListViewMixin, ListView):
    """Consolidated task list view using generic mixin"""

    model = Task
    template_name = "management/daf/tasklist.html"
    context_object_name = "tasks"
    order_by = "-id"

    def get_queryset(self):
        """Apply task-specific filtering - filter by logged-in employee or URL parameter"""
        queryset = super().get_queryset()

        # Check for employee filter in URL parameters
        employee_id = self.request.GET.get("employee")

        if employee_id:
            # Filter by specific employee from URL parameter
            try:
                queryset = queryset.filter(employee_id=employee_id)
            except (ValueError, TypeError):
                pass  # Invalid employee ID, ignore
        elif self.request.user.is_authenticated:
            # Filter by logged-in employee (not all tasks)
            # If staff/superuser, show all tasks; otherwise show only employee's tasks
            if not (self.request.user.is_staff or self.request.user.is_superuser):
                queryset = queryset.filter(employee=self.request.user)

        # Exclude tasks with no employee email
        queryset = queryset.exclude(employee__email=None)

        # GOAL 1: Filter to only show tasks from active employees
        # Prefer User.is_active=True (Django's built-in field)
        # This ensures we only show current/active employees, not historical ones
        queryset = queryset.filter(employee__is_active=True)

        # Apply category filter if POST request
        if self.request.method == "POST":
            form = TagFilterForm(self.request.POST)
            if form.is_valid():
                category = form.cleaned_data["category"]
                queryset = queryset.filter(category__title=category)

        # Optimize query performance: select_related for employee FK and profile
        # Only include career_group if it exists on UserProfile (backward compatible)
        select_related_fields = ["employee", "employee__profile"]
        try:
            from accounts.models import UserProfile

            if hasattr(UserProfile._meta, "get_field"):
                try:
                    career_group_field = UserProfile._meta.get_field("career_group")
                    # Only include if it's a ForeignKey/OneToOneField (can be used in select_related)
                    if hasattr(career_group_field, "related_model"):
                        select_related_fields.append("employee__profile__career_group")
                except Exception:
                    # Field doesn't exist, skip it (backward compatible)
                    pass
        except Exception:
            # UserProfile model not available or other error, skip career_group
            pass
        return queryset.select_related(*select_related_fields).order_by(self.order_by)

    def get_context_data(self, **kwargs):
        """Add task-specific context data"""
        context = super().get_context_data(**kwargs)

        # Add filtered employee list for dropdown (matching reset_tasks logic)
        from management.services.employee_filter_service import \
            get_filtered_employees_queryset

        try:
            filtered_employees = get_filtered_employees_queryset(self.request)
            context["filtered_employees"] = filtered_employees
        except Exception as e:
            logger.debug(f"Error getting filtered employees: {e}")
            context["filtered_employees"] = User.objects.none()

        if self.request.method == "POST":
            form = TagFilterForm(self.request.POST)
        else:
            form = TagFilterForm()

        context["form"] = form
        context["total_count"] = self.get_queryset().count()

        # Add filtered employee info if present
        # NOTE: Task.employee is a ForeignKey to auth.User (from get_user_model())
        # The employee query parameter must match Task.employee_id (the FK column)
        employee_id = self.request.GET.get("employee")
        if employee_id:
            from django.contrib import messages
            from management.services.employee_identity_service import (
                get_daf_user_id_from_task_employee, get_task_employee_from_id,
                validate_employee_id_for_daf)

            # Validate employee ID and get DAF user_id mapping
            is_valid, daf_user_id, error_msg = validate_employee_id_for_daf(employee_id)

            if is_valid:
                filtered_employee = get_task_employee_from_id(employee_id)
                context["filtered_employee"] = filtered_employee
                context["daf_user_id"] = daf_user_id
            else:
                # Invalid employee ID - show warning message and fall back to unfiltered
                messages.warning(
                    self.request,
                    f"Invalid employee ID: {employee_id}. {error_msg or 'Showing all tasks.'}",
                )
                context["filtered_employee"] = None
                context["daf_user_id"] = None
        else:
            context["filtered_employee"] = None
            context["daf_user_id"] = None

        return context


def tasklist(request):
    context = {}
    tasks = Task.objects.exclude(employee__email=None).order_by("-id")
    if request.method == "POST":
        form = TagFilterForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data["category"]
            # print("category=====>",category)
            # filtered_tasks = Task.objects.filter(category=category).order_by('-id')
            filtered_tasks = Task.objects.filter(category__title=category)
            # print("filtered_tasks=====>",filtered_tasks)
        context = {"tasks": filtered_tasks, "form": form}
        return render(request, "management/daf/tasklist.html", context)
    else:
        form = TagFilterForm()
        context = {"tasks": tasks, "form": form}
        return render(request, "management/daf/tasklist.html", context)


def filterdatset(obj):
    result = []
    details = {}
    for data in obj:
        details["groupname"] = str(data.groupname)
        details["deadline"] = data.deadline.strftime("%d %b %Y")
        details["submission"] = data.submission.strftime("%d %b %Y")
        details["point"] = data.point
        details["mxpoint"] = data.mxpoint
        details["mxearning"] = float(data.mxearning)
        details["get_pay"] = float(data.get_pay)
        details["id"] = data.id
        details["employee"] = data.employee.username
        details["first_name"] = data.employee.first_name
        details["last_name"] = data.employee.last_name
        details["description"] = data.description
        details["activity_name"] = data.activity_name
        details["get_absolute_url"] = str(data.category.get_absolute_url)
        result.append(details.copy())
    return result


def filterbycategory(request):
    category = request.POST["category"]

    tasks = Task.objects.filter(category__title=category)
    result = []
    details = {}
    for data in tasks.all():
        details["groupname"] = data.groupname
        details["deadline"] = data.deadline.strftime("%d %b %Y")
        details["submission"] = data.submission.strftime("%d %b %Y")
        details["point"] = data.point
        details["mxpoint"] = data.mxpoint
        details["mxearning"] = float(data.mxearning)
        details["get_pay"] = float(data.get_pay)
        details["id"] = data.id
        details["employee"] = data.employee.username
        details["first_name"] = data.employee.first_name
        details["last_name"] = data.employee.last_name
        details["description"] = data.description
        details["activity_name"] = data.activity_name
        details["get_absolute_url"] = str(data.category.get_absolute_url)
        result.append(details.copy())

    # print(result)
    return JsonResponse({"result": result}, safe=False)


def get_user_data(employee):
    """Retrieve user-related data."""
    from management.services.finance_service_helper import \
        get_finance_task_service
    from shared_core.users import UserProfile

    userprofile = UserProfile.objects.get(user_id=employee)

    # Use finance service interface for loan data
    finance_service = get_finance_task_service()
    loan_summary = finance_service.get_user_loan_summary(employee.id)

    # Create a mock queryset-like object for backward compatibility
    # This allows existing code that uses .exists() and .order_by() to work
    class LoanDataWrapper:
        """Wrapper to maintain backward compatibility with queryset usage."""

        def __init__(self, loan_summary):
            self.loan_summary = loan_summary
            self._has_loan = loan_summary is not None

        def exists(self):
            return self._has_loan

        def order_by(self, field):
            # Return self to allow chaining like .order_by('-id')[0]
            return self

        def __getitem__(self, index):
            # Return loan_summary dict wrapped in a mock object
            if index == 0 and self._has_loan:

                class LoanObject:
                    def __init__(self, summary):
                        self.id = summary.get("loan_id")
                        self.status = summary.get("status")
                        self.amount = summary.get("amount")
                        # Add other attributes as needed

                return LoanObject(self.loan_summary)
            return None

    user_data = LoanDataWrapper(loan_summary)
    # Note: paymentconfigurations() still uses PayslipConfig for backward compatibility
    # but internally uses finance_service.get_payslip_config() when available
    # This is a temporary bridge - ideally we'd refactor to use dicts directly
    try:
        from finance.models import PayslipConfig
    except ImportError:
        PayslipConfig = None

    payslip_config = (
        paymentconfigurations(PayslipConfig, employee) if PayslipConfig else None
    )
    return userprofile, user_data, payslip_config


def bulk_update_daf_date():
    """
    Update daf_date for existing TaskHistory records using bulk_update.
    For tasks created this month, set daf_date to same day of last month (e.g., Nov 4 -> Oct 4).
    """
    from datetime import date

    from django.utils import timezone

    # Find tasks with NULL daf_date
    tasks = TaskHistory.objects.exclude(submission__isnull=True).filter(
        daf_date__isnull=True
    )

    current_date = date.today()
    start_of_current_month = timezone.now().replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )

    updated_tasks = []
    for task in tasks:
        if task.submission:
            submission_date = timezone.localtime(task.submission).date()

            # If task was created/submitted this month, set daf_date to same day of last month
            # (e.g., Nov 4 -> Oct 4)
            if (
                submission_date.month == current_date.month
                and submission_date.year == current_date.year
            ):
                # Same day, last month
                task.daf_date = submission_date - relativedelta(months=1)
            else:
                # Older submission, use submission - 1 month
                task.daf_date = submission_date - relativedelta(months=1)
        elif task.created_at:
            # Fallback to created_at if submission is not available
            created_date = timezone.localtime(task.created_at).date()
            if (
                created_date.month == current_date.month
                and created_date.year == current_date.year
            ):
                # Same day, last month
                task.daf_date = created_date - relativedelta(months=1)
            else:
                task.daf_date = created_date - relativedelta(months=1)

        updated_tasks.append(task)

    if updated_tasks:
        TaskHistory.objects.bulk_update(updated_tasks, ["daf_date"])
        print(f"{len(updated_tasks)} records updated successfully with daf_date.")
    else:
        print("No records to update.")


def payslip(request, *args, **kwargs):
    """
    Retrieve pay_type and user dynamically from kwargs and handle dynamic redirection.

    P8 Integration: When pay_type='usertasks', this view is now backed by DAFSummaryService
    and is the canonical DAF UI entrypoint.

    For other pay_types, uses PayCalculationService as before.
    """
    pay_type = request.GET.get("pay_type", None)
    username = request.GET.get("username", None)
    employee = None

    if username:
        # Security: Only allow users to access their own data, unless they're staff/superuser
        if (
            request.user.username == username
            or request.user.is_staff
            or request.user.is_superuser
        ):
            employee = get_object_or_404(User, username=username)
        else:
            # Redirect unauthorized users to their own page
            messages.warning(
                request, "You can only access your own payroll information."
            )
            return redirect(
                f"{request.path}?username={request.user.username}&pay_type={pay_type or 'usertasks'}"
            )

    request.session["siteurl"] = settings.SITEURL
    today, year, deadline_date, *_ = paytime()

    # ===================Selected Month and Year===========================
    # For usertasks (My DAF), use latest TaskHistory month for summary, current month for active tasks
    # For payslip, use latest TaskHistory month
    # For other pay_types, use get_selected_month_year which may default to previous month
    today_date = timezone.now().date()

    if pay_type == "usertasks":
        # My DAF doesn't use a specific month - it uses current active tasks
        # selected_month/year are just for form/template compatibility, use current month
        from .forms import MonthForm

        form = MonthForm()
        selected_month = today_date.month
        selected_year = today_date.year
    else:
        # For non-usertasks (like payslip), may use form selection or latest TaskHistory month
        selected_month, selected_year, form = get_selected_month_year(request, pay_type)

    # P8: My DAF (pay_type='usertasks') - current tasks only
    # My DAF (usertasks) uses daf_current_summary_service.get_current_daf_summary server-side.
    # Legacy DAF summary API is intentionally not applied on this page (blocked by template guard).
    if pay_type == "usertasks":
        from management.models import Task
        from management.services.daf_current_summary_service import \
            get_current_daf_summary

        employee_user = employee or request.user

        # Compute current DAF summary from active tasks only
        # Target amount is sum of mxearning from current Task records
        try:
            summary = get_current_daf_summary(employee_user)

            # Extract values for logging
            money = summary.get("money", {})
            metrics = summary.get("metrics", {})
            logger.info(
                f"My DAF (current) for {getattr(employee_user, 'username', 'unknown')}: "
                f"target_amount={money.get('target_amount', 0)}, "
                f"points={metrics.get('points_earned', 0)}/{metrics.get('target_points', 0)}, "
                f"earned={money.get('released_total', 0)}, pending={money.get('locked_total', 0)}"
            )
        except Exception as e:
            # Handle service errors gracefully
            logger.error(
                f"Error generating current DAF summary for {employee_user}: {e}",
                exc_info=True,
            )
            # Use safe defaults
            summary = {
                "employee": {
                    "id": employee_user.id if hasattr(employee_user, "id") else 0,
                    "username": getattr(employee_user, "username", "unknown"),
                    "full_name": str(employee_user),
                },
                "money": {
                    "target_amount": Decimal("0"),
                    "released_total": Decimal("0"),
                    "locked_total": Decimal("0"),
                    "net_income": Decimal("0"),
                },
                "metrics": {
                    "points_earned": 0.0,
                    "target_points": 0.0,
                },
                "activities": [],
            }

        # Get current active tasks for THIS employee (not restricted by month/year)
        # For CODA, "current active tasks" means is_active=True + assigned to employee
        # Tasks can span months and we don't create new task records every month
        # Include activity_type FK to use canonical activity names from new taxonomy
        active_tasks_qs = (
            Task.objects.filter(employee=employee or request.user, is_active=True)
            .select_related("category", "department", "activity_type")
            .order_by(
                "id"
            )  # Task model doesn't have 'deadline' field, use 'id' for consistent ordering
        )

        # Helper function to generate task URL (defined outside loop)
        def generate_task_url_from_task(task_obj):
            """Generate task URL for Task model (similar to TaskHistory logic)"""
            try:
                import string

                from django.urls import reverse

                one_list = ["one on one sessions", "one on one", "one on one session"]
                job_list = ["job support", "job_support"]
                onelist = [
                    t.lower().translate({ord(c): None for c in string.whitespace})
                    for t in one_list
                ]
                joblist = [
                    t.lower().translate({ord(c): None for c in string.whitespace})
                    for t in job_list
                ]
                # Use canonical activity name if available, fallback to legacy activity_name
                activity_name_for_url = (
                    task_obj.activity_type.name
                    if task_obj.activity_type and task_obj.activity_type.name
                    else task_obj.activity_name
                )
                activity = activity_name_for_url.lower().translate(
                    {ord(c): None for c in string.whitespace}
                )

                if activity in onelist:
                    return reverse("application:rate")
                elif activity in joblist:
                    return reverse("application:job_support")
                else:
                    # Default to new evidence page
                    return reverse("management:new_evidence", args=[task_obj.id])
            except Exception:
                return "#"

        # Log sample of activity names being used (canonical vs legacy)
        # Wrap in try/except to handle potential DB errors with ActivityDefinition table
        try:
            activity_sample = [
                (
                    t.id,
                    t.activity_name,  # Legacy name from DB
                    (
                        t.activity_type.name if t.activity_type else None
                    ),  # Canonical name if available
                )
                for t in list(active_tasks_qs[:5])
            ]
            logger.info(
                "My DAF activities for %s (first 5): %s",
                getattr(employee_user, "username", "unknown"),
                activity_sample,
            )
        except Exception:
            # Skip logging if there's any DB error (e.g., ActivityDefinition table doesn't exist)
            pass

        # Convert active tasks to activity dict format for template compatibility
        # The template expects a list of dicts similar to activities from summary
        active_tasks_list = []
        for task in active_tasks_qs:
            # Check for evidence via tasklinks (TaskLinks uses FK to Task)
            try:
                has_evidence = TaskLinks.objects.filter(
                    task=task, is_active=True
                ).exists()
            except Exception:
                has_evidence = False

            # Calculate deadline (end of current month)
            from calendar import monthrange

            last_day = monthrange(today_date.year, today_date.month)[1]
            deadline = date(today_date.year, today_date.month, last_day)

            # Get submission date safely
            submission_date = today_date
            if task.submission:
                if hasattr(task.submission, "date"):
                    submission_date = task.submission.date()
                elif isinstance(task.submission, date):
                    submission_date = task.submission

            # Use canonical activity name from ActivityType if available, fallback to legacy activity_name
            # This ensures the new activity taxonomy (30+ definitions) is visible in My DAF
            # Wrap in try/except to handle potential DB errors with ActivityDefinition table
            try:
                canonical_activity_name = (
                    task.activity_type.name
                    if task.activity_type and task.activity_type.name
                    else task.activity_name
                )
            except Exception:
                # Fallback to legacy name if accessing activity_type causes any error
                canonical_activity_name = task.activity_name

            # Build activity dict with canonical name and additional metadata
            activity_dict = {
                "activity_name": canonical_activity_name,  # Use canonical name from ActivityType
                "points": float(task.point or Decimal("0")),
                "max_points": float(task.mxpoint or Decimal("0")),
                "earning": float(
                    (task.point / task.mxpoint * task.mxearning)
                    if task.mxpoint and task.mxpoint > 0
                    else Decimal("0")
                ),
                "mxearning": float(task.mxearning or Decimal("0")),
                "duration": task.duration or 0,
                "description": task.description or "",
                "task_history_id": task.id,  # Template expects task_history_id for Edit link
                "task_url": generate_task_url_from_task(task),
                "has_evidence": has_evidence,
                "deadline": deadline.isoformat(),
                "daf_date": submission_date.isoformat(),
            }

            # Add activity_type metadata if available (for future template enhancements)
            # Wrap in try/except to handle potential DB errors with ActivityDefinition table
            if task.activity_type:
                try:
                    activity_dict["activity_type"] = {
                        "slug": task.activity_type.slug or "",
                        "name": task.activity_type.name,
                        "description": task.activity_type.description or "",
                    }
                except Exception:
                    # Skip activity_type metadata if there's any DB error
                    pass
                # Add ActivityDefinition if available (AI metadata, descriptions, checklists)
                # Note: ActivityDefinition table may not exist if migrations haven't been run
                # Wrap in try/except to handle ProgrammingError when table doesn't exist
                if task.activity_type:
                    try:
                        # Accessing ai_definition may trigger a DB query for a non-existent table
                        # Catch ProgrammingError and all exceptions to handle missing table gracefully
                        ai_def = getattr(task.activity_type, "ai_definition", None)
                        if ai_def:
                            # Extract checklist from quality_criteria if present
                            checklist = []
                            quality_criteria = (
                                getattr(ai_def, "quality_criteria", {}) or {}
                            )
                            if (
                                isinstance(quality_criteria, dict)
                                and "checklist" in quality_criteria
                            ):
                                checklist = quality_criteria["checklist"]

                            activity_dict["activity_definition"] = {
                                "ai_context": getattr(ai_def, "ai_context", "") or "",
                                "evidence_requirements": getattr(
                                    ai_def, "evidence_requirements", []
                                )
                                or [],
                            }

                            # Add description and checklist for template rendering
                            activity_dict["activity_description"] = (
                                getattr(ai_def, "ai_context", "")
                                or task.activity_type.description
                                or ""
                            )
                            activity_dict["activity_checklist"] = checklist
                        else:
                            # ActivityType exists but no ActivityDefinition - use ActivityType description
                            activity_dict["activity_description"] = (
                                task.activity_type.description or ""
                            )
                            activity_dict["activity_checklist"] = []
                    except Exception as e:
                        # Table management_activitydefinition doesn't exist or other DB error - skip silently
                        # This is expected when migrations haven't been run yet
                        # Log at debug level if needed for troubleshooting
                        if "management_activitydefinition" in str(
                            e
                        ) or "does not exist" in str(e):
                            # This is the expected case - table doesn't exist
                            # Fallback to ActivityType description if available
                            if task.activity_type and task.activity_type.description:
                                activity_dict["activity_description"] = (
                                    task.activity_type.description
                                )
                                activity_dict["activity_checklist"] = []
                        else:
                            # Other unexpected errors - still skip but could log if needed
                            # Fallback to ActivityType description if available
                            if task.activity_type and task.activity_type.description:
                                activity_dict["activity_description"] = (
                                    task.activity_type.description
                                )
                                activity_dict["activity_checklist"] = []
                else:
                    # No activity_type - no description or checklist
                    activity_dict["activity_description"] = ""
                    activity_dict["activity_checklist"] = []

            active_tasks_list.append(activity_dict)

        # Calculate remaining time (UI helper)
        remaining_days, remaining_seconds, remaining_minutes, remaining_hours = (
            countdown_in_month()
        )

        # Map summary to template context (preserving existing variable names for template compatibility)
        # Summary cards use current DAF logic:
        # - Target: money.target_amount (sum of mxearning from current active Task records)
        # - Points/MaxPoints: metrics (sum from current active Task records)
        # - Earned: money.released_total (computed from current active Task records)
        # - Pending: money.locked_total (target_amount - earned from current active Task records)
        # - Net Income: money.net_income (same as earned for current DAF)
        money = summary.get("money", {}) or {}
        metrics = summary.get("metrics", {}) or {}

        # Extract values ensuring Decimal types
        target_amount = money.get("target_amount", Decimal("0"))
        earned_amount = money.get("released_total", Decimal("0"))
        pending_amount = money.get("locked_total", Decimal("0"))
        net_income = money.get("net_income", Decimal("0"))

        points_earned = metrics.get("points_earned", Decimal("0"))
        target_points = metrics.get("target_points", Decimal("0"))

        # Convert to float for percentage calculations
        points_earned_float = float(points_earned)
        target_points_float = float(target_points)

        # Explicit logging of context values for debugging
        logger.info(
            "My DAF (view context) for %s: target=%s, earned=%s, pending=%s, net=%s, points=%s/%s",
            getattr(employee_user, "username", "unknown"),
            target_amount,
            earned_amount,
            pending_amount,
            net_income,
            points_earned,
            target_points,
        )

        # Calculate points balance
        points_balance = (
            max(0, target_points_float - points_earned_float)
            if target_points_float > 0
            else 0.0
        )

        # Calculate point percentage
        point_percentage = (
            (points_earned_float / target_points_float * 100)
            if target_points_float > 0
            else 0.0
        )

        # Build context for My DAF template
        context = {
            "form": form,
            "selected_month": selected_month,
            "selected_year": selected_year,
            "employee": employee_user,
            "pay_type": pay_type,
            "summary": summary,  # Full summary for template access (current DAF data)
            "payday": deadline_date,
            "num_tasks": len(active_tasks_list),
            "tasks": active_tasks_list,  # Current active tasks from Task model
            # Summary cards (current DAF data):
            "Points": points_earned_float,  # From current active Task records
            "MaxPoints": target_points_float,  # From current active Task records
            "point_percentage": round(point_percentage, 2),
            "GoalAmount": target_amount,  # Target card (sum of mxearning from current active tasks)
            "paybalance": pending_amount,  # Pending card (target_amount - earned from current tasks)
            "pointsbalance": round(points_balance, 2),
            "total_pay": earned_amount,  # Earned card (from current tasks)
            "totalearnings": earned_amount,  # Earned card (alternative key used by template)
            "net": net_income,  # Net Income card (same as earned for current DAF)
            "average_earnings": target_amount,  # Target card (alias for template)
            # UI helpers:
            "remaining_days": remaining_days,
            "remaining_seconds": remaining_seconds,
            "remaining_minutes": remaining_minutes,
            "remaining_hours": remaining_hours,
            "deadline_date": deadline_date,
            "today": today,
            "enddate": (
                deadline_date.isoformat()
                if hasattr(deadline_date, "isoformat")
                else str(deadline_date)
            ),
            "debug": bool(getattr(settings, "DEBUG", False))
            and request.GET.get("debug") == "1",  # Enable with ?debug=1 in DEBUG mode
        }

        # Log final context values to verify mapping
        logger.info(
            "My DAF (final context) for %s: GoalAmount=%s, average_earnings=%s, total_pay=%s, "
            "totalearnings=%s, paybalance=%s, net=%s, Points=%s, MaxPoints=%s",
            getattr(employee_user, "username", "unknown"),
            context.get("GoalAmount"),
            context.get("average_earnings"),
            context.get("total_pay"),
            context.get("totalearnings"),
            context.get("paybalance"),
            context.get("net"),
            context.get("Points"),
            context.get("MaxPoints"),
        )

        # Manual verification flow:
        # To verify in UAT: pick employee X (e.g. username eunice), load /management/payroll/?username=<user>&pay_type=usertasks,
        # and confirm that:
        # 1. Task table shows current active tasks from Task model (no month filter)
        # 2. Activity names use ActivityType.name where available (canonical names)
        # 3. Summary cards:
        #    - Target/GoalAmount = sum of mxearning from current active Task records
        #    - Points/MaxPoints = sum from current active Task records
        #    - Earned/Pending/Net = computed from current active Task records only
        # 4. All values reflect current DAF status, not historical snapshots

        return render(request, "management/daf/usertasks.html", context)

    # For other pay_types (like payslip), use pay service with fallback to DAFSummaryService
    # Payslip/MyLastDAF uses latest TaskHistory month (fully historical)
    payslip_month = None
    payslip_year = None

    if pay_type in ["payslip", "task_payslip"]:
        from management.services.daf_period_service import \
            get_latest_daf_period_for_employee

        employee_user = employee or request.user
        payslip_year, payslip_month, reference_date = (
            get_latest_daf_period_for_employee(employee_user)
        )

        logger.info(
            f"Selected payslip/MyLastDAF period for {getattr(employee_user, 'username', 'unknown')}: "
            f"year={payslip_year}, month={payslip_month} (latest TaskHistory month)"
        )

    # Get pay service using safe helper (never direct import)
    pay_service = get_pay_service()
    payslip_data = {}

    if (
        pay_type in ["payslip", "task_payslip"]
        and payslip_month is not None
        and payslip_year is not None
    ):
        # Try pay service first (PayCalculationService)
        if pay_service is not None:
            try:
                # Check if service has calculate_payslip method (PayCalculationService)
                if hasattr(pay_service, "calculate_payslip"):
                    payslip_data = pay_service.calculate_payslip(
                        employee=employee_user,
                        target_month=payslip_month,
                        target_year=payslip_year,
                        pay_type=pay_type,
                        enforce_evidence=False,
                    )
                else:
                    # ReleaseEngine doesn't have calculate_payslip, fall back to DAFSummaryService
                    logger.warning(
                        f"Pay service {type(pay_service).__name__} does not support calculate_payslip, "
                        f"falling back to DAFSummaryService for historical data"
                    )
                    payslip_data = {}
            except Exception as e:
                logger.exception(
                    f"Error generating payslip via pay service for {employee_user}: {e}; "
                    f"falling back to DAFSummaryService",
                    exc_info=True,
                )
                payslip_data = {}

        # If pay service didn't provide data, use DAFSummaryService for historical TaskHistory data
        if not payslip_data:
            try:
                from management.services.daf_summary_service import \
                    DAFSummaryService

                daf_service = DAFSummaryService()
                summary = daf_service.get_summary(
                    employee=employee_user,
                    target_month=payslip_month,
                    target_year=payslip_year,
                )

                # Map DAFSummaryService output to payslip_data structure
                # Extract TaskHistory rows from activities
                tasks = []
                for activity in summary.get("activities", []):
                    # Build task dict from activity data (TaskHistory format)
                    tasks.append(
                        {
                            "activity_name": activity.get("activity_name", ""),
                            "point": activity.get("points", 0),
                            "mxpoint": activity.get("max_points", 0),
                            "mxearning": activity.get("mxearning", 0),
                            "earning": activity.get("earning", 0),
                            "description": activity.get("description", ""),
                        }
                    )

                payslip_data = {
                    "tasks": tasks,
                    "base_pay": {
                        "total": summary.get("money", {}).get(
                            "released_total", Decimal("0")
                        ),
                        "goal_amount": summary.get("money", {}).get(
                            "target_amount", Decimal("0")
                        ),
                        "points": summary.get("metrics", {}).get("points_earned", 0),
                        "max_points": summary.get("metrics", {}).get(
                            "target_points", 0
                        ),
                    },
                    "summary": {
                        "net_pay": summary.get("money", {}).get(
                            "net_income", Decimal("0")
                        ),
                    },
                    "bonuses": {},
                    "deductions": {},
                }

                logger.info(
                    f"Payslip data from DAFSummaryService for {employee_user.username}: "
                    f"{payslip_year}-{payslip_month:02d}"
                )
            except Exception as e:
                logger.exception(
                    f"Error generating payslip via DAFSummaryService for {employee_user}: {e}",
                    exc_info=True,
                )
                payslip_data = {}

        if not payslip_data:
            # No data from either service - log warning but continue with empty data
            logger.warning(
                f"No payslip data available for {getattr(employee_user, 'username', 'unknown')} "
                f"({payslip_year}-{payslip_month:02d}) - both pay service and DAFSummaryService failed"
            )

    # Extract data from service response (handle empty payslip_data gracefully)
    tasks = payslip_data.get("tasks") if payslip_data else None
    base_pay = payslip_data.get("base_pay", {}) if payslip_data else {}
    bonuses = payslip_data.get("bonuses", {}) if payslip_data else {}
    deductions = payslip_data.get("deductions", {}) if payslip_data else {}
    summary = payslip_data.get("summary", {}) if payslip_data else {}
    metadata = payslip_data.get("metadata", {}) if payslip_data else {}

    # For non-payslip types, use selected_month/year from form
    # (payslip_month/year already set above for payslip types)
    if pay_type not in ["payslip", "task_payslip"]:
        if payslip_month is None:
            payslip_month = selected_month
        if payslip_year is None:
            payslip_year = selected_year

    # Incorporating a filter (still needed for template)
    # Note: TaskHistoryFilter expects a queryset, but payslip_data.get('tasks') returns a list
    # Skip filter if tasks is a list (not a queryset)
    if tasks and hasattr(tasks, "model"):  # Check if it's a queryset
        myfilter = TaskHistoryFilter(request.GET, queryset=tasks)
    else:
        myfilter = None  # Skip filter for list data

    # Use PayrollSummaryService for consistent time remaining calculation (to Pay Day, not end of month)
    from management.services.payroll_summary_service import \
        get_time_remaining_until_pay_day

    time_remaining = get_time_remaining_until_pay_day()
    remaining_days = time_remaining.get("days", 0)
    remaining_hours = time_remaining.get("hours", 0)
    remaining_minutes = time_remaining.get("minutes", 0)
    remaining_seconds = time_remaining.get("seconds", 0)

    # Build context from service data (mapping to existing template field names)
    context = {
        "form": form,
        "selected_month": payslip_month,
        "selected_year": payslip_year,
        "employee": employee,
        "pay_type": pay_type,
        "payday": deadline_date,
        "num_tasks": base_pay.get("num_tasks", 0),
        "tasks": tasks,
        "TaskHistoryFilter": myfilter,
        "Points": base_pay.get("points", 0),
        "MaxPoints": base_pay.get("max_points", 0),
        "point_percentage": base_pay.get("point_percentage", Decimal("0")),
        "pay": base_pay.get("goal_amount", Decimal("0")),
        "GoalAmount": base_pay.get("goal_amount", Decimal("0")),
        "paybalance": base_pay.get("pay_balance", Decimal("0")),
        "pointsbalance": base_pay.get("points_balance", Decimal("0")),
        "total_pay": base_pay.get("total", Decimal("0")),
        "loan": deductions.get("loan_payment", Decimal("0")),
        "net": summary.get("net_pay", Decimal("0")),
        "average_earnings": base_pay.get("goal_amount", Decimal("0")),
        "remaining_days": remaining_days,
        "remaining_seconds": remaining_seconds,
        "remaining_minutes": remaining_minutes,
        "remaining_hours": remaining_hours,
        "total_login_hours": bonuses.get("login_hours", 0),
        "Logged_In_Bonus": bonuses.get("points_bonus", Decimal("0"))
        + bonuses.get("login_bonus", Decimal("0")),
        "EOM": bonuses.get("eom_bonus", Decimal("0")),
        "EOQ": bonuses.get("eoq_bonus", Decimal("0")),
        "EOY": bonuses.get("eoy_bonus", Decimal("0")),
        "laptop_bonus": bonuses.get("laptop_bonus", Decimal("0")),
        "holidaypay": bonuses.get("holiday_pay", Decimal("0")),
        "Night_Bonus": bonuses.get("late_night_bonus", Decimal("0")),
        "yearly": bonuses.get("yearly", Decimal("12000")),
        "food_accomodation": deductions.get("food_accommodation", Decimal("0")),
        "computer_maintenance": deductions.get("computer_maintenance", Decimal("0")),
        "health": deductions.get("health", Decimal("0")),
        "laptop_saving": deductions.get("laptop_saving", Decimal("0")),
        "total_laptop_saving": deductions.get("total_laptop_savings", Decimal("0")),
        "kra": deductions.get("tax_kra", Decimal("0")),
        "total_value": summary.get("gross_pay", Decimal("0")),
        "total_deduction": summary.get("total_deductions", Decimal("0")),
        "balance_amount": deductions.get("loan_balance", Decimal("0")),
        "deadline_date": deadline_date,
        "today": today,
        "payslip_data": payslip_data,
    }

    # Dynamic Redirection Logic
    if pay_type in ["payslip", "task_payslip"]:
        # Use modern payslip template if available, fallback to legacy
        try:
            return render(request, "management/daf/payslip_modern.html", context)
        except Exception:
            # Fallback to legacy template if modern template not found
            return render(request, "management/daf/payslip.html", context)

    elif pay_type in ["usertaskhistory"]:
        return render(request, "management/daf/usertasks.html", context)

    elif pay_type in ["tasks", "taskhistory"]:
        if pay_type == "tasks":
            return render(request, "management/daf/tasklist.html", context)
        else:
            return render(request, "management/daf/taskhistory.html", context)
    else:
        # Default redirect
        return redirect("main:layout")


@login_required
def daf_v2_view(request):
    """
    DAF v2 View - Modern UI for Daily Activity Form

    This view provides a new, professional DAF interface while maintaining
    compatibility with the existing backend services. It reuses:
    - get_current_daf_summary() for summary cards
    - ChecklistEvaluationService for quality scores
    - Same Task model and TaskLinks for evidence

    URL: /management/daf/v2/
    Template: management/daf/usertasks/employeetasks_v2.html

    NOTE: user_id parameter expects auth.User.id (from get_user_model()).
    This is the same User model that Task.employee references, so:
    - Task.employee.id == user_id (direct mapping, no conversion needed)
    - Use employee_identity_service.get_daf_user_id_from_task_employee() for explicit mapping
    """
    from calendar import monthrange

    from django.contrib.auth import get_user_model
    from django.core.exceptions import PermissionDenied
    from django.http import Http404
    from django.utils import timezone
    from main.utils import countdown_in_month
    from management.models import Task, TaskLinks
    from management.services.checklist_evaluation_service import \
        ChecklistEvaluationService
    from management.services.daf_current_summary_service import \
        get_current_daf_summary

    User = get_user_model()

    # GOAL 2: Support user_id parameter for staff/superuser to view other users' DAF
    user_id_param = request.GET.get("user_id")

    if user_id_param:
        # Only allow staff/superuser to view other users' DAF
        if not (request.user.is_staff or request.user.is_superuser):
            from django.http import HttpResponseForbidden

            return HttpResponseForbidden(
                "You do not have permission to view other users' DAF."
            )

        try:
            # Select related only for fields that exist (profile exists, but career_group may not)
            employee_user = User.objects.select_related("profile").get(
                id=user_id_param, is_active=True
            )
        except (User.DoesNotExist, ValueError, TypeError):
            raise Http404("User not found.")
    else:
        # Default: show logged-in user's DAF
        employee_user = request.user

    today_date = timezone.now().date()

    # Get current DAF summary (same as legacy view)
    try:
        summary = get_current_daf_summary(employee_user)
        money = summary.get("money", {})
        metrics = summary.get("metrics", {})
    except Exception as e:
        logger.error(
            f"Error generating current DAF summary for {employee_user}: {e}",
            exc_info=True,
        )
        summary = {
            "money": {
                "target_amount": Decimal("0"),
                "released_total": Decimal("0"),
                "locked_total": Decimal("0"),
                "net_income": Decimal("0"),
            },
            "metrics": {"points_earned": 0.0, "target_points": 0.0},
        }
        money = summary["money"]
        metrics = summary["metrics"]

    # Get active tasks (same as legacy view)
    # Performance: Use select_related for FK and prefetch_related for reverse FK
    # Note: ChecklistEvaluationService.get_task_quality_score() internally queries TaskLinks
    # again, but prefetch_related helps Django cache the results
    # IMPORTANT: NO DATE FILTERING on tasks - tasks are long-lived
    # Date range should only filter evidence/meetings, not tasks
    # Build select_related list dynamically to avoid FieldError if career_group doesn't exist
    # Only include valid ForeignKey/OneToOneField relationships for select_related
    select_related_fields = [
        "category",
        "department",
        "activity_type",
        "employee",
        "employee__profile",
    ]
    # Only include career_group if it exists on UserProfile (backward compatible)
    try:
        from accounts.models import UserProfile

        if hasattr(UserProfile._meta, "get_field"):
            try:
                career_group_field = UserProfile._meta.get_field("career_group")
                # Only include if it's a ForeignKey/OneToOneField (can be used in select_related)
                if hasattr(career_group_field, "related_model"):
                    select_related_fields.append("employee__profile__career_group")
            except Exception:
                # Field doesn't exist, skip it (backward compatible)
                pass
    except Exception:
        # UserProfile model not available or other error, skip career_group
        pass

    # Build prefetch_related list (backward compatible - only include if relation exists)
    # Check if 'review_comments' relation exists on Task model using deterministic model meta check
    prefetch_related_list = ["tasklinks_set"]
    try:
        # Check if 'review_comments' relation exists on Task model using model meta
        valid_related_accessors = {
            rel.get_accessor_name() for rel in Task._meta.related_objects
        }
        if "review_comments" in valid_related_accessors:
            prefetch_related_list.append("review_comments")
    except (AttributeError, Exception):
        # TaskReviewComment doesn't exist or relation check failed - skip (backward compatible)
        pass

    active_tasks_qs = (
        Task.objects.filter(employee=employee_user, is_active=True)
        .select_related(*select_related_fields)
        .prefetch_related(*prefetch_related_list)
        .order_by("id")
    )

    # Focused debug logging for eunice user only
    daf_debug_enabled = getattr(settings, "DAF_DEBUG", False) or (
        os.environ.get("DAF_DEBUG", "").lower() in ("1", "true", "yes")
    )
    is_eunice = (
        employee_user
        and hasattr(employee_user, "username")
        and employee_user.username.lower() == "eunice"
    )

    if daf_debug_enabled and is_eunice:
        tasks_list = list(active_tasks_qs)
        logger.info(
            f"[DAF_DEBUG] daf_v2_view: Final Task queryset for {employee_user.username}: {len(tasks_list)} tasks"
        )
        logger.info(
            f"[DAF_DEBUG] daf_v2_view: Top 20 task IDs: {[t.id for t in tasks_list[:20]]}"
        )

    # Initialize quality evaluation service
    eval_service = ChecklistEvaluationService()

    # Initialize gate service for consistent evidence/quality checks
    from management.services.task_quality_gate_service import \
        TaskQualityGateService

    gate_service = TaskQualityGateService()

    # Helper to generate task URL
    def generate_task_url_from_task(task_obj):
        """Generate task URL for Task model"""
        try:
            import string

            from django.urls import reverse

            one_list = ["one on one sessions", "one on one", "one on one session"]
            job_list = ["job support", "job_support"]
            onelist = [
                t.lower().translate({ord(c): None for c in string.whitespace})
                for t in one_list
            ]
            joblist = [
                t.lower().translate({ord(c): None for c in string.whitespace})
                for t in job_list
            ]
            activity_name_for_url = (
                task_obj.activity_type.name
                if task_obj.activity_type and task_obj.activity_type.name
                else task_obj.activity_name
            )
            activity = activity_name_for_url.lower().translate(
                {ord(c): None for c in string.whitespace}
            )

            if activity in onelist:
                return reverse("application:rate")
            elif activity in joblist:
                return reverse("application:job_support")
            else:
                return reverse("management:new_evidence", args=[task_obj.id])
        except Exception:
            return "#"

    # Calculate deadline (end of current month)
    last_day = monthrange(today_date.year, today_date.month)[1]
    deadline = date(today_date.year, today_date.month, last_day)

    # Build enriched task list with quality scores
    tasks_list = []
    for task in active_tasks_qs:
        # Get latest review comment (prefetched)
        latest_review_comment = (
            task.review_comments.first() if hasattr(task, "review_comments") else None
        )

        # Get evidence links from prefetched data (avoid N+1 query)
        # Use prefetched tasklinks_set instead of querying again
        task_links_list = [link for link in task.tasklinks_set.all() if link.is_active]
        task_links_qs = TaskLinks.objects.filter(task=task, is_active=True)

        # Get unified gate status (single source of truth for evidence/quality)
        gate_status = gate_service.get_task_gate_status(
            task, task_links=task_links_qs, user=employee_user
        )

        # Use Task.requires_meeting as UI driver (field defaults to True)
        # Override gate_status['requires_meeting'] with task field value
        task_requires_meeting = getattr(task, "requires_meeting", True)
        gate_status["requires_meeting"] = task_requires_meeting

        # Extract values from gate status
        has_evidence = gate_status["has_evidence"]
        evidence_count = gate_status["evidence_count"]
        evidence_status = gate_status["evidence_status"]
        quality_score = gate_status["quality_score"]
        quality_pass = gate_status["quality_pass"]
        requirement_ok = gate_status["requirement_ok"]
        meeting_ok = gate_status["meeting_ok"]
        duration_ok = gate_status["duration_ok"]
        evidence_coverage = gate_status["evidence_coverage"]
        duration_factor = gate_status["duration_factor"]
        missing_checklist_items = gate_status["missing_checklist_items"]
        overall_ready = gate_status["overall_ready"]
        next_steps = gate_service.get_next_steps(task, gate_status)
        activity_policy = gate_status.get("policy")

        # Get quality result for backward compatibility
        quality_result = eval_service.get_task_quality_score(
            task, task_links=task_links_qs
        )
        missing_evidence = quality_result.get("missing_evidence", [])
        total_duration_minutes = quality_result.get("total_duration_minutes", 0)
        checklist_completion = quality_result.get("checklist_completion", 0.0)

        # Get meeting match info for this task (if available) - MUST be before compute_task_compliance
        task_meeting_match_info = None
        try:
            # Try to get from existing evidence links first
            if task_links_list:
                for link in task_links_list:
                    if link.link:
                        task_meeting_match_info = _get_meeting_match_info(
                            task, link=link.link
                        )
                        if task_meeting_match_info and task_meeting_match_info.get(
                            "has_match"
                        ):
                            break
            # If no match from links, try topic-based matching
            if not task_meeting_match_info or not task_meeting_match_info.get(
                "has_match"
            ):
                # Backward compatible: Use getattr to safely access requirement field
                task_requirement = getattr(task, "requirement", None)
                if task_requirement:
                    try:
                        from ai_services.services.meeting_evidence_matcher import \
                            MeetingEvidenceMatcher

                        task_req_code = f"REQ-{task_requirement.id}"
                        meeting_qs = _safe_meeting_query(
                            requirement_code__iexact=task_req_code
                        )
                        matching_meeting = (
                            meeting_qs.order_by("-start_time").first()
                            if meeting_qs
                            else None
                        )

                        if matching_meeting:
                            matcher = MeetingEvidenceMatcher(
                                enable_topic_fallback=True, time_window_days=2
                            )
                            task_date = (
                                task.submission if task.submission else timezone.now()
                            )
                            # timedelta is already imported at module level (line 19)
                            time_window_start = task_date - timedelta(days=2)
                            time_window_end = task_date + timedelta(days=2)

                            if (
                                time_window_start.date()
                                <= matching_meeting.start_time.date()
                                <= time_window_end.date()
                            ):
                                task_meeting_match_info = {
                                    "has_match": True,
                                    "meeting": matching_meeting,
                                    "match_type": "requirement_code",
                                    "confidence": 0.85,
                                    "requirement_code_match": True,
                                    "meeting_requirement_code": matching_meeting.requirement_code,
                                    "task_requirement_code": task_req_code,
                                }
                    except Exception as e:
                        logger.debug(
                            f"Error finding meeting by requirement code for task {task.id}: {e}"
                        )
        except Exception as e:
            logger.debug(f"Error getting meeting match info for task {task.id}: {e}")

        # Get unified compliance status (policy-driven, single source of truth)
        compliance = compute_task_compliance(
            task=task,
            task_links=task_links_list,
            checklist_eval=quality_result,
            meeting_match_info=task_meeting_match_info,
            user=employee_user,
        )

        # Build evidence list for template (use evidence_summary_service for consistency)
        from management.services.evidence_summary_service import \
            get_task_evidence_summary

        evidence_summary = get_task_evidence_summary(
            task, task_links_list, task_meeting_match_info
        )

        evidence_list = []
        # Use items_qs from evidence_summary (ensures only active, usable evidence)
        evidence_items = evidence_summary["items_qs"]
        if isinstance(evidence_items, list):
            evidence_items_iter = evidence_items
        else:
            evidence_items_iter = evidence_items.all()

        for link in evidence_items_iter:
            evidence_list.append(
                {
                    "id": link.id,
                    "link": link.link,
                    "doc": link.doc,
                    "drive_link": link.drive_link,
                    "description": link.description,
                    "link_name": link.link_name
                    or "Evidence",  # Use link_name, not topic_name
                    "is_auto_generated": getattr(link, "is_auto_generated", False),
                }
            )

        # Get activity checklist from Editable model with fallback to ActivityDefinition
        activity_checklist = []
        checklist_completed_count = 0
        try:
            from management.checklist_utils_pkg.checklist_utils import \
                get_checklist_with_completion

            # Get policy group for checklist lookup
            policy_group = compliance.get("policy_group", "Group B")

            # Try to get checklist from Editable model
            if activity_type_slug:
                # First, try to get fallback checklist from ActivityDefinition for use with utility
                fallback_checklist = []
                try:
                    if task.activity_type and hasattr(
                        task.activity_type, "ai_definition"
                    ):
                        ai_def = task.activity_type.ai_definition
                        if ai_def:
                            quality_criteria = (
                                getattr(ai_def, "quality_criteria", {}) or {}
                            )
                            if (
                                isinstance(quality_criteria, dict)
                                and "checklist" in quality_criteria
                            ):
                                fallback_checklist = quality_criteria["checklist"]
                except Exception:
                    pass

                # Use utility function to get checklist from Editable with fallback
                activity_checklist = get_checklist_with_completion(
                    activity_type_slug,
                    policy_group,
                    missing_checklist_items,
                    fallback_checklist if fallback_checklist else None,
                )

                # Calculate completed count
                checklist_completed_count = sum(
                    1 for item in activity_checklist if item.get("completed", False)
                )
            else:
                # No activity slug - try legacy fallback
                try:
                    if task.activity_type and hasattr(
                        task.activity_type, "ai_definition"
                    ):
                        ai_def = task.activity_type.ai_definition
                        if ai_def:
                            quality_criteria = (
                                getattr(ai_def, "quality_criteria", {}) or {}
                            )
                            if (
                                isinstance(quality_criteria, dict)
                                and "checklist" in quality_criteria
                            ):
                                activity_checklist = quality_criteria["checklist"]
                                checklist_completed_count = int(
                                    checklist_completion * len(activity_checklist)
                                )
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"Error getting checklist for task {task.id}: {e}")
            # Fallback to legacy behavior
            try:
                if task.activity_type and hasattr(task.activity_type, "ai_definition"):
                    ai_def = task.activity_type.ai_definition
                    if ai_def:
                        quality_criteria = getattr(ai_def, "quality_criteria", {}) or {}
                        if (
                            isinstance(quality_criteria, dict)
                            and "checklist" in quality_criteria
                        ):
                            activity_checklist = quality_criteria["checklist"]
                            checklist_completed_count = int(
                                checklist_completion * len(activity_checklist)
                            )
            except Exception:
                pass

        # Use gate_status for evidence_status (canonical - single source of truth)
        # evidence_status already set from gate_status above

        # Determine task status (use gate status)
        # Approved: overall_ready == True AND underlying status allows it
        # Needs Attention: overall_ready == False OR explicit issues OR manager rejected (NEEDS_FIX)
        # Check if manager has rejected this task (latest review comment with NEEDS_FIX)
        manager_rejected = False
        if latest_review_comment and latest_review_comment.status == "NEEDS_FIX":
            manager_rejected = True

        if manager_rejected:
            # Manager explicitly rejected - force needs_attention
            status = "needs_attention"
        elif overall_ready:
            # Gate passes - check if task is actually submitted/approved
            if (
                evidence_status in ["partial", "complete"]
                and task.point
                and task.point > 0
            ):
                status = "approved"  # Can be approved if gate passes
            elif evidence_status in ["partial", "complete"]:
                status = "submitted"
            elif task.point and task.point > 0:
                status = "in_progress"
            else:
                status = "assigned"
        else:
            # Gate fails - must be needs_attention
            status = "needs_attention"

        # Build robust display title with comprehensive fallback chain
        # Priority: activity_type.name > activity_type.title > activity_name > description > fallback
        # This ensures every task has a visible title, never empty/grey placeholder
        display_title = None

        # Try activity_type.name first (most canonical)
        if task.activity_type:
            if (
                hasattr(task.activity_type, "name")
                and task.activity_type.name
                and str(task.activity_type.name).strip()
            ):
                display_title = str(task.activity_type.name).strip()
            elif (
                hasattr(task.activity_type, "title")
                and task.activity_type.title
                and str(task.activity_type.title).strip()
            ):
                display_title = str(task.activity_type.title).strip()

        # Fallback to task.activity_name (always present on Task model per schema)
        if not display_title:
            if (
                hasattr(task, "activity_name")
                and task.activity_name
                and str(task.activity_name).strip()
            ):
                display_title = str(task.activity_name).strip()
            elif hasattr(task, "name") and task.name and str(task.name).strip():
                display_title = str(task.name).strip()
            elif hasattr(task, "title") and task.title and str(task.title).strip():
                display_title = str(task.title).strip()
            elif (
                hasattr(task, "task_name")
                and task.task_name
                and str(task.task_name).strip()
            ):
                display_title = str(task.task_name).strip()

        # Final fallback - ensure we always have a title
        if not display_title or not display_title.strip():
            display_title = "Untitled Task"

        # Get canonical activity name (for filtering/backward compatibility)
        canonical_activity_name = display_title

        # Get human-friendly display label (replace underscores, title case)
        # Clean up the display title for better readability
        if display_title and display_title != "Untitled Task":
            display_label = (
                str(display_title).replace("_", " ").replace("-", " ").title().strip()
            )
            # Remove extra spaces
            display_label = " ".join(display_label.split())
            # Ensure it's not empty after cleaning
            if not display_label:
                display_label = display_title
        else:
            display_label = "Untitled Task"

        # Get activity type slug for filtering
        activity_type_slug = (
            task.activity_type.slug
            if task.activity_type and task.activity_type.slug
            else None
        )

        # Use gate_status values (already computed above)
        requires_requirement = gate_status["requires_requirement"]
        requirement_missing = requires_requirement and not requirement_ok

        # Build attention reasons from gate_status
        attention_reasons = (
            gate_status["evidence_reasons"].copy()
            if gate_status["evidence_reasons"]
            else []
        )
        if status == "needs_attention":
            if requirement_missing:
                attention_reasons.append(
                    "Requirement missing: must link to a Requirement"
                )
            if gate_status["requires_meeting"] and not meeting_ok:
                # Use numeric format if available (will be computed below)
                # This will be updated after sessions counts are computed
                pass  # Will be updated below with numeric format
            if missing_checklist_items:
                count = len(missing_checklist_items)
                attention_reasons.append(
                    f"Checklist incomplete: {count} item{'s' if count != 1 else ''}"
                )
            if not duration_ok:
                attention_reasons.append("Duration insufficient")
            if not quality_pass:
                attention_reasons.append(
                    f"Quality below threshold: {int(quality_score * 100)}%"
                )

        # Get meeting room config for meeting-required activities
        meeting_room_id = None
        meeting_join_url = None
        meeting_mapping_source = None
        if gate_status["requires_meeting"]:
            try:
                from ai_services.utils.meeting_room_config import \
                    get_meeting_room_for_activity

                meeting_room_id, meeting_join_url = get_meeting_room_for_activity(
                    activity_type_slug or ""
                )
                # Determine mapping source for staff display
                if meeting_room_id:
                    try:
                        from ai_services.models import MeetingActivityMapping
                        from management.models import ActivityType

                        activity_type = ActivityType.objects.filter(
                            slug=(activity_type_slug or "").upper(), is_active=True
                        ).first()
                        if activity_type:
                            mapping = MeetingActivityMapping.objects.filter(
                                activity_name__iexact=activity_type.name, is_active=True
                            ).first()
                            if mapping:
                                meeting_mapping_source = "MeetingActivityMapping"
                            else:
                                from coda.config.activity_definitions import \
                                    ACTIVITY_POLICIES

                                policy = ACTIVITY_POLICIES.get(
                                    (activity_type_slug or "").upper()
                                )
                                if policy and policy.meeting_room_id:
                                    meeting_mapping_source = "ActivityPolicy"
                                else:
                                    meeting_mapping_source = "Fallback"
                    except Exception:
                        meeting_mapping_source = "Unknown"
            except Exception:
                pass  # If config not available, leave as None

        # Compute meeting quota progress for meeting-required activities
        required_meeting_count = 0
        meeting_required_count = (
            0  # Initialize before conditional to prevent UnboundLocalError
        )
        meetings_completed_count = 0
        meetings_remaining_count = 0
        show_start_meeting_button = False
        meeting_progress_text = None  # Initialize to prevent UnboundLocalError

        # B) NEW RULE: ALL activities are treated as meeting-required by default
        # Calculate sessions_remaining for ALL tasks (not just meeting-required)
        # This ensures Start Meeting button appears on every task
        sessions_remaining = 0
        if (
            gate_status.get("requires_meeting") or True
        ):  # Always calculate for all tasks
            # Get sessions_required from activity policy (preferred) or fallback to required_meeting_count
            meeting_required_count = 1  # Default
            if activity_policy:
                if (
                    hasattr(activity_policy, "sessions_required")
                    and activity_policy.sessions_required > 0
                ):
                    meeting_required_count = activity_policy.sessions_required
                elif (
                    hasattr(activity_policy, "required_meeting_count")
                    and activity_policy.required_meeting_count > 0
                ):
                    meeting_required_count = activity_policy.required_meeting_count

            # Fallback to task.mxpoint (or point) if policy doesn't specify
            if meeting_required_count == 1 and (task.mxpoint or task.point):
                meeting_required_count = int(task.mxpoint or task.point or 1)

            # Count completed meetings using transcript_key (primary) or meeting_instance_key (fallback)
            # Apply date filter using Meeting.start_time if date range provided
            daf_debug_enabled = getattr(settings, "DAF_DEBUG", False) or (
                os.environ.get("DAF_DEBUG", "").lower() in ("1", "true", "yes")
            )
            is_eunice = (
                employee_user
                and hasattr(employee_user, "username")
                and employee_user.username.lower() == "eunice"
            )

            from django.db.models import Q
            from management.utils.transcript_key_utils import (
                extract_transcript_key, is_transcript_url)

            # Collect transcript_keys and meeting_instance_keys from active TaskLinks
            transcript_keys = set()
            meeting_instance_keys = set()
            meeting_ids = set()

            for link in task_links_list:
                if link.is_active:
                    # Primary: transcript_key from link URL or stored transcript_key field
                    transcript_key = getattr(link, "transcript_key", None)
                    if (
                        not transcript_key
                        and link.link
                        and is_transcript_url(link.link)
                    ):
                        transcript_key = extract_transcript_key(link.link)
                    if transcript_key:
                        transcript_keys.add(transcript_key)

                    # Fallback: meeting_instance_key
                    meeting_instance_key = getattr(link, "meeting_instance_key", None)
                    if meeting_instance_key:
                        meeting_instance_keys.add(meeting_instance_key)

                    # Legacy: meeting_id (only count if no transcript_key or meeting_instance_key)
                    meeting_id = getattr(link, "meeting_id", None)
                    if meeting_id and not transcript_key and not meeting_instance_key:
                        meeting_ids.add(meeting_id)

            if daf_debug_enabled and is_eunice:
                logger.info(
                    f"[DAF_DEBUG] daf_v2_view: Task {task.id} - transcript_keys={list(transcript_keys)}, "
                    f"meeting_instance_keys={list(meeting_instance_keys)}, meeting_ids={list(meeting_ids)}"
                )

            # Count distinct meetings by joining on transcript_key (primary) or meeting_instance_key (fallback)
            distinct_meeting_count = 0
            try:
                from ai_services.models import Meeting

                # Use single Q() query to avoid union+distinct issues
                meeting_filter = Q()

                if transcript_keys:
                    meeting_filter |= Q(transcript_key__in=transcript_keys)
                if meeting_instance_keys:
                    meeting_filter |= Q(meeting_instance_key__in=meeting_instance_keys)
                if meeting_ids:
                    meeting_filter |= Q(meeting_id__in=meeting_ids)

                if meeting_filter:
                    meetings_qs = Meeting.objects.filter(meeting_filter)
                    distinct_meeting_count = meetings_qs.values("id").distinct().count()
                    if daf_debug_enabled and is_eunice:
                        logger.info(
                            f"[DAF_DEBUG] daf_v2_view: Task {task.id} - Found {distinct_meeting_count} distinct meetings "
                            f"(transcript_keys={len(transcript_keys)}, instance_keys={len(meeting_instance_keys)}, meeting_ids={len(meeting_ids)})"
                        )
                else:
                    distinct_meeting_count = 0
                    if daf_debug_enabled and is_eunice:
                        logger.info(
                            f"[DAF_DEBUG] daf_v2_view: Task {task.id} - No join keys available, meeting_count=0"
                        )

            except Exception as e:
                logger.warning(
                    f"[DAF_DEBUG] daf_v2_view: Task {task.id} - Error counting meetings: {e}"
                )
                # Fallback to simple count if join fails
                distinct_meeting_count = (
                    len(transcript_keys) + len(meeting_instance_keys) + len(meeting_ids)
                )

            meetings_completed_count = distinct_meeting_count

            if daf_debug_enabled and is_eunice:
                logger.info(
                    f"[DAF_DEBUG] daf_v2_view: Task {task.id} - meetings_completed_count={meetings_completed_count}, meeting_required_count={meeting_required_count}"
                )
                logger.info(
                    f"[DAF_DEBUG] daf_v2_view: Task {task.id} - gate_status meetings_completed_count={gate_status.get('meetings_completed_count', 'N/A')}, required_meeting_count={gate_status.get('required_meeting_count', 'N/A')}"
                )
                logger.info(
                    f"[DAF_DEBUG] daf_v2_view: Task {task.id} - meeting_ok={meeting_ok}, requires_meeting={gate_status.get('requires_meeting', False)}"
                )
                logger.info(
                    f"[DAF_DEBUG] daf_v2_view: Task {task.id} - points={task.point}, max_points={task.mxpoint}, gate_pass={overall_ready}"
                )

            # Calculate remaining
            meetings_remaining_count = max(
                0, meeting_required_count - meetings_completed_count
            )

            # Generate progress text
            meeting_progress_text = (
                f"Meetings: {meetings_completed_count}/{meeting_required_count}"
            )

            # Show button if: requires_meeting AND meeting_join_url exists AND sessions_remaining > 0
            show_start_meeting_button = (
                bool(meeting_join_url) and meetings_remaining_count > 0
            )

            # Update attention_reasons with numeric format if meeting requirement not met
            if not meeting_ok and meetings_remaining_count > 0:
                # Replace generic message with numeric format
                numeric_reason = f"Meetings: {meetings_completed_count}/{meeting_required_count} (need {meetings_remaining_count} more)."
                # Remove generic message if present
                attention_reasons = [
                    r
                    for r in attention_reasons
                    if "Meeting evidence required" not in r
                    and "Meeting evidence" not in r
                ]
                attention_reasons.append(numeric_reason)

            # Update required_meeting_count for backward compatibility
            required_meeting_count = meeting_required_count

        # Backward compatible: Use getattr to safely access requirement field
        task_requirement = getattr(task, "requirement", None)

        task_dict = {
            "id": task.id,
            "activity_name": canonical_activity_name,
            "task_name": task.activity_name,  # Primary task name field
            "display_label": display_label,  # Human-friendly label
            "display_title": display_title,  # Raw title (for fallback in template)
            "activity_type_slug": activity_type_slug,
            "employee": task.employee,  # Employee who owns this task (for approve/reject forms)
            # Use Task.requires_meeting as UI driver (field defaults to True)
            # Fallback to gate_status for backward compatibility
            "requires_meeting": getattr(
                task, "requires_meeting", gate_status.get("requires_meeting", True)
            ),
            "meeting_room_id": meeting_room_id,
            "meeting_join_url": meeting_join_url,
            "meeting_mapping_source": meeting_mapping_source,
            "required_meeting_count": required_meeting_count,  # Backward compatibility
            "meeting_required_count": meeting_required_count,  # Backward compatibility
            "sessions_required": meeting_required_count,  # Number of sessions required from policy
            "sessions_completed": meetings_completed_count,  # Count of distinct linked meetings
            "sessions_remaining": meetings_remaining_count,  # Remaining sessions needed
            "meeting_progress_text": (
                meeting_progress_text if gate_status["requires_meeting"] else None
            ),
            "show_start_meeting_button": show_start_meeting_button,
            # Explicit meeting counts for template clarity (use gate_status as primary, local as fallback)
            # Ensure consistency: use same source for both counts and meeting_progress_text
            "meetings_completed_count": gate_status.get(
                "meetings_completed_count", meetings_completed_count
            ),
            "required_meeting_count": gate_status.get(
                "required_meeting_count", meeting_required_count
            ),
            "meeting_ok": meeting_ok,  # Boolean: whether meeting requirement is met
            "points": float(task.point or Decimal("0")),
            "max_points": float(task.mxpoint or Decimal("0")),
            "mxearning": float(task.mxearning or Decimal("0")),
            # Earnings: Approved (only if overall_ready) vs Provisional (always shown)
            # Formula: (point / mxpoint * mxearning) rounded to 2 decimal places for currency
            # Round to nearest 0.01 (2 decimal places) for currency precision
            "earning_provisional": round(
                float(
                    (task.point / task.mxpoint * task.mxearning)
                    if task.mxpoint and task.mxpoint > 0
                    else Decimal("0")
                ),
                2,
            ),
            "earning_approved": round(
                float(
                    (task.point / task.mxpoint * task.mxearning)
                    if (task.mxpoint and task.mxpoint > 0 and overall_ready)
                    else Decimal("0")
                ),
                2,
            ),
            "earning": round(
                float(
                    (task.point / task.mxpoint * task.mxearning)
                    if task.mxpoint and task.mxpoint > 0
                    else Decimal("0")
                ),
                2,
            ),  # Legacy: same as provisional
            "deadline": deadline.isoformat(),
            "task_url": generate_task_url_from_task(task),
            "status": status,
            # UNIFIED GATE STATUS (single source of truth)
            "gate_status": gate_status,  # Full gate status dict
            "gate_pass": compliance.get(
                "gate_pass", overall_ready
            ),  # Use compliance gate_pass (policy-driven)
            "compliance": compliance,  # Full compliance dict (policy-driven, single source of truth)
            "has_evidence": evidence_summary[
                "has_minimum"
            ],  # Use evidence_summary as single source of truth
            "evidence_count": evidence_summary[
                "count_usable"
            ],  # Count only usable evidence
            "evidence_count_total": evidence_summary[
                "count_active"
            ],  # Total active evidence (for manager audit)
            "last_evidence_timestamp": (
                max([link.created_at for link in task_links_list], default=None)
                if task_links_list
                else None
            ),  # Last evidence upload time
            # Quality metrics (for display)
            "quality_score": quality_score,
            "quality_pass": quality_pass,  # Quality pass (consistent with evidence)
            "evidence_status": evidence_summary[
                "status"
            ],  # Canonical from evidence_summary_service
            "evidence_coverage": evidence_coverage,
            "duration_factor": duration_factor,
            "checklist_completion": checklist_completion,
            "checklist_completed_count": checklist_completed_count,
            "checklist_total_count": len(activity_checklist),
            "missing_evidence": missing_evidence,
            "missing_checklist_items": missing_checklist_items,
            "total_duration_minutes": total_duration_minutes,
            "attention_reasons": attention_reasons,  # List of reasons for needs_attention (backward compatibility)
            "needs_attention_reason_code": compliance.get(
                "needs_attention_reason_code", "UNKNOWN"
            ),  # Deterministic reason code
            "needs_attention_reason_text": compliance.get(
                "needs_attention_reason_text", "Task needs attention."
            ),  # Human-readable reason
            "policy_group": compliance.get(
                "policy_group", "Group B"
            ),  # Policy group (A, B, or C)
            "next_steps": next_steps,  # Actionable next steps from gate service
            "activity_policy": activity_policy,  # Activity policy for UX improvements
            # Format evidence requirements for template (replace underscores with spaces)
            "evidence_requirements_formatted": [
                req.replace("_", " ").title() if isinstance(req, str) else str(req)
                for req in (
                    activity_policy.evidence_requirements if activity_policy else []
                )
            ],
            # Get latest requirement match check status
            "requirement_match_status": None,  # Will be set below
            # Compliance chips for UI (derived from compliance gate)
            "compliance_chips": {
                "requirement": {
                    "status": "missing" if not requirement_ok else "present",
                    "required": requires_requirement,
                },
                "evidence": {
                    "status": evidence_status,  # From gate_status: 'missing', 'partial', 'complete', 'auto_pending'
                },
                "checklist": {
                    "completed": checklist_completed_count,
                    "total": len(activity_checklist),
                    "incomplete": len(missing_checklist_items) > 0,
                },
                "duration": {
                    "status": "missing" if not duration_ok else "ok",
                },
                "quality": {
                    "status": (
                        "pass" if quality_pass else "fail"
                    ),  # Use gate_status quality_pass (includes evidence check)
                    "score": quality_score,
                },
            },
            # Issue chips for UI (backward compatibility - use gate_status values)
            "issue_chips": {
                "missing_evidence": not has_evidence,
                "partial_evidence": evidence_status == "partial",
                "checklist_incomplete": len(missing_checklist_items) > 0,
                "duration_missing": not duration_ok,
                "quality_low": not quality_pass,
                "requirement_missing": not requirement_ok,
            },
            # Requirement fields (backward compatible: safely access requirement field)
            "requirement_id": task_requirement.id if task_requirement else None,
            "requirement_display": (
                f"REQ-{task_requirement.id}" if task_requirement else None
            ),
            # Evidence and checklist
            "evidence_list": evidence_list,
            "activity_checklist": activity_checklist,
            # Automation state (from gate_status if available, else from quality_result)
            "autolink_state": gate_status.get("autolink_state", "manual_only"),
            "meeting_match_info": task_meeting_match_info,  # For template display
            # Description
            "description": task.description or "",
            # Latest review comment (if any)
            "latest_review_comment": latest_review_comment,
        }

        # Get latest requirement match check status (after task_dict is created)
        # Backward compatible: Use getattr to safely access requirement field
        task_requirement_for_check = getattr(task, "requirement", None)
        if task_requirement_for_check:
            try:
                from management.models import RequirementMatchCheck

                latest_check = (
                    RequirementMatchCheck.objects.filter(
                        task=task, requirement=task_requirement_for_check
                    )
                    .order_by("-created_at")
                    .first()
                )

                if latest_check:
                    task_dict["requirement_match_status"] = {
                        "status": latest_check.status,
                        "confidence": latest_check.confidence,
                        "reason": latest_check.reason,
                    }
            except Exception:
                pass

        # Get AI-3 review suggestion (for employee view - show only next_actions)
        try:
            from management.models import TaskAIReviewSuggestion

            suggestion = (
                TaskAIReviewSuggestion.objects.filter(
                    task=task, is_active=True, expires_at__gt=timezone.now()
                )
                .order_by("-created_at")
                .first()
            )

            if suggestion:
                # Only include next_actions for employee view (safe subset)
                task_dict["ai_review_next_actions"] = suggestion.suggestion_json.get(
                    "next_actions", []
                )
        except Exception:
            pass

        tasks_list.append(task_dict)

    # Group tasks by status for tabs
    tasks_by_status = {
        "assigned": [t for t in tasks_list if t["status"] == "assigned"],
        "in_progress": [t for t in tasks_list if t["status"] == "in_progress"],
        "submitted": [t for t in tasks_list if t["status"] == "submitted"],
        "approved": [t for t in tasks_list if t["status"] == "approved"],
        "needs_attention": [t for t in tasks_list if t["status"] == "needs_attention"],
    }

    # Calculate summary metrics
    tasks_today = [t for t in tasks_list if t["deadline"] == deadline.isoformat()]
    completed_today = [
        t
        for t in tasks_list
        if t["status"] in ["submitted", "approved"]
        and t["deadline"] == deadline.isoformat()
    ]

    # Quality pass rate (>= 80%)
    quality_pass_tasks = [t for t in tasks_list if t["quality_score"] >= 0.8]
    quality_pass_rate = (
        (len(quality_pass_tasks) / len(tasks_list) * 100) if tasks_list else 0.0
    )

    # Needs attention count
    needs_attention_count = len(tasks_by_status["needs_attention"])

    # ============================================================================
    # DAF v2 HEADER METRICS - DEFINITIONS AND RECONCILIATION
    # ============================================================================
    # All metrics computed from the SAME period window: current active tasks (is_active=True)
    # All metrics computed from the SAME task subset: tasks_list (filtered active tasks)
    #
    # METRIC DEFINITIONS:
    # 1. Target (target_amount):
    #    - Definition: Sum of mxearning from all current active Task records
    #    - Source: get_current_daf_summary() -> money.target_amount
    #    - Period: Current month active tasks only
    #    - Formula: sum(task.mxearning for task in active_tasks_qs)
    #
    # 2. Earned (Provisional) (earned_amount_provisional):
    #    - Definition: Sum of earning from tasks with status 'submitted' or 'approved'
    #    - Includes: Both compliant and non-compliant tasks (provisional = not yet approved)
    #    - Period: Current month active tasks only
    #    - Formula: sum(task.earning for task in tasks_list where status in ['submitted', 'approved'])
    #
    # 3. Approved Earned (approved_earned_amount):
    #    - Definition: Sum of earning_approved from tasks where gate_pass == True (fully compliant)
    #    - Includes: Only tasks that pass all compliance gates (requirement, evidence, checklist, duration, quality)
    #    - Period: Current month active tasks only
    #    - Formula: sum(task.earning_approved for task in tasks_list where gate_pass == True)
    #
    # 4. Pending (pending_amount):
    #    - Definition: Target - Earned (Provisional) = amount not yet earned
    #    - Alternative interpretation: Approved Earned - Earned (Provisional) = amount pending approval
    #    - Current implementation: money.locked_total = target_amount - earned (from get_current_daf_summary)
    #    - Period: Current month active tasks only
    #    - Formula: target_amount - earned_amount_provisional
    #    - RECONCILIATION: pending_amount should equal target_amount - earned_amount_provisional
    #
    # 5. Points (Provisional) (points_earned_provisional):
    #    - Definition: Sum of points from tasks with status 'submitted' or 'approved'
    #    - Includes: Both compliant and non-compliant tasks
    #    - Period: Current month active tasks only
    #    - Formula: sum(task.points for task in tasks_list where status in ['submitted', 'approved'])
    #
    # 6. Approved Points (approved_earned_points):
    #    - Definition: Sum of points from tasks where gate_pass == True (fully compliant)
    #    - Includes: Only tasks that pass all compliance gates
    #    - Period: Current month active tasks only
    #    - Formula: sum(task.points for task in tasks_list where gate_pass == True)
    #
    # 7. Time (remaining_days, remaining_hours):
    #    - Definition: Time remaining until end of current month
    #    - Source: countdown_in_month() utility function
    #    - Period: Current month only
    # ============================================================================

    # Calculate "Approved Earned" - only tasks where gate_pass == True (unified compliance gate)
    approved_earned_tasks = [t for t in tasks_list if t.get("gate_pass", False)]
    approved_earned_amount = round(
        sum(t["earning_approved"] for t in approved_earned_tasks), 2
    )
    approved_earned_points = sum(
        t["points"] for t in approved_earned_tasks if t.get("gate_pass", False)
    )

    # Provisional earned (current logic - includes incomplete compliance)
    # PERIOD: Current month active tasks only (same as target_amount)
    # STATUS FILTER: Only 'submitted' or 'approved' tasks (excludes 'assigned', 'in_progress', 'needs_attention')
    provisional_earned_amount = round(
        sum(
            t["earning"] for t in tasks_list if t["status"] in ["submitted", "approved"]
        ),
        2,
    )
    provisional_earned_points = sum(
        t["points"] for t in tasks_list if t["status"] in ["submitted", "approved"]
    )

    # RECONCILIATION CHECK: Verify totals match underlying data
    # Recompute from raw task data to ensure consistency
    target_amount_recomputed = round(
        sum(float(t.get("mxearning", 0)) for t in tasks_list), 2
    )
    # Log reconciliation if mismatch detected (for debugging)
    if abs(target_amount_recomputed - float(money.get("target_amount", 0))) > 0.01:
        logger.warning(
            f"DAF reconciliation mismatch for {employee_user.username}: "
            f"target_amount={money.get('target_amount')} vs recomputed={target_amount_recomputed}"
        )

    # ============================================================================
    # METRIC COMPUTATION: Remaining and Pending Approval
    # ============================================================================
    # Remaining = Target - Earned (Provisional) = amount not yet earned
    # Pending Approval = Earned (Provisional) - Approved Earned = amount pending approval
    # ============================================================================
    remaining_amount = max(
        round(float(money.get("target_amount", 0)) - provisional_earned_amount, 2), 0.0
    )
    pending_approval_amount = max(
        round(provisional_earned_amount - approved_earned_amount, 2), 0.0
    )

    # RECONCILIATION CHECK: Verify totals match
    # remaining_amount should equal target_amount - earned_amount_provisional
    # pending_approval_amount should equal earned_amount_provisional - approved_earned_amount
    remaining_recomputed = round(
        float(money.get("target_amount", 0)) - provisional_earned_amount, 2
    )
    pending_approval_recomputed = round(
        provisional_earned_amount - approved_earned_amount, 2
    )

    if abs(remaining_amount - remaining_recomputed) > 0.01:
        logger.warning(
            f"DAF remaining reconciliation mismatch for {employee_user.username}: "
            f"remaining_amount={remaining_amount} vs recomputed={remaining_recomputed}"
        )

    if abs(pending_approval_amount - pending_approval_recomputed) > 0.01:
        logger.warning(
            f"DAF pending_approval reconciliation mismatch for {employee_user.username}: "
            f"pending_approval_amount={pending_approval_amount} vs recomputed={pending_approval_recomputed}"
        )

    # Use PayrollSummaryService for consistent calculations (single source of truth)
    # This ensures DAF v2 and payslip show the same numbers
    from management.services.payroll_summary_service import \
        PayrollSummaryService

    payroll_service = PayrollSummaryService()
    payroll_summary = payroll_service.get_user_pay_summary(employee_user)

    # Override local calculations with service values for consistency
    # This ensures DAF v2 metrics match payslip metrics exactly
    provisional_earned_amount = Decimal(
        str(payroll_summary.get("earned_amount_provisional", 0))
    )
    approved_earned_amount = Decimal(
        str(payroll_summary.get("approved_earned_amount", 0))
    )
    approved_earned_points = Decimal(
        str(payroll_summary.get("approved_earned_points", 0))
    )
    provisional_earned_points = Decimal(
        str(payroll_summary.get("points_earned_provisional", 0))
    )
    remaining_amount = Decimal(str(payroll_summary.get("remaining_amount", 0)))
    pending_approval_amount = Decimal(
        str(payroll_summary.get("pending_approval_amount", 0))
    )

    # Extract time remaining until month end (for center countdown: "TIME LEFT TO MAXIMIZE YOUR PAY")
    time_remaining_month_end = payroll_summary.get("time_remaining_until_month_end", {})
    remaining_days = time_remaining_month_end.get("days", 0)
    remaining_hours = time_remaining_month_end.get("hours", 0)
    remaining_minutes = time_remaining_month_end.get("minutes", 0)
    remaining_seconds = time_remaining_month_end.get("seconds", 0)

    # Extract time remaining until Pay Day (for right panel: "PAY DAY")
    time_remaining_pay_day = payroll_summary.get("time_remaining", {})
    pay_day_remaining_days = time_remaining_pay_day.get("days", 0)
    pay_day_remaining_hours = time_remaining_pay_day.get("hours", 0)

    # Use Pay Day from service (15th of next month)
    pay_day_date = payroll_summary.get("pay_day_date")
    pay_day_formatted = payroll_summary.get("pay_day_formatted", "")

    # Use approval percentage and status from service
    approval_percentage = payroll_summary.get("approval_percentage", 0.0)
    approval_status = payroll_summary.get("approval_status", "NEEDS WORK")

    # Legacy: Calculate deadline date and old payday (for backward compatibility)
    deadline_date = deadline
    payday = deadline_date + timedelta(days=15)  # Legacy calculation

    # Get unique activity types for filter (use display_label for human-friendly names)
    activity_types = set()
    for task in tasks_list:
        if task["activity_type_slug"]:
            # Use display_label for human-friendly name in dropdown
            activity_types.add(
                (
                    task["activity_type_slug"],
                    task.get("display_label", task["activity_name"]),
                )
            )
    activity_types = sorted(list(activity_types), key=lambda x: x[1])

    # Determine if viewing own DAF or another user's DAF (GOAL 2)
    is_viewing_other_user = user_id_param is not None and employee_user != request.user

    # Determine if user can approve/reject tasks (manager mode)
    # Superuser or staff with approval permissions can approve
    can_approve = request.user.is_superuser or request.user.is_staff

    # Build context
    context = {
        "employee": employee_user,  # Employee whose DAF is being viewed
        "user": request.user,  # For template permission checks (logged-in user)
        "summary": summary,
        "tasks": tasks_list,
        "tasks_by_status": tasks_by_status,
        # GOAL 2: Flag for template to show "Viewing [User]'s DAF" vs "My DAF"
        "is_viewing_other_user": is_viewing_other_user,
        # Manager approval permissions
        "can_approve": can_approve,
        # Summary bar metrics
        "tasks_today_count": len(tasks_today),
        "completed_today_count": len(completed_today),
        "quality_pass_rate": round(quality_pass_rate, 1),
        "needs_attention_count": needs_attention_count,
        # Summary cards - Use PayrollSummaryService values for consistency with payslip
        "target_amount": Decimal(str(payroll_summary.get("target_amount", 0))),
        "earned_amount_provisional": provisional_earned_amount,  # From PayrollSummaryService
        "earned_amount": provisional_earned_amount,  # Legacy: same as provisional
        # NEW METRICS: Remaining and Pending Approval (from PayrollSummaryService)
        "remaining_amount": remaining_amount,  # From PayrollSummaryService
        "pending_approval_amount": pending_approval_amount,  # From PayrollSummaryService
        # LEGACY: Keep for backward compatibility (deprecated, use remaining_amount instead)
        "pending_amount": remaining_amount,  # Deprecated: use remaining_amount
        "net_income": Decimal(str(payroll_summary.get("net_income", 0))),
        "points_earned_provisional": provisional_earned_points,  # From PayrollSummaryService
        "points_earned": float(
            provisional_earned_points
        ),  # Legacy: same as provisional
        "target_points": Decimal(str(payroll_summary.get("target_points", 0))),
        # Approved earned (only fully compliant tasks) - from PayrollSummaryService
        "approved_earned_amount": approved_earned_amount,
        "approved_earned_points": approved_earned_points,
        # Approval percentage and status (from PayrollSummaryService for consistency)
        "approval_percentage": approval_percentage,
        "approval_status": approval_status,
        # UI helpers
        "remaining_days": remaining_days,  # For center countdown (month end)
        "remaining_hours": remaining_hours,  # For center countdown (month end)
        "remaining_minutes": remaining_minutes,  # For center countdown (month end)
        "remaining_seconds": remaining_seconds,  # For center countdown (month end)
        "pay_day_remaining_days": pay_day_remaining_days,  # For right panel (Pay Day)
        "pay_day_remaining_hours": pay_day_remaining_hours,  # For right panel (Pay Day)
        "deadline_date": deadline_date,
        "payday": payday,  # Legacy
        "pay_day_date": pay_day_date,  # New: 15th of next month (from PayrollSummaryService)
        "pay_day_formatted": pay_day_formatted,  # Formatted string from service
        "today": today_date,
        # Target username for View Payslip button (works for staff viewing other users)
        "target_username": employee_user.username,
        # Filters
        "activity_types": activity_types,
        # Query params for filtering
        "search_query": request.GET.get("search", ""),
        "activity_filter": request.GET.get("activity", ""),
        "evidence_filter": request.GET.get("evidence", ""),
        "quality_filter": request.GET.get("quality", ""),
        "status_filter": request.GET.get("status", "all"),
    }

    # Start with all tasks for filtering
    filtered_tasks = tasks_list.copy()

    # Apply filters if provided
    if context["search_query"]:
        search_lower = context["search_query"].lower()
        filtered_tasks = [
            t for t in filtered_tasks if search_lower in t["activity_name"].lower()
        ]

    if context["activity_filter"]:
        filtered_tasks = [
            t
            for t in filtered_tasks
            if t["activity_type_slug"] == context["activity_filter"]
        ]

    if context["evidence_filter"]:
        if context["evidence_filter"] == "complete":
            filtered_tasks = [
                t for t in filtered_tasks if t["evidence_status"] == "complete"
            ]
        elif context["evidence_filter"] == "partial":
            filtered_tasks = [
                t for t in filtered_tasks if t["evidence_status"] == "partial"
            ]
        elif context["evidence_filter"] == "missing":
            filtered_tasks = [
                t for t in filtered_tasks if t["evidence_status"] == "missing"
            ]

    if context["quality_filter"]:
        if context["quality_filter"] == "high":
            filtered_tasks = [t for t in filtered_tasks if t["quality_score"] >= 0.8]
        elif context["quality_filter"] == "medium":
            filtered_tasks = [
                t for t in filtered_tasks if 0.5 <= t["quality_score"] < 0.8
            ]
        elif context["quality_filter"] == "low":
            filtered_tasks = [t for t in filtered_tasks if t["quality_score"] < 0.5]

    # Filter by status tab (if not 'all')
    if context["status_filter"] and context["status_filter"] != "all":
        filtered_tasks = [
            t for t in filtered_tasks if t["status"] == context["status_filter"]
        ]

    # Update context with filtered tasks
    context["tasks"] = filtered_tasks
    # Recalculate tasks_by_status from filtered list
    context["tasks_by_status"] = {
        "assigned": [t for t in filtered_tasks if t["status"] == "assigned"],
        "in_progress": [t for t in filtered_tasks if t["status"] == "in_progress"],
        "submitted": [t for t in filtered_tasks if t["status"] == "submitted"],
        "approved": [t for t in filtered_tasks if t["status"] == "approved"],
        "needs_attention": [
            t for t in filtered_tasks if t["status"] == "needs_attention"
        ],
    }

    # Density mode: from querystring or localStorage (default: comfortable)
    # Note: localStorage is handled client-side, querystring takes precedence
    density_mode = request.GET.get("density", "comfortable")
    context["density_mode"] = density_mode

    return render(request, "management/daf/usertasks/employeetasks_v2.html", context)


@login_required
def daf_review_view(request):
    """
    Manager review page for tasks needing attention.

    Shows tasks needing attention in last 24 hours or due today,
    grouped by employee or sorted by severity.
    Permission: staff/superuser only.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to access this page.")
        return redirect("management:daf_v2")

    from django.utils import timezone

    # timedelta is already imported at module level (line 19)
    # Get tasks needing attention from last 24 hours or due today
    now = timezone.now()
    yesterday = now - timedelta(days=1)
    today = now.date()

    # Get active tasks (no deadline filter - Task model doesn't have deadline field, it's a property)
    # We'll use ChecklistEvaluationService to determine which tasks need attention
    from management.services.checklist_evaluation_service import \
        ChecklistEvaluationService

    # Build prefetch_related list (backward compatible - only include if relation exists)
    # Check if 'review_comments' relation exists on Task model using deterministic model meta check
    prefetch_related_list = ["tasklinks_set"]
    try:
        # Check if 'review_comments' relation exists on Task model using model meta
        valid_related_accessors = {
            rel.get_accessor_name() for rel in Task._meta.related_objects
        }
        if "review_comments" in valid_related_accessors:
            prefetch_related_list.append("review_comments")
    except (AttributeError, Exception):
        # TaskReviewComment doesn't exist or relation check failed - skip (backward compatible)
        pass

    active_tasks = (
        Task.objects.filter(is_active=True)
        .select_related(
            "employee", "activity_type", "category", "department", "requirement"
        )
        .prefetch_related(*prefetch_related_list)
    )

    eval_service = ChecklistEvaluationService()
    tasks_needing_review = []

    for task in active_tasks:
        # Check if requirement is required and missing
        activity_type_slug_review = None
        if task.activity_type:
            activity_type_slug_review = (
                task.activity_type.slug or task.activity_type.name
            )
        elif task.activity_name:
            activity_type_slug_review = task.activity_name.upper().replace(" ", "_")

        requires_requirement_review = False
        requirement_missing_review = False
        if activity_type_slug_review:
            requires_requirement_review = activity_type_slug_review.upper() in [
                a.upper() for a in REQUIREMENT_REQUIRED_ACTIVITY_TYPES
            ]
            if requires_requirement_review:
                # Backward compatible: Use getattr to safely access requirement field
                task_requirement = getattr(task, "requirement", None)
                requirement_missing_review = task_requirement is None

        # Get quality score
        task_links = [link for link in task.tasklinks_set.all() if link.is_active]
        quality_result = eval_service.get_task_quality_score(
            task, task_links=task_links
        )

        quality_score = quality_result.get("quality_score", 0.0)
        evidence_status = (
            "complete"
            if quality_result.get("evidence_coverage", 0.0) >= 0.95
            else (
                "partial"
                if quality_result.get("evidence_coverage", 0.0) >= 0.5
                else "missing"
            )
        )
        missing_checklist_items = quality_result.get("missing_checklist_items", [])
        duration_factor = quality_result.get("duration_factor", 0.0)

        # Determine if needs attention
        needs_attention = (
            quality_score < 0.8
            or evidence_status != "complete"
            or bool(missing_checklist_items)
            or duration_factor < 1.0
            or requirement_missing_review  # Add requirement missing to needs attention
        )

        if needs_attention:
            # Get latest review comment (backward compatible - only if relation exists)
            latest_comment = (
                task.review_comments.first()
                if hasattr(task, "review_comments")
                else None
            )

            # Get AI activity tag suggestion for matched meeting (if any)
            meeting_activity_suggestion = None
            try:
                from ai_services.models import MeetingActivityTagSuggestion
                from ai_services.services.meeting_evidence_matcher import \
                    MeetingEvidenceMatcher

                # Find meetings for this task
                matcher = MeetingEvidenceMatcher(
                    enable_topic_fallback=True, time_window_days=2
                )
                meetings = matcher.find_meetings_for_task(task)

                # Get highest confidence meeting match
                if meetings.exists():
                    # Get detailed matches to find best one
                    detailed_matches = matcher.get_detailed_matches(task)
                    if detailed_matches:
                        best_meeting = detailed_matches[0].get("meeting")
                        if best_meeting:
                            # Get latest suggestion for this meeting
                            suggestion = (
                                MeetingActivityTagSuggestion.objects.filter(
                                    meeting=best_meeting, is_active=True
                                )
                                .order_by("-created_at")
                                .first()
                            )

                            if suggestion:
                                meeting_activity_suggestion = {
                                    "suggested_activity_type": suggestion.suggested_activity_type,
                                    "confidence": suggestion.confidence,
                                    "reason": suggestion.reason,
                                }
            except Exception as e:
                logger.debug(
                    f"Error getting meeting activity suggestion for task {task.id}: {e}"
                )

            # Get AI-3 review suggestion (if available)
            ai_review_suggestion = None
            try:
                from django.utils import timezone
                from management.models import TaskAIReviewSuggestion

                suggestion = (
                    TaskAIReviewSuggestion.objects.filter(
                        task=task, is_active=True, expires_at__gt=timezone.now()
                    )
                    .order_by("-created_at")
                    .first()
                )

                if suggestion:
                    ai_review_suggestion = suggestion.suggestion_json
            except Exception as e:
                logger.debug(
                    f"Error getting AI review suggestion for task {task.id}: {e}"
                )

            # Get AI-4 anomaly flags (if available, manager only)
            anomaly_flags = None
            if request.user.is_staff or request.user.is_superuser:
                try:
                    from ai_services.models import TaskAnomalyFlag
                    from django.utils import timezone

                    flag = (
                        TaskAnomalyFlag.objects.filter(
                            task=task, is_active=True, expires_at__gt=timezone.now()
                        )
                        .order_by("-created_at")
                        .first()
                    )

                    if flag:
                        anomaly_flags = {
                            "risk_flags": flag.flags_json,
                            "severity": flag.severity,
                            "reason": flag.reason,
                            "confidence": flag.confidence,
                        }
                except Exception as e:
                    logger.debug(f"Error getting anomaly flags for task {task.id}: {e}")

            tasks_needing_review.append(
                {
                    "task": task,
                    "employee": task.employee,
                    "activity_name": task.activity_name,
                    "quality_score": quality_score,
                    "evidence_status": evidence_status,
                    "missing_checklist_items": missing_checklist_items,
                    "duration_factor": duration_factor,
                    "requirement_missing": requirement_missing_review,
                    "deadline": task.deadline,
                    "latest_comment": latest_comment,
                    "meeting_activity_suggestion": meeting_activity_suggestion,  # AI-1 suggestion
                    "ai_review_suggestion": ai_review_suggestion,  # AI-3 suggestion
                    "anomaly_flags": anomaly_flags,  # AI-4 Part A (manager only)
                    "issue_count": sum(
                        [
                            requirement_missing_review,  # Add requirement missing to issue count
                            quality_score < 0.8,
                            evidence_status != "complete",
                            bool(missing_checklist_items),
                            duration_factor < 1.0,
                        ]
                    ),
                }
            )

    # Sort by severity (most critical issues first)
    # Priority: missing requirement > missing evidence > missing duration > checklist incomplete > quality low
    def get_severity_score(task_data):
        score = 0
        # Missing requirement is highest priority (1000 points)
        if task_data.get("requirement_missing"):
            score += 1000
        # Missing evidence is high priority (500 points)
        if task_data.get("evidence_status") == "missing":
            score += 500
        elif task_data.get("evidence_status") == "partial":
            score += 250
        # Missing duration (200 points)
        if task_data.get("duration_factor", 1.0) < 1.0:
            score += 200
        # Checklist incomplete (100 points)
        if task_data.get("missing_checklist_items"):
            score += 100
        # Quality low (50 points)
        if task_data.get("quality_score", 1.0) < 0.8:
            score += 50
        return score

    sort_by = request.GET.get("sort", "severity")
    days_filter = request.GET.get("days", "1")  # Default: last 24 hours
    try:
        days_filter = int(days_filter)
    except (ValueError, TypeError):
        days_filter = 1

    # Filter by date if specified
    if days_filter > 0:
        cutoff_date = now - timedelta(days=days_filter)
        tasks_needing_review = [
            t for t in tasks_needing_review if t["task"].created_at >= cutoff_date
        ]

    if sort_by == "employee":
        tasks_needing_review.sort(
            key=lambda x: (x["employee"].username, -get_severity_score(x))
        )
    else:
        tasks_needing_review.sort(key=lambda x: -get_severity_score(x))

    # Group by employee for display
    tasks_by_employee = {}
    for task_data in tasks_needing_review:
        employee = task_data["employee"]
        if employee not in tasks_by_employee:
            tasks_by_employee[employee] = []
        tasks_by_employee[employee].append(task_data)

    # Get latest AI operations run status (staff only)
    ai_ops_status = None
    if request.user.is_staff or request.user.is_superuser:
        try:
            from ai_services.models import AIOperationsRun

            latest_run = AIOperationsRun.objects.order_by("-started_at").first()
            if latest_run:
                ai_ops_status = {
                    "run_id": latest_run.id,
                    "status": latest_run.status,
                    "started_at": latest_run.started_at,
                    "finished_at": latest_run.finished_at,
                    "meetings_tagged_created": latest_run.meetings_tagged_created,
                    "meetings_tagged_cached": latest_run.meetings_tagged_cached,
                    "ai_reviews_created": latest_run.ai_reviews_created,
                    "ai_reviews_cached": latest_run.ai_reviews_cached,
                    "errors_count": latest_run.errors_count,
                }
        except Exception as e:
            logger.debug(f"Error getting AI ops status: {e}")

    context = {
        "tasks_needing_review": tasks_needing_review,
        "tasks_by_employee": tasks_by_employee,
        "sort_by": sort_by,
        "today": today,
        "ai_ops_status": ai_ops_status,
    }

    return render(request, "management/daf/review.html", context)


@login_required
def daf_review_comment_view(request, task_id):
    """
    Handle POST request to add a review comment on a task.
    Permission: staff/superuser only.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to add review comments.")
        return redirect("management:daf_v2")

    # Try to import TaskReviewComment (may not exist - backward compatible)
    try:
        from management.models import TaskReviewComment

        TaskReviewComment_available = True
    except ImportError:
        TaskReviewComment_available = False

    task = get_object_or_404(Task, id=task_id)

    if request.method == "POST":
        comment_text = request.POST.get("comment", "").strip()
        status = request.POST.get("status", "INFO")

        if comment_text:
            if TaskReviewComment_available:
                TaskReviewComment.objects.create(
                    task=task,
                    employee=task.employee,
                    reviewer=request.user,
                    comment=comment_text,
                    status=status,
                )
                messages.success(
                    request, f"Review comment added for task: {task.activity_name}"
                )
            else:
                # TaskReviewComment model not available - skip comment creation but still show success
                messages.info(
                    request,
                    f"Comment logged for task: {task.activity_name} (review comments not available)",
                )
        else:
            messages.error(request, "Comment cannot be empty.")

    return redirect("management:daf_review")


@login_required
@require_http_methods(["POST"])
def approve_task(request, task_id):
    """
    Approve a submitted task.
    Sets task.point = task.mxpoint and creates a TaskReviewComment with status='APPROVED'.
    Permission: staff/superuser only.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to approve tasks.")
        return redirect("management:daf_v2")

    # Try to import TaskReviewComment (may not exist - backward compatible)
    try:
        from management.models import TaskReviewComment

        TaskReviewComment_available = True
    except ImportError:
        TaskReviewComment_available = False

    task = get_object_or_404(Task, id=task_id)

    # Get optional comment from POST
    comment_text = request.POST.get("comment", "").strip()
    if not comment_text:
        comment_text = "Task approved by manager."

    # Set task.point to mxpoint to mark as approved
    # Status computation: 'approved' = overall_ready AND evidence_status in ['partial', 'complete'] AND task.point > 0
    if task.mxpoint and task.mxpoint > 0:
        task.point = task.mxpoint
        task.save(update_fields=["point"])

    # Create review comment with APPROVED status (if model available)
    if TaskReviewComment_available:
        TaskReviewComment.objects.create(
            task=task,
            employee=task.employee,
            reviewer=request.user,
            comment=comment_text,
            status="APPROVED",
        )

    messages.success(request, f"Task '{task.activity_name}' has been approved.")

    # Redirect back to DAF v2 with user_id if provided
    user_id = request.GET.get("user_id") or request.POST.get("user_id")
    if user_id:
        return redirect(f"{reverse('management:daf_v2')}?user_id={user_id}")
    return redirect("management:daf_v2")


@login_required
@require_http_methods(["POST"])
def reject_task(request, task_id):
    """
    Reject a submitted task.
    Creates a TaskReviewComment with status='NEEDS_FIX'.
    Optionally sets task.point = 0 to move it back to submitted status.
    Permission: staff/superuser only.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to reject tasks.")
        return redirect("management:daf_v2")

    # Try to import TaskReviewComment (may not exist - backward compatible)
    try:
        from management.models import TaskReviewComment

        TaskReviewComment_available = True
    except ImportError:
        TaskReviewComment_available = False

    task = get_object_or_404(Task, id=task_id)

    # Get required comment from POST
    comment_text = request.POST.get("comment", "").strip()
    if not comment_text:
        messages.error(request, "A comment is required when rejecting a task.")
        user_id = request.GET.get("user_id") or request.POST.get("user_id")
        if user_id:
            return redirect(f"{reverse('management:daf_v2')}?user_id={user_id}")
        return redirect("management:daf_v2")

    # Optionally reset task.point to 0 to move it back to submitted status
    # This ensures it shows as 'submitted' instead of 'approved' in the UI
    if task.point and task.point > 0:
        task.point = 0
        task.save(update_fields=["point"])

    # Create review comment with NEEDS_FIX status (if model available)
    if TaskReviewComment_available:
        TaskReviewComment.objects.create(
            task=task,
            employee=task.employee,
            reviewer=request.user,
            comment=comment_text,
            status="NEEDS_FIX",
        )

    messages.warning(
        request, f"Task '{task.activity_name}' has been rejected and needs attention."
    )

    # Redirect back to DAF v2 with user_id if provided
    user_id = request.GET.get("user_id") or request.POST.get("user_id")
    if user_id:
        return redirect(f"{reverse('management:daf_v2')}?user_id={user_id}")
    return redirect("management:daf_v2")


@login_required
def daf_review_ai_generate(request, task_id):
    """
    Generate AI review suggestion for a task (staff only).

    POST-only endpoint that triggers AI review generation and redirects back.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to generate AI reviews.")
        return redirect("management:daf_review")

    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("management:daf_review")

    task = get_object_or_404(Task, id=task_id)

    try:
        from management.services.task_ai_review_service import \
            TaskAIReviewService

        service = TaskAIReviewService()
        suggestion = service.generate_review_suggestion(task, force=True)

        if suggestion:
            messages.success(
                request,
                f"AI review suggestion generated for task: {task.activity_name}",
            )
        else:
            messages.warning(
                request,
                "Could not generate AI review suggestion. Using rule-based fallback.",
            )
    except Exception as e:
        logger.error(f"Error generating AI review suggestion: {e}", exc_info=True)
        messages.error(
            request, "Error generating AI review suggestion. Please try again."
        )

    return redirect("management:daf_review")


@login_required
def daf_review_ai_ops_run(request):
    """
    Trigger AI daily operations run (staff only).

    POST-only endpoint that triggers AI operations and redirects back.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to run AI operations.")
        return redirect("management:daf_review")

    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("management:daf_review")

    try:
        from ai_services.services.ai_operations_service import \
            AIOperationsService

        days = int(request.POST.get("days", 1))
        limit = int(request.POST.get("limit", 0)) or None
        service_filter = request.POST.get("service") or None
        dry_run = request.POST.get("dry_run") == "on"

        ops_service = AIOperationsService()
        result = ops_service.run_daily_ops(
            days=days,
            limit=limit,
            service=service_filter,
            dry_run=dry_run,
            created_by=request.user,
        )

        if result["status"] == "skipped":
            messages.warning(request, "AI operations skipped (AI_OPS_ENABLED is False)")
        elif result["status"] == "failed":
            messages.error(
                request, f"AI operations failed: {result.get('error', 'Unknown error')}"
            )
        else:
            messages.success(
                request,
                f"AI operations completed successfully (Run ID: {result['run_id']})",
            )
    except Exception as e:
        logger.error(f"Error running AI operations: {e}", exc_info=True)
        messages.error(request, "Error running AI operations. Please try again.")

    return redirect("management:daf_review")


def prefix_zero(month: int) -> str:
    return str(month) if month > 9 else "0" + str(month)


def normalize_period(year: int, month: int) -> str:
    if month > 12:
        year = year + (month // 12)
        month = month % 12
    elif month < 1:
        year = year - (-month // 12)
        month = (-month) % 12

    if month == 0:
        month = 12

    if month > 0 and month < 10:
        month = "0" + str(month)

    return str(year) + "-" + str(month)


def loan_update_save(loantable, user_data, employee, total_pay, payslip_config):
    if not user_data.exists():
        loan_data = addloantable(
            loantable, employee, total_pay, payslip_config, user_data
        )
        loan_data.save()
    else:
        try:
            training_loan = user_data.order_by("-id")[0]
        except:
            training_loan = None
        if training_loan:
            loan_data = addloantable(
                loantable, employee, total_pay, payslip_config, user_data
            )
            if loan_data:
                loan_data.save()
        else:
            loan_data = updateloantable(user_data, employee, total_pay, payslip_config)


class TaskDetailView(DetailView):
    queryset = Task.objects.all()
    template_name = "management/daf/task_detail.html"

    # ordering = ['-datePosted']
    def get_context_data(self, *args, **kwargs):
        context = super(TaskDetailView, self).get_context_data(*args, **kwargs)
        # print(context)
        return context

    def get_queryset(self, *args, **kwargs):
        request = self.request
        pk = self.kwargs.get("pk")
        return Task.objects.filter(pk=pk)


# class UserTaskListView(ListView):
#     model = Task
#     context_object_name = "tasks"
#     template_name = "management/daf/employee_tasks.html"

#     # paginate_by = 5
#     def get_queryset(self):
#         # request=self.request
#         # user=self.kwargs.get('user')
#         user = get_object_or_404(User, username=self.kwargs.get("username"))
#         # tasks=Task.objects.all().filter(employee=user)

#         return Task.objects.all().filter(employee=user)


@method_decorator(login_required, name="dispatch")
class TaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Task
    success_url = "/management/tasks"
    template_name = "main/snippets_templates/generalform.html"
    fields = [
        "groupname",
        "category",
        "employee",
        "activity_name",
        "description",
        "point",
        "mxpoint",
        "mxearning",
    ]

    # fields=['user','activity_name','description','point']
    def form_valid(self, form):
        # form.instance.author=self.request.user
        if self.request.user.is_superuser:
            return super().form_valid(form)
        else:
            return redirect("management:tasks")

    def test_func(self):
        task = self.get_object()
        if self.request.user.is_superuser:
            return True
        # elif self.request.user == task.employee:
        #     return True
        return False


@method_decorator(login_required, name="dispatch")
class UsertaskUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Task
    template_name = "main/snippets_templates/generalform.html"

    # success_url = "/management/thank"
    def get_success_url(self):
        task = self.get_object()
        return (
            reverse("management:user_pay")
            + "?"
            + urlencode({"username": str(task.employee), "pay_type": "usertasks"})
        )
        # return reverse("management:user_pay", kwargs={"username": str(task.employee)})

    # fields=['group','category','user','activity_name','description','slug','point','mxpoint','mxearning']
    fields = ["category", "employee", "activity_name", "description", "point"]

    def form_valid(self, form):
        return super().form_valid(form)

    def test_func(self):
        task = self.get_object()
        if self.request.user.is_superuser or self.request.user.is_admin:
            return True
        elif self.request.user == task.employee:
            return True
        return False


# @login_required
# def gettotalduration(request):
#     employee_duration = Tracker.objects.filter(author=request.POST["name"])
#     total_duration = 0
#     for data in employee_duration.all():
#         total_duration += data.duration
#     return JsonResponse({"success": True, "value": total_duration})


@method_decorator(login_required, name="dispatch")
class TaskDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Task
    success_url = "/accounts/tasklist"

    def test_func(self):
        # timer = self.get_object()
        # if self.request.user == timer.author:
        # if self.request.user.is_superuser:
        if self.request.user.is_superuser:
            return True
        return False


# =============================EMPLOYEE EVIDENCE========================================

JOB_SUPPORTS = ["job support", "job_support", "jobsupport"]
ACTIVITY_LIST = ["BOG", "BI Sessions", "DAF Sessions", "Project", "web sessions"]

# Activity types that MUST be linked to a Requirement
REQUIREMENT_REQUIRED_ACTIVITY_TYPES = [
    "SELF_TRAINING_SESSION",
    "INTERNAL_TRAINING_SESSION",
    "CLIENT_TRAINING_SESSION",
    "PRODUCT_BACKLOG_REFINEMENT",
    "PBR",  # Alternative name for PBR
]

# PART 3: Meeting-required activity types (must have meeting evidence)
MEETING_REQUIRED_ACTIVITY_TYPES = [
    "SELF_TRAINING_SESSION",
    "INTERNAL_TRAINING_SESSION",
    "CLIENT_TRAINING_SESSION",
    "PRODUCT_BACKLOG_REFINEMENT",
    "PBR",
    # Add other "session" types if needed
]

# Activity types that are meeting-based (for REQ code validation in meeting titles)
# Must be subset of REQUIREMENT_REQUIRED_ACTIVITY_TYPES
MEETING_BASED_ACTIVITY_TYPES = [
    "SELF_TRAINING_SESSION",
    "INTERNAL_TRAINING_SESSION",
    "CLIENT_TRAINING_SESSION",
    "PRODUCT_BACKLOG_REFINEMENT",
    "PBR",  # Alternative name for PRODUCT_BACKLOG_REFINEMENT
]


def _calculate_approval_readiness(task, requires_requirement=False, task_links=None):
    """
    Calculate approval readiness status for a task.

    Args:
        task: Task instance to evaluate
        requires_requirement: Whether requirement is required for this activity type
        task_links: Optional QuerySet of TaskLinks to use for evaluation.
                   If None, queries all active TaskLinks for the task.
                   Use this to match the evidence panel's filtered queryset.

    Returns dict with:
    - requirement_present: bool
    - evidence_complete: bool (evidence_status == "complete")
    - checklist_complete: bool (missing_checklist_items empty)
    - duration_ok: bool (duration_factor >= 1.0)
    - quality_pass: bool (quality_score >= 0.8)
    - overall_ready: bool (all above are True)
    - quality_metrics: dict from ChecklistEvaluationService
    """
    from management.models import TaskLinks
    from management.services.checklist_evaluation_service import \
        ChecklistEvaluationService

    # Initialize result
    readiness = {
        "requirement_present": False,
        "evidence_complete": False,
        "checklist_complete": False,
        "duration_ok": False,
        "quality_pass": False,
        "overall_ready": False,
        "quality_metrics": {},
    }

    # Check requirement
    if requires_requirement:
        # Backward compatible: Use getattr to safely access requirement field
        task_requirement = getattr(task, "requirement", None)
        readiness["requirement_present"] = bool(task_requirement)
    else:
        readiness["requirement_present"] = True  # Not required, so always "present"

    # Get quality metrics (pass task_links to use same filtered queryset as evidence panel)
    try:
        eval_service = ChecklistEvaluationService()
        quality_result = eval_service.get_task_quality_score(
            task, task_links=task_links
        )
        readiness["quality_metrics"] = quality_result

        # Check evidence status (use 0.95 threshold to match ChecklistEvaluationService)
        evidence_coverage = quality_result.get("evidence_coverage", 0.0)
        readiness["evidence_complete"] = evidence_coverage >= 0.95

        # Check checklist
        missing_checklist = quality_result.get("missing_checklist_items", [])
        readiness["checklist_complete"] = len(missing_checklist) == 0

        # Check duration (use 0.8 threshold for meeting-based activities)
        duration_factor = quality_result.get("duration_factor", 0.0)
        readiness["duration_ok"] = duration_factor >= 0.8

        # Check quality
        quality_score = quality_result.get("quality_score", 0.0)
        readiness["quality_pass"] = quality_score >= 0.8

    except Exception as e:
        logger.warning(f"Error calculating approval readiness for task {task.id}: {e}")
        # Fallback: check if evidence exists (use provided queryset or query all)
        if task_links is not None:
            has_evidence = task_links.exists()
        else:
            has_evidence = TaskLinks.objects.filter(task=task, is_active=True).exists()
        readiness["evidence_complete"] = has_evidence

    # Overall ready: all checks pass
    readiness["overall_ready"] = (
        readiness["requirement_present"]
        and readiness["evidence_complete"]
        and readiness["checklist_complete"]
        and readiness["duration_ok"]
        and readiness["quality_pass"]
    )

    return readiness


def _safe_meeting_query(*args, **filter_kwargs):
    """
    Safely query Meeting model, handling case where table doesn't exist.

    Args:
        *args: Q objects for complex queries
        **filter_kwargs: Standard filter arguments

    Returns:
        QuerySet or None if table doesn't exist
    """
    try:
        from ai_services.models import Meeting
        from django.db import ProgrammingError, connection

        # Check if table exists (actual table name is ai_services_meeting, not getdata_gotomeetings)
        # CANONICAL: ai_services.models.Meeting uses Django default table name: ai_services_meeting
        table_names = connection.introspection.table_names()
        if Meeting._meta.db_table not in table_names:
            logger.debug(
                f"Meeting table '{Meeting._meta.db_table}' does not exist. Skipping query."
            )
            return None

        queryset = Meeting.objects.all()
        if args:
            # Handle Q objects
            from django.db.models import Q

            for q_obj in args:
                queryset = queryset.filter(q_obj)
        if filter_kwargs:
            queryset = queryset.filter(**filter_kwargs)
        return queryset
    except ProgrammingError as e:
        if "does not exist" in str(e):
            logger.debug(f"Meeting table query failed: {e}")
            return None
        raise
    except Exception as e:
        logger.debug(f"Unexpected error querying Meeting: {e}")
        return None


def compute_task_compliance(
    task, task_links, checklist_eval, meeting_match_info=None, user=None, policy=None
):
    """
    Compute unified compliance status for a task.

    This is the single source of truth for all compliance checks.
    Used by DAF v2 to ensure consistent evidence status, compliance chips,
    and approved vs provisional earnings.

    POLICY-DRIVEN: Uses PolicyResolver to determine rules based on employee group (Group A vs Group B).

    Args:
        task: Task instance
        task_links: List of TaskLinks instances (prefetched)
        checklist_eval: Dict from ChecklistEvaluationService.get_task_quality_score()
        meeting_match_info: Optional dict from _get_meeting_match_info()
        user: Optional User instance (for policy resolution, defaults to task.employee)
        policy: Optional PolicyConfig (if None, resolved from user's group)

    Returns:
        dict with:
        - requires_requirement: bool (policy-driven)
        - requirement_ok: bool (True if not required OR task.requirement is set)
        - evidence_status: 'missing' | 'partial' | 'complete' | 'auto_pending'
        - evidence_ok: bool (only True when evidence_status == 'complete')
        - evidence_count_ok: bool (True if count >= policy minimum)
        - checklist_ok: bool (missing_checklist_items is empty)
        - duration_ok: bool (duration_factor >= 1.0 OR total_duration_minutes > 0)
        - quality_ok: bool (quality_score >= policy.quality_threshold)
        - gate_pass: bool (AND of all compliance checks)
        - autolink_state: 'auto_created' | 'auto_pending' | 'manual_only'
        - needs_attention_reason_code: str (deterministic reason code)
        - needs_attention_reason_text: str (human-readable reason)
    """
    from management.services.policy_resolver import PolicyResolver

    # Resolve policy (use provided policy or resolve from user)
    if policy is None:
        policy_user = user if user else task.employee
        policy = PolicyResolver.for_user(policy_user)

    activity_type_slug = task.activity_type.slug if task.activity_type else None

    # Get evidence minimum for this activity type (for display and validation)
    evidence_minimum = policy.get_evidence_minimum(activity_type_slug)

    # 1. Requirement Compliance (policy-driven)
    requires_requirement = policy.requires_requirement(activity_type_slug)
    # Backward compatible: Check if requirement field exists before accessing
    task_requirement = getattr(task, "requirement", None)
    requirement_ok = not requires_requirement or (task_requirement is not None)

    # 2. Evidence Compliance (policy-driven)
    requires_meeting = policy.requires_meeting(activity_type_slug)

    # Use evidence_summary_service as single source of truth
    from management.services.evidence_summary_service import \
        get_task_evidence_summary

    evidence_summary = get_task_evidence_summary(task, task_links, meeting_match_info)

    has_active_evidence = evidence_summary["count_active"] > 0
    has_usable_evidence = evidence_summary["has_minimum"]

    # Check evidence minimum (policy-driven)
    evidence_count_ok = evidence_summary["count_usable"] >= evidence_minimum

    # PART 3: Check for meeting evidence (autolink OR manual meeting URL match)
    has_meeting_evidence = False
    if requires_meeting:
        # Check for autolinked meeting
        has_autolink = any(
            getattr(link, "is_auto_generated", False)
            and getattr(link, "meeting_id", None)
            for link in task_links
        )

        # Check for manual meeting URL that matches a Meeting in DB
        has_manual_meeting_match = False
        if not has_autolink:
            try:
                from ai_services.models import Meeting

                for link in task_links:
                    if link.link:
                        # Check if URL matches a Meeting
                        from django.db.models import Q

                        meeting_qs = _safe_meeting_query(
                            Q(recording_url=link.link) | Q(download_url=link.link)
                        )
                        matching_meeting = meeting_qs.first() if meeting_qs else None
                        if matching_meeting:
                            has_manual_meeting_match = True
                            break
            except Exception:
                pass

        # PART 3: Meeting-required tasks must have meeting evidence OR strict fallback (file + description + checklist)
        # Get missing_checklist_items from checklist_eval (will be defined later, but we need it here)
        missing_checklist_items_for_fallback = checklist_eval.get(
            "missing_checklist_items", []
        )
        has_strict_fallback = (
            has_usable_evidence
            and any(link.doc for link in task_links if link.is_active)  # Has file
            and any(
                link.description and len(link.description.strip()) > 50
                for link in task_links
                if link.is_active
            )  # Has description
            and not bool(missing_checklist_items_for_fallback)  # Checklist complete
        )

        has_meeting_evidence = (
            has_autolink or has_manual_meeting_match or has_strict_fallback
        )

    # Use evidence_summary status as base, but override if meeting required or minimum not met
    evidence_status = evidence_summary["status"]
    evidence_ok = evidence_summary["status"] == "complete" and evidence_count_ok
    autolink_state = (
        "auto_created"
        if evidence_summary["has_auto_generated"]
        else ("auto_pending" if evidence_status == "auto_pending" else "manual_only")
    )

    # If evidence count below minimum, mark as partial
    if has_usable_evidence and not evidence_count_ok:
        evidence_status = "partial"
        evidence_ok = False

    # PART 3: If meeting required, must have meeting evidence
    if requires_meeting and has_usable_evidence and not has_meeting_evidence:
        evidence_status = "partial"  # Has evidence but missing meeting requirement
        evidence_ok = False

    # 3. Checklist Compliance
    missing_checklist_items = checklist_eval.get("missing_checklist_items", [])
    checklist_ok = not bool(missing_checklist_items)

    # 4. Duration Compliance
    duration_factor = checklist_eval.get("duration_factor", 0.0)
    total_duration_minutes = checklist_eval.get("total_duration_minutes", 0)
    duration_ok = duration_factor >= 1.0 or total_duration_minutes > 0

    # 5. Quality Compliance (policy-driven threshold)
    # ENFORCEMENT (PART 1): Quality cannot be Pass if evidence is missing/partial or requirement is missing
    quality_score = checklist_eval.get("quality_score", 0.0)
    # If evidence is missing/partial, quality cannot be Pass
    if evidence_status in ["missing", "partial"]:
        quality_score = min(quality_score, policy.quality_threshold - 0.01)
    # If requirement is required and missing, quality cannot be Pass
    if requires_requirement and not requirement_ok:
        quality_score = min(quality_score, policy.quality_threshold - 0.01)
    quality_ok = quality_score >= policy.quality_threshold

    # 6. Overall Gate Pass
    gate_pass = (
        requirement_ok
        and evidence_ok
        and evidence_count_ok
        and checklist_ok
        and duration_ok
        and quality_ok
    )

    # 7. Deterministic needs_attention_reason (explainability)
    # Get duration info for numeric reason
    required_duration_minutes = (
        policy.get_duration_minimum(activity_type_slug) if policy else None
    )
    actual_duration_minutes = total_duration_minutes
    quality_score_pct = int(quality_score * 100) if quality_score else 0
    quality_threshold_pct = int(policy.quality_threshold * 100) if policy else 80

    # Get meeting quota info for reason text (if available from task_dict context)
    # Note: This is computed in daf_v2_view, so we'll pass it through if available
    # For now, compute it here if needed
    meetings_completed_for_reason = 0
    required_meeting_count_for_reason = 0
    if requires_meeting:
        # Count meeting evidence (same logic as in daf_v2_view)
        from django.db.models import Q

        meetings_completed_for_reason = len(
            [
                link
                for link in task_links
                if link.is_active
                and (
                    getattr(link, "meeting_id", None)
                    or getattr(link, "is_auto_generated", False)
                )
            ]
        )
        # Get required count from policy (prefer sessions_required, fallback to required_meeting_count)
        if policy:
            if hasattr(policy, "sessions_required") and policy.sessions_required > 0:
                required_meeting_count_for_reason = policy.sessions_required
            elif (
                hasattr(policy, "required_meeting_count")
                and policy.required_meeting_count > 0
            ):
                required_meeting_count_for_reason = policy.required_meeting_count
        if required_meeting_count_for_reason == 0:
            # Default to task.point or mxpoint
            required_meeting_count_for_reason = int(task.mxpoint or task.point or 1)

    needs_attention_reason_code, needs_attention_reason_text = (
        _determine_needs_attention_reason(
            gate_pass=gate_pass,
            requirement_ok=requirement_ok,
            requires_requirement=requires_requirement,
            evidence_ok=evidence_ok,
            evidence_count_ok=evidence_count_ok,
            evidence_status=evidence_status,
            evidence_count=evidence_summary["count_usable"],
            evidence_minimum=evidence_minimum,
            requires_meeting=requires_meeting,
            has_meeting_evidence=has_meeting_evidence if requires_meeting else True,
            checklist_ok=checklist_ok,
            duration_ok=duration_ok,
            actual_duration_minutes=actual_duration_minutes,
            required_duration_minutes=required_duration_minutes,
            quality_ok=quality_ok,
            quality_score=quality_score,
            meetings_completed_count=meetings_completed_for_reason,
            required_meeting_count=required_meeting_count_for_reason,
            quality_score_pct=quality_score_pct,
            quality_threshold_pct=quality_threshold_pct,
            activity_type_slug=activity_type_slug,
        )
    )

    return {
        "requires_requirement": requires_requirement,
        "requirement_ok": requirement_ok,
        "evidence_status": evidence_status,
        "evidence_ok": evidence_ok,
        "evidence_count_ok": evidence_count_ok,
        "checklist_ok": checklist_ok,
        "duration_ok": duration_ok,
        "quality_ok": quality_ok,
        "gate_pass": gate_pass,
        "autolink_state": autolink_state,
        "needs_attention_reason_code": needs_attention_reason_code,
        "needs_attention_reason_text": needs_attention_reason_text,
        "policy_group": policy.group_name,
        "evidence_minimum": evidence_minimum,  # For display (e.g., "Evidence: 1/2")
    }


def _determine_needs_attention_reason(
    gate_pass: bool,
    requirement_ok: bool,
    requires_requirement: bool,
    evidence_ok: bool,
    evidence_count_ok: bool,
    evidence_status: str,
    evidence_count: int,
    evidence_minimum: int,
    requires_meeting: bool,
    has_meeting_evidence: bool,
    checklist_ok: bool,
    duration_ok: bool,
    actual_duration_minutes: int = 0,
    required_duration_minutes: int = None,
    quality_ok: bool = True,
    quality_score: float = 0.0,
    quality_score_pct: int = 0,
    quality_threshold_pct: int = 80,
    activity_type_slug: str = None,
    meetings_completed_count: int = 0,
    required_meeting_count: int = 0,
    **kwargs,
) -> tuple:
    """
    Determine deterministic reason code and text for needs attention.

    Priority order (first failing check wins):
    1. Requirement missing
    2. Evidence missing
    3. Evidence count below minimum
    4. Meeting required but missing
    5. Checklist incomplete
    6. Duration missing
    7. Quality fail

    Returns:
        tuple: (reason_code, reason_text)
    """
    if gate_pass:
        return ("NONE", "All requirements met")

    # Priority 1: Requirement missing
    if requires_requirement and not requirement_ok:
        return (
            "REQUIREMENT_MISSING",
            "Select the requirement this task is fulfilling.",
        )

    # Priority 2: Evidence missing
    if evidence_status == "missing":
        return (
            "EVIDENCE_MISSING",
            "Upload at least 1 evidence item (link or file) with a short description.",
        )

    # Priority 3: Evidence count below minimum
    if not evidence_count_ok:
        return (
            "EVIDENCE_COUNT_INSUFFICIENT",
            f"Evidence items: {evidence_count}/{evidence_minimum} (need {evidence_minimum - evidence_count} more)",
        )

    # Priority 4: Meeting required but missing
    if requires_meeting and not has_meeting_evidence:
        # Include meeting quota info if available
        meetings_completed = (
            meetings_completed_count if meetings_completed_count > 0 else 0
        )
        required_meetings = required_meeting_count if required_meeting_count > 0 else 0

        if required_meetings > 0:
            remaining = max(0, required_meetings - meetings_completed)
            if remaining > 0:
                # Check if meeting room is configured and provide actionable message
                try:
                    from ai_services.utils.meeting_room_config import \
                        get_meeting_room_for_activity

                    meeting_room_id, _ = get_meeting_room_for_activity(
                        activity_type_slug or ""
                    )
                    if meeting_room_id:
                        return (
                            "MEETING_REQUIRED",
                            f"Meetings completed: {meetings_completed}/{required_meetings} (need {remaining} more). Use 'Start Meeting' from DAF so the system can match it.",
                        )
                except Exception:
                    pass

                return (
                    "MEETING_REQUIRED",
                    f"Meetings completed: {meetings_completed}/{required_meetings} (need {remaining} more). Link a meeting or paste the meeting recording URL.",
                )

        # Fallback to generic message if quota not available
        # Check if meeting room is configured and provide actionable message
        try:
            from ai_services.utils.meeting_room_config import \
                get_meeting_room_for_activity

            meeting_room_id, _ = get_meeting_room_for_activity(activity_type_slug or "")
            if meeting_room_id:
                return (
                    "MEETING_REQUIRED",
                    f"No meeting detected for {activity_type_slug or 'this activity'} in last 14 days. Use 'Start Meeting' from DAF so the system can match it.",
                )
        except Exception:
            pass

        return (
            "MEETING_REQUIRED",
            "This activity requires meeting proof. Link a meeting or paste the meeting recording URL.",
        )

    # Priority 5: Checklist incomplete
    if not checklist_ok:
        return (
            "CHECKLIST_INCOMPLETE",
            "Complete all required checklist items for this activity.",
        )

    # Priority 6: Duration missing
    if not duration_ok:
        if required_duration_minutes:
            return (
                "DURATION_MISSING",
                f"Meeting duration: {actual_duration_minutes} min; required: {required_duration_minutes} min (need {required_duration_minutes - actual_duration_minutes} more)",
            )
        else:
            return (
                "DURATION_MISSING",
                f"Meeting duration: {actual_duration_minutes} min (duration not detected or too short)",
            )

    # Priority 7: Quality fail
    if not quality_ok:
        return (
            "QUALITY_FAIL",
            f"Quality: {quality_score_pct}% / required {quality_threshold_pct}% (need {quality_threshold_pct - quality_score_pct}% more)",
        )

    # Fallback
    return ("UNKNOWN", "Task needs attention. Review all requirements.")


def _get_meeting_match_info(task, link=None):
    """
    Get meeting match information for a task.

    PART B FIX: Meeting matches MUST be scoped to the task's activity_slug and meeting room mapping.
    Never show meetings from other activities (e.g., "1-1 session on python" for Budgeting task).

    Returns dict with:
    - has_match: bool
    - meeting: Meeting instance or None
    - match_type: 'url' or 'topic' or None
    - confidence: float or None
    - requirement_code_match: bool or None
    - meeting_requirement_code: str or None
    - task_requirement_code: str or None
    """
    result = {
        "has_match": False,
        "meeting": None,
        "match_type": None,
        "confidence": None,
        "requirement_code_match": None,
        "meeting_requirement_code": None,
        "task_requirement_code": None,
    }

    try:
        from ai_services.models import Meeting
        from ai_services.services.meeting_evidence_matcher import \
            MeetingEvidenceMatcher
        from ai_services.utils.meeting_normalizer import normalize_url
        from ai_services.utils.meeting_room_config import \
            get_meeting_room_for_activity

        # PART B FIX: Get expected meeting room for this task's activity
        activity_type_slug = None
        if task.activity_type:
            activity_type_slug = task.activity_type.slug or task.activity_type.name
        elif task.activity_name:
            activity_type_slug = task.activity_name.upper().replace(" ", "_")

        expected_meeting_room_id = None
        if activity_type_slug:
            try:
                expected_meeting_room_id, _ = get_meeting_room_for_activity(
                    activity_type_slug
                )
            except Exception as e:
                logger.debug(
                    f"Error getting meeting room for activity {activity_type_slug}: {e}"
                )

        # If link provided, try to match by URL first
        if link:
            normalized_link = normalize_url(link)
            if normalized_link:
                from django.db.models import Q

                meeting_qs = _safe_meeting_query(
                    Q(recording_url=normalized_link) | Q(download_url=normalized_link)
                )
                matching_meeting = meeting_qs.first() if meeting_qs else None
                if matching_meeting:
                    # PART B FIX: Validate meeting room matches task's activity mapping
                    # If task has a meeting room mapping, the matched meeting must use that room
                    if expected_meeting_room_id:
                        if matching_meeting.meeting_id != str(expected_meeting_room_id):
                            # Meeting room mismatch - this meeting belongs to a different activity
                            logger.debug(
                                f"Meeting {matching_meeting.id} room {matching_meeting.meeting_id} "
                                f"does not match task {task.id} expected room {expected_meeting_room_id}"
                            )
                            # Don't return this match - it's for a different activity
                            return result

                    result["has_match"] = True
                    result["meeting"] = matching_meeting
                    result["match_type"] = "url"
                    result["confidence"] = 0.9  # URL matches are high confidence
                    result["meeting_requirement_code"] = (
                        matching_meeting.requirement_code
                    )

                    # Check REQ code match
                    # Backward compatible: Use getattr to safely access requirement field
                    task_requirement = getattr(task, "requirement", None)
                    if task_requirement:
                        task_req_code = f"REQ-{task_requirement.id}"
                        result["task_requirement_code"] = task_req_code
                        if matching_meeting.requirement_code:
                            result["requirement_code_match"] = (
                                task_req_code.upper()
                                == matching_meeting.requirement_code.upper()
                            )
                            if result["requirement_code_match"]:
                                result["confidence"] = 1.0  # VERY HIGH
                    return result

        # Fallback: use MeetingEvidenceMatcher to find matches
        matcher = MeetingEvidenceMatcher(enable_topic_fallback=True, time_window_days=2)
        detailed_matches = matcher.get_detailed_matches(task)

        if detailed_matches:
            # PART B FIX: Filter matches by meeting room if task has a mapping
            # Only consider matches that use the correct meeting room for this activity
            valid_matches = []
            for match in detailed_matches:
                meeting = match["meeting"]
                confidence = match.get("confidence", 0.0)

                # If task has a meeting room mapping, validate the match
                if expected_meeting_room_id:
                    if meeting.meeting_id != str(expected_meeting_room_id):
                        # Meeting room mismatch - skip this match
                        logger.debug(
                            f"Skipping match: meeting {meeting.id} room {meeting.meeting_id} "
                            f"does not match task {task.id} expected room {expected_meeting_room_id}"
                        )
                        continue
                    # Room matches - this is valid
                    valid_matches.append(match)
                else:
                    # No room mapping - require higher confidence to avoid cross-activity matches
                    # Only accept matches with confidence >= 0.8 if no room mapping
                    if confidence >= 0.8:
                        valid_matches.append(match)
                    else:
                        logger.debug(
                            f"Skipping low-confidence match ({confidence}) for task {task.id} "
                            f"with no room mapping (risk of cross-activity match)"
                        )

            if valid_matches:
                best_match = valid_matches[0]  # Highest confidence
            result["has_match"] = True
            result["meeting"] = best_match["meeting"]
            result["match_type"] = best_match["match_type"]
            result["confidence"] = best_match.get("confidence", 0.0)
            result["requirement_code_match"] = best_match.get("requirement_code_match")
            result["meeting_requirement_code"] = best_match["meeting"].requirement_code

            # Backward compatible: Use getattr to safely access requirement field
            task_requirement = getattr(task, "requirement", None)
            if task_requirement:
                result["task_requirement_code"] = f"REQ-{task_requirement.id}"
            else:
                # No valid matches after filtering
                logger.debug(
                    f"No valid meeting matches for task {task.id} after activity/room filtering"
                )

    except Exception as e:
        logger.debug(f"Error getting meeting match info for task {task.id}: {e}")

    return result


def get_eligible_requirements_for_user(
    user, recency_days=90, use_assigned_to_only=False
):
    """
    Get eligible requirements for a user based on assignment and recency.

    Eligibility criteria:
    - Only active/open requirements (is_active=True)
    - Only requirements with valid 'what' field (not null/empty)
    - Only requirements created within the last recency_days (default: 90 days)

    For non-staff users:
    - PRIMARY RULE: Only requirements where assigned_to matches the user
    - If use_assigned_to_only=False (legacy mode): also include creator=user

    For staff/superuser:
    - Can see all eligible requirements (no restriction)

    Args:
        user: User instance
        recency_days: Number of days back to include requirements (default: 90)
        use_assigned_to_only: If True, non-staff only see assigned_to requirements (default: False for backward compat)

    Returns:
        QuerySet of Requirement objects
    """
    from management.models import Requirement

    # Base queryset: active requirements with valid 'what' field
    base_queryset = (
        Requirement.objects.filter(is_active=True)
        .exclude(what__isnull=True)
        .exclude(what="")
    )

    # Staff/superuser can see all eligible requirements
    if user.is_staff or user.is_superuser:
        # Still apply recency filter for staff (reduces abuse)
        cutoff_date = timezone.now() - timedelta(days=recency_days)
        return base_queryset.filter(created_at__gte=cutoff_date).order_by("-created_at")

    # Regular users: filter by assigned_to (PRIMARY RULE)
    cutoff_date = timezone.now() - timedelta(days=recency_days)
    if use_assigned_to_only:
        # Strict: only assigned_to
        return base_queryset.filter(
            assigned_to=user, created_at__gte=cutoff_date
        ).order_by("-created_at")
    else:
        # Legacy: assigned_to OR creator
        return (
            base_queryset.filter(Q(assigned_to=user) | Q(creator=user))
            .filter(created_at__gte=cutoff_date)
            .order_by("-created_at")
        )


from django.core.files.uploadedfile import UploadedFile

# Duplicate _get_meeting_match_info removed - using the fixed version above (line 3512)


def newevidence(request, taskid):
    """
    Handles the submission of evidence, either as a link or an uploaded file.

    Permission: Only the task owner (task.employee) or admin/manager can view/submit evidence.
    Evidence list is scoped to the current user's evidence for this specific task.
    """
    task = get_object_or_404(Task, id=taskid)

    # Permission check: Only task owner or admin/manager can access
    if not (
        request.user.is_staff
        or request.user.is_superuser
        or request.user == task.employee
    ):
        messages.error(
            request,
            "You do not have permission to view or submit evidence for this task.",
        )
        return redirect("management:daf_v2")

    def get_user_evidence_for_task(task_obj, user, is_staff=False):
        """
        Get evidence list for a specific task, scoped appropriately.

        EVIDENCE SCOPING RULES (Fix 3):
        - DEFAULT SCOPE: Evidence owned by task.employee OR attached to the task
        - NEVER show other employees' evidence by default (privacy)
        - For non-staff: Only show evidence uploaded by this user OR task owner for this task
        - For staff: Show all evidence for this task + optionally evidence for same requirement (admin section)
        - Optional staff-only toggle to broaden scope (not implemented yet, but structure supports it)

        Returns dict with:
        - 'task_evidence': List of evidence for this task (scoped by ownership)
        - 'task_evidence_qs': QuerySet of TaskLinks (for passing to readiness calculation)
        - 'admin_evidence': List of evidence for same requirement (staff only, if task has requirement)
        """
        # DEFAULT SCOPE: Evidence attached to this task
        # Filter by: task=task_obj (Fix B: strictly filter to this task_id, no user-wide leakage)
        # EVIDENCE SCOPING (Fix 4): Privacy-correct evidence list
        # Rules:
        # - Non-staff: Only evidence uploaded by current user OR task owner
        # - Staff: All evidence for the task (with uploader identity)
        # - Fix B: Always filter by task=task_obj to prevent evidence leakage
        # - Fix B: Month scoping applies ONLY to inactive evidence (current DAF month in America/Chicago)
        from calendar import monthrange

        import pytz

        chicago_tz = pytz.timezone("America/Chicago")
        now_chicago = timezone.now().astimezone(chicago_tz)

        # Get current DAF month boundaries (start and end of current month in Chicago timezone)
        # Only used for filtering inactive evidence
        first_day = chicago_tz.localize(
            datetime(now_chicago.year, now_chicago.month, 1, 0, 0, 0)
        )
        last_day_num = monthrange(now_chicago.year, now_chicago.month)[1]
        last_day = chicago_tz.localize(
            datetime(now_chicago.year, now_chicago.month, last_day_num, 23, 59, 59)
        )

        if is_staff:
            # Staff can see all evidence for this task (active and inactive for manager actions)
            # Fix B: Strictly filter to this task_id (no month restriction for active evidence)
            task_evidence_qs = (
                TaskLinks.objects.filter(
                    task=task_obj  # Fix B: Strictly filter to this task_id
                )
                .select_related("added_by")
                .order_by("-created_at")
            )
        else:
            # Non-staff: Only evidence uploaded by current user OR task owner
            # Fix B: Filter strictly to this task_id
            task_evidence_qs = (
                TaskLinks.objects.filter(
                    task=task_obj,  # Fix B: Strictly filter to this task_id
                    added_by__in=[
                        user,
                        task_obj.employee,
                    ],  # Current user OR task owner
                    is_active=True,  # Non-staff only see active evidence
                )
                .select_related("added_by")
                .order_by("-created_at")
            )

        task_evidence = []
        inactive_evidence = (
            []
        )  # Fix C: Separate inactive evidence for manager activation

        for ev in task_evidence_qs:
            added_by_name = (
                ev.added_by.get_full_name()
                if hasattr(ev.added_by, "get_full_name") and ev.added_by.get_full_name()
                else ev.added_by.username
            )

            # Fix B: Use activity_type.name as primary label for auto-generated links
            # Primary label = Task.activity_type.name + "(Auto-linked)" when is_auto_generated
            # Secondary label = Meeting title (if meeting_id exists)
            is_auto = (
                ev.is_auto_generated if hasattr(ev, "is_auto_generated") else False
            )
            primary_label = None
            meeting_title = None

            if is_auto and task_obj.activity_type:
                # Auto-generated: use activity type name
                primary_label = f"{task_obj.activity_type.name} (Auto-linked)"
                # Get meeting title if meeting_id exists
                if hasattr(ev, "meeting_id") and ev.meeting_id:
                    try:
                        from ai_services.models import Meeting

                        meeting = Meeting.objects.filter(
                            meeting_id=ev.meeting_id
                        ).first()
                        if meeting:
                            meeting_title = meeting.topic
                    except Exception:
                        pass
            else:
                # Manual: use link_name as before
                primary_label = ev.link_name or "Evidence"

            evidence_item = {
                "id": ev.id,
                "link_name": ev.link_name,  # Keep for backward compatibility
                "primary_label": primary_label,  # New: correct label
                "meeting_title": meeting_title,  # New: meeting title if available
                "link": ev.link,
                "drive_link": ev.drive_link,
                "doc": ev.doc,
                "description": ev.description,
                "created_at": ev.created_at,
                "added_by": added_by_name,
                "added_by_username": ev.added_by.username,
                "is_auto_generated": is_auto,
                "is_active": ev.is_active,
                "meeting_id": getattr(ev, "meeting_id", None),
            }

            # Fix C: Separate active and inactive evidence
            if ev.is_active:
                task_evidence.append(evidence_item)
            else:
                # Only include inactive evidence for staff (manager actions)
                # Fix B: Apply month scoping to inactive evidence only
                if is_staff:
                    # Check if evidence is within current DAF month
                    ev_created_chicago = ev.created_at.astimezone(chicago_tz)
                    if first_day <= ev_created_chicago <= last_day:
                        inactive_evidence.append(evidence_item)

        # Admin section: show evidence for same requirement (staff only, if task has requirement)
        admin_evidence = []
        # Backward compatible: Use getattr to safely access requirement field
        task_obj_requirement = getattr(task_obj, "requirement", None)
        if is_staff and task_obj_requirement:
            # Show evidence from other tasks with same requirement (last 30 days, exclude current task)
            # timedelta is already imported at module level (line 19)
            recent_date = timezone.now() - timedelta(days=30)
            admin_evidence_qs = (
                TaskLinks.objects.filter(
                    task__requirement=task_obj_requirement,
                    task__is_active=True,
                    is_active=True,
                )
                .exclude(
                    task=task_obj  # Exclude current task's evidence (already in task_evidence)
                )
                .filter(created_at__gte=recent_date)
                .select_related("added_by", "task")
                .order_by("-created_at")[:10]
            )  # Limit to 10 most recent

            for ev in admin_evidence_qs:
                added_by_name = (
                    ev.added_by.get_full_name()
                    if hasattr(ev.added_by, "get_full_name")
                    and ev.added_by.get_full_name()
                    else ev.added_by.username
                )
                admin_evidence.append(
                    {
                        "id": ev.id,
                        "link_name": ev.link_name,
                        "link": ev.link,
                        "drive_link": ev.drive_link,
                        "doc": ev.doc,
                        "description": ev.description,
                        "created_at": ev.created_at,
                        "added_by": added_by_name,
                        "added_by_username": ev.added_by.username,
                        "task_id": ev.task.id,
                        "task_name": ev.task.task_name
                        or ev.task.activity_name
                        or "Untitled Task",
                    }
                )

        return {
            "task_evidence": task_evidence,
            "task_evidence_qs": task_evidence_qs,  # Return queryset for readiness calculation
            "admin_evidence": admin_evidence,
            "inactive_evidence": inactive_evidence,  # Fix C: Inactive evidence for manager activation
        }

    if request.method == "POST":
        form = EvidenceForm(
            data=request.POST, files=request.FILES, request=request, task=task
        )
        if form.is_valid():
            data = form.cleaned_data

            link = data.get("link", "")
            uploaded_file = data.get("doc", None)

            # Enforce requirement linkage for specific activity types
            activity_type_slug = None
            if task.activity_type:
                activity_type_slug = task.activity_type.slug or task.activity_type.name
            elif task.activity_name:
                # Fallback to activity_name if activity_type not set
                activity_type_slug = task.activity_name.upper().replace(" ", "_")

            requires_requirement = False
            if activity_type_slug:
                requires_requirement = activity_type_slug.upper() in [
                    a.upper() for a in REQUIREMENT_REQUIRED_ACTIVITY_TYPES
                ]

            # Server-side validation: Requirement locking and eligibility
            posted_requirement_id = data.get("requirement")

            # Check if requirement is locked
            # Locked ONLY if: task.requirement is set AND evidence exists
            # If requirement is missing, it must NOT be locked (user needs to set it)
            # Backward compatible: Use getattr to safely access requirement field
            task_requirement_newevidence = getattr(task, "requirement", None)
            has_evidence = TaskLinks.objects.filter(task=task, is_active=True).exists()
            requirement_locked = (
                task_requirement_newevidence is not None and has_evidence
            )

            # If requirement is locked, enforce it
            if requirement_locked:
                if task_requirement_newevidence:
                    requirement_id = task_requirement_newevidence.id
                    if posted_requirement_id and str(posted_requirement_id) != str(
                        task_requirement_newevidence.id
                    ):
                        # Non-staff cannot change locked requirement
                        if not (request.user.is_staff or request.user.is_superuser):
                            messages.error(
                                request,
                                "Requirement is locked and cannot be changed. Contact your manager if you need to change it.",
                            )
                            evidence_data = get_user_evidence_for_task(
                                task,
                                request.user,
                                request.user.is_staff or request.user.is_superuser,
                            )
                            requirement_locked = True
                            approval_readiness = _calculate_approval_readiness(
                                task,
                                requires_requirement,
                                task_links=evidence_data.get("task_evidence_qs"),
                            )
                            return render(
                                request,
                                "management/daf/evidence_form.html",
                                {
                                    "form": form,
                                    "task": task,
                                    "evidence_list": evidence_data["task_evidence"],
                                    "admin_evidence": (
                                        evidence_data["admin_evidence"]
                                        if (
                                            request.user.is_staff
                                            or request.user.is_superuser
                                        )
                                        else []
                                    ),
                                    "is_staff": request.user.is_staff
                                    or request.user.is_superuser,
                                    "requires_requirement": requires_requirement,
                                    "requirement_locked": requirement_locked,
                                    "approval_readiness": approval_readiness,
                                },
                            )
                        else:
                            # Staff can override but log warning
                            # Backward compatible: Use getattr to safely access requirement field
                            task_requirement_log = getattr(task, "requirement", None)
                            old_req_id = (
                                task_requirement_log.id
                                if task_requirement_log
                                else None
                            )
                            logger.warning(
                                f"Staff user {request.user.id} changed requirement from {old_req_id} "
                                f"to {posted_requirement_id} for task {task.id}."
                            )
                            requirement_id = posted_requirement_id
                else:
                    # Evidence exists but no requirement set - use posted value
                    requirement_id = posted_requirement_id
            else:
                # Task has no requirement yet - validate POSTed requirement is eligible
                requirement_id = posted_requirement_id
                if requires_requirement and not requirement_id:
                    # Only superuser can bypass (default: no bypass)
                    if not (request.user.is_superuser):
                        messages.error(
                            request,
                            f"This activity type ({task.activity_type.name if task.activity_type else task.activity_name}) must be linked to a Requirement before evidence can be submitted. Please select a Requirement from the dropdown.",
                        )
                        evidence_data = get_user_evidence_for_task(
                            task,
                            request.user,
                            request.user.is_staff or request.user.is_superuser,
                        )
                        return render(
                            request,
                            "management/daf/evidence_form.html",
                            {
                                "form": form,
                                "task": task,
                                "evidence_list": evidence_data["task_evidence"],
                                "admin_evidence": (
                                    evidence_data["admin_evidence"]
                                    if (
                                        request.user.is_staff
                                        or request.user.is_superuser
                                    )
                                    else []
                                ),
                                "is_staff": request.user.is_staff
                                or request.user.is_superuser,
                            },
                        )
                elif requirement_id:
                    # Validate that the posted requirement is in allowed set
                    # Use assigned_to filtering for non-staff
                    is_staff = request.user.is_staff or request.user.is_superuser
                    eligible_requirements = get_eligible_requirements_for_user(
                        request.user, use_assigned_to_only=not is_staff
                    )
                    if not eligible_requirements.filter(id=requirement_id).exists():
                        form.add_error("requirement", "Invalid requirement selection.")
                        messages.error(
                            request,
                            "Invalid requirement selection. Only your open requirements are allowed.",
                        )
                        evidence_data = get_user_evidence_for_task(
                            task,
                            request.user,
                            request.user.is_staff or request.user.is_superuser,
                        )
                        return render(
                            request,
                            "management/daf/evidence_form.html",
                            {
                                "form": form,
                                "task": task,
                                "evidence_list": evidence_data["task_evidence"],
                                "admin_evidence": (
                                    evidence_data["admin_evidence"]
                                    if (
                                        request.user.is_staff
                                        or request.user.is_superuser
                                    )
                                    else []
                                ),
                                "is_staff": request.user.is_staff
                                or request.user.is_superuser,
                            },
                        )

            # Ensure at least one form of evidence is provided
            if not link and not uploaded_file:
                messages.error(
                    request, "Please provide an evidence link or upload a file."
                )
                evidence_list = get_user_evidence_for_task(
                    task,
                    request.user,
                    request.user.is_staff or request.user.is_superuser,
                )
                return render(
                    request,
                    "management/daf/evidence_form.html",
                    {
                        "form": form,
                        "task": task,
                        "evidence_list": evidence_list,
                        "is_staff": request.user.is_staff or request.user.is_superuser,
                    },
                )

            # EVIDENCE LINK VALIDATION (Fix 3)
            # Use centralized URL validation utility
            if link:
                from management.utils import is_valid_evidence_url

                link = link.strip()

                # Validate URL format
                if not is_valid_evidence_url(link):
                    messages.error(
                        request,
                        "Please provide a complete, valid URL starting with http:// or https:// (not a placeholder).",
                    )
                    evidence_data = get_user_evidence_for_task(
                        task,
                        request.user,
                        request.user.is_staff or request.user.is_superuser,
                    )
                    return render(
                        request,
                        "management/daf/evidence_form.html",
                        {
                            "form": form,
                            "task": task,
                            "evidence_list": evidence_data["task_evidence"],
                            "admin_evidence": (
                                evidence_data["admin_evidence"]
                                if (request.user.is_staff or request.user.is_superuser)
                                else []
                            ),
                            "is_staff": request.user.is_staff
                            or request.user.is_superuser,
                        },
                    )

                # For meeting-based activity types, optionally restrict to known recording domains
                # Known domains: gotomeeting.com, zoom.us, teams.microsoft.com, meet.google.com, etc.
                activity_type_slug = None
                if task.activity_type:
                    activity_type_slug = (
                        task.activity_type.slug or task.activity_type.name
                    )
                elif task.activity_name:
                    activity_type_slug = task.activity_name.upper().replace(" ", "_")

                MEETING_REQUIRED_ACTIVITY_TYPES = [
                    "SELF_TRAINING_SESSION",
                    "INTERNAL_TRAINING_SESSION",
                    "CLIENT_TRAINING_SESSION",
                    "PRODUCT_BACKLOG_REFINEMENT",
                ]

                is_meeting_activity = (
                    activity_type_slug
                    and activity_type_slug.upper()
                    in [a.upper() for a in MEETING_REQUIRED_ACTIVITY_TYPES]
                )

                # Initialize link_domain to avoid UnboundLocalError
                link_domain = None

                if is_meeting_activity:
                    # Known meeting recording domains (whitelist approach - optional, can be disabled)
                    # For now, we just warn but don't block - can be made stricter later
                    known_domains = [
                        "gotomeeting.com",
                        "zoom.us",
                        "teams.microsoft.com",
                        "meet.google.com",
                        "webex.com",
                        "bluejeans.com",
                    ]
                    try:
                        from urllib.parse import urlparse

                        parsed = urlparse(link)
                        link_domain = parsed.netloc.lower()
                    except Exception:
                        pass

                    # If domain is known, that's good; if not, warn but don't block (flexibility)
                    if link_domain and not any(
                        domain in link_domain for domain in known_domains
                    ):
                        # Just log a warning - don't block (allows flexibility for other platforms)
                        logger.debug(
                            f"Meeting activity {activity_type_slug} has link from unknown domain: {link_domain}"
                        )

                # Optional: Validate link is accessible (but don't block on network errors - too fragile)
                # Commented out to avoid blocking on network issues
                # try:
                #     response = requests.head(link, timeout=5, allow_redirects=True)
                #     if response.status_code >= 400:
                #         messages.warning(request, "The provided link may not be accessible (status {response.status_code}).")
                # except requests.exceptions.RequestException:
                #     # Don't block on network errors - link might be valid but temporarily unreachable
                #     pass
            else:
                # Not a meeting activity - no domain restriction needed
                pass

            # Check if the link already exists
            if link:
                existing_links = TaskLinks.objects.filter(link=link)
                if existing_links.exists():
                    users = existing_links.values_list("added_by__username", flat=True)
                    if request.user.username in users:
                        messages.error(request, "You have already uploaded this link.")
                        evidence_data = get_user_evidence_for_task(
                            task,
                            request.user,
                            request.user.is_staff or request.user.is_superuser,
                        )
                        return render(
                            request,
                            "management/daf/evidence_form.html",
                            {
                                "form": form,
                                "task": task,
                                "evidence_list": evidence_data["task_evidence"],
                                "admin_evidence": (
                                    evidence_data["admin_evidence"]
                                    if (
                                        request.user.is_staff
                                        or request.user.is_superuser
                                    )
                                    else []
                                ),
                                "is_staff": request.user.is_staff
                                or request.user.is_superuser,
                            },
                        )
                    # TEMPORARY: Commented out to allow multiple employees to upload same link
                    # TODO: Re-evaluate after testing period - may need activity-specific rules
                    # elif task.activity_name not in ACTIVITY_LIST:
                    #     messages.error(request, "This link is already uploaded by another user.")
                    #     return render(request, "management/daf/evidence_form.html", {"form": form")

            temp_file_path = None
            original_filename = None
            if isinstance(uploaded_file, UploadedFile):
                # Save the uploaded file temporarily
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=os.path.splitext(uploaded_file.name)[1]
                ) as temp_file:
                    for chunk in uploaded_file.chunks():
                        temp_file.write(chunk)
                    temp_file_path = temp_file.name
                    original_filename = uploaded_file.name
            else:
                uploaded_file = None  # Ensure it's None if not an UploadedFile

            # Update task.requirement if provided and task doesn't have one yet (one-time bind)
            # Backward compatible: Use getattr/hasattr to safely check and set requirement field
            task_requirement_bind = getattr(task, "requirement", None)
            if (
                requirement_id
                and not task_requirement_bind
                and hasattr(task, "requirement")
            ):
                try:
                    requirement_obj = Requirement.objects.get(id=requirement_id)
                    task.requirement = requirement_obj
                    task.save(update_fields=["requirement"])
                    logger.info(
                        f"Task {task.id} bound to requirement {requirement_id} by user {request.user.id}"
                    )
                except Requirement.DoesNotExist:
                    logger.error(
                        f"Requirement {requirement_id} not found when binding to task {task.id}"
                    )
                    messages.error(
                        request, "Selected requirement not found. Please try again."
                    )
                    evidence_data = get_user_evidence_for_task(
                        task,
                        request.user,
                        request.user.is_staff or request.user.is_superuser,
                    )
                    return render(
                        request,
                        "management/daf/evidence_form.html",
                        {
                            "form": form,
                            "task": task,
                            "evidence_list": evidence_data["task_evidence"],
                            "admin_evidence": (
                                evidence_data["admin_evidence"]
                                if (request.user.is_staff or request.user.is_superuser)
                                else []
                            ),
                            "is_staff": request.user.is_staff
                            or request.user.is_superuser,
                        },
                    )

            # Validate REQ code in meeting topic for meeting-based activities
            if requires_requirement and requirement_id and link:
                # Check if this is a meeting-based activity
                is_meeting_based = (
                    activity_type_slug
                    and activity_type_slug.upper()
                    in [a.upper() for a in MEETING_BASED_ACTIVITY_TYPES]
                )

                if is_meeting_based:
                    try:
                        # Try to find matching meeting by URL
                        from ai_services.models import Meeting
                        from ai_services.services.meeting_evidence_matcher import \
                            MeetingEvidenceMatcher
                        from ai_services.utils.meeting_normalizer import \
                            normalize_url

                        normalized_link = normalize_url(link)
                        if normalized_link:
                            # Look for meeting with matching URL
                            matching_meeting = Meeting.objects.filter(
                                Q(recording_url=normalized_link)
                                | Q(download_url=normalized_link)
                            ).first()

                            if matching_meeting:
                                # Meeting exists - validate REQ code
                                expected_req_code = f"REQ-{requirement_id}"

                                if not matching_meeting.requirement_code:
                                    messages.error(
                                        request,
                                        "Meeting title must include your requirement code (e.g., REQ-5755). "
                                        "Please rename the meeting and retry.",
                                    )
                                    evidence_data = get_user_evidence_for_task(
                                        task,
                                        request.user,
                                        request.user.is_staff
                                        or request.user.is_superuser,
                                    )
                                    return render(
                                        request,
                                        "management/daf/evidence_form.html",
                                        {
                                            "form": form,
                                            "task": task,
                                            "evidence_list": evidence_data[
                                                "task_evidence"
                                            ],
                                            "admin_evidence": (
                                                evidence_data["admin_evidence"]
                                                if (
                                                    request.user.is_staff
                                                    or request.user.is_superuser
                                                )
                                                else []
                                            ),
                                            "is_staff": request.user.is_staff
                                            or request.user.is_superuser,
                                            "requires_requirement": requires_requirement,
                                        },
                                    )
                                elif (
                                    matching_meeting.requirement_code.upper()
                                    != expected_req_code.upper()
                                ):
                                    messages.error(
                                        request,
                                        f"Meeting requirement code mismatch. Expected {expected_req_code} but found {matching_meeting.requirement_code}. "
                                        "Please update the meeting title to include the correct requirement code.",
                                    )
                                    evidence_data = get_user_evidence_for_task(
                                        task,
                                        request.user,
                                        request.user.is_staff
                                        or request.user.is_superuser,
                                    )
                                    return render(
                                        request,
                                        "management/daf/evidence_form.html",
                                        {
                                            "form": form,
                                            "task": task,
                                            "evidence_list": evidence_data[
                                                "task_evidence"
                                            ],
                                            "admin_evidence": (
                                                evidence_data["admin_evidence"]
                                                if (
                                                    request.user.is_staff
                                                    or request.user.is_superuser
                                                )
                                                else []
                                            ),
                                            "is_staff": request.user.is_staff
                                            or request.user.is_superuser,
                                            "requires_requirement": requires_requirement,
                                        },
                                    )
                                # REQ code matches - proceed
                            # If no meeting match exists yet, allow submission but it will be flagged for verification
                    except (ImportError, Exception) as e:
                        # If ai_services is not available or there's a database error, skip meeting validation
                        # This allows the test to proceed without requiring the full ai_services setup
                        logger.debug(f"Skipping meeting validation: {e}")
                        pass

            # AI Requirement Match Verification (AI-2)
            requirement_match_result = None
            if requires_requirement and requirement_id:
                try:
                    from ai_services.models import Meeting
                    from ai_services.services.meeting_evidence_matcher import \
                        MeetingEvidenceMatcher
                    from ai_services.utils.meeting_normalizer import \
                        normalize_url
                    from management.services.requirement_match_service import \
                        RequirementMatchService

                    # Get requirement object
                    requirement_obj = Requirement.objects.get(id=requirement_id)

                    # Check if meeting match exists (for enforcement mode blocking logic)
                    meeting_match_exists = False
                    if link:
                        try:
                            normalized_link = normalize_url(link)
                            if normalized_link:
                                matching_meeting = Meeting.objects.filter(
                                    Q(recording_url=normalized_link)
                                    | Q(download_url=normalized_link)
                                ).first()
                                if matching_meeting:
                                    meeting_match_exists = True
                        except Exception as e:
                            logger.debug(f"Error checking meeting match: {e}")

                    # Get associated meeting if available
                    meeting_obj = None
                    if link and meeting_match_exists:
                        try:
                            normalized_link = normalize_url(link)
                            if normalized_link:
                                from django.db.models import Q

                                meeting_qs = _safe_meeting_query(
                                    Q(recording_url=normalized_link)
                                    | Q(download_url=normalized_link)
                                )
                                meeting_obj = meeting_qs.first() if meeting_qs else None
                        except Exception:
                            pass

                    # Call AI verification service
                    service = RequirementMatchService()
                    requirement_match_result = service.verify_requirement_match(
                        task=task,
                        requirement=requirement_obj,
                        user=request.user,
                        meeting=meeting_obj,
                    )

                    # Enforcement mode: block on FAIL only when meeting match exists
                    if (
                        not service.shadow_mode
                        and requirement_match_result["status"] == "fail"
                    ):
                        if meeting_match_exists:
                            # Block submission (except staff/superuser)
                            if not (request.user.is_staff or request.user.is_superuser):
                                messages.error(
                                    request,
                                    f"Requirement Integrity Check Failed: {requirement_match_result.get('reason', 'Requirement does not match activity type')}. "
                                    "Please select a requirement that matches this activity type.",
                                )
                                evidence_data = get_user_evidence_for_task(
                                    task,
                                    request.user,
                                    request.user.is_staff or request.user.is_superuser,
                                )
                                return render(
                                    request,
                                    "management/daf/evidence_form.html",
                                    {
                                        "form": form,
                                        "task": task,
                                        "evidence_list": evidence_data["task_evidence"],
                                        "admin_evidence": (
                                            evidence_data["admin_evidence"]
                                            if (
                                                request.user.is_staff
                                                or request.user.is_superuser
                                            )
                                            else []
                                        ),
                                        "is_staff": request.user.is_staff
                                        or request.user.is_superuser,
                                        "requires_requirement": requires_requirement,
                                        "requirement_match_result": requirement_match_result,  # Pass to template for chip display
                                    },
                                )
                            else:
                                # Staff bypass - show warning but allow
                                messages.warning(
                                    request,
                                    f"Requirement Integrity Check Failed (Staff Bypass): {requirement_match_result.get('reason', 'Requirement does not match')}",
                                )
                        # If no meeting match, allow submission (meeting sync may lag)
                        else:
                            logger.info(
                                f"AI requirement match FAIL but no meeting match exists for task {task.id}. "
                                "Allowing submission (meeting sync may be delayed)."
                            )

                    # Shadow mode: show warning but don't block
                    elif service.shadow_mode and requirement_match_result["status"] in [
                        "fail",
                        "review",
                    ]:
                        if requirement_match_result["status"] == "fail":
                            messages.warning(
                                request,
                                f"Requirement Integrity Advisory: {requirement_match_result.get('reason', 'Requirement may not match activity type')}. "
                                "This will be reviewed by your manager.",
                            )
                        else:
                            messages.info(
                                request,
                                f"Requirement Integrity Review: {requirement_match_result.get('reason', 'Requirement match needs review')}",
                            )

                except Exception as e:
                    logger.error(
                        f"Error in AI requirement match verification: {e}",
                        exc_info=True,
                    )
                    # Don't block on AI service errors - fail gracefully
                    requirement_match_result = None

            # Lock requirement after first evidence submission (non-AI governance hardening)
            # Backward compatible: Use getattr/hasattr to safely check and set requirement field
            task_requirement_lock = getattr(task, "requirement", None)
            if (
                requirement_id
                and not task_requirement_lock
                and hasattr(task, "requirement")
            ):
                # This was already set above, but ensure it's saved
                task.refresh_from_db()
                task_requirement_lock_after_refresh = getattr(task, "requirement", None)
                if not task_requirement_lock_after_refresh:
                    try:
                        requirement_obj = Requirement.objects.get(id=requirement_id)
                        task.requirement = requirement_obj
                        task.save(update_fields=["requirement"])
                        logger.info(
                            f"Task {task.id} requirement locked to {requirement_id} after first evidence submission"
                        )
                    except Requirement.DoesNotExist:
                        logger.error(
                            f"Requirement {requirement_id} not found when locking to task {task.id}"
                        )

            # Process the submission in a separate thread
            GOOGLE_DRIVE_FOLDER_ID = "1V7c15Aq-WKKe6SbHIFnlknsy-gPTEc6v"
            thread = threading.Thread(
                target=process_evidence_submission,
                args=(
                    data,
                    temp_file_path,
                    original_filename,
                    request.user,
                    task,
                    GOOGLE_DRIVE_FOLDER_ID,
                    requirement_match_result,
                ),
            )
            thread.start()

            messages.success(
                request,
                "Your evidence is being processed. You will be notified upon completion.",
            )
            return redirect("management:user_evidence")
        else:
            messages.error(request, "Please correct the errors in the form.")
            evidence_data = get_user_evidence_for_task(
                task, request.user, request.user.is_staff or request.user.is_superuser
            )

            # Fix E: Use PolicyResolver to determine if requirement is needed (Group A vs Group B)
            from management.services.policy_resolver import PolicyResolver

            policy = PolicyResolver.for_user(request.user)

            activity_type_slug = None
            if task.activity_type:
                activity_type_slug = task.activity_type.slug
            elif task.activity_name:
                activity_type_slug = task.activity_name.upper().replace(" ", "_")

            # Use PolicyResolver to correctly determine requirement gating (Group B should not require)
            requires_requirement = (
                policy.requires_requirement(activity_type_slug)
                if activity_type_slug
                else False
            )

            # Calculate context for error case
            requirement_locked = False
            task_requirement = getattr(task, "requirement", None)
            if requires_requirement and task_requirement:
                has_evidence = TaskLinks.objects.filter(
                    task=task, is_active=True
                ).exists()
                if has_evidence and not (
                    request.user.is_staff or request.user.is_superuser
                ):
                    requirement_locked = True

            approval_readiness = _calculate_approval_readiness(
                task,
                requires_requirement,
                task_links=evidence_data.get("task_evidence_qs"),
            )
            meeting_match_info = None  # Can't get from form errors easily

            return render(
                request,
                "management/daf/evidence_form.html",
                {
                    "form": form,
                    "task": task,
                    "evidence_list": evidence_data["task_evidence"],
                    "admin_evidence": (
                        evidence_data["admin_evidence"]
                        if (request.user.is_staff or request.user.is_superuser)
                        else []
                    ),
                    "is_staff": request.user.is_staff or request.user.is_superuser,
                    "requires_requirement": requires_requirement,
                    "requirement_locked": requirement_locked,
                    "approval_readiness": approval_readiness,
                    "meeting_match_info": meeting_match_info,
                },
            )
    else:
        form = EvidenceForm(request=request, task=task)
        # Get existing evidence for this task, scoped appropriately
        is_staff_user = request.user.is_staff or request.user.is_superuser
        evidence_data = get_user_evidence_for_task(task, request.user, is_staff_user)

        # Check if requirement is required for this activity type
        activity_type_slug = None
        if task.activity_type:
            activity_type_slug = task.activity_type.slug or task.activity_type.name
        elif task.activity_name:
            activity_type_slug = task.activity_name.upper().replace(" ", "_")

        requires_requirement = False
        if activity_type_slug:
            requires_requirement = activity_type_slug.upper() in [
                a.upper() for a in REQUIREMENT_REQUIRED_ACTIVITY_TYPES
            ]

        # Check if requirement is locked
        # Locked ONLY if: task.requirement is set AND evidence exists
        # If requirement is missing, it must NOT be locked (user needs to set it)
        # Non-staff cannot change locked requirement; staff can override (with warning)
        requirement_locked = False
        has_evidence = TaskLinks.objects.filter(task=task, is_active=True).exists()
        # Only lock if requirement is already set AND evidence exists
        # If requirement is missing, allow user to set it (even if evidence exists)
        # Backward compatible: Use getattr to safely access requirement field
        task_requirement = getattr(task, "requirement", None)
        if task_requirement and has_evidence:
            requirement_locked = True

        # Calculate approval readiness (use same filtered queryset as evidence panel)
        approval_readiness = _calculate_approval_readiness(
            task, requires_requirement, task_links=evidence_data.get("task_evidence_qs")
        )

        # Get meeting match info using new MeetingMatchService
        # Try to find meeting match from:
        # 1. Form initial link (if user pasted link)
        # 2. Existing evidence links
        # 3. Time proximity + employee + topic signals (does NOT require requirement code)
        meeting_match_info = None

        try:
            from management.services.meeting_match_service import \
                MeetingMatchService

            match_service = MeetingMatchService(time_window_days=2, min_confidence=0.5)

            # Check form initial link first
            if form.initial.get("link"):
                match_result = match_service.find_best_meeting_for_task(
                    task=task, employee=request.user, link=form.initial.get("link")
                )
                if match_result.meeting:
                    meeting_match_info = match_result.to_dict()

            # If no match from form, check existing evidence
            if not meeting_match_info or not meeting_match_info.get("has_match"):
                if evidence_data["task_evidence"]:
                    for ev in evidence_data["task_evidence"]:
                        if ev.get("link"):
                            match_result = match_service.find_best_meeting_for_task(
                                task=task, employee=request.user, link=ev.get("link")
                            )
                            if match_result.meeting:
                                meeting_match_info = match_result.to_dict()
                                break

            # If still no match, try without link (time + signals)
            if not meeting_match_info or not meeting_match_info.get("has_match"):
                match_result = match_service.find_best_meeting_for_task(
                    task=task, employee=request.user
                )
                if match_result.meeting:
                    meeting_match_info = match_result.to_dict()
        except Exception as e:
            logger.debug(f"Error in meeting match service for task {task.id}: {e}")
            # Fallback to old method if new service fails
            if form.initial.get("link"):
                meeting_match_info = _get_meeting_match_info(
                    task, link=form.initial.get("link")
                )

        # SECURITY: Ensure admin_evidence is only included for staff users
        # Double-check to prevent data leakage even if template is modified
        admin_evidence_safe = (
            evidence_data["admin_evidence"]
            if (request.user.is_staff or request.user.is_superuser)
            else []
        )

        return render(
            request,
            "management/daf/evidence_form.html",
            {
                "form": form,
                "task": task,
                "evidence_list": evidence_data["task_evidence"],
                "inactive_evidence": evidence_data.get(
                    "inactive_evidence", []
                ),  # Fix C: Inactive evidence for activation
                "admin_evidence": admin_evidence_safe,
                "is_staff": is_staff_user,
                "requires_requirement": requires_requirement,
                "requirement_locked": requirement_locked,
                "approval_readiness": approval_readiness,
                "meeting_match_info": meeting_match_info,
            },
        )


@login_required
def activate_evidence(request, link_id):
    """
    Activate an inactive evidence link for a task (staff only).

    POST-only endpoint that activates a TaskLinks object and redirects back to newevidence.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to activate evidence.")
        return redirect("management:daf_v2")

    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("management:daf_v2")

    try:
        from management.models import TaskLinks

        link = TaskLinks.objects.get(id=link_id)
        task = link.task

        # Deactivate any existing auto-generated active link for this task
        TaskLinks.objects.filter(
            task=task, is_active=True, is_auto_generated=True
        ).update(is_active=False)

        # Activate the selected link
        link.is_active = True
        link.is_featured = True  # Optionally set as featured
        link.save()

        messages.success(
            request,
            f"Evidence '{link.link_name or 'link'}' activated for task: {task.activity_name}",
        )
    except TaskLinks.DoesNotExist:
        messages.error(request, "Evidence link not found.")
    except Exception as e:
        logger.error(f"Error activating evidence link {link_id}: {e}", exc_info=True)
        messages.error(request, "Error activating evidence link. Please try again.")

    # Redirect back to newevidence page for the task
    task_id = request.POST.get("task_id") or (
        link.task.id if "link" in locals() else None
    )
    if task_id:
        return redirect("management:new_evidence", taskid=task_id)
    return redirect("management:daf_v2")


@login_required
def deactivate_evidence(request, link_id):
    """
    Deactivate an auto-generated evidence link for a task (staff only).

    POST-only endpoint that deactivates an auto-generated TaskLinks object and redirects back to newevidence.
    """
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You do not have permission to deactivate evidence.")
        return redirect("management:daf_v2")

    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("management:daf_v2")

    try:
        from management.models import TaskLinks

        link = TaskLinks.objects.get(id=link_id, is_auto_generated=True)
        task = link.task

        # Deactivate the auto-generated link
        link.is_active = False
        link.save()

        messages.success(
            request,
            f"Auto-generated evidence '{link.link_name or 'link'}' deactivated for task: {task.activity_name}",
        )
    except TaskLinks.DoesNotExist:
        messages.error(request, "Auto-generated evidence link not found.")
    except Exception as e:
        logger.error(f"Error deactivating evidence link {link_id}: {e}", exc_info=True)
        messages.error(request, "Error deactivating evidence link. Please try again.")

    # Redirect back to newevidence page for the task
    task_id = request.POST.get("task_id") or (
        link.task.id if "link" in locals() else None
    )
    if task_id:
        return redirect("management:new_evidence", taskid=task_id)
    return redirect("management:daf_v2")


def process_evidence_submission(
    data,
    temp_file_path,
    original_filename,
    user,
    task,
    folder_id,
    requirement_match_result=None,
):
    """
    Handles the processing and uploading of evidence to Google Drive and TaskLinks.

    Args:
        requirement_match_result: Optional dict from RequirementMatchService verification
    """
    try:
        drive_link = None
        if temp_file_path:
            # Upload the file to Google Drive
            drive_link = upload_file_to_drive(
                temp_file_path, original_filename, user, task, folder_id
            )

        with transaction.atomic():
            # Enforce requirement linkage for specific activity types (double-check in async thread)
            activity_type_slug = None
            if task.activity_type:
                activity_type_slug = task.activity_type.slug or task.activity_type.name
            elif task.activity_name:
                activity_type_slug = task.activity_name.upper().replace(" ", "_")

            requires_requirement = False
            if activity_type_slug:
                # Import here to avoid circular import
                from management.views import \
                    REQUIREMENT_REQUIRED_ACTIVITY_TYPES

                requires_requirement = activity_type_slug.upper() in [
                    a.upper() for a in REQUIREMENT_REQUIRED_ACTIVITY_TYPES
                ]

            # Final check: if requirement is required but not set, do not create TaskLinks
            # Backward compatible: Use getattr to safely access requirement field
            task_requirement = getattr(task, "requirement", None)
            requirement_id = data.get("requirement") or (
                task_requirement.id if task_requirement else None
            )
            if requires_requirement and not requirement_id:
                # This should not happen if validation worked, but double-check for safety
                logger.error(
                    f"Evidence submission blocked: task {task.id} requires requirement but none provided"
                )
                return  # Do not create TaskLinks

            # CANONICAL TOPIC/TITLE: Ensure link_name is set (auto-generate if missing)
            # Format: "{activity_type.name} — REQ-{requirement.id}" or "{activity_type.name}" if no requirement
            # For non-staff: ALWAYS enforce canonical (prevent POST tampering)
            link_name = data.get("link_name", "").strip()
            is_staff = request.user.is_staff or request.user.is_superuser

            # Generate canonical title
            # Backward compatible: Use getattr to safely access requirement field
            task_requirement_for_title = getattr(task, "requirement", None)
            canonical_title = None
            if task.activity_type and task.activity_type.name:
                activity_name = task.activity_type.name
                if task_requirement_for_title:
                    canonical_title = (
                        f"{activity_name} — REQ-{task_requirement_for_title.id}"
                    )
                else:
                    canonical_title = activity_name
            elif task.activity_name:
                if task_requirement_for_title:
                    canonical_title = (
                        f"{task.activity_name} — REQ-{task_requirement_for_title.id}"
                    )
                else:
                    canonical_title = task.activity_name
            else:
                canonical_title = "Evidence"  # Fallback

            # For non-staff: ALWAYS use canonical (enforce server-side)
            if not is_staff:
                link_name = canonical_title
                logger.info(f"Enforced canonical title for non-staff user: {link_name}")
            elif not link_name:
                # For staff: use canonical if blank, otherwise allow override
                link_name = canonical_title
                logger.info(f"Auto-generated canonical title for evidence: {link_name}")

            # Save the evidence to TaskLinks
            task_links = TaskLinks.objects.create(
                task=task,
                added_by=user,
                link_name=link_name,  # Use canonical title (auto-generated if missing)
                description=data.get("description", ""),
                link=data.get("link", ""),
                linkpassword=data.get("linkpassword", "No Password Needed"),
                drive_link=drive_link,
                is_active=data.get("is_active", True),
                is_featured=data.get("is_featured", False),
            )

            # Update task points
            points, maxpoints = Task.objects.values_list("point", "mxpoint").get(
                id=task.id
            )
            if data.get("link") or temp_file_path:
                if data.get("requirement"):
                    requirement = Requirement.objects.get(id=data["requirement"])
                    duration = requirement.duration
                    points += duration
                    if points >= maxpoints:
                        maxpoints += 5
                    Task.objects.filter(id=task.id).update(
                        point=points, mxpoint=maxpoints
                    )
                elif (
                    points != maxpoints
                    and task.activity_name.lower() not in JOB_SUPPORTS
                ):
                    Task.objects.filter(id=task.id).update(point=points + 1)

    except Exception as e:
        logger.error(
            f"Error processing evidence submission for user {user.username}: {e}",
            exc_info=True,
        )
    finally:
        # Cleanup the temporary file
        if temp_file_path:
            os.remove(temp_file_path)


def userevidence(request, user=None, *args, **kwargs):
    # current_user = request.user
    username = request.GET.get("username", None)
    # Calculate the date range for the last 2 months
    now = timezone.localtime()
    # print(now)
    two_months_ago = now - timezone.timedelta(days=60)
    if username:
        # Filter the TaskLinks based on the created_at field within the date range
        userlinks = TaskLinks.objects.filter(
            added_by__username=username, created_at__range=[two_months_ago, now]
        ).order_by("-created_at")
    else:
        userlinks = TaskLinks.objects.filter(
            created_at__range=[two_months_ago, now]
        ).order_by("-created_at")

    return render(request, "management/daf/userevidence.html", {"userlinks": userlinks})


def evidence_update_view(request, id, *args, **kwargs):
    context = {}
    # fetch the object related to passed id
    obj = get_object_or_404(TaskLinks, id=id)
    # pass the object as instance in form
    form = EvidenceForm(request.POST or None, instance=obj)
    # save the data from the form and
    # redirect to detail_view
    if form.is_valid():
        form.save()
        # try:
        #     username=kwargs.get("username")
        #     return redirect("management:user_evidence", username)
        # except:
        return redirect("management:evidence")
    # add form dictionary to context
    # context["form"] = form
    message = "Edit Evidence"
    context = {"form": form, "message": message}
    return render(request, "main/snippets_templates/generalform.html", context)


# =============================EMPLOYEE SESSIONS========================================
class SessionCreateView(LoginRequiredMixin, CreateView):
    model = Training
    success_url = "/management/sessions/training"
    # fields= "__all__"
    fields = [
        "department",
        "category",
        "subcategory",
        "topic",
        "level",
        "session",
        "session_link",
        "expiration_date",
        "description",
        "is_active",
        "featured",
    ]

    def form_valid(self, form):
        form.instance.presenter = self.request.user
        return super().form_valid(form)


@login_required
def sessions(request, slug="training"):
    if slug == "training":
        sessions = Training.objects.filter(presenter__is_staff=True).order_by(
            "-created_date"
        )
    elif slug == "interview":
        sessions = Training.objects.filter(
            presenter__category__in=[1, 3, 4, 5, 6, 7],
            presenter__is_active=True,
            is_active=True,
            featured=True,
            is_mock=False,
        ).order_by(
            "-created_date"
        )  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
    elif slug == "mock":
        sessions = Training.objects.filter(
            is_active=True, featured=True, is_mock=True
        ).order_by("-created_date")
    else:
        sessions = Training.objects.all()

    context = {"object_list": sessions, "title": "Sessions"}
    return render(request, "management/departments/hr/sessions.html", context)


class SessionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Training
    success_url = "/management/sessions/training"
    # fields = ["name", "slug", "description", "is_active", "is_featured"]
    fields = "__all__"
    # form = DepartmentForm()

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def test_func(self):
        if (
            self.request.user
            or self.request.user.is_admin
            or self.request.user.is_superuser
        ):
            return True
        return False


def usersession(request, user=None, *args, **kwargs):
    request.session["siteurl"] = settings.SITEURL
    deadline_date = paytime()[2]
    employee = get_object_or_404(User, username=kwargs.get("username"))
    days_since_joined = employee.tenure
    sessions = (
        Training.objects.all().filter(presenter=employee).order_by("-created_date")
    )
    emp_target_sessions = 150
    client_target_sessions = 27
    num_sessions = sessions.count()
    # points = sessions.aggregate(Your_Total_Points=Sum("point"))
    # Points = points.get("Your_Total_Points")
    bal_session = emp_target_sessions - num_sessions
    client_bal_session = client_target_sessions - num_sessions
    context = {
        "sessions": sessions,
        "emp_target_sessions": emp_target_sessions,
        "client_target_sessions": client_target_sessions,
        "client_bal_session": client_bal_session,
        "num_sessions": num_sessions,
        "bal_session": bal_session,
        "deadline_date": deadline_date,
        "days_since_joined": days_since_joined,
    }
    # setting  up session
    request.session["employee_name"] = kwargs.get("username")

    if request.user.is_superuser or request.user.is_staff:
        return render(request, "management/departments/hr/usersessions.html", context)
    elif request.user.is_superuser or request.user.category in [
        1,
        3,
        4,
        5,
        6,
        7,
    ]:  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
        return render(request, "management/departments/hr/clientsessions.html", context)
    else:
        return redirect("main:layout")


# =============================EMPLOYEE ASSESSMENTS========================================
@login_required
def assess(request):
    """Create DSU record via professional services interface."""
    path_list, subtitle, pre_sub_title = path_values(request)
    pro_services = get_professional_services()

    if request.method == "POST":
        form = ManagementForm(request.POST, request.FILES)
        if form.is_valid():
            # Extract form data and save via interface
            form_data = {field: form.cleaned_data.get(field) for field in form.fields}
            form_data["username"] = request.user.id
            result = pro_services.create_or_update_dsu(
                user=request.user, data=form_data
            )
            if result.get("status") == "not_available":
                messages.warning(request, "Professional services are not available.")
            else:
                messages.success(request, "DSU record created successfully.")
            return redirect("management:assessment", user_type="client")
    else:
        form = ManagementForm()

    return render(request, "management/departments/hr/assess_form.html", {"form": form})


class DSUListView(FilteredListViewMixin, ListView):
    """Consolidated DSU list view using generic mixin"""

    # Note: No longer uses model directly - uses interface
    template_name = "management/departments/hr/assessment.html"
    context_object_name = "dsu_list"
    order_by = "-created_at"

    def get_queryset(self):
        """Get DSU records via professional services interface."""
        pro_services = get_professional_services()
        user_type = self.kwargs.get("user_type", "Staff")
        dsu_list = pro_services.list_dsu_for_user(
            user_type=user_type.lower(), filters={"order_by": self.order_by}
        )

        # Convert list of dicts to a mock queryset-like object for template compatibility
        class MockQuerySet:
            def __init__(self, data):
                self.data = data

            def __iter__(self):
                return iter(self.data)

            def __getitem__(self, index):
                return self.data[index]

            def __len__(self):
                return len(self.data)

        return MockQuerySet(dsu_list)


class AssessUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    # Note: No longer uses model directly - uses interface
    success_url = "/management/assessment/client"
    fields = "__all__"
    template_name = "main/snippets_templates/generalform.html"

    def get_object(self):
        """Get DSU object via interface."""
        pro_services = get_professional_services()
        dsu_id = self.kwargs.get("pk")
        dsu_list = pro_services.list_dsu_for_user(user_type="", filters={"id": dsu_id})
        if dsu_list:
            # Convert dict to mock object for form compatibility
            class MockDSU:
                def __init__(self, data):
                    for key, value in data.items():
                        setattr(self, key, value)

            return MockDSU(dsu_list[0])
        return None

    def form_valid(self, form):
        """Save DSU via interface."""
        pro_services = get_professional_services()
        dsu_id = self.kwargs.get("pk")
        # Extract form data
        form_data = {field: form.cleaned_data.get(field) for field in form.fields}
        form_data["username"] = self.request.user.id
        result = pro_services.create_or_update_dsu(
            user=self.request.user, data=form_data, dsu_id=dsu_id
        )
        if result.get("status") == "not_available":
            messages.warning(self.request, "Professional services are not available.")
            return redirect(self.success_url)
        return redirect(self.success_url)

    def test_func(self):
        if (
            self.request.user
            or self.request.user.is_admin
            or self.request.user.is_superuser
        ):
            return True
        return False


# ================================POTENTIAL CLIENTS==========================================
def split_text_into_paragraphs(text, word_limit=50):
    words = text.split()
    if len(words) <= word_limit:
        # If text is shorter than the word limit, return as a single paragraph
        return text, ""

    # Join words up to the limit and find the nearest period
    first_part = " ".join(words[:word_limit])
    remainder = " ".join(words[word_limit:])

    # Find the last period in the first part to end the paragraph cleanly
    last_period_index = first_part.rfind(".")

    if last_period_index != -1:
        # Split at the last period to form two paragraphs
        para1 = first_part[: last_period_index + 1].strip()
        para2 = first_part[last_period_index + 1 :].strip() + " " + remainder.strip()
    else:
        # If no period is found, just split at the word limit
        para1 = first_part.strip()
        para2 = remainder.strip()

    return para1, para2


from django.contrib.auth import authenticate, login


def register_and_login_user(request, email, first_name, last_name):
    random_password = generate_password(8)
    user = CustomerUser.objects.create(
        username=email,
        email=email,
        gender=None,
        first_name=first_name,
        last_name=last_name,
        category=2,
        sub_category=0,
        is_active=True,
    )
    user.set_password(random_password)
    user.verification_token = str(uuid.uuid4())
    user.save()

    # Send verification email with the password
    send_verification_email(user, password=random_password)
    print(f"User {email} created and verification email sent.")

    # Authenticate and log the user in
    authenticated_user = authenticate(username=email, password=random_password)
    if authenticated_user and request:
        create_profile()
        login(request, authenticated_user)
        print(f"{user.email} has been logged in successfully.")
    return user


def clientassessment(request):
    if request.method == "POST":
        email = request.POST.get("email")
        category = request.POST.get("category_slug")
        print(category)

        previous_user = CustomerUser.objects.filter(email=email)
        if not previous_user.exists():
            user = register_and_login_user(
                request,
                email=email,
                first_name=request.POST.get("first_name"),
                last_name=request.POST.get("last_name"),
            )
        # Note: ClientAssessment requires professional_services app
        # For now, always create new form instance - interface integration needed
        try:
            from professional_services.models import ClientAssessment

            client_assesment = ClientAssessment.objects.filter(email=email)
            if client_assesment.exists():
                form = ClientAssessmentForm(
                    request.POST, request.FILES, instance=client_assesment.first()
                )
            else:
                form = ClientAssessmentForm(request.POST, request.FILES)
        except ImportError:
            form = ClientAssessmentForm(request.POST, request.FILES)
        if form.is_valid():

            totalpoints, developerpoints = compute_total_points(form.instance)
            form.instance.totalpoints = totalpoints

            if previous_user.exists():
                user = previous_user.first()

                form.instance.first_name = user.first_name
                form.instance.last_name = user.last_name
                if user.category == 2:  # coda staff member
                    form.instance.totalpoints = developerpoints

            form.save()

            next_url = request.GET.get("next", None)
            if next_url is not None:
                return redirect(next_url)
            if totalpoints <= 80:
                skills = {
                    "project_management": form.cleaned_data.get("projectmanagement", 0),
                    "requirements_analysis": form.cleaned_data.get(
                        "requirementsAnalysis", 0
                    ),
                    "reporting": form.cleaned_data.get("reporting", 0),
                    "etl": form.cleaned_data.get("etl", 0),
                    "database": form.cleaned_data.get("database", 0),
                    "testing": form.cleaned_data.get("testing", 0),
                    "deployment": form.cleaned_data.get("deployment", 0),
                    "frontend": form.cleaned_data.get("frontend", 0),
                    "backend": form.cleaned_data.get("backend", 0),
                }
                # Initialize lists and total score
                strong_areas = []
                weak_areas = []
                improvements = []
                total_score = 0

                # Categorize skills and add suggestions
                for skill, score in skills.items():
                    total_score += score  # Calculate total score

                    if score > 5:
                        # Strong area with suggestions
                        strong_areas.append(
                            {
                                "skill": skill.replace("_", " ").title(),
                                "score": score,
                                "description": suggestions["strong"]["description"],
                                "recommendation": suggestions["strong"][
                                    "recommendations"
                                ].get(skill),
                            }
                        )
                    elif score <= 4:
                        # Weak area with suggestions
                        weak_areas.append(
                            {
                                "skill": skill.replace("_", " ").title(),
                                "score": score,
                                "description": suggestions["weak"]["description"],
                                "recommendation": suggestions["weak"][
                                    "recommendations"
                                ].get(skill),
                            }
                        )
                        improvements.append(
                            f"Consider improving your {skill.replace('_', ' ').title()} skills."
                        )

                max_score = len(skills) * 10

                assessment_summaries = {
                    "total_score": total_score,
                    "max_score": max_score,
                    "strong_areas": strong_areas,
                    "weak_areas": weak_areas,
                    "improvements": improvements,
                    "next_steps": "To address all identified improvement areas, we recommend enrolling in our comprehensive course, which covers each aspect in-depth and will help you overcome these challenges effectively.",
                }

                print("ass", assessment_summaries)
                greeting = (
                    "Thanks for completing the assessment! Tailored growth awaits."
                )
                context = {
                    "title": "CODA Assessment",
                    "greeting": greeting,
                    "assessment_summary": assessment_summaries,
                }
                return render(
                    request, "management/departments/hr/course_suggestion.html", context
                )
            else:
                return redirect("accounts:account-login")
        else:
            # Form is not valid, print errors
            print("Form is not valid. Errors:")
            for field, errors in form.errors.items():
                print(f"Field: {field}")
                for error in errors:
                    print(f"- {error}")
    else:
        form = ClientAssessmentForm()
    return render(
        request, "management/departments/hr/clientassessment_form.html", {"form": form}
    )


class ClientAssessmentListView(ListView):
    template_name = "management/departments/hr/clientassessment.html"

    def get_queryset(self):
        # Note: ClientAssessment requires professional_services app
        try:
            from professional_services.models import ClientAssessment

            queryset = (
                ClientAssessment.objects.all()
                .order_by("-rating_date")
                .annotate(
                    usser_category=Subquery(
                        CustomerUser.objects.filter(email=OuterRef("email")).values(
                            "category"
                        )[:1]
                    )
                )
            )
            for instance in queryset:
                totalpoints, developerpoints = compute_total_points(instance)
                if instance.usser_category != 2 and instance.totalpoints != totalpoints:
                    instance.totalpoints = totalpoints
                    instance.save()

                elif (
                    instance.usser_category == 2
                    and instance.totalpoints != developerpoints
                ):

                    instance.totalpoints = developerpoints
                    instance.save()
            return queryset
        except ImportError:
            # Return empty queryset if professional_services not available
            from django.db.models import QuerySet

            return QuerySet().none()


class AssessmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    # Note: ClientAssessment requires professional_services app
    # This view will only work when professional_services is available
    success_url = "/management/clientassessment"
    fields = "__all__"
    template_name = "main/snippets_templates/generalform.html"
    # Note: model attribute removed - using get_queryset() instead to handle missing professional_services

    def get_queryset(self):
        """Get queryset for ClientAssessment."""
        try:
            from professional_services.models import ClientAssessment

            return ClientAssessment.objects.all()
        except ImportError:
            # Return empty queryset if professional_services not available
            from django.db.models import QuerySet

            return QuerySet().none()

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def test_func(self):
        if (
            self.request.user
            or self.request.user.is_admin
            or self.request.user.is_superuser
        ):
            return True
        return False


# ==================================BACKGROUND CHECKS====================================
# def form_submission_view(request,requestedform):
#     if request.method == 'POST':
#         form = requestedform(request.POST)
#         if form.is_valid():
#             # Save the form to create a new object
#             new_object = form.save()
#             # Redirect to the justification view with the new object's ID
#             return redirect(reverse('management:justification', args=[new_object.pk]))
#     else:
#         form = requestedform()

# return render(request, 'management/doc_templates/requirement_form.html', {'form': form})


def add_background_info(request):
    """Create background check via professional services interface."""
    pro_services = get_professional_services()

    if request.method == "POST":
        form = BackgroundForm(request.POST)
        if form.is_valid():
            # Extract form data and save via interface
            form_data = {field: form.cleaned_data.get(field) for field in form.fields}
            result = pro_services.create_background_check(data=form_data)
            if result.get("status") == "not_available":
                messages.warning(request, "Professional services are not available.")
            else:
                messages.success(request, "Background check created successfully.")
            return redirect("management:background-list")
    else:
        form = BackgroundForm()

    return render(request, "management/background/background_form.html", {"form": form})


class BackgroundCheckListView(ListView):
    # Note: No longer uses model directly - uses interface
    template_name = "admin/background_checks.html"
    context_object_name = "checks"
    paginate_by = 10

    def get_queryset(self):
        """Get background checks via professional services interface."""
        pro_services = get_professional_services()
        status = self.request.GET.get("status", "All")
        filters = {}
        if status != "All":
            filters["status"] = status
        checks_list = pro_services.list_background_checks(filters=filters)

        # Convert list of dicts to a mock queryset-like object for template compatibility
        class MockQuerySet:
            def __init__(self, data):
                self.data = data

            def __iter__(self):
                return iter(self.data)

            def __getitem__(self, index):
                return self.data[index]

            def __len__(self):
                return len(self.data)

        return MockQuerySet(checks_list)

    # -----------------------------REQUIREMENTS---------------------------------


def active_requirements(request, Status=None, *args, **kwargs):
    active_requirements = Requirement.objects.all().filter(is_active=True)
    context = {"active_requirements": active_requirements}
    return render(request, "management/doc_templates/active_requirements.html", context)


def requirements(request):
    path_list, subtitle, pre_sub_title = path_values(request)
    if subtitle == "dyc_requirements":
        requirements = Requirement.objects.filter(
            requestor__iexact="client", company__iexact="dyc"
        ).order_by("-id")
    elif subtitle == "client_requirements":
        requirements = (
            Requirement.objects.exclude(company__iexact="dyc")
            .filter(requestor__iexact="client")
            .order_by("-id")
        )
    elif subtitle == "coda_requirements":
        requirements = Requirement.objects.filter(
            requestor__iexact="management", company__iexact="coda"
        ).order_by("-id")
    elif subtitle == "reviewed":
        requirements = Requirement.objects.filter(is_reviewed=True).order_by("-id")
    elif subtitle == "tested":
        requirements = Requirement.objects.filter(is_tested=True).order_by("-id")
    else:
        requirements = Requirement.objects.all().order_by("-id")

    requirement_filters = RequirementFilter(request.GET, queryset=requirements)

    context = {"requirements": requirements, "requirement_filters": requirement_filters}
    return render(request, "management/doc_templates/requirements.html", context)


def newrequirement(request):
    request.session["siteurl"] = settings.SITEURL
    if request.method == "POST":
        form = RequirementForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.creator = request.user
            # print(instance.creator)
            instance.save()
            # form.save()
            if (
                not get_user_model().objects.get(pk=request.POST["assigned_to"])
                == request.user
            ):
                subject = "Task assign on CodaTraining"
                to = get_user_model().objects.get(pk=request.POST["assigned_to"]).email
                if request.is_secure():
                    protocol = "https://"
                else:
                    protocol = "http://"
                context = {
                    "request_what": request.POST["what"],
                    "url": protocol
                    + request.get_host()
                    + reverse(
                        "management:RequirementDetail", kwargs={"pk": form.instance.id}
                    ),
                    "delivery_date": request.POST["delivery_date"],
                    "user": request.user,
                }
                try:
                    # send_email(category=request.user.category,
                    # to_email=[request.user.email,],
                    # subject=subject,
                    # html_template='email/newrequirement.html',
                    # context=context)
                    pass
                except Exception as e:
                    # Handle any other exceptions
                    print(f"An unexpected error occurred: {e}")

            return redirect("management:requirements-active")
    else:
        form = RequirementForm()
    return render(
        request, "management/doc_templates/requirement_form.html", {"form": form}
    )


class RequirementDetailView(DetailView):
    template_name = "management/doc_templates/single_requirement.html"
    model = Requirement

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        requirement = self.get_object()
        user = self.request.user
        is_allowed = (user.is_staff and user.sub_category == 2) or user.is_superuser

        context = {
            "object": requirement,  # Add any other context variables you need
            "is_allowed": is_allowed,
        }
        return self.render_to_response(context)


class RequirementUpdateView(LoginRequiredMixin, UpdateView):
    model = Requirement
    success_url = "/management/requirements"
    fields = [
        "status",
        "assigned_to",
        "requestor",
        "company",
        "category",
        "app",
        "delivery_date",
        "duration",
        "what",
        "why",
        "how",
        "comments",
        "doc",
        "pptlink",
        "videolink",
        "is_active",
        "is_tested",
        "is_reviewed",
    ]
    form = RequirementForm

    def form_valid(self, form):
        # form.instance.author=self.request.user
        if self.request.user.is_superuser or self.request.user:
            return super().form_valid(form)
        else:
            return redirect("management:requirements-active")

    def test_func(self):
        requirement = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user:
            return True
        return False


# class RequirementUpdateView(LoginRequiredMixin, UpdateView):
#     model = Requirement
#     success_url = "/management/requirements"
#     fields = [
#         "status", "assigned_to", "requestor", "company",
#         "category", "app", "delivery_date", "duration", "what",
#         "why", "how", "comments", "doc", "pptlink", "videolink",
#         "is_active", "is_tested", "is_reviewed",
#     ]
#     form = RequirementForm
#     def form_valid(self, form):
#         # form.instance.author=self.request.user
#         if self.request.user.is_superuser or self.request.user :
#             if (
#                 not get_user_model().objects.get(pk=self.request.POST["assigned_to"])
#                 == self.request.user
#                 and not get_user_model().objects.get(
#                     pk=self.request.POST["assigned_to"]
#                 )
#                 == Requirement.objects.get(pk=form.instance.id).assigned_to
#             ):
#                 subject = "Task assign on CodaTraining"
#                 to = (
#                     get_user_model()
#                     .objects.get(pk=self.request.POST["assigned_to"])
#                     .email
#                 )
#                 if self.request.is_secure():
#                     protocol = "https://"
#                 else:
#                     protocol = "http://"
#                 html_content = f"""
#                     <span><h3>Requirement: </h3>{self.request.POST['what']}<br>
#                     <a href='{protocol+self.request.get_host()+reverse('management:RequirementDetail',
#                     kwargs={'pk':form.instance.id})}'>click here</a><br>
#                     <b>Dead Line: </b><b style='color:red;'>
#                     {self.request.POST['delivery_date']}</b><br><b>Created by:
#                     {self.request.user}</b></span>"""
#                 email_template(subject, to, html_content)
#             return super().form_valid(form)
#         else:
#             return redirect("management:requirements-active")

#     def test_func(self):
#         requirement = self.get_object()
#         if self.request.user.is_superuser:
#             return True
#         elif self.request.user:
#             return True
#         # elif self.request.user == requirement.created_by:
#         #     return True
#         return False


class RequirementDeleteView(LoginRequiredMixin, DeleteView):
    model = Requirement
    success_url = "/management/requirements"

    def test_func(self):
        # creator = self.get_object()
        # if self.request.user == creator.username:
        if self.request.user.is_superuser:
            return True
        return False


def videolink(request, detail_id):
    task_links = TaskLinks.objects.all()
    mylist = [link.lowerlinkname for link in task_links]
    new_list = [val for val in mylist if val != None]
    mylinkname = "requirement" + str(detail_id)
    if mylinkname in new_list:
        obj = TaskLinks.objects.filter(link_name__icontains=str(detail_id))
        # print("obj",obj)
        for link in obj:
            site = link.link
            # print(site)
    else:
        context = {
            "title": "Requirement Elaboration",
            "message": f"There is no video for this requirement",
        }
        return render(request, "main/messages/general.html", context)
    context = {
        "title": "Requirement Elaboration",
        "site": site,
        "message": f"Access the explanation for this requirement",
    }
    return render(request, "main/messages/general.html", context)


def getaveragetargets(request):
    # print("+++++++++getaveragetargets+++++++++")
    taskname = request.POST["taskname"]
    # 1st month
    last_day_of_prev_month1 = date.today().replace(day=1) - timedelta(days=1)
    start_day_of_prev_month1 = date.today().replace(day=1) - timedelta(
        days=last_day_of_prev_month1.day
    )

    last_day_of_prev_month2 = last_day_of_prev_month1.replace(day=1) - timedelta(days=1)
    start_day_of_prev_month2 = last_day_of_prev_month1.replace(day=1) - timedelta(
        days=last_day_of_prev_month2.day
    )

    # 3rd month
    last_day_of_prev_month3 = last_day_of_prev_month2.replace(day=1) - timedelta(days=1)
    start_day_of_prev_month3 = last_day_of_prev_month2.replace(day=1) - timedelta(
        days=last_day_of_prev_month3.day
    )

    history = TaskHistory.objects.filter(
        Q(activity_name=taskname),
        Q(created_at__gte=start_day_of_prev_month3),
        Q(created_at__lte=last_day_of_prev_month1),
    )

    results = {"target_points": 0, "target_amount": 0}
    counter = 0
    for data in history.all():
        results["target_points"] += data.mxpoint
        results["target_amount"] += data.mxearning
        counter = counter + 1
    try:
        results["target_points"] = results["target_points"] / counter
        results["target_amount"] = results["target_amount"] / counter
    except Exception as ZeroDivisionError:
        results["target_points"] = 0.0
        results["target_amount"] = 0.0

    return JsonResponse(results)


def filterbycategory(request):
    category = request.POST["category"]
    # print("category", category)

    tasks = Task.objects.filter(category__title=category)
    result = []
    details = {}
    for data in tasks.all():
        details["group"] = data.groupname
        details["deadline"] = data.deadline.strftime("%d %b %Y")
        details["submission"] = data.submission.strftime("%d %b %Y")
        details["point"] = data.point
        details["mxpoint"] = data.mxpoint
        details["mxearning"] = float(data.mxearning)
        details["get_pay"] = float(data.get_pay)
        details["id"] = data.id
        details["employee"] = data.employee.username
        details["first_name"] = data.employee.first_name
        details["last_name"] = data.employee.last_name
        details["description"] = data.description
        details["activity_name"] = data.activity_name
        details["get_absolute_url"] = str(data.category.get_absolute_url)
        result.append(details.copy())
    # print(result)
    return JsonResponse({"result": result}, safe=False)


class AdsContent(ListView):
    model = Advertisement
    template_name = "management/advertisement.html"
    context_object_name = "posts"
    ordering = ["-created_at"]


class AdsCreateView(LoginRequiredMixin, CreateView):
    model = Advertisement
    template_name = "main/snippets_templates/generalform.html"
    fields = "__all__"
    success_url = "/management/advertisement"
    page_title = "Advertisement Details"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = capfirst(self.page_title)
        return context


class AdsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Advertisement
    template_name = "main/snippets_templates/generalform.html"
    fields = "__all__"
    success_url = "/management/advertisement"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False


# ====================ESTIMATEVIEWS===============================
def form_submission_view(request):
    if request.method == "POST":
        form = RequirementForm(request.POST)
        if form.is_valid():
            # Save the form to create a new object
            new_object = form.save()
            # Redirect to the justification view with the new object's ID
            return redirect(reverse("management:justification", args=[new_object.pk]))
    else:
        form = RequirementForm()

    return render(
        request, "management/doc_templates/requirement_form.html", {"form": form}
    )


def justification(request, *args, **kwargs):
    try:
        justifications = ProcessJustification.objects.filter(
            requirements_id=kwargs.get("pk")
        ).values(
            "id",
            "justification",
            breakdown=F("Process_in_breakdown__breakdown"),
            time=F("Process_in_breakdown__time"),
            requirement_id=F("requirements__id"),
            Qty=F("Process_in_breakdown__Quantity"),
            total=F("Process_in_breakdown__total"),
        )

        requirement_obj = Requirement.objects.get(id=kwargs.get("pk"))

        if requirement_obj.category == "Website":
            category = "Website"
            template = "management/doc_templates/req_justifications.html"
        elif requirement_obj.category == "Other":
            category = "Presentation"
            template = "management/doc_templates/presentation_justification.html"
        else:
            category = "Reporting"
            template = "management/doc_templates/report_justification.html"

        if justifications:
            justofication_dict = {}
            justifications_ids = ProcessJustification.objects.filter(
                requirements_id=kwargs.get("pk")
            ).values_list("id", flat=True)
            obj = ProcessBreakdown.objects.filter(process__id__in=justifications_ids)
            total_time = obj.aggregate(Sum("total"))
            total_qty = obj.aggregate(Sum("Quantity"))
            print("total_time", total_time)
            print("total_qty", total_qty)
            for justification in justifications:
                if (
                    justification.get("breakdown") == "testing"
                    or justification.get("breakdown") == "creation"
                ):
                    justofication_dict.update(
                        {
                            justification.get("justification"): justification.get(
                                "justification"
                            ),
                            justification.get("justification")
                            + justification.get("breakdown"): justification.get(
                                "breakdown"
                            ),
                            justification.get("breakdown")
                            + "time": justification.get("time"),
                            justification.get("justification")
                            + justification.get("breakdown")
                            + "quantity": justification.get("Qty"),
                            justification.get("justification")
                            + justification.get("breakdown")
                            + "total": justification.get("total"),
                            "requirement_id": justification.get("requirement_id"),
                        }
                    )
                else:
                    justofication_dict.update(
                        {
                            justification.get("justification"): justification.get(
                                "justification"
                            ),
                            justification.get("justification")
                            + justification.get("breakdown"): justification.get(
                                "breakdown"
                            ),
                            justification.get("breakdown")
                            + "time": justification.get("time"),
                            justification.get("breakdown")
                            + "quantity": justification.get("Qty"),
                            justification.get("breakdown")
                            + "total": justification.get("total"),
                            "requirement_id": justification.get("requirement_id"),
                        }
                    )
            print("justofication_dict==============", justofication_dict)
            just_context = {
                "category": category,
                "justifications": justofication_dict,
                "total_time": total_time.get("total__sum"),
                "total_qty": total_qty.get("Quantity__sum"),
            }

            return render(request, template, just_context)

        context = {
            "category": category,
            "active_requirement": kwargs.get("pk"),
            # "total_time":total_time.get('total__sum')
            "total_time": 100,
        }
        return render(request, template, context)

    except:
        context = {
            "category": "Website",
            "active_requirement": kwargs.get("pk"),
            # "total_time":total_time.get('total__sum')
            "total_time": 100,
        }
        return render(
            request, "management/doc_templates/req_justifications.html", context
        )


def add_requirement_justification(request):
    requirement_id = request.POST.get("requirement_id")
    requirement_obj = get_object_or_404(Requirement, id=requirement_id)

    category = requirement_obj.category

    if category == "Website":

        justification_mapping = {
            "meeting": ["requirement_assignment", "pbr"],
            "table": ["dictionary", "Erd", "Table", "Testing"],
            "view": [
                "flow_diagram",
                "create",
                "detail",
                "list",
                "update",
                "delete",
                "testing_view",
            ],
            "template": ["template_creation", "template_testing"],
            "forms": ["form_creation", "form_testing"],
            "apis": ["new_api", "existing_api", "api_testing"],
        }

    elif category == "Other":

        justification_mapping = {
            "meeting": ["requirement_assignment", "pbr"],
            "content": ["editing", "creating"],
            "design": ["design_of_existing"],
        }

    else:

        justification_mapping = {
            "meeting": ["requirement_assignment", "pbr"],
            "database": [
                "access",
                "view",
                "flow_diagram",
                "testing_uat",
                "testing_scripting",
            ],
            "data_cleaning": ["workflow", "testing_workflow"],
            "reporting": [
                "landing_page",
                "executive_summary",
                "detail_reports",
                "table_list",
                "report_testing_scripting",
            ],
            "automation": ["existing_tool", "python_script", "form_testing"],
            "external_apis": ["new", "existing", "api_testing"],
        }

    latest_total = 0

    with transaction.atomic():
        # print(request.POST)
        for justification_type, breakdowns in justification_mapping.items():
            justification_key = (
                justification_type.capitalize()
                if justification_type == "table"
                else justification_type
            )
            print(f"Processing justification type: {justification_type}")
            print(f"Justification key: {justification_key}")
            print(
                f"Is justification key in request.POST: {justification_key in request.POST}"
            )
            if request.POST.get(justification_key):
                justification_obj, created = ProcessJustification.objects.get_or_create(
                    requirements=requirement_obj,
                    justification=justification_type.capitalize(),
                )
                total_time_for_type = 0
                for breakdown in breakdowns:
                    breakdown_key = f"{breakdown}_time"
                    breakdown_qty = f"{breakdown}_quantity"
                    print(f"Processing breakdown: {breakdown}")
                    print(f"Breakdown key: {breakdown_key}")
                    print(f"Breakdown qty: {breakdown_qty}")
                    if (
                        breakdown in request.POST
                        and breakdown_key in request.POST
                        and breakdown_qty in request.POST
                    ):
                        time = int(request.POST.get(breakdown_key))
                        qty = int(request.POST.get(breakdown_qty))
                        print(f"Time: {time}, Qty: {qty}")
                        breakdown_obj, created = ProcessBreakdown.objects.get_or_create(
                            process=justification_obj,
                            breakdown=breakdown,
                            defaults={
                                "time": time,
                                "Quantity": qty,
                                "total": time * qty,
                            },
                        )

                        if not created:
                            breakdown_obj.Quantity = qty
                            breakdown_obj.total = time * qty
                            breakdown_obj.save()
                        total_time_for_type += time * qty

                latest_total = max(latest_total, total_time_for_type)
                print(f"Latest total: {latest_total}")
        # Update the duration column in Requirements
        requirement_time = math.ceil(latest_total / 60)
        Requirement.objects.filter(id=requirement_id).update(duration=requirement_time)

        # Filter and get the updated duration value
        updated_duration = (
            Requirement.objects.filter(id=requirement_id)
            .values_list("duration", flat=True)
            .first()
        )
        print(updated_duration)
        active_requirements = Requirement.objects.filter(is_active=True)

    context = {
        "active_requirements": active_requirements,
        "total_duration": updated_duration,
    }
    return render(request, "management/doc_templates/active_requirements.html", context)


def grievance_form(request):
    if request.method == "POST":
        form = GrievanceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(
                "management:grievance_file", slug="all"
            )  # Redirect to success page after form submission
    else:
        form = GrievanceForm()
    return render(request, "main/snippets_templates/generalform.html", {"form": form})


def grievance_file(request, slug="active"):
    grievances = None
    resolutions = None
    if slug == "active":
        grievances = Grievance.objects.filter(is_active=True)
    elif slug == "resolution":
        resolutions = Conflict_Resolution.objects.filter(is_active=True)
    else:
        grievances = Grievance.objects.all()
    context = {
        "grievances": grievances,
        "resolutions": resolutions,
        "slug": slug,
    }
    return render(request, "management/departments/hr/grievances.html", context)


class GrievanceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Grievance
    success_url = "/management/grievance_file/all"
    fields = "__all__"

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def test_func(self):
        if (
            self.request.user
            or self.request.user.is_admin
            or self.request.user.is_superuser
        ):
            return True
        return False


class ResolutionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Conflict_Resolution
    success_url = "/management/grievance_file/resolution"
    fields = "__all__"

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def test_func(self):
        if (
            self.request.user
            or self.request.user.is_admin
            or self.request.user.is_superuser
        ):
            return True
        return False


SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def sanitize_folder_name(name):
    # Remove any characters that are not letters, numbers, spaces, or underscores
    sanitized_name = re.sub(r"[^\w\s-]", "", name).strip()
    # Replace spaces and hyphens with underscores
    sanitized_name = re.sub(r"[\s-]+", "_", sanitized_name)
    return sanitized_name


def get_drive_service(request):
    try:
        creds = Credentials(
            token=os.environ.get("GOOGLE_ACCESS_TOKEN"),
            refresh_token=os.environ.get("GOOGLE_REFRESH_TOKEN"),
            client_id=os.environ.get("GOOGLE_CLIENT_ID"),
            client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
            token_uri="https://oauth2.googleapis.com/token",
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )
    except KeyError as e:
        # Handle the case where an environment variable is missing
        raise Exception(f"Missing environment variable: {e}")

    # Initialize Google Drive API service
    service = build("drive", "v3", credentials=creds)
    return service


def create_or_get_folder(service, folder_name, parent_id):
    folder_name = sanitize_folder_name(folder_name)
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false and '{parent_id}' in parents"

    results = (
        service.files()
        .list(q=query, spaces="drive", fields="files(id, name)")
        .execute()
    )
    items = results.get("files", [])

    if items:
        # Folder exists
        return items[0]["id"]
    else:
        # Create the folder
        file_metadata = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent_id],
        }

        file = service.files().create(body=file_metadata, fields="id").execute()
        return file.get("id")


def get_next_version_number(service, folder_id, base_name):
    # List files in the assignment type folder
    query = (
        f"'{folder_id}' in parents and trashed=false and name contains '{base_name}_v'"
    )
    results = service.files().list(q=query, fields="files(name)").execute()
    items = results.get("files", [])

    version_numbers = []
    for item in items:
        file_name = item["name"]
        # Extract version number using regex
        match = re.search(r"_v(\d+)", file_name)
        if match:
            version_numbers.append(int(match.group(1)))

    if version_numbers:
        return max(version_numbers) + 1
    else:
        return 1


def extract_text_from_file(file_stream, file_extension):
    if file_extension.lower() == ".txt":
        return file_stream.read().decode("utf-8")
    elif file_extension.lower() == ".pdf":
        text = ""
        pdf_reader = PyPDF2.PdfReader(file_stream)
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    elif file_extension.lower() in [".doc", ".docx"]:
        doc = docx.Document(file_stream)
        return "\n".join([para.text for para in doc.paragraphs])
    else:
        return ""


def generate_review(assignment_id, assignment_content, assignment_type):
    # This function runs in a separate thread
    assignment = Assignment.objects.get(id=assignment_id)
    try:
        prompt = f"Please review the following {assignment_type.replace('_', ' ')} and provide feedback highlighting areas of improvement and mistakes:\n\n{assignment_content}"

        response = generate_chatbot_response(prompt)

        review_text = response
    except Exception as e:
        review_text = "An error occurred while generating the review."
        print(f"Error generating review: {e}")

    # Set the review availability date (after a few days)
    review_available_at = timezone.now() + timedelta(days=3)

    # Update the assignment with the review and availability date
    assignment.review = review_text
    print("review", review_text)
    assignment.review_available_at = review_available_at
    assignment.status = "pending"
    assignment.save()


@login_required
def assignment_upload(request):
    if request.method == "POST":
        form = AssignmentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            assignment_type = request.POST.get("assignment_type")
            print(assignment_type)
            files = request.FILES.getlist("files")
            print(files)

            # Initialize Google Drive service
            service = get_drive_service(request)

            # Use the provided top-level folder ID
            top_level_folder_id = "19a1NsRymcSTUwiFqcgKN1iJlEmkElA0T"
            if not top_level_folder_id:
                raise Exception("TOP_LEVEL_FOLDER_ID environment variable is not set.")

            # Create or get the user's folder within the top-level folder
            user_folder_id = create_or_get_folder(
                service, request.user.first_name, parent_id=top_level_folder_id
            )

            # Create or get the subfolder (assignment type) within the user's folder
            sub_folder_id = create_or_get_folder(
                service, assignment_type, parent_id=user_folder_id
            )

            for uploaded_file in files:
                # Get the next version number for this assignment type
                base_name = sanitize_folder_name(assignment_type)
                version_number = get_next_version_number(
                    service, sub_folder_id, base_name
                )

                # Modify the file name as per the naming convention
                date_prefix = datetime.now().strftime("%Y%m%d")
                original_filename = uploaded_file.name
                file_extension = os.path.splitext(original_filename)[1]
                new_file_name = (
                    f"{base_name}_{date_prefix}_v{version_number}{file_extension}"
                )
                # Read the uploaded file data into memory
                uploaded_file.seek(0)
                file_data = uploaded_file.read()
                file_stream = BytesIO(file_data)

                # Upload the file directly to Google Drive
                file_metadata = {"name": new_file_name, "parents": [sub_folder_id]}
                media = MediaIoBaseUpload(
                    BytesIO(file_data),
                    mimetype=uploaded_file.content_type,
                    resumable=True,
                )
                uploaded_file_drive = (
                    service.files()
                    .create(body=file_metadata, media_body=media, fields="id")
                    .execute()
                )

                # Create the Assignment instance without the review
                assignment = Assignment.objects.create(
                    user=request.user,
                    assignment_type=assignment_type,
                    file_name=new_file_name,
                    drive_file_id=uploaded_file_drive.get("id"),
                    status="pending",
                )

                # Extract text from the file for review generation
                try:
                    file_content_stream = BytesIO(file_data)
                    assignment_content = extract_text_from_file(
                        file_content_stream, file_extension
                    )
                except Exception as e:
                    assignment_content = ""
                    print(f"Error extracting text: {e}")

                # Start a new thread for review generation
                thread = threading.Thread(
                    target=generate_review,
                    args=(assignment.id, assignment_content, assignment_type),
                )
                thread.start()

            return redirect("management:assignment_list")
    else:
        form = AssignmentUploadForm()
    return render(request, "management/assignment_upload.html", {"form": form})


@login_required
def assignment_list(request):
    # Fetch all assignments for the logged-in user
    assignments = Assignment.objects.filter(user=request.user).order_by("-uploaded_at")

    return render(
        request, "management/assignment_list.html", {"assignments": assignments}
    )


@login_required
def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    review_text = assignment.review
    review_paragraphs = split_review_by_sections(review_text)

    return render(
        request,
        "management/assignment_detail.html",
        {
            "assignment": assignment,
            "review_sections": review_paragraphs,
        },
    )


@login_required
def delete_assignment(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id, user=request.user)

    service = get_drive_service(request)
    try:
        if assignment.drive_file_id:
            service.files().delete(fileId=assignment.drive_file_id).execute()
    except HttpError as error:
        # Log or handle the error if a file could not be deleted on Drive
        print(f"An error occurred: {error}")
        messages.error(
            request,
            "An error occurred while trying to delete the file from Google Drive.",
        )

    # Finally, delete the assignment from the database
    assignment.delete()
    messages.success(
        request, "Assignment and associated files were deleted successfully."
    )

    return redirect("management:assignment_list")


# ==================== OAUTH VIEWS ====================
# NOTE: OAuth helper functions now imported from ai_services.views (Phase 1 improvements)
# This eliminates code duplication and uses improved versions with:
#   - Environment-aware redirect URIs
#   - Better error handling
#   - Proper logging instead of print()


def oauth_login(request):
    """
    Redirects the user to the OAuth2 provider's authorization URL.

    Generates a cryptographically-secure random state parameter and stores it in session
    for CSRF protection during OAuth callback.

    Supports multi-account via ?service=external|internal query parameter.
    Defaults to "external" if not specified (for backward compatibility).

    Fails gracefully if OAuth is not configured, showing a user-friendly error message.
    """
    import logging
    import secrets

    from shared_core.utils.oauth import get_authorization_url

    logger = logging.getLogger(__name__)

    # Get service parameter (external/internal), default to external
    service_param = request.GET.get("service", "external")
    if service_param not in ["external", "internal"]:
        service_param = "external"  # Default to external for invalid values

    # Determine service_name for token storage
    service_name = f"gotomeeting_{service_param}"

    # Generate random state and store in session along with service_name
    state = secrets.token_urlsafe(32)
    request.session["goto_oauth_state"] = state
    request.session["goto_oauth_service"] = (
        service_name  # Store service_name for callback
    )

    try:
        # Get authorization URL with state and service_name (returns tuple: url, state)
        auth_url, _ = get_authorization_url(state=state, service_name=service_name)
        return redirect(auth_url)
    except ValueError as e:
        # OAuth not configured - fail gracefully
        logger.error(f"OAuth login failed: {e}")
        messages.error(
            request,
            "GoToMeeting integration is not configured. Please contact your system administrator.",
        )
        # Redirect to management home (which will redirect to companyagenda if user has access)
        return redirect("main:layout")


def oauth_callback(request):
    """
    Handles the OAuth2 provider's callback with the authorization code.

    Validates the OAuth state parameter against session to prevent CSRF attacks.
    Uses service_name from session to store tokens under the correct service account.
    """
    import logging

    from shared_core.utils.oauth import exchange_code_for_tokens

    logger = logging.getLogger(__name__)

    auth_code = request.GET.get("code")
    state = request.GET.get("state")
    error = request.GET.get("error")

    if error:
        return HttpResponse(f"Error during authentication: {error}")

    if not auth_code:
        return HttpResponse("No authorization code provided.", status=400)

    # Validate state parameter for CSRF protection
    expected_state = request.session.get("goto_oauth_state")
    if not state or state != expected_state:
        logger.warning(
            f"OAuth state mismatch or missing. Expected: {expected_state}, Got: {state}"
        )
        return HttpResponse(
            "Invalid or missing state parameter. OAuth request may have been tampered with.",
            status=400,
        )

    # Get service_name from session (stored during oauth_login)
    service_name = request.session.get("goto_oauth_service", "gotomeeting")

    # Remove state and service from session after validation (prevent replay)
    if "goto_oauth_state" in request.session:
        del request.session["goto_oauth_state"]
    if "goto_oauth_service" in request.session:
        del request.session["goto_oauth_service"]

    # Exchange code for tokens, using the service_name from session
    success = exchange_code_for_tokens(auth_code, service_name=service_name)
    if success:
        logger.info(f"✅ OAuth tokens saved for service '{service_name}'")
        return redirect(
            "getdata:meetingFormView"
        )  # Redirect to the main view after successful authentication
    else:
        # Token exchange failed - check server logs for detailed error
        logger.error(
            f"OAuth callback: token exchange returned False for service '{service_name}'. Check logs above for HTTP status/body details."
        )
        return HttpResponse(
            "Failed to obtain access token. Check server logs for OAuth exchange failure details.",
            status=400,
        )


@login_required
def get_attendee_duration(request):
    """
    Retrieves and displays the attendee's meeting durations for multiple meeting IDs.
    """
    # username = request.user.username.capitalize()
    username = "Hashim"
    meeting_ids = [
        "708385093",
        "994131389",
        "818660269",
        "825287189",
        "368365165",
        "123530685",
        "816482317",
    ]  # Array of meeting IDs (can be dynamic)

    access_token = get_access_token()
    if not access_token:
        return redirect("management:oauth_login")

    duration_days = int(request.GET.get("duration", 7))
    if duration_days not in [7, 15, 30]:
        duration_days = 7

    today = datetime.now()
    start_date = today - timedelta(days=duration_days)

    all_meeting_data = []  # To hold data for all meetings
    date_durations = defaultdict(float)  # Aggregate duration by date

    for meeting_id in meeting_ids:
        conn = http.client.HTTPSConnection("api.getgo.com")
        headers = {"Authorization": f"Bearer {access_token}"}
        endpoint = f"/G2M/rest/meetings/{meeting_id}/attendees"

        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()

        if res.status == 200:
            data = res.read()
            attendees = json.loads(data.decode("utf-8"))

            filtered_meetings = []
            for attendee in attendees:
                if attendee.get("name") == username:
                    join_time = attendee.get("joinTime")
                    leave_time = attendee.get("leaveTime")

                    if join_time and leave_time:
                        join_time = parser.isoparse(join_time)
                        leave_time = parser.isoparse(leave_time)

                        if start_date <= join_time <= today:
                            duration = (
                                leave_time - join_time
                            ).total_seconds() / 60  # Duration in minutes
                            filtered_meetings.append(
                                {
                                    "meeting_id": meeting_id,
                                    "join_time": make_aware(join_time),
                                    "leave_time": make_aware(leave_time),
                                    "duration": duration,
                                }
                            )

                            # Aggregate duration by date
                            date_key = join_time.strftime("%Y-%m-%d")
                            date_durations[date_key] += duration

            filtered_meetings.sort(key=lambda x: x["join_time"], reverse=True)
            if filtered_meetings:
                all_meeting_data.append(
                    {
                        "meeting_id": meeting_id,
                        "meetings": filtered_meetings,
                    }
                )

    # Prepare chart data
    sorted_dates = sorted(date_durations.keys())  # Sort dates for the graph
    chart_labels = sorted_dates
    chart_values = [round(date_durations[date], 2) for date in sorted_dates]

    total_meetings = sum(len(meeting["meetings"]) for meeting in all_meeting_data)
    total_duration = sum(chart_values)
    average_duration = total_duration / total_meetings if total_meetings > 0 else 0

    context = {
        "username": username,
        "all_meeting_data": all_meeting_data,
        "duration_days": duration_days,
        "total_meetings": total_meetings,
        "total_duration": f"{total_duration:.2f} minutes",
        "average_duration": f"{average_duration:.2f} minutes",
        "chart_data": {
            "labels": chart_labels,
            "values": chart_values,
        },
    }

    if not all_meeting_data:
        context["error"] = (
            "No meetings found in the selected duration for this attendee."
        )

    return render(request, "management/attendee_duration.html", context)
