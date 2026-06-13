import http.client
import json
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
from accounts.models import UserProfile
from accounts.utils import calculate_login_bonus, send_verification_email
from accounts.views import create_profile
from core.utils import generate_password
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
from management.utils.task_initializer import create_default_tasks_for_user
from django.utils.text import capfirst
from django.utils.timezone import make_aware
from django.views.generic import (CreateView, DeleteView, DetailView, ListView,
                                  UpdateView)
from mail.custom_email import send_email
from management.forms import (AssignmentUploadForm, BackgroundForm,
                              ClientAssessmentForm, DepartmentForm,
                              EmployeeContractForm, EvidenceForm,
                              GrievanceForm, ManagementForm, MeetingForm,
                              PolicyForm, RequirementForm, TagFilterForm,
                              dynamic_agenda_form)
from management.models import (Advertisement, Assignment, Conflict_Resolution,
                               Grievance, Link, Meetings, Policy,
                               ProcessBreakdown, ProcessJustification,
                               Requirement, SubCategory, Task, TaskCategory,
                               TaskHistory, TaskLinks, Training)
from professional_services.models import DSU, BackgroundCheck, ClientAssessment
from shared_core.mixins import FilteredListViewMixin
from shared_core.users import CustomerUser, Department
from shared_core.users import UserCategory as CategoryChoices

# Optional import - finance_service_helper may not exist
try:
    from management.services.finance_service_helper import \
        get_finance_task_service
except ImportError:

    def get_finance_task_service():
        class NoOpFinanceService:
            def has_payment_history(self, user_id):
                return False

        return NoOpFinanceService()


import logging

import docx
import PyPDF2
from accounts.models import TaskGroups, Tracker
from coda_project import settings
from coda_project.task import dump_data
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from main.filters import RequirementFilter, TaskHistoryFilter
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

# OAUTH CONSTANTS - Import from ai_services (Phase 1 improvements)
# Removed duplicate definitions to prevent code duplication
# Using improved versions from ai_services with:
#   - Environment-aware redirect URIs
#   - Better error handling
#   - Proper logging
from ai_services.views import (API_AUTHORIZATION_URL, API_CLIENT_ID,
                               API_CLIENT_SECRET, API_TOKEN_URL,
                               REFRESH_TOKEN_CACHE_KEY, TOKEN_CACHE_KEY,
                               exchange_code_for_tokens, get_access_token,
                               get_authorization_url, get_oauth_redirect_uri,
                               refresh_access_token)

# For backward compatibility
API_REDIRECT_URI = get_oauth_redirect_uri()

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
    from management.services.activity_type_service import \
        ActivityTypeApplicationService

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
             Task.objects.update_or_create(
                 employee_id=emp,
                 category_id=category,
                 activity_name=act,
                 defaults={
                     "groupname_id": group,
                     "group": group_title,
                     "description": description,
                     "point": 0.00,
                     "mxpoint": mxpoint,
                     "mxearning": mxearning,
                 }
             )

        # return redirect("management:tasks")
        return JsonResponse({"success": True})
    else:
        task_categories = TaskCategory.objects.all()
        group = TaskGroups.objects.all()
        employess = User.objects.filter(
            Q(is_staff=True) | Q(is_admin=True) | Q(is_superuser=True)
        ).all()

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

        # Apply category filter if POST request
        if self.request.method == "POST":
            form = TagFilterForm(self.request.POST)
            if form.is_valid():
                category = form.cleaned_data["category"]
                queryset = queryset.filter(category__title=category)

        return queryset.order_by(self.order_by)

    def get_context_data(self, **kwargs):
        """Add task-specific context data"""
        context = super().get_context_data(**kwargs)

        if self.request.method == "POST":
            form = TagFilterForm(self.request.POST)
        else:
            form = TagFilterForm()

        context["form"] = form
        context["total_count"] = self.get_queryset().count()

        # Add filtered employee info if present
        employee_id = self.request.GET.get("employee")
        if employee_id:
            try:
                from shared_core.users import CustomerUser

                filtered_employee = CustomerUser.objects.get(id=employee_id)
                context["filtered_employee"] = filtered_employee
            except (CustomerUser.DoesNotExist, ValueError):
                pass

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
    from accounts.models import UserProfile
    from finance.models import PayslipConfig

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
    payslip_config = paymentconfigurations(PayslipConfig, employee)
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

    Refactored to use PayCalculationService as the single source of truth for payslip computation.
    Falls back to ReleaseEngine or legacy methods if PayCalculationService is not available.
    """
    # Try to import PayCalculationService with fallback to ReleaseEngine
    pay_service = None
    try:
        from management.services.pay_calculation_service import \
            PayCalculationService

        pay_service = PayCalculationService()
    except (ModuleNotFoundError, ImportError):
        try:
            from management.services.release_engine import ReleaseEngine

            pay_service = ReleaseEngine()
        except (ModuleNotFoundError, ImportError):
            # Fallback to legacy pay calculation methods
            pay_service = None

    pay_type = request.GET.get("pay_type", None)
    username = request.GET.get("username", None)
    employee = None

    if username:
      try:
          if (
              request.user.username == username
              or request.user.is_staff
              or request.user.is_superuser
          ):
              employee = get_object_or_404(User, username=username)
          else:
              messages.warning(
                  request, "You can only access your own payroll information."
              )
              return redirect(
                  f"{request.path}?username={request.user.username}&pay_type={request.GET.get('pay_type', 'usertasks')}"
              )
      except Exception as e:
            print("⚠️ Username lookup failed:", e)


    request.session["siteurl"] = settings.SITEURL
    today, year, deadline_date, *_ = paytime()

    # ===================Selected Month and Year===========================
    selected_month, selected_year, form = get_selected_month_year(request, pay_type)

    # Use pay_service with fallback logic (same as legacy_views.py)
    payslip_data = {}
    if pay_service is not None:
        try:
            # Check if service has calculate_payslip method (PayCalculationService)
            if hasattr(pay_service, "calculate_payslip"):
                payslip_data = pay_service.calculate_payslip(
                    employee=employee,
                    target_month=selected_month,
                    target_year=selected_year,
                    pay_type=pay_type,
                    enforce_evidence=False,  # Phase P1: not enforcing evidence yet
                )
            else:
                # ReleaseEngine or other service doesn't have calculate_payslip - use legacy methods
                payslip_data = {}
        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.exception(
                f"Error generating payslip via pay service for {employee}: {e}; "
                f"falling back to legacy methods",
                exc_info=True,
            )
            payslip_data = {}

    # If pay_service didn't provide data, use legacy pay calculation methods
    if not payslip_data:
        # Fallback to legacy pay calculation (from utils.py functions)
        # Note: paytime is already imported at module level (line 102), don't re-import here
        from management.models import TaskHistory
        from management.utils import (compute_total_points, deductions,
                                      get_bonus_and_summary, loan_computation,
                                      paymentconfigurations)

        # Get tasks for the selected month/year
        if Task.objects.filter(employee=employee).count() == 0:
            create_default_tasks_for_user(employee)
        if pay_type in ["usertasks", "usertaskhistory"]:
            if employee:
                tasks = Task.objects.filter(employee=employee)

            else:
                tasks = Task.objects.none()
        
        else:
            # TaskHistory for selected month/year
            if employee:
                tasks = TaskHistory.objects.filter(
                    employee=employee,
                    daf_date__year=selected_year,
                    daf_date__month=selected_month,
                )
            else:
                tasks = TaskHistory.objects.none()
        
        # ✅ Debug AFTER assignment (correct place)
        print("🔥 TASKS QUERY:", tasks.query)
        print("🔥 EMPLOYEE:", employee)
        print("🔥 TASK COUNT:", tasks.count())
        print("🔥 USER ID:", request.user.id)
        # ================= TOTAL CALCULATION =================
        total_points = sum(float(t.point or 0) for t in tasks)
        max_points = sum(float(t.mxpoint or 0) for t in tasks)

        balance_points = max_points - total_points

        if balance_points < 0:
            balance_points = 0
        
        point_percentage = 0
        if max_points > 0:
            point_percentage = (total_points / max_points) * 100

        # # ================= TOTAL POINTS =================
        # if tasks.exists():
        #     total_points, max_points = compute_total_points(tasks)
        # else:
        #     total_points = 0
        #     max_points = 0

        # point_percentage = 0

        # if max_points > 0:
        #     point_percentage = (total_points / max_points) * 100
    
        print("🔥 TOTAL:", total_points)
        print("🔥 MAX:", max_points)
        print("🔥 BALANCE:", balance_points)

        # Calculate pay using legacy methods
        base_pay = {
            "num_tasks": tasks.count(),
            "points": total_points,
            "max_points": max_points,  # Will be calculated from tasks
            "point_percentage": point_percentage,
            "goal_amount": Decimal("0"),
            "pay_balance": Decimal("0"),
            "pointsbalance": balance_points,
            "total": Decimal("0"),
        }

        # Get user_data and payslip_config for get_bonus_and_summary
        bonuses = {}
        summary_dict = {}
        deductions_dict = {}
        if employee:
            try:
                # get_user_data is defined in this file, no need to import
                userprofile, user_data, payslip_config = get_user_data(employee)

                # Calculate total_pay from tasks using get_points_and_earnings
                total_pay = Decimal("0")
                if tasks.exists():
                    from management.utils import get_points_and_earnings

                    _, _, _, _, _, pay, _ = get_points_and_earnings(tasks)
                    total_pay = pay if pay else Decimal("0")

                # Call get_bonus_and_summary with correct arguments
                # Signature: get_bonus_and_summary(employee, tasks, total_pay, user_data, payslip_config)
                bonus_results = get_bonus_and_summary(
                    employee, tasks, total_pay, user_data, payslip_config
                )
                # get_bonus_and_summary returns a tuple: (bonus_points_ammount, latenight_Bonus, yearly, offpay, EOM, EOQ, EOY, sub_bonus, total_deduction, total_bonus)
                bonuses = {
                    "bonus_points_amount": (
                        bonus_results[0] if len(bonus_results) > 0 else Decimal("0")
                    ),
                    "late_night_bonus": (
                        bonus_results[1] if len(bonus_results) > 1 else Decimal("0")
                    ),
                    "yearly": (
                        bonus_results[2] if len(bonus_results) > 2 else Decimal("0")
                    ),
                    "holiday_pay": (
                        bonus_results[3] if len(bonus_results) > 3 else Decimal("0")
                    ),
                    "eom_bonus": (
                        bonus_results[4] if len(bonus_results) > 4 else Decimal("0")
                    ),
                    "eoq_bonus": (
                        bonus_results[5] if len(bonus_results) > 5 else Decimal("0")
                    ),
                    "eoy_bonus": (
                        bonus_results[6] if len(bonus_results) > 6 else Decimal("0")
                    ),
                    "sub_bonus": (
                        bonus_results[7] if len(bonus_results) > 7 else Decimal("0")
                    ),
                    "total_bonus": (
                        bonus_results[9] if len(bonus_results) > 9 else Decimal("0")
                    ),
                }
                summary_dict = {
                    "total_deductions": (
                        bonus_results[8] if len(bonus_results) > 8 else Decimal("0")
                    ),
                }
                # Call deductions with correct arguments
                # Signature: deductions(employee, user_data, payslip_config, total_pay)
                deductions_result = deductions(
                    employee, user_data, payslip_config, total_pay
                )
                # deductions returns a tuple: (food_accommodation, computer_maintenance, health, kra, laptop_saving, total_laptop_savings, loan_payment, total_deductions)
                if isinstance(deductions_result, tuple) and len(deductions_result) >= 8:
                    deductions_dict = {
                        "food_accommodation": deductions_result[0],
                        "computer_maintenance": deductions_result[1],
                        "health": deductions_result[2],
                        "tax_kra": deductions_result[3],  # kra is at index 3
                        "laptop_saving": deductions_result[4],
                        "total_laptop_savings": deductions_result[5],
                        "loan_payment": deductions_result[6],
                        "total_deductions": deductions_result[7],
                    }
                else:
                    deductions_dict = {}
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Error calculating bonuses/deductions for {employee}: {e}"
                )
                # Fallback to empty dicts if calculation fails
                bonuses = {}
                summary_dict = {}
                deductions_dict = {}

        payslip_data = {
            "tasks": tasks,
            "base_pay": base_pay,
            "bonuses": bonuses,
            "deductions": deductions_dict,
            "summary": summary_dict,
            "metadata": {},
        }

    # Extract data from service response (or legacy fallback)
    tasks = payslip_data.get("tasks")
    base_pay = payslip_data.get("base_pay", {})
    bonuses = payslip_data.get("bonuses", {})
    deductions = payslip_data.get("deductions", {})
    summary = payslip_data.get("summary", {})
    metadata = payslip_data.get("metadata", {})

    # Incorporating a filter (still needed for template)
    # Note: TaskHistoryFilter expects a queryset, but tasks might be a list
    if tasks and hasattr(tasks, "model"):  # Check if it's a queryset
        myfilter = (
            TaskHistoryFilter(request.GET, queryset=tasks)
            if TaskHistoryFilter
            else None
        )
    else:
        myfilter = None  # Skip filter for list data

    # Calculate remaining time (UI helper, not part of pay calculation)
    remaining_days, remaining_seconds, remaining_minutes, remaining_hours = (
        countdown_in_month()
    )

    # Build context from service data (mapping to existing template field names)
    context = {
        "form": form,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "employee": employee,
        "pay_type": pay_type,
        "payday": deadline_date,
        "num_tasks": base_pay.get("num_tasks", 0),
        "tasks": tasks,
        "TaskHistoryFilter": myfilter,
        "Points": total_points,
        "MaxPoints": max_points,
        "point_percentage": base_pay.get("point_percentage", Decimal("0")),
        "pay": base_pay.get(
            "goal_amount", Decimal("0")
        ),  # 'pay' in old context was GoalAmount
        "GoalAmount": base_pay.get("goal_amount", Decimal("0")),
        "paybalance": base_pay.get("pay_balance", Decimal("0")),
        "pointsbalance": balance_points,
        "total_pay": base_pay.get("total", Decimal("0")),
        "loan": deductions.get("loan_payment", Decimal("0")),
        "net": summary.get("net_pay", Decimal("0")),
        "average_earnings": base_pay.get(
            "goal_amount", Decimal("0")
        ),  # average_earnings was GoalAmount
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
        # Include full payslip_data for future use
        "payslip_data": payslip_data,
    }
    print("🔥 CONTEXT BALANCE:", balance_points)
    # Dynamic Redirection Logic
    if pay_type in ["payslip", "task_payslip"]:
        return render(request, "management/daf/payslip.html", context)

    elif pay_type in ["usertasks", "usertaskhistory"]:
        return render(request, "management/daf/usertasks.html", context)

    elif pay_type in ["tasks", "taskhistory"]:
        if pay_type == "tasks":
            return render(request, "management/daf/tasklist.html", context)
        else:
            return render(request, "management/daf/taskhistory.html", context)
    else:
        # Default redirect
        return redirect("main:layout")


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


from accounts.models import CustomerUser

class UserTaskListView(ListView):
    model = Task
    context_object_name = "tasks"
    template_name = "management/daf/employee_tasks.html"

    def get_queryset(self):
        user = get_object_or_404(
            CustomerUser,
            username=self.kwargs.get("username")
        )
        return Task.objects.filter(employee=user)



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
from django.core.files.uploadedfile import UploadedFile


def newevidence(request, taskid):
    """
    Handles the submission of evidence, either as a link or an uploaded file.
    """
    task = get_object_or_404(Task, id=taskid)

    if request.method == "POST":
        form = EvidenceForm(data=request.POST, files=request.FILES, request=request)
        if form.is_valid():
            data = form.cleaned_data

            link = data.get("link", "")
            uploaded_file = data.get("doc", None)

            # Ensure at least one form of evidence is provided
            if not link and not uploaded_file:
                messages.error(
                    request, "Please provide an evidence link or upload a file."
                )
                return render(
                    request, "management/daf/evidence_form.html", {"form": form}
                )

            # Validate the link if provided
            if link:
                try:
                    response = requests.head(
                        link, timeout=5
                    )  # Using HEAD for faster validation
                    if response.status_code >= 400:
                        messages.error(
                            request, "The provided link is not valid or accessible."
                        )
                        return render(
                            request, "management/daf/evidence_form.html", {"form": form}
                        )
                except requests.exceptions.RequestException as e:
                    messages.error(request, f"Error validating the link: {str(e)}")
                    return render(
                        request, "management/daf/evidence_form.html", {"form": form}
                    )

            # Check if the link already exists
            if link:
                existing_links = TaskLinks.objects.filter(link=link)
                if existing_links.exists():
                    users = existing_links.values_list("added_by__username", flat=True)
                    if request.user.username in users:
                        messages.error(request, "You have already uploaded this link.")
                        return render(
                            request, "management/daf/evidence_form.html", {"form": form}
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
            return render(request, "management/daf/evidence_form.html", {"form": form})
    else:
        form = EvidenceForm(request=request)
        return render(request, "management/daf/evidence_form.html", {"form": form})


def process_evidence_submission(
    data, temp_file_path, original_filename, user, task, folder_id
):
    """
    Handles the processing and uploading of evidence to Google Drive and TaskLinks.
    """
    try:
        drive_link = None
        if temp_file_path:
            # Upload the file to Google Drive
            drive_link = upload_file_to_drive(
                temp_file_path, original_filename, user, task, folder_id
            )

        with transaction.atomic():
            # Save the evidence to TaskLinks
            task_links = TaskLinks.objects.create(
                task=task,
                added_by=user,
                link_name=data.get("link_name", "General"),
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

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse

@login_required
def evidence_delete(request, pk):
    """Delete evidence link"""
    evidence = get_object_or_404(TaskLinks, pk=pk)  # Replace 'Evidence' with your model name
    
    # Optional: Check permissions - only allow certain users to delete
    if request.user.is_superuser or request.user == evidence.added_by:
        evidence.delete()
        messages.success(request, 'Evidence deleted successfully!')
    else:
        messages.error(request, 'You do not have permission to delete this evidence.')
    
    # Redirect back to the evidence list page
    # Adjust the redirect URL as needed
    return redirect('management:user_evidence')




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
    path_list, subtitle, pre_sub_title = path_values(request)
    if subtitle == "client_assessment":
        if request.method == "POST":
            form = ManagementForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return redirect("management:assessment", user_type="client")
        else:
            form = ManagementForm()
    else:
        if request.method == "POST":
            form = ManagementForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                return redirect("management:assessment", user_type="client")
        else:
            form = ManagementForm()
    return render(request, "management/departments/hr/assess_form.html", {"form": form})


class DSUListView(FilteredListViewMixin, ListView):
    """Consolidated DSU list view using generic mixin"""

    model = DSU
    template_name = "management/departments/hr/assessment.html"
    context_object_name = "dsu_list"
    order_by = "-created_at"

    def get_queryset(self):
        queryset = super().get_queryset()
        user_type = self.kwargs.get("user_type", "Staff")
        return queryset.filter(type__iexact=user_type.lower()).order_by(self.order_by)


class AssessUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = DSU
    success_url = "/management/assessment/client"
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
        client_assesment = ClientAssessment.objects.filter(email=email)
        if client_assesment.exists():
            form = ClientAssessmentForm(
                request.POST, request.FILES, instance=client_assesment.first()
            )
        else:
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
        # import pdb; pdb.set_trace()
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
                instance.usser_category == 2 and instance.totalpoints != developerpoints
            ):

                instance.totalpoints = developerpoints
                instance.save()
        return queryset


class AssessmentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ClientAssessment
    success_url = "/management/clientassessment"
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
    if request.method == "POST":
        form = BackgroundForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("management:background-list")
    else:
        form = BackgroundForm()
    return render(request, "management/background/background_form.html", {"form": form})


class BackgroundCheckListView(ListView):
    model = BackgroundCheck
    template_name = "admin/background_checks.html"
    context_object_name = "checks"
    paginate_by = 10

    def get_queryset(self):
        status = self.request.GET.get("status", "All")
        if status != "All":
            return BackgroundCheck.objects.filter(status=status)
        return BackgroundCheck.objects.all()

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
    """
    auth_url = get_authorization_url()
    return redirect(auth_url)


def oauth_callback(request):
    """
    Handles the OAuth2 provider's callback with the authorization code.
    """
    auth_code = request.GET.get("code")
    state = request.GET.get("state")
    error = request.GET.get("error")

    if error:
        return HttpResponse(f"Error during authentication: {error}")

    if not auth_code:
        return HttpResponse("No authorization code provided.", status=400)

    success = exchange_code_for_tokens(auth_code)
    if success:
        return redirect(
            "getdata:meetingFormView"
        )  # Redirect to the main view after successful authentication
    else:
        return HttpResponse("Failed to obtain access token.", status=400)


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
