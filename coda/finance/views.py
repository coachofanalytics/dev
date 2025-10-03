import os
import json
import csv
import tempfile
import logging
from decimal import *
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.utils.decorators import method_decorator
from django.db.models import Sum, Q, F
from django.db.models.query import QuerySet
from django.http import QueryDict, Http404, JsonResponse, HttpResponse
# from requests import request  # Unused import removed
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.views.generic import (
    CreateView,
    ListView,
    UpdateView,
    DetailView,
    DeleteView,
)
from accounts.models import CustomerUser, Department
from finance.services.eligibility_service import EligibilityService
from accounts.choices import UserCategory as CategoryChoices
from .models import (
    Payment_Information,
    Payment_History,
    LoanProduct,
    DeletedPaymentHistory,
    Default_Payment_Fees,
    LoanApplication,
    Inflow,
    Transaction,
    PayslipConfig,
    Supplier,
    Food,
    FoodHistory,
    DC48_Inflow,
    Field_Expense,
    Budget,
    CodaBudget,
    BalanceSheetCategory,
    web_budget,
)
from .utils.calculation_utils import CalculationUtils
from .utils.filter_utils import FilterUtils
from .services.budget_estimation_service import BudgetEstimationService
from .services.budget_consolidation_service import BudgetConsolidationService
from .forms import (
    TransactionForm,
    InflowForm,
    DepartmentFilterForm,
    FoodHistoryForm,
    BudgetForm,
)
from dateutil.relativedelta import relativedelta
from mail.custom_email import send_email
from coda_project.settings import payment_details
from main.utils import path_values, countdown_in_month, dates_functionality
from main.filters import FoodFilter
from main.models import Service, ServiceCategory, Pricing, Company
from investing.models import Investment_rates, Investor_Information
from investing.utils import calculate_investor_returns
from management.utils import paytime
from management.models import Requirement
from .utils import *
from django.apps import apps
from ai_services.models import Editable
from django.core.exceptions import MultipleObjectsReturned
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

# In finance/views.py:
from core.utils import verify_otp

from accounts.mixins import FilteredListViewMixin

# Import service layer (OUR ARCHITECTURE!)
from finance.services import (
    LoanService,
    PaymentService,
    BudgetService,
    FinancialAnalyticsService,
)

# Import analytics services
from .analytics import get_all_analytics_services

User = get_user_model()

# payment details
phone_number, email_info, cashapp, venmo, account_no = payment_details(None)

# Time details
(remaining_days, remaining_seconds, remaining_minutes, remaining_hours) = (
    countdown_in_month()
)
today_date = timezone.now().date().strftime("%Y-%m-%d")
# Exchange Rate details
try:
    usd_to_kes = get_exchange_rate("USD", "KES")
except NameError:
    usd_to_kes = 150.0  # Default exchange rate
rate = round(Decimal(usd_to_kes), 2)

logger = logging.getLogger(__name__)


def finance_index(request):
    """Finance app index view - redirects to appropriate dashboard based on user role"""
    from accounts.user_utils import get_user_permissions
    
    # Get user permissions
    permissions = get_user_permissions(request.user)
    
    # Redirect based on user permissions
    if permissions.get('can_access_finance'):
        # User has finance access - redirect to finance dashboard
        return redirect('finance:finance-dashboard', company_slug='coda')
    else:
        # User doesn't have finance access - show limited access page
        return render(request, "finance/limited_access.html", {
            "title": "Finance Access",
            "message": "You don't have permission to access the finance system."
        })


def finance_report(request):
    return render(request, "finance/reports/finance.html", {"title": "Finance"})


# Exchange Rate details
try:
    usd_to_kes = get_exchange_rate("USD", "KES")
except NameError:
    usd_to_kes = 150.0  # Default exchange rate
rate = round(Decimal(usd_to_kes), 2)

logger = logging.getLogger(__name__)


def finance_report(request):
    return render(request, "finance/reports/finance.html", {"title": "Finance"})


# ==================== REFACTORED LOAN VIEWS ====================


@login_required
def loan_application_home(request):
    """Display the loan application home page with information and application button."""
    from finance.models import LoanProduct
    from datetime import date

    today_date = date.today()

    # Use service layer (OUR ARCHITECTURE!)
    eligibility_service = EligibilityService(request.user)
    loan_service = LoanService()
    
    # Import KCC service
    from finance.services.kcc_service import KCCOptimizationService

    # Check loan eligibility through service
    eligibility = eligibility_service.check_loan_eligibility()

    # Get user's currency for display (keep this utility for now)
    from finance.utils import get_user_currency

    user_currency = get_user_currency(request.user)
    currency_symbol = {"USD": "$", "KSH": "KSh", "EUR": "€", "GBP": "£"}.get(
        user_currency, user_currency
    )

    # Get user-specific loan limits through service
    user_loan_limits = None
    if eligibility["eligible"]:
        if eligibility["user_type"] == "kcc_member":
            kcc_service = KCCOptimizationService()
            kcc_limits = kcc_service.get_kcc_loan_limits(request.user)
            if kcc_limits["status"] == "success":
                user_loan_limits = kcc_limits["limits"]
        else:
            user_loan_limits = eligibility.get("loan_limits")

    # Check KCC membership through service
    is_kcc_member = eligibility.get("user_type") == "kcc_member"

    # Get available loan products based on user type
    if request.user.is_superuser:
        # Superusers can see all loan products
        loan_products = LoanProduct.objects.filter(is_active=True).order_by("name")
    elif is_kcc_member:
        # KCC members see only KCC-specific loans, ordered by credit tier
        from finance.services.credit_scoring_service import CreditScoringService
        
        # Get user's credit score and recommended tier
        credit_service = CreditScoringService(request.user)
        credit_report = credit_service.get_credit_report()
        
        # Get all KCC products ordered by tier (min_amount)
        all_products = LoanProduct.objects.filter(
            is_active=True, 
            product_type="kcc_premium"
        ).order_by("min_amount")
        
        # Prioritize user's current tier product first
        recommended_product = credit_report['recommended_product']
        loan_products = []
        
        if recommended_product:
            loan_products.append(recommended_product)
            # Add other products after the recommended one
            other_products = all_products.exclude(id=recommended_product.id)
            loan_products.extend(other_products)
        else:
            loan_products = list(all_products)
    elif request.user.category == 2:  # Staff members
        # Staff members see only staff-specific loans
        loan_products = LoanProduct.objects.filter(
            is_active=True, product_type__in=["staff_emergency", "staff_development"]
        ).order_by("name")
    else:
        # External users see general/external loans and other relevant types
        loan_products = LoanProduct.objects.filter(
            is_active=True, 
            product_type__in=[
                "external", "general", "business_startup", "education", 
                "home_improvement", "medical_emergency", "vehicle_purchase", 
                "debt_consolidation", "wedding_events"
            ]
        ).order_by("name")

    # Get user's loans through service
    user_loans_result = loan_service.get_user_loans(request.user)

    if user_loans_result.get("success", False):
        # Get loans from the service response
        loan_data = user_loans_result.get("data", {})
        user_loans = loan_data.get("applications", [])
        
        # Convert to a queryset-like object for filtering
        from django.db.models import Q
        from finance.models import LoanApplication
        
        # Get actual LoanApplication objects for filtering
        loan_ids = [loan["id"] for loan in user_loans]
        user_loans_queryset = LoanApplication.objects.filter(id__in=loan_ids)

        # Separate loans by status for better display
        active_loans = user_loans_queryset.filter(status__in=["approved", "active", "overdue"])
        pending_loans = user_loans_queryset.filter(
            status__in=["draft", "submitted", "pending_guarantor", "under_review"]
        )
        completed_loans = user_loans_queryset.filter(status__in=["repaid", "rejected"])

        context = {
            "today_date": today_date,
            "user_currency": user_currency,
            "currency_symbol": currency_symbol,
            "eligibility": eligibility,
            "user_loan_limits": user_loan_limits,
            "is_kcc_member": is_kcc_member,
            "loan_products": loan_products,
            "user_loans": user_loans_queryset,
            "active_loans": active_loans,
            "pending_loans": pending_loans,
            "completed_loans": completed_loans,
            "total_loans": user_loans_queryset.count(),
        }
        
        # Add credit report for KCC members
        if is_kcc_member:
            from finance.services.credit_scoring_service import CreditScoringService
            credit_service = CreditScoringService(request.user)
            context["credit_report"] = credit_service.get_credit_report()
    else:
        # Handle service error
        messages.error(request, "Error loading loan information")
        context = {
            "today_date": today_date,
            "user_currency": user_currency,
            "currency_symbol": currency_symbol,
            "eligibility": eligibility,
            "user_loan_limits": user_loan_limits,
            "is_kcc_member": is_kcc_member,
            "loan_products": loan_products,
            "user_loans": [],
            "active_loans": [],
            "pending_loans": [],
            "completed_loans": [],
            "total_loans": 0,
        }
        
        # Add credit report for KCC members
        if is_kcc_member:
            from finance.services.credit_scoring_service import CreditScoringService
            credit_service = CreditScoringService(request.user)
            context["credit_report"] = credit_service.get_credit_report()

    return render(request, "finance/loan_application_home.html", context)


@login_required
def apply_for_loan(request, plan_id=None, *args, **kwargs):
    """Step 1: Display loan application review and requirements page."""
    
    # Check if user is authenticated
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    
    # Handle POST request (form submission)
    if request.method == "POST":
        print(f"�� DEBUG: POST data = {dict(request.POST)}")
        
        # Check if required fields are present
        required_fields = ['total_amount', 'purpose', 'payment_method']
        missing_fields = [field for field in required_fields if not request.POST.get(field)]
        if missing_fields:
            messages.error(request, f"Missing required fields: {', '.join(missing_fields)}")
            return redirect("finance:apply-for-loan", plan_id=plan_id)
        
        
        # Check guarantor fields based on user type
        if request.user.category == 2:  # Staff user
            selected_guarantor = request.POST.get("selected_guarantor")
            if not selected_guarantor:
                messages.error(request, "Staff members must select a guarantor from the eligible staff list.")
                return redirect("finance:apply-for-loan", plan_id=plan_id)
        elif hasattr(request.user, 'profile') and request.user.profile.is_karen_country_club_member:  # KCC member
            selected_guarantor = request.POST.get("selected_guarantor")
            if not selected_guarantor:
                messages.error(request, "KCC members must select a guarantor from the eligible KCC member list.")
                return redirect("finance:apply-for-loan", plan_id=plan_id)
        else:  # External user (non-KCC, non-staff)
            # External users must provide guarantor + collateral
            guarantor_fields = ['guarantor_first_name', 'guarantor_last_name', 'guarantor_phone', 'guarantor_email', 'guarantor_relationship']
            missing_guarantor = [field for field in guarantor_fields if not request.POST.get(field)]
            if missing_guarantor:
                messages.error(request, f"External users must provide guarantor information. Please provide: {', '.join(missing_guarantor)}")
                return redirect("finance:apply-for-loan", plan_id=plan_id)
            
            # Check collateral requirement for external users
            collateral = request.POST.get("collateral", "").strip()
            # External users will be redirected to collateral form after loan creation
        
        try:
            # Get form data
            total_amount = request.POST.get("total_amount")
            purpose = request.POST.get("purpose")
            payment_method = request.POST.get("payment_method")
            
            
            # Determine if guarantor is required based on amount
            loan_amount = float(total_amount)
            requires_guarantor = loan_amount > 500

            # Initialize guarantor variables
            guarantor_user = None
            guarantor_relationship = None

            # Get guarantor information - check if staff user selected a guarantor
            selected_guarantor_id = request.POST.get("selected_guarantor")
            print(f"�� DEBUG: selected_guarantor_id = {selected_guarantor_id}")

            if requires_guarantor and selected_guarantor_id and request.user.category == 2:
                # Staff user selected a guarantor from the list
                try:
                    guarantor_user = CustomerUser.objects.get(id=selected_guarantor_id)
                    guarantor_relationship = request.POST.get(
                        "guarantor_relationship", "colleague"
                    )
                except CustomerUser.DoesNotExist:
                    messages.error(request, "Selected guarantor not found.")
                    return redirect("finance:apply-for-loan", plan_id=plan_id)
            elif requires_guarantor:
                # External guarantor or manual entry
                guarantor_first_name = request.POST.get("guarantor_first_name")
                guarantor_last_name = request.POST.get("guarantor_last_name")
                guarantor_phone = request.POST.get("guarantor_phone")
                guarantor_email = request.POST.get("guarantor_email")
                guarantor_relationship = request.POST.get("guarantor_relationship")


                if not all(
                    [
                        guarantor_first_name,
                        guarantor_last_name,
                        guarantor_phone,
                        guarantor_email,
                    ]
                ):
                    messages.error(
                        request, "Please provide complete guarantor information."
                    )
                    return redirect("finance:apply-for-loan", plan_id=plan_id)

                # Auto-create guarantor user if not exists
                try:
                    # First try to find existing user by email
                    guarantor_user = CustomerUser.objects.get(email=guarantor_email)
                    # Update existing user info if needed
                    if (
                        guarantor_user.first_name != guarantor_first_name
                        or guarantor_user.last_name != guarantor_last_name
                    ):
                        guarantor_user.first_name = guarantor_first_name
                        guarantor_user.last_name = guarantor_last_name
                        guarantor_user.phone = guarantor_phone
                        guarantor_user.save()
                        messages.info(
                            request,
                            f"Updated existing guarantor information for {guarantor_user.get_full_name()}",
                        )
                    else:
                        messages.info(
                            request,
                            f"Using existing guarantor: {guarantor_user.get_full_name()}",
                        )
                except CustomerUser.DoesNotExist:
                    # Create new guarantor user
                    guarantor_user = CustomerUser.objects.create(
                        username=f"guarantor_{guarantor_email.split('@')[0]}",
                        email=guarantor_email,
                        first_name=guarantor_first_name,
                        last_name=guarantor_last_name,
                        phone=guarantor_phone,
                        category=4,  # External user
                        is_active=True,
                        is_staff=False,
                    )
                    print(f"�� DEBUG: Created new guarantor user: {guarantor_user}")
                    messages.success(
                        request,
                        f"Created new guarantor user: {guarantor_user.get_full_name()}",
                    )

            # Get the loan plan
            if plan_id:
                plan = get_object_or_404(LoanProduct, id=plan_id, is_active=True)
            else:
                plan = LoanProduct.objects.filter(is_active=True).first()
                if not plan:
                    messages.error(request, "No loan plans available.")
                    return redirect("finance:loan-home")

            # Create loan application
            
            # Convert amount to Decimal
            from decimal import Decimal
            amount_decimal = Decimal(str(total_amount))

            # Create loan application directly instead of Payment
            loan_app = LoanApplication.objects.create(
                borrower=request.user,
                amount_requested=amount_decimal,
                purpose=purpose,
                guarantor=guarantor_user if requires_guarantor else None,
                guarantor_relationship=guarantor_relationship if requires_guarantor else "",
                loan_product=plan,
                loan_plan_id=plan.id,  # Set loan_plan_id to match loan_product
                duration=plan.term_months,  # Set duration from loan product
                interest_rate=plan.interest_rate,  # Set interest rate from loan product
                status="pending",
                submitted_at=timezone.now(),  # Set submission timestamp
            )

            # Calculate guarantor eligibility score if staff and guarantor exists
            if guarantor_user and guarantor_user.category == 2:
                from .utils import calculate_guarantor_eligibility_score

                eligibility = calculate_guarantor_eligibility_score(guarantor_user)
                loan_app.guarantor_eligibility_score = eligibility["score"]

                # Set initial status based on guarantor type
                if guarantor_user.category == 2:  # Staff guarantor
                    loan_app.status = "pending_guarantor"
                    loan_app.guarantor_approval_status = "pending"
                else:  # External guarantor
                    loan_app.status = "under_review"
            else:
                # No guarantor required, set status to under_review
                loan_app.status = "under_review"

            loan_app.save()

            # Send guarantor approval request if staff guarantor exists
            if guarantor_user and guarantor_user.category == 2:
                try:
                    loan_app.send_guarantor_approval_request()
                    messages.success(
                        request,
                        f"Loan application submitted! Guarantor approval request sent to {guarantor_user.get_full_name()}. You will be notified once they approve.",
                    )
                except Exception as e:
                    messages.warning(
                        request,
                        f"Loan application submitted, but failed to send guarantor approval request: {e}",
                    )
            else:
                if guarantor_user:
                    pass
                else:
                    pass
                messages.success(
                    request,
                    f"Loan application submitted successfully! Amount: ${total_amount}",
                )

            # Redirect based on user type
            if request.user.category == 4:  # External user - redirect to collateral form
                return redirect("finance:collateral-form", loan_id=loan_app.id)
            else:  # Staff or KCC member - go directly to confirmation
                return redirect("finance:loan-application-confirmation")

        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"🚨 ERROR: Loan application failed: {e}")
            print(f"🚨 TRACEBACK: {error_traceback}")
            messages.error(request, f"Error processing loan application: {e}")
            return redirect("finance:apply-for-loan", plan_id=plan_id)

    # Handle GET request (display form)
    today_date = date.today()

    # Use service layer for eligibility FIRST to get is_kcc_member
    eligibility_service = EligibilityService(request.user)
    eligibility = eligibility_service.check_loan_eligibility()
    print(f"�� DEBUG: Eligibility result: {eligibility}")

    if not eligibility["eligible"]:
        messages.error(request, eligibility["message"])
        return redirect("finance:loan-home")
    
    # Check for existing pending/under review loans
    existing_loans = LoanApplication.objects.filter(
        borrower=request.user,
        status__in=['pending', 'under_review', 'pending_guarantor']
    ).order_by('-created_at')
    
    if existing_loans.exists():
        latest_loan = existing_loans.first()
        messages.warning(
            request, 
            f"You already have a loan application #{latest_loan.application_number} that is {latest_loan.get_status_display()}. "
            f"Please wait for it to be processed or edit your existing application."
        )
        return redirect("finance:loan-detail", pk=latest_loan.id)

    # Get the loan plan - either from plan_id parameter or default to first available
    try:
        # Check KCC membership through service - DEFINE THIS INSIDE TRY BLOCK
        is_kcc_member = eligibility.get("user_type") == "kcc_member"
        if plan_id:
            plan = get_object_or_404(LoanProduct, id=plan_id, is_active=True)

            # Validate user has access to this loan product
            if not request.user.is_superuser:
                if is_kcc_member and plan.product_type != "kcc_member":
                    messages.error(
                        request, "You can only apply for KCC member loan products."
                    )
                    return redirect("finance:loan-home")
                elif request.user.category == 2 and plan.product_type != "staff_only":
                    messages.error(
                        request, "You can only apply for staff loan products."
                    )
                    return redirect("finance:loan-home")
                elif (
                    not is_kcc_member
                    and request.user.category != 2
                    and plan.product_type not in ["external", "general"]
                ):
                    messages.error(
                        request, "You can only apply for general loan products."
                    )
                    return redirect("finance:loan-home")
        else:
            # Get first available loan product based on user type
            if request.user.is_superuser:
                plan = LoanProduct.objects.filter(is_active=True).first()
            elif is_kcc_member:
                # Prioritize KCC Quick Cash (2 weeks) for new users
                plan = LoanProduct.objects.filter(
                    is_active=True, 
                    product_type="kcc_member",
                    name__icontains="Quick Cash"
                ).first()
                
                # If Quick Cash not found, get the first KCC member plan
                if not plan:
                    plan = LoanProduct.objects.filter(
                        is_active=True, product_type="kcc_member"
                    ).first()
            elif request.user.category == 2:
                plan = LoanProduct.objects.filter(
                    is_active=True, product_type="staff_only"
                ).first()
            else:
                plan = LoanProduct.objects.filter(
                    is_active=True, product_type__in=["external", "general"]
                ).first()

            if not plan:
                messages.error(
                    request, "No loan plans available for your account type."
                )
                return redirect("finance:loan-home")
    except Exception as e:
        messages.error(request, f"Error loading loan plan: {e}")
        return redirect("finance:loan-home")

    # Get user's currency for display
    from finance.utils import get_user_currency

    user_currency = get_user_currency(request.user)
    currency_symbol = {"USD": "$", "KSH": "KSh", "EUR": "€", "GBP": "£"}.get(
        user_currency, user_currency
    )

    # Get loan limits through service
    user_loan_limits = None
    if eligibility["user_type"] == "kcc_member":
        from finance.services.kcc_service import KCCOptimizationService
        kcc_service = KCCOptimizationService()
        kcc_limits = kcc_service.get_kcc_loan_limits(request.user)
        if kcc_limits["status"] == "success":
            user_loan_limits = kcc_limits["limits"]
            print(f"�� DEBUG: KCC limits: {user_loan_limits}")
    else:
        user_loan_limits = eligibility.get("loan_limits")

    # Get existing guarantor information for staff (keep utility for now)
    from finance.utils import get_existing_guarantor_info, get_eligible_staff_guarantors, get_eligible_kcc_guarantors

    existing_guarantor_info = get_existing_guarantor_info(request.user)
    
    # Get appropriate guarantor lists based on user type
    eligible_guarantors = []
    guarantor_type = None
    
    if request.user.category == 2:  # Staff members
        eligible_guarantors = get_eligible_staff_guarantors(limit=10)
        guarantor_type = "staff"
    elif hasattr(request.user, 'profile') and request.user.profile.is_karen_country_club_member:  # KCC members
        eligible_guarantors = get_eligible_kcc_guarantors(limit=10)
        guarantor_type = "kcc"
    # External users don't get a pre-populated list - they must provide manual guarantor info

    context = {
        "plan": plan,
        "today_date": today_date,
        "user_currency": user_currency,
        "currency_symbol": currency_symbol,
        "eligibility": eligibility,
        "user_loan_limits": user_loan_limits,
        "existing_guarantor_info": existing_guarantor_info,
        "is_kcc_member": is_kcc_member,
        "eligible_guarantors": eligible_guarantors,
        "guarantor_type": guarantor_type,
    }
    

    return render(request, "finance/apply_for_loan.html", context)


@login_required
def process_payment(request, loan_id):
    """Process a payment for a loan using service layer."""
    if request.method == "POST":
        payment_amount = request.POST.get("amount")
        payment_method = request.POST.get("payment_method")

        # Use service layer
        payment_service = PaymentService()
        result = payment_service.process_payment(
            loan_id, payment_amount, payment_method, request.user
        )

        if result["status"] == "success":
            messages.success(request, "Payment processed successfully!")
            return redirect("finance:loan-status")
        else:
            messages.error(request, result["message"])
            return redirect("finance:loan-detail", loan_id=loan_id)

    return render(request, "finance/process_payment.html")


# ==================== REFACTORED ANALYTICS VIEWS ====================


@login_required
def loan_analytics(request):
    """Loan analytics using service layer."""
    # Use service layer
    analytics_service = FinancialAnalyticsService()

    if request.user.is_staff:
        # Staff gets system-wide analytics
        report = analytics_service.generate_performance_report()
    else:
        # Regular users get their own analytics
        report = analytics_service.generate_performance_report(user=request.user)

    if report and report.get("status") == "success":
        context = {"report": report.get("report", {})}
    else:
        messages.error(request, "Error generating analytics report")
        context = {"report": {}}

    return render(request, "finance/loan_analytics.html", context)


@login_required
def loan_performance_analytics(request):
    """Loan performance analytics using service layer."""
    # Use service layer
    analytics_service = FinancialAnalyticsService()

    # Get user-specific analytics
    user_analytics = analytics_service.get_user_performance_analytics(request.user)

    if user_analytics["status"] == "success":
        context = {"analytics": user_analytics["analytics"]}
    else:
        messages.error(request, "Error loading performance analytics")
        context = {"analytics": None}

    return render(request, "finance/loan_performance_analytics.html", context)


# ==================== REFACTORED ADMIN VIEWS ====================


@login_required
def admin_loan_applications(request):
    """Admin loan applications using service layer."""
    if not request.user.is_staff:
        messages.error(request, "Access denied")
        return redirect("finance:loan-home")

    # Use service layer
    loan_service = LoanService()
    analytics_service = FinancialAnalyticsService()

    # Get loan statistics
    loan_stats = loan_service.get_loan_statistics()

    # Get system overview
    system_overview = analytics_service.get_system_overview()

    context = {
        "loan_statistics": loan_stats.get("statistics", {}),
        "system_overview": system_overview.get("overview", {}),
    }

    return render(request, "finance/admin/loan_applications.html", context)


@login_required
def approve_loan_application(request, pk):
    """Approve loan application using service layer."""
    if not request.user.is_staff:
        messages.error(request, "Access denied")
        return redirect("finance:loan-home")

    # Use service layer
    loan_service = LoanService()

    # Update loan status through service
    result = loan_service.update_loan_status(pk, "approved")

    if result["status"] == "success":
        messages.success(request, "Loan application approved successfully!")
    else:
        messages.error(request, result["message"])

    return redirect("finance:admin-loan-applications")


@login_required
def reject_loan_application(request, pk):
    """Reject loan application using service layer."""
    if not request.user.is_staff:
        messages.error(request, "Access denied")
        return redirect("finance:loan-home")

    # Use service layer
    loan_service = LoanService()

    # Update loan status through service
    result = loan_service.update_loan_status(pk, "rejected")

    if result["status"] == "success":
        messages.success(request, "Loan application rejected successfully!")
    else:
        messages.error(request, result["message"])

    return redirect("finance:admin-loan-applications")


# ==================== REFACTORED GUARANTOR VIEWS ====================


@login_required
def guarantor_approval_request(request, loan_id):
    """Request guarantor approval using service layer."""
    # Use service layer
    loan_service = LoanService()

    # Get loan details
    loan_result = loan_service.get_user_loans(request.user, status="pending_guarantor")

    if loan_result["status"] == "success":
        context = {"loans": loan_result["loans"]}
    else:
        messages.error(request, "Error loading loan information")
        context = {"loans": []}

    return render(request, "finance/guarantor_approval_request.html", context)


@login_required
def guarantor_approve_loan(request, loan_id):
    """
    Display guarantor approval page using service layer.
    Supports both logged-in and email-verified guarantors.
    """
    try:
        # Use service layer for data validation and retrieval
        loan_service = LoanService()

        # Determine guarantor user (logged-in or email-verified)
        guarantor_user = request.user if request.user.is_authenticated else None

        result = loan_service.get_guarantor_approval_page_data(loan_id, guarantor_user)

        if result["status"] == "error":
            if result["code"] == "UNAUTHORIZED":
                messages.error(request, "Please verify your email address first.")
            elif result["code"] == "ALREADY_PROCESSED":
                messages.info(
                    request,
                    f"This loan application has already been {result['message']}.",
                )
            else:
                messages.error(request, result["message"])
            return redirect("finance:loan-home")

        # Render approval page with service-provided data
        context = {
            "loan_app": result["loan_app"],
            "guarantor": result["guarantor"],
            "borrower": result["borrower"],
            "loan_product": result["loan_product"],
        }

        return render(request, "finance/guarantor_approval.html", context)

    except Exception as e:
        logger.error(f"Error in guarantor approval view: {e}")
        messages.error(request, "An error occurred while loading the approval page.")
        return redirect("finance:loan-home")


def guarantor_process_approval(request, loan_id):
    """
    Process guarantor approval/rejection using service layer.
    Supports both AJAX and form submissions.
    """
    if request.method != "POST":
        if request.headers.get("Accept") == "application/json":
            return JsonResponse(
                {"success": False, "error": "POST required"}, status=405
            )
        return redirect("finance:guarantor-approve-loan", loan_id=loan_id)

    try:
        # Use service layer for business logic
        loan_service = LoanService()

        # Determine guarantor user
        guarantor_user = request.user if request.user.is_authenticated else None

        # Get form data
        decision = request.POST.get("decision")
        notes = request.POST.get("notes", "")

        # Process through service layer
        result = loan_service.process_guarantor_approval(
            loan_id, guarantor_user, decision, notes
        )

        # Handle response based on request type
        if request.headers.get("Accept") == "application/json":
            # AJAX response
            if result["status"] == "success":
                return JsonResponse(
                    {
                        "success": True,
                        "status": result["loan_status"],
                        "approval_status": result["approval_status"],
                        "message": result["message"],
                    }
                )
            else:
                return JsonResponse(
                    {
                        "success": False,
                        "error": result["message"],
                        "code": result.get("code", "UNKNOWN"),
                    },
                    status=400,
                )
        else:
            # Form submission response
            if result["status"] == "success":
                messages.success(request, result["message"])
            else:
                messages.error(request, result["message"])
            return redirect("finance:loan-home")

    except Exception as e:
        logger.error(f"Error processing guarantor approval: {e}")
        if request.headers.get("Accept") == "application/json":
            return JsonResponse(
                {"success": False, "error": "Internal server error"}, status=500
            )
        else:
            messages.error(request, "An error occurred while processing your decision.")
            return redirect("finance:guarantor-approve-loan", loan_id=loan_id)


@login_required
def guarantor_reject_loan(request, loan_id):
    """Guarantor reject loan using service layer."""
    # Use service layer
    loan_service = LoanService()

    # Update loan status through service
    result = loan_service.update_loan_status(loan_id, "rejected")

    if result["status"] == "success":
        messages.success(request, "Loan rejected by guarantor successfully!")
    else:
        messages.error(request, result["message"])

    return redirect("finance:guarantor-approval-request")


# ==================== KEEP EXISTING UTILITY VIEWS ====================
@login_required
def add_budget_item(request):
    if request.method == "POST":
        form = BudgetForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            instance = form.save(commit=False)
            print(request.user)
            instance.budget_lead = request.user
            instance.save()
            return redirect("finance:budget", company_slug="coda")
    else:
        form = BudgetForm()
    return render(request, "finance/budgets/newbudget.html", {"form": form})


def budget(request, company_slug="coda"):
    try:
        # Fetch the company object based on the slug
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        return redirect(
            "some_error_view"
        )  # Redirect to an error page if company doesn't exist

    # Fetch budgets for the company
    company_budgets = Budget.objects.filter(company=company)
    site_budgets = Budget.objects.filter(company=company, category__name="Web")

    # Calculate total budgets
    total_budget = sum(site.amount for site in company_budgets)
    total_site_budget = sum(site.amount for site in site_budgets)
    total_operation = total_budget - total_site_budget

    # Construct link URL
    link_url = reverse(
        "finance:site_budget_with_subcategory",
        kwargs={"company_slug": company_slug, "category": "Web", "subcategory": "all"},
    )

    # Prepare summary data
    summary = [
        {"title": "Total Budget", "value": total_budget, "link": ""},
        {"title": "Operations", "value": total_operation, "link": ""},
        {"title": "Web Development", "value": total_site_budget, "link": link_url},
    ]

    # Fetch other necessary data
    webhour = PayslipConfig.objects.values_list("web_pay_hour", flat=True).first()
    delta = PayslipConfig.objects.values_list("web_delta", flat=True).first()

    context = {
        "company_name": company.name,
        "budget_obj": company_budgets,
        "data": summary,
        "webhour": webhour,
        "delta": delta,
    }
    return render(request, "finance/budgets/budget.html", context)


def site_budget(
    request, company_slug="CODA", category="Design and Development", subcategory="all"
):
    # cat=category
    company_name = Company.objects.filter(slug=company_slug).first()
    # print(company_name,company_slug,category,subcategory)
    # site_budget_all = Budget.objects.filter(company__slug=company_slug, category__name=category)
    site_budget_all = web_budget.objects.filter(company__slug=company_slug)
    # print(site_budget_all)
    if subcategory == "all":
        # site_budget = web_budget.objects.filter(company__slug=company_slug, category__name=category)
        site_budget = web_budget.objects.filter(company__slug=company_slug)
    else:
        site_budget = web_budget.objects.filter(
            company__slug=company_slug,
            category__name=category,
            subcategory__name=subcategory,
        )
        # site_budget = Budget.objects.filter(company__slug=company_slug, category__name=category, subcategory=subcategory)
        print(site_budget)

    # Initialize a dictionary to store subcategory totals
    category_totals = {}

    # Calculate total amount for each subcategory
    for budget in site_budget_all:
        if budget.category.name not in category_totals:
            category_totals[budget.category] = 0
        # subcategory_totals[budget.subcategory] += budget.amount
        category_totals[budget.category] += budget.amount

    # Prepare context to pass to template
    context = {
        "companies": Company.objects.filter(is_featured=True),
        "company_name": company_name,
        "institution_slug": company_slug,
        "subcat": subcategory.upper(),
        "site_budget": site_budget,
        "subcategory_totals": category_totals.items(),  # Convert dictionary items to list of tuples
    }
    # return render(request, "finance/budgets/dynamic_site_budget.html", context)
    return render(request, "finance/budgets/site_budget.html", context)


def coda_budget_estimation(request, app="all"):
    coda_budget_json = Editable.objects.filter(name="coda_budget")
    if coda_budget_json.exists():

        coda_budget_json = coda_budget_json.get().value
    else:
        coda_budget_json = {
            "createview": {"hour": 10, "quntity": 1, "unit_price": 30},
            "updateview": {"hour": 5, "quntity": 1, "unit_price": 30},
            "listview": {"hour": 3, "quntity": 1, "unit_price": 30},
            "detailview": {"hour": 3, "quntity": 1, "unit_price": 30},
            "deleteview": {"hour": 2, "quntity": 1, "unit_price": 30},
            "template": {"hour": 5, "quntity": 3, "unit_price": 30},
            "form": {"hour": 4, "quntity": 1, "unit_price": 30},
            "api": {"hour": 10, "quntity": 3, "unit_price": 30},
        }

        Editable.objects.create(name="coda_budget", value=coda_budget_json)

    coda_applications = [
        app.split(".")[0] for app in settings.INSTALLED_APPS if ".apps." in app
    ]

    application_table_dict = []
    filter_table_dict = []
    for application in coda_applications:
        try:
            app_models = apps.get_app_config(application).get_models()
            table_names = [
                model._meta.verbose_name.replace("_", " ").capitalize()
                for model in app_models
            ]
            if app == "all":
                application_table_dict.append(
                    {
                        "application_name": application,
                        "modle": ", ".join(table_names),
                        "no_of_model": len(table_names),
                    }
                )
            else:
                if application == app:
                    application_table_dict.append(
                        {
                            "application_name": application,
                            "modle": ", ".join(table_names),
                            "no_of_model": len(table_names),
                        }
                    )
            filter_table_dict.append(
                {"application_name": application, "no_of_model": len(table_names)}
            )
        except:
            application_table_dict = []
            filter_table_dict = []

    ####################################
    # calculation
    ####################################

    one_model_calculation = 0
    for coda_budget_element_key, coda_budget_element_value in coda_budget_json.items():
        one_model_calculation += (
            coda_budget_element_value.get("quntity", 1)
            * coda_budget_element_value.get("hour", 1)
            * coda_budget_element_value.get("unit_price")
        )
        coda_budget_element_value["amount"] = (
            coda_budget_element_value.get("quntity", 1)
            * coda_budget_element_value.get("hour", 1)
            * coda_budget_element_value.get("unit_price")
        )
        coda_budget_element_value["name"] = coda_budget_element_key

    final_budget_amount = 0
    for application in application_table_dict:

        application["task"] = "model"
        application["sub_task"] = coda_budget_json.values()
        application["total_amount"] = application["no_of_model"] * one_model_calculation
        application["one_model_calculation"] = one_model_calculation
        final_budget_amount += application["total_amount"]

    context = {
        "application_data_json": application_table_dict,
        "final_budget_amount": final_budget_amount,
        "filter_list": filter_table_dict,
        "one_model_calculation": one_model_calculation,
    }

    return render(request, "finance/budgets/coda_budget.html", context=context)


class BudgetUpdateView(UpdateView):
    model = Budget
    success_url = "/finance/budget/coda"
    template_name = "main/snippets_templates/generalform.html"
    fields = "__all__"

    def form_valid(self, form):
        if self.request.user.is_superuser or self.request.user:
            return super().form_valid(form)
        else:
            return render(request, "main/snippets_templates/generalform.html")

    def test_func(self):
        # task = self.get_object()
        if self.request.user.is_superuser:
            return True
        if self.request.user:
            return True


class WebBudgetUpdateView(UpdateView):
    model = web_budget
    success_url = "/finance/budget/coda"
    template_name = "main/snippets_templates/generalform.html"
    fields = "__all__"

    def form_valid(self, form):
        if self.request.user.is_superuser or self.request.user:
            return super().form_valid(form)
        else:
            return render(request, "main/snippets_templates/generalform.html")

    def test_func(self):
        # task = self.get_object()
        if self.request.user.is_superuser:
            return True
        if self.request.user:
            return True


def investment_report(request):
    return render(
        request, "finance/reports/investment_report.html", {"title": "Investment"}
    )


# ================STUDENT AND JOB SUPPORT CONTRACT FORM SUBMISSION=============
def contract_data_submission(request):
    (today, *_) = paytime()
    try:
        if request.method == "POST":
            user_student_data = request.POST.get("usr_data")
            contract_charge = request.POST.get("contract_charge")
            contract_duration = request.POST.get("contract_duration")
            contract_period = request.POST.get("contract_period")
            student_dict_data = QueryDict(user_student_data)
            username = student_dict_data.get("username")
            try:
                customer = CustomerUser.objects.get(username=username)
                ss = customer.id
            except:
                customer = request.user
            payment_fees = float(contract_charge)
            down_payment = int(payment_fees * 0.33)
            student_bonus_amount = 0
            fee_balance = payment_fees - down_payment
            plan = int(contract_duration)
            payment_method = request.POST.get("payment_type")
            client_signature = username
            company_rep = "coda"
            client_date = today
            rep_date = today
            try:
                # payment = Payment_Information.objects.get(customer_id_id=customer.id)
                payment = Payment_Information.objects.filter(
                    customer_id=customer.id
                ).first()

            except:
                payment = None
            if payment:
                payment_data = Payment_Information.objects.filter(
                    customer_id_id=int(customer.id)
                ).update(
                    payment_fees=int(payment_fees),
                    down_payment=down_payment,
                    student_bonus=student_bonus_amount,
                    fee_balance=int(fee_balance),
                    plan=plan,
                    payment_method=payment_method,
                    client_signature=client_signature,
                    company_rep=company_rep,
                    client_date=client_date,
                    rep_date=rep_date,
                )
            else:
                payment_data = Payment_Information(
                    payment_fees=int(payment_fees),
                    down_payment=down_payment,
                    student_bonus=student_bonus_amount,
                    fee_balance=int(fee_balance),
                    plan=plan,
                    payment_method=payment_method,
                    client_signature=client_signature,
                    company_rep=company_rep,
                    client_date=client_date,
                    rep_date=rep_date,
                    customer_id_id=int(customer.id),
                )
                payment_data.save()
            payment_history_data = Payment_History(
                payment_fees=int(payment_fees),
                down_payment=down_payment,
                student_bonus=student_bonus_amount,
                fee_balance=int(fee_balance),
                plan=plan,
                payment_method=payment_method,
                client_signature=client_signature,
                company_rep=company_rep,
                client_date=client_date,
                rep_date=rep_date,
                customer_id=int(customer.id),
            )
            payment_history_data.save()
            new_payment_added = Payment_Information.objects.filter(
                customer_id_id=customer.id
            ).first()

            if new_payment_added:
                # messages.success(request, f'Added New Contract For the {username}!')
                return redirect("management:companyagenda")
            else:
                # messages.success(request, f'Account created for {username}!')
                if request.user.category == 3 or request.user.is_superuser:
                    return redirect("main:job_support")
                if request.user.category == 4 or request.user.is_superuser:
                    return redirect("main:full_course")
                else:
                    return redirect("management:companyagenda")

    except Exception:
        # print("Student Form Creation Error ==>",print(e))
        message = f"Hi,{request.user}, there is an issue on our end kindly contact us directly at info@codanalytics.net"
        context = {
            "title": "CONTRACT",
            "message": message,
        }
        return render(request, "main/errors/generalerrors.html", context)


def contract_investment_submission(request):
    (today, *_) = paytime()
    contract_start_date = today + relativedelta(3)
    try:
        if request.method == "POST":
            print("request.POST=====>", request.POST)
            user_investor_data = request.POST.get("usr_data")
            investment_contract = request.POST.get("investment_contract")
            total_amount = float(request.POST.get("total_amount"))
            amount_invested = float(request.POST.get("amount_invested"))
            contract_duration = request.POST.get("contract_duration")
            model_type = request.POST.get("model_type")
            beneficiary_name = request.POST.get("beneficiary_name", None)
            beneficiary_relation = request.POST.get("beneficiary_relation", None)
            investor_dict_data = QueryDict(user_investor_data)
            username = investor_dict_data.get("username")

            try:
                investor = CustomerUser.objects.get(username=username)
                ss = investor.id
            except:
                investor = request.user
            payment_method = request.POST.get("payment_type")
            client_signature = username
            company_rep = "coda"
            print("investor=====>", investor)
            investor_data = Investor_Information(
                investor_id=int(investor.id),
                total_amount=total_amount,
                amount_invested=amount_invested,
                investment_threshold=0,
                duration=int(contract_duration),
                revenue_share_percentage=0.05,
                model_type=model_type,
                beneficiary_name=beneficiary_name,
                beneficiary_relation=beneficiary_relation,
                company_rep=company_rep,
                contract_date=contract_start_date,
                # status
                client_signature=client_signature,
            )
            investor_data.save()
            print("investor_data=====>", investor_data)
            payment_data = Payment_Information(
                payment_fees=int(total_amount),
                down_payment=int(0),
                # fee_balance=int(total_amount)-0,
                payment_method=payment_method,
                client_signature=client_signature,
                company_rep=company_rep,
                client_date=datetime.today(),
                rep_date=datetime.today(),
                customer_id_id=int(request.user.id),
                plan=999,
            )
            payment_data.save()
            return redirect("finance:pay")
    except Exception as e:
        message = f"Hi,{request.user}, there is an issue on our end kindly contact us directly at info@codanalytics.net"
        print("error is", {e})
        context = {
            "title": "CONTRACT",
            "message": message,
        }
        return render(request, "main/errors/generalerrors.html", context)


@login_required
def mycontract(request, *args, **kwargs):
    username = kwargs.get("username")
    client_data = CustomerUser.objects.get(username=username)
    if client_data.category == 5:
        try:
            investor_details = (
                Investor_Information.objects.filter(investor_id=client_data.id)
                .order_by("-contract_date")
                .first()
            )
            if investor_details:
                contract_date = investor_details.contract_date.strftime("%d %B, %Y")
                context = {
                    "client_data": client_data,
                    "contract_date": contract_date,
                    "investor_data": investor_details,
                }
                return render(
                    request, "management/contracts/my_investor_contract.html", context
                )
            else:
                return redirect("investing:investments")

        except Investor_Information.DoesNotExist:
            return redirect("investing:investments")
    else:
        try:
            payment_details = Payment_Information.objects.filter(
                customer_id_id=client_data.id
            ).first()
            contract_date = payment_details.contract_submitted_date.strftime(
                "%d %B, %Y"
            )
            context = {
                "job_support_data": client_data,
                "contract_date": contract_date,
                "payment_data": payment_details,
            }
            if client_data.category == 3 or client_data.category == 4:
                return render(
                    request,
                    "management/contracts/my_supportcontract_form.html",
                    context,
                )
            else:
                raise Http404("Login/Wrong Page: Are You a Client?")

        except Payment_Information.DoesNotExist:
            if client_data.category == 3:
                return redirect("main:job_support")
            elif client_data.category == 4:
                return redirect("main:service_plans", slug="full-course")
            else:
                return redirect("main:bi_services")


@login_required
def new_investment_contract(request, plan_id=None, *args, **kwargs):
    client_data = CustomerUser.objects.get(username=request.user)
    print(client_data.username)
    today = date.today()
    contract_payment_start = today + relativedelta(months=3)
    # Fetch plan details from API or local database
    plan = None
    try:
        response = requests.get(f"https://api.example.com/investment_plans/{plan_id}")
        plan_data = response.json()
        if not isinstance(plan_data, dict):
            raise ValueError("Invalid API response format")
        plan_name = plan_data.get("name", "Unknown Plan")
        rate = Decimal(plan_data.get("rate", 0.05))
        tax_rate = Decimal(plan_data.get("tax_rate", 0.05))
    except (requests.exceptions.RequestException, ValueError):
        plan = get_object_or_404(Investment_rates, id=plan_id, is_active=True)
        plan_name = plan.name
        print("plan_name=====>", plan_name)
        rate = plan.rate
        tax_rate = plan.tax

    if request.method == "POST":
        try:
            amount_invested = Decimal(request.POST.get("amount"))
            duration = int(request.POST.get("duration"))
            print(amount_invested, duration)
            # Validate inputs
            if (
                amount_invested < plan.share_price_min
                or amount_invested > plan.share_price_max
            ):
                messages.error(
                    request,
                    f"Amount must be between ${plan.share_price_min} and ${plan.share_price_max}.",
                )
                return redirect("investing:investment_plan_list")
            if duration < 6:
                messages.error(request, "Duration must be at least 6 months.")
                return redirect("investing:investment_plan_list")
            # Calculate returns
            investment_obj = Investor_Information.objects.filter(model_type=plan_name)
            model_type = plan_name
            business_revenue = Decimal(3000)
            investment_goal = Decimal(plan.base_amount)

            total_amount, monthly_payments, number_positions = (
                calculate_investor_returns(
                    request,
                    investment_obj,
                    amount_invested,
                    model_type,
                    rate,
                    duration,
                    business_revenue,
                    investment_goal,
                )
            )
            tax_amount = monthly_payments * tax_rate
            context = {
                "client_data": client_data,
                "category": CategoryChoices,
                "interest_rate": rate * 100,
                "tax_rate": tax_rate * 100,
                "tax_amount": tax_amount,
                "total_amount": total_amount,
                "amount_invested": (
                    total_amount * Decimal(0.30)
                    if model_type == "options"
                    else amount_invested
                ),
                "protected_capital": total_amount * Decimal(0.70),
                "monthly_payments": monthly_payments,
                "contract_duration": duration,
                "number_positions": number_positions,
                "contract_date": today.strftime("%d %B, %Y"),
                "contract_payment_start": contract_payment_start.strftime("%d %B, %Y"),
                "model_type": model_type,
            }
            messages.success(
                request, f"Investment of ${amount_invested} successfully created!"
            )
            return render(
                request, "management/contracts/client_investment_contract.html", context
            )
        except (ValueError, Decimal.InvalidOperation):
            messages.error(request, "Invalid amount or duration entered.")
            return redirect("investing:investment_plan_list")
    # Default rendering if not a POST request
    return redirect("investing:investment_plan_list")


@login_required
def new_contract(request, *args, **kwargs):
    plan_name = request.POST.get("category")
    if plan_name == "interview":
        pre_sub_title = plan_name
    else:
        path_list, sub_title, pre_sub_title = path_values(request)
    # print("subtile--->",pre_sub_title)
    username = kwargs.get("username")
    client_data = CustomerUser.objects.get(username=username)

    today = date.today()
    plan_title = (
        request.POST.get("service_title").lower()
        if request.method == "POST" and request.POST.get("service_title")
        else None
    )
    plan = contract_charge = contract_duration = contract_period = None
    print(plan_title)
    try:
        if pre_sub_title:
            service_category_instance = ServiceCategory.objects.get(slug=pre_sub_title)
        else:
            return redirect("main:display_service")
    except ServiceCategory.DoesNotExist:
        return redirect("main:display_service")

    # Access the service_instance properties
    service_instance = Service.objects.filter(
        servicecategory__name=service_category_instance.name
    ).first()
    if service_instance:
        service_title = service_instance.title
        service_title_uppercase = service_title.upper()
        service_description = service_instance.description
    else:
        print("No service found for the given pricing title.")

    plan = Pricing.objects.filter(
        category=service_category_instance.id, title__iexact=plan_title
    ).first()
    print(plan)
    if plan:
        contract_charge = plan.price
        contract_duration = plan.duration
        contract_period = plan.contract_length
        plan_id = plan.id
    context = {
        "service_title": service_title,
        "service_title_uppercase": service_title_uppercase,
        "client_data": client_data,
        "contract_data": plan,
        "contract_charge": contract_charge,
        "contract_duration": contract_duration,
        "contract_period": contract_period,
        "plan_id": plan_id,
        "contract_date": today.strftime("%d %B, %Y"),
    }
    return render(request, "management/contracts/client_contract.html", context)


# ==================PAYMENT CONFIGURATIONS VIEWS=======================
class PaymentConfigCreateView(LoginRequiredMixin, CreateView):
    model = PayslipConfig
    success_url = "/finance/paymentconfigs/"
    fields = "__all__"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class PaymentConfigListView(ListView):
    model = PayslipConfig
    template_name = "finance/payments/paymentconfigs.html"
    context_object_name = "payconfigs"


class PaymentConfigUpdateView(UpdateView):
    model = PayslipConfig
    success_url = "/finance/paymentconfigs/"

    fields = "__all__"

    def form_valid(self, form):
        # form.instance.author=self.request.user
        if self.request.user.is_superuser:
            return super().form_valid(form)
        else:
            # return redirect("management:tasks")
            return render(request, "management/contracts/supportcontract_form.html")

    def test_func(self):
        # task = self.get_object()
        if self.request.user.is_superuser:
            return True
        # elif self.request.user == task.employee:
        #     return True
        return False


# ==================PAYMENTVIEWS=======================
class PaymentCreateView(LoginRequiredMixin, CreateView):
    model = Default_Payment_Fees
    success_url = "/finance/contract_form"
    fields = [
        "job_down_payment_per_month",
        "job_plan_hours_per_month",
        "student_down_payment_per_month",
        "student_bonus_payment_per_month",
    ]

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


# def payments(request,title='history', status=None):
#     path_list,sub_title,pre_sub_title=path_values(request)
#     Payment_Info=None
#     payment_history=None
#     if path_list[2]=='info':
#         Payment_Info=Payment_Information.objects.all()
#     else:
#         if status == "complete":
#             payment_history = [p for p in Payment_History.objects.all() if p.fee_balance == 0]

#         elif status == "in_progress":
#             payment_history = [p for p in Payment_History.objects.all() if p.is_active and p.is_featured and p.fee_balance > 0]

#         elif status == "collection":
#             payment_history = Payment_History.objects.filter(is_active=False, is_featured=True, payment_method='paypal')

#         elif status == "bad":
#             payment_history = Payment_History.objects.exclude(customer__category__in=[1, 3, 4, 5, 6, 7])  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
#     context={
#         "heading":"PAYMENT INFORMATION" if path_list[2]=='info' else "PAYMENT HISTORY",
#         "payment_history":payment_history,
#         "Payment_Info":Payment_Info,
#         "status":status
#     }
#     return render(request,"finance/payments/payments.html",context)


def payments(request, title="history", status=None):
    path_list, sub_title, pre_sub_title = path_values(request)
    Payment_Info = None
    payment_history = None

    # Check if user is staff/superuser/admin (can see all payments)
    # Using your CustomerUser model fields
    is_staff_user = (
        request.user.is_staff
        or request.user.is_superuser
        or getattr(request.user, "is_admin", False)
        or request.user.category == 2  # Staff category from your choices
    )

    if path_list[2] == "info":
        if is_staff_user:
            Payment_Info = Payment_Information.objects.all()
        else:
            Payment_Info = Payment_Information.objects.filter(customer_id=request.user)
    else:
        if status == "complete":
            if is_staff_user:
                payment_history = [
                    p for p in Payment_History.objects.all() if p.fee_balance == 0
                ]
            else:
                payment_history = [
                    p
                    for p in Payment_History.objects.filter(customer=request.user)
                    if p.fee_balance == 0
                ]

        elif status == "in_progress":
            if is_staff_user:
                payment_history = [
                    p
                    for p in Payment_History.objects.all()
                    if p.is_active and p.is_featured and p.fee_balance > 0
                ]
            else:
                payment_history = [
                    p
                    for p in Payment_History.objects.filter(customer=request.user)
                    if p.is_active and p.is_featured and p.fee_balance > 0
                ]

        elif status == "collection":
            if is_staff_user:
                payment_history = Payment_History.objects.filter(
                    is_active=False, is_featured=True, payment_method="paypal"
                )
            else:
                payment_history = Payment_History.objects.filter(
                    customer=request.user,
                    is_active=False,
                    is_featured=True,
                    payment_method="paypal",
                )

        elif status == "bad":
            if is_staff_user:
                payment_history = Payment_History.objects.exclude(
                    customer__category__in=[1, 3, 4, 5, 6, 7]
                )
            else:
                payment_history = Payment_History.objects.filter(
                    customer=request.user
                ).exclude(customer__category__in=[1, 3, 4, 5, 6, 7])

    context = {
        "heading": (
            "PAYMENT INFORMATION" if path_list[2] == "info" else "PAYMENT HISTORY"
        ),
        "payment_history": payment_history,
        "Payment_Info": Payment_Info,
        "status": status,
        "is_staff_user": is_staff_user,  # Add this to context for template use
    }
    return render(request, "finance/payments/payments.html", context)


def payment_plan(request, payment_id):
    # Get the specific payment information based on payment_id
    pay_obj = get_object_or_404(Payment_History, id=payment_id)
    pay_amount = pay_obj.payment_fees
    if 1000 < pay_amount <= 3000:
        divided_amount = pay_amount / 3
    elif pay_amount > 3000:
        divided_amount = pay_amount / 4
    else:
        divided_amount = pay_amount

    context = {
        "payment_info": [pay_obj],
        "divided_amount": divided_amount,
        "payment_id": payment_id,
        "username": pay_obj.customer.username,
    }
    # Check if the user requested to send an email
    if request.method == "POST":
        current_site = Site.objects.get_current()
        domain = current_site.domain
        subject = f"Payment Plan for {pay_obj.customer.username}"
        payment_plan_url = f"https://{domain}/finance/payment_plan/{payment_id}"
        # print('url',payment_plan_url)
        message = f"""
        Hi {pay_obj.customer.username},

        Please find your payment plan by clicking the link below:

        {payment_plan_url}

        Thank you for your continued trust in us.
        """
        recipient = pay_obj.customer.email  # Assuming the customer has an email field

        send_email_to_client(subject, message, recipient)

    return render(request, "finance/payments/plan.html", context)


def save_and_upload_to_drive(request):
    if request.method == "POST" and request.FILES.get("pdf"):
        pdf_file = request.FILES["pdf"]

        # Save PDF temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            for chunk in pdf_file.chunks():
                temp_pdf.write(chunk)
            temp_pdf_path = temp_pdf.name

        # Google Drive API setup using direct credentials
        creds = Credentials(
            token=os.environ.get("GOOGLE_ACCESS_TOKEN"),
            refresh_token=os.environ.get("GOOGLE_REFRESH_TOKEN"),
            client_id=os.environ.get("GOOGLE_CLIENT_ID"),
            client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
            token_uri="https://oauth2.googleapis.com/token",
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )
        # Initialize Google Drive API service
        service = build("drive", "v3", credentials=creds)
        file_name = pdf_file.name
        # print(file_name)

        # Set metadata and upload file to Google Drive
        file_metadata = {
            "name": file_name,
            "parents": ["1AY8BxebyXNg5ED5TOlwNzoArDUwXaBxG"],
        }
        media = MediaFileUpload(temp_pdf_path, mimetype="application/pdf")
        try:
            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id")
                .execute()
            )
            success = True
            message = f"File uploaded successfully with file ID: {file.get('id')}"
        except Exception as e:
            success = False
            message = f"Error uploading file to Google Drive: {e}"

        # Cleanup and respond
        os.remove(temp_pdf_path)  # Remove temporary file
        return JsonResponse({"success": success, "message": message})
    return JsonResponse({"success": False, "message": "No PDF file found in request."})


def payment(request, method):
    path_list, sub_title, pre_sub_title = path_values(request)
    subject = "PAYMENT"
    url = "email/payment/payment_method.html"
    message = f"Hi,{request.user.first_name}, an email has been sent \
            with {sub_title} details for your payment.In the unlikely event\
            that you have not received it, kindly \
            check your spam folder."
    error_message = f"Hi,{request.user.first_name}, there seems to be an issue on our end.kindly contact us directly for payment details."
    context = {
        "subtitle": sub_title,
        "user": request.user.first_name,
        "mpesa_number": phone_number,
        "cashapp": cashapp,
        "venmo": venmo,
        "account_no": account_no,
        "email": email_info,
        "message": message,
        "error_message": error_message,
        "contact_message": "info@codanalytics.net",
    }
    try:
        send_email(
            category=request.user.category,
            to_email=[
                request.user.email,
            ],
            subject=subject,
            html_template=url,
            context=context,
        )
        return render(request, "email/payment/payment_method.html", context)
    except:
        return render(request, "email/payment/payment_method.html", context)


def send_notification(request, payment_id=None):
    path_list, sub_title, pre_sub_title = path_values(request)
    url = None
    user_payment_information = Payment_History.objects.get(id=payment_id)
    user_category = user_payment_information.customer.category
    user_plan = user_payment_information.plan

    current_site = Site.objects.get_current()
    domain = current_site.domain
    payment_plan_url = f"https://{domain}/finance/payment_plan/{payment_id}"

    # Fetch repayment rate from payslipConfigs

    try:
        payslip_config = PayslipConfig.objects.filter(
            user__username=user_payment_information.customer.username
        ).latest("installment_date")
    except PayslipConfig.DoesNotExist:
        payslip_config = PayslipConfig.objects.get(user__username="coda_info")
    except MultipleObjectsReturned:
        payslip_config = (
            PayslipConfig.objects.filter(
                user__username=user_payment_information.customer.username
            )
            .order_by("-installment_date")
            .first()
        )

    # Convert notification days from string to integer if needed
    Number_notification_days = int(user_payment_information.notification_days)

    if Number_notification_days > 7:
        # Send notification logic here
        user_payment_information.rep_date = timezone.now().date().strftime("%Y-%m-%d")
        user_payment_information.save()

    # Determine email subject and template based on subtitle and user plan
    if pre_sub_title == "collection":
        subject = "Urgent: Outstanding Dues - Immediate Action Required"
        url = "email/payment/collection.html"
    elif pre_sub_title == "in_progress":
        url = "email/payment/invoice.html"
        subject = "Loan Amount" if user_plan == 4 else "Training and Support"
    else:
        return redirect("finance:payments", title="history", status="collection")

    # Calculate Repayment amount
    if payslip_config.loan_repayment_percentage > Decimal(0):
        # print("Percentage=====>",payslip_config.loan_repayment_percentage)
        repayment_amount = (
            user_payment_information.fee_balance
            * payslip_config.loan_repayment_percentage
        )
    else:
        repayment_amount = user_payment_information.fee_balance
        # print("repayment_amount=====>",repayment_amount,payslip_config.loan_repayment_percentage)

    # Calculate overdue days and due date
    contract_submitted_date = user_payment_information.contract_submitted_date
    number_days = (datetime.now().date() - contract_submitted_date.date()).days
    months = round(number_days / 30, 2)
    next_month = datetime.today() + relativedelta(months=1)
    next_month_15th = next_month.replace(day=15)
    message = (
        f"Hi {request.user.first_name}, Your message was successfully sent to "
        f"{user_payment_information.customer.email}. To confirm, please check "
        f"sent mails of finance@codanalytics.net. Thank You."
    )
    context = {
        "purpose": "payment",
        "subject": subject,
        "user_info": user_payment_information,
        "number_days_overdue": number_days,
        "time_overdue": months,
        "due_date": next_month_15th.date(),
        "repayment_amount": repayment_amount,
        "repayment_rate": payslip_config.loan_repayment_percentage,
        "email_info": email_info,
        "cashapp": cashapp,
        "address": (
            user_payment_information.customer.address
            if user_payment_information.customer.address
            else ""
        ),
        "city": (
            user_payment_information.customer.city
            if user_payment_information.customer.city
            else ""
        ),
        "state": (
            user_payment_information.customer.state
            if user_payment_information.customer.state
            else ""
        ),
        "country": (
            user_payment_information.customer.country
            if user_payment_information.customer.country
            else ""
        ),
        "message": message,
        "payment_plan_url": payment_plan_url,
    }

    try:
        send_email(
            category=user_category,
            to_email=[user_payment_information.customer.email],
            subject=subject,
            html_template=url,
            context=context,
        )
        # return render(request,url, context)
        return render(request, "main/messages/message.html", context)
    except Exception as e:
        error_message = (
            f"Hi {request.user.first_name}, Your message to "
            f"{user_payment_information.customer.email} was unsuccessful. "
            f"Please try again or contact finance@codanalytics.net. Thank You. "
            f"Error: {e}"
        )
        return render(request, "main/messages/message.html", {"message": error_message})


def send_invoice(request, type="collection"):
    service = "Training and Job Support"
    url = None
    ###############################
    # due payment userlist
    ###############################
    # user_payment_information = Payment_History.objects.filter(fee_balance__gt=0, customer__is_client=True).distinct('customer_id')
    if type == "collection":
        url = "email/payment/collection.html"
        user_payment_information = Payment_History.objects.filter(
            fee_balance__gt=0, is_active=False, is_featured=True
        ).distinct("customer_id")
    else:
        user_payment_information = Payment_History.objects.filter(
            fee_balance__gt=0, is_active=True, is_featured=True
        ).distinct("customer_id")
        url = "email/payment/invoice.html"

    successful_user_list = []

    for customer_payment_information in user_payment_information:
        print("user_payment_information=======>", customer_payment_information)
        successful_user_list.append(customer_payment_information)

        if PayslipConfig.objects.filter(
            user__username=customer_payment_information.customer.username
        ).exists():
            payslip_config = PayslipConfig.objects.get(
                user__username=customer_payment_information.customer.username
            )
        else:
            payslip_config = PayslipConfig.objects.get(user__username="coda_info")
            # payslip_config = PayslipConfig.objects.create(
            #     user = customer_payment_information.customer,
            #     loan_amount = customer_payment_information.payment_fees,
            #     loan_repayment_percentage = 0,
            #     rp_starting_period= customer_payment_information.contract_submitted_date.strftime("%Y-%m-%d"),
            #     installment_amount = customer_payment_information.down_payment,
            #     installment_date = datetime.now().date()
            # )

        if (
            payslip_config.installment_date
            and payslip_config.installment_date.day == datetime.today().date().day
        ):
            organization = Company.objects.filter(
                user__username=customer_payment_information.customer.username
            )
            client = customer_payment_information.customer
            client_email = client.email
            today = datetime.now()
            date = datetime(today.year, today.month, 1)
            debt_amount = customer_payment_information.fee_balance
            repayment_amount = payslip_config.installment_amount
            balance_amount = (
                debt_amount - repayment_amount
                if debt_amount - repayment_amount > 0
                else debt_amount
            )
            context = {
                "service": service,
                "date": date,
                "first_name": client.first_name,
                "last_name": client.last_name,
                "organization": (
                    organization.first().name
                    if organization.exists()
                    else f"{client.first_name} {client.last_name}"
                ),
                "address": client.address if client.address is not None else "",
                "city": client.city if client.city is not None else "",
                "state": client.state if client.state is not None else "",
                "country": client.country if client.country is not None else "",
                "zipcode": client.zipcode if client.zipcode is not None else "",
                "account_no": account_no,
                "user_email": client.email,
                "debt_amount": debt_amount,
                "repayment_amount": repayment_amount,
                "balance_amount": balance_amount,
                "email": email_info,
                "message": "sucess",
                "error_message": "error_message",
                "contact_message": "info@codanalytics.net",
            }
            try:
                # send_email( category=request.user.category,
                #             to_email=[client_email],#[request.user.email,],
                #             subject=service, html_template=url,
                #             context=context
                #             )
                successful_user_list.append(context)
                return render(request, url, context)
            except:
                pass
    return render(
        request,
        "finance/payments/sendinvoice.html",
        {"customer_payment_information": successful_user_list},
    )


@login_required
def pay(request, *args, **kwargs):
    contract_url = reverse("finance:newcontract", args=[request.user.username])
    payment_info = None

    if request.method == "POST" and request.POST.get("fees"):
        total_fee = float(request.POST.get("fees"))
        if not request.POST.get("is_direct", False):
            downpayment = total_fee * 0.30
        else:
            downpayment = total_fee
        fee_balance = total_fee - downpayment
        payment_info = Payment_Information.objects.create(
            customer_id=request.user,
            payment_fees=total_fee,
            down_payment=downpayment,
            student_bonus=0,
            plan=request.POST.get(
                "service_category_id", 999
            ),  # added service_category id
            subplan=request.POST.get("subplan_id", None),
            pricing_plan=request.POST.get("pricing_serial", None),
            # fee_balance=fee_balance,
            payment_method="mpesa",
            contract_submitted_date=date.today(),
            client_signature="client",
            company_rep="coda",
            client_date=date.today(),
            rep_date=date.today(),
        )
        paypal_charges = (
            calculate_paypal_charges(payment_info.down_payment) if payment_info else 0
        )
    else:
        try:
            payment_info = (
                Payment_Information.objects.filter(customer_id=request.user.id)
                .order_by("-contract_submitted_date")
                .first()
            )
            print(payment_info.payment_fees)
            paypal_charges = (
                calculate_paypal_charges(payment_info.payment_fees)
                if payment_info
                else 0
            )
        except:
            payment_info = (
                Investor_Information.objects.filter(investor=request.user.id)
                .order_by("-contract_date")
                .first()
            )
            # Need modification to take the user to the interested page.
            return redirect("main:layout")
            paypal_charges = (
                calculate_paypal_charges(payment_info.amount_invested)
                if payment_info
                else 0
            )

    total_amount = amount_due = payment_info.payment_fees + paypal_charges
    amount_due = payment_info.down_payment + paypal_charges

    context = {
        "title": "PAYMENT",
        "payments": payment_info,
        "total_amount": total_amount,
        "amount_due": amount_due,
        "paypal_charges": paypal_charges,
        "message": f"Hi {request.user}, you are yet to sign the contract with us. Kindly contact us at info@codanalytics.net.",
        "link": contract_url,
    }
    return render(request, "finance/payments/pay.html", context)


def paymentComplete(request):
    payments = Payment_Information.objects.filter(customer_id=request.user.id).first()
    customer = request.user
    body = json.loads(request.body)
    payment_fees = body["payment_fees"]
    down_payment = payments.down_payment
    studend_bonus = payments.student_bonus
    plan = payments.plan
    subplan = payments.subplan
    pricing_plan = payments.pricing_plan
    # fee_balance = payments.fee_balance
    payment_mothod = payments.payment_method
    contract_submitted_date = payments.contract_submitted_date
    client_signature = payments.client_signature
    company_rep = payments.company_rep
    client_date = payments.client_date
    rep_date = payments.rep_date
    Payment_History.objects.create(
        customer=customer,
        payment_fees=payment_fees,
        down_payment=down_payment,
        student_bonus=studend_bonus,
        plan=plan,
        subplan=subplan,
        pricing_plan=pricing_plan,
        # fee_balance=fee_balance,
        payment_method=payment_mothod,
        contract_submitted_date=contract_submitted_date,
        client_signature=client_signature,
        company_rep=company_rep,
        client_date=client_date,
        rep_date=rep_date,
    )
    try:
        if PayslipConfig.objects.filter(user__username=request.user.username).exists():
            payslip_config = PayslipConfig.objects.get(
                user__username=request.user.username
            )
            payslip_config.loan_amount = payment_fees
            payslip_config.installment_amount = down_payment
            payslip_config.save()

        else:
            payslip_config = PayslipConfig.objects.create(
                user=request.user.customer_id,
                loan_amount=payment_fees,
                loan_repayment_percentage=0,
                installment_amount=down_payment,
            )
    except:
        pass

    return JsonResponse("Payment completed!", safe=False)


class DefaultPaymentListView(ListView):
    model = Default_Payment_Fees
    template_name = "finance/payments/defaultpayments.html"
    context_object_name = "defaultpayments"


class DefaultPaymentUpdateView(UpdateView):
    model = Default_Payment_Fees
    success_url = "/finance/payments"

    fields = [
        "job_down_payment_per_month",
        "job_plan_hours_per_month",
        "student_down_payment_per_month",
        "student_bonus_payment_per_month",
        "loan_amount",
    ]

    # fields=['user','activity_name','description','point']
    def form_valid(self, form):
        # form.instance.author=self.request.user
        if self.request.user.is_superuser:
            return super().form_valid(form)
        else:
            # return redirect("management:tasks")
            return render(request, "management/contracts/supportcontract_form.html")

    def test_func(self):
        task = self.get_object()
        if self.request.user.is_superuser:
            return True
        # elif self.request.user == task.employee:
        #     return True
        return False


class PaymentInformationUpdateView(UpdateView):
    model = Payment_Information
    success_url = "/finance/payments/info/None"
    template_name = "main/snippets_templates/generalform.html"

    fields = "__all__"

    # fields=['customer_id','down_payment']
    def form_valid(self, form):
        # form.instance.author=self.request.user
        # if self.request.user.is_superuser or self.request.user:
        if self.request.user is not None:
            return super().form_valid(form)
        else:
            # return redirect("management:tasks")
            return render(request, "main/snippets_templates/generalform.html")

    def test_func(self):
        task = self.get_object()
        # if self.request.user.is_superuser:
        # 	return True
        # elif self.request.user == task.employee:
        if self.request.user:
            return True


class PaymentHistoryUpdateView(UpdateView):
    model = Payment_History
    success_url = "/finance/payments/history/in_progress"
    template_name = "main/snippets_templates/generalform.html"

    fields = "__all__"

    # fields=['customer_id','down_payment']
    def form_valid(self, form):
        # form.instance.author=self.request.user
        # if self.request.user.is_superuser or self.request.user:
        if self.request.user is not None:
            return super().form_valid(form)
        else:
            # return redirect("management:tasks")
            return render(request, "main/snippets_templates/generalform.html")

    def test_func(self):
        task = self.get_object()
        # if self.request.user.is_superuser:
        # 	return True
        # elif self.request.user == task.employee:
        if self.request.user:
            return True


class UserPayUpdateView(UpdateView):
    model = Payment_Information
    success_url = "/finance/pay/"
    template_name = "main/snippets_templates/generalform.html"

    # fields ="__all__"
    fields = ["customer_id", "down_payment"]

    def form_valid(self, form):
        # form.instance.author=self.request.user
        # if self.request.user.is_superuser or self.request.user:
        if self.request.user is not None:
            return super().form_valid(form)
        else:
            # return redirect("management:tasks")
            return render(request, "main/snippets_templates/generalform.html")

    def test_func(self):
        task = self.get_object()
        # if self.request.user.is_superuser:
        # 	return True
        # elif self.request.user == task.employee:
        if self.request.user:
            return True


# ----------------------CASH OUTFLOW CLASS-BASED VIEWS--------------------------------
@login_required
def transact(request):
    if request.method == "POST":
        form = TransactionForm(request.POST, request.FILES)
        if form.is_valid():
            # form.save()
            instance = form.save(commit=False)
            instance.sender = request.user
            amount_ksh = instance.amount
            cost_ksh = instance.transaction_cost
            amount_usd = round(Decimal(amount_ksh / rate), 2)
            cost_usd = round(Decimal(cost_ksh / rate), 2)
            description = f"On {today_date},Ksh.{amount_ksh}/usd.{amount_usd} went for {instance.category},more specifically {instance.subcategory.name},there was a transaction fee of Ksh.{instance.transaction_cost}(usd {cost_usd})"
            # print(description)
            instance.description = description
            instance.save()
            return redirect("/finance/transaction/operations")
        else:
            print(form.errors)
    else:
        form = TransactionForm()
    return render(request, "finance/payments/transact.html", {"form": form})


class TransactionListView(ListView):
    model = Transaction
    template_name = "finance/cashflows/cashflows.html"
    context_object_name = "transactions"
    # ordering=['-transaction_date']


@method_decorator(login_required, name="dispatch")
class TransanctionDetailView(DetailView):
    template_name = "finance/payments/transaction_detail.html"
    model = Transaction
    ordering = ["-transaction_date"]


class TransactionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Transaction
    success_url = "/finance/cashflows/outflow"
    fields = [
        "transaction_date",
        "sender",
        "receiver",
        "vendor_supplier",
        "phone",
        "department",
        "category",
        "subcategory",
        "type",
        "payment_method",
        "qty",
        "amount",
        "transaction_cost",
        "description",
        "receipt_link",
    ]
    form = TransactionForm()

    def form_valid(self, form):
        form.instance.username = self.request.user
        amount_ksh = form.instance.amount
        amount_usd = round(Decimal(amount_ksh / rate), 2)
        cost_ksh = form.instance.transaction_cost
        cost_usd = round(Decimal(cost_ksh / rate), 2)
        description = f"Ksh.{amount_ksh}/usd.{amount_usd} went for {form.instance.category},more specifically {form.instance.subcategory.name},there was a transaction fee of Ksh.{form.instance.transaction_cost}(usd {cost_usd})"
        print(description)
        form.instance.description = description
        return super().form_valid(form)

    # def get_success_url(self):
    # 	reverse('finance:transaction-list', kwargs={'transaction_type': 'operations'})

    # def test_func(self):
    # 	inflow = self.get_object()
    # 	if self.request.user == inflow.sender:
    # 		return True
    # 	elif self.request.user.is_admin or self.request.user.is_superuser:
    # 		return True
    # 	return False

    def test_func(self):
        if self.request.user:
            return True
        return False


@method_decorator(login_required, name="dispatch")
class TransactionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Transaction
    success_url = "/finance/cashflows/outflow"

    def test_func(self):
        transaction = self.get_object()
        if self.request.user == transaction.sender:
            return True
        elif self.request.user.is_superuser or self.request.user.is_admin:
            return True
        return False


def filteroutflowsbydepartment(request, cashflows):
    if request.method == "POST":
        form = DepartmentFilterForm(request.POST)
        if form.is_valid():
            department = form.cleaned_data["name"]
            filtered_cashflows = cashflows.filter(department__name=department).order_by(
                "-id"
            )
        return filtered_cashflows, form
    else:
        form = DepartmentFilterForm()
        return cashflows, form


def filteroutflowsbydepartment(request, cashflows: QuerySet):
    """
    Filters cashflows by department if a valid department name is provided via a POST request.
    Args:
        request (HttpRequest): The current HTTP request object.
        cashflows (QuerySet): A queryset of cashflows to filter.
    Returns:
        tuple: (filtered_cashflows, form) where:
            - filtered_cashflows (QuerySet): The filtered queryset.
            - form (DepartmentFilterForm): The department filter form.
    """
    # Initialize form
    form = DepartmentFilterForm(request.POST or None)
    # Check if the form is valid for a POST request
    if request.method == "POST" and form.is_valid():
        department = form.cleaned_data.get("name")
        print(f"Filtering by department: {department}")

        # Filter cashflows by department name
        try:
            filtered_cashflows = cashflows.filter(department__name=department).order_by(
                "-id"
            )
        except Exception as e:
            print(f"Error while filtering: {e}")
            filtered_cashflows = (
                cashflows  # Default to the original queryset in case of errors
            )
        return filtered_cashflows, form

    # Return the unfiltered queryset and the form for GET or invalid POST requests
    return cashflows, form


# ----------------------CASH INFLOW CLASS-BASED VIEWS--------------------------------
def inflow(request):
    if request.method == "POST":
        form = InflowForm(request.POST, request.FILES)
        if form.is_valid():
            form.instance.sender = request.user
            form.save()
            return redirect("/finance/cashflows/inflow/")
    else:
        form = InflowForm()
    return render(request, "finance/cashflows/inflow_entry.html", {"form": form})


@method_decorator(login_required, name="dispatch")
class InflowDetailView(DetailView):
    template_name = "finance/cashflows/inflow_detail.html"
    model = Inflow
    ordering = ["-transaction_date"]


@login_required
def cashflows(request, type=None, time_filter="30_days"):
    """
    Unified function to handle both inflows and outflows.
    """
    cashflows = None
    total_amount = Decimal(0)
    data = []
    webhour, delta = PayslipConfig.objects.values_list(
        "web_pay_hour", "web_delta"
    ).first()
    # Handle dates_functionality which might return None
    dates_result = dates_functionality()
    if dates_result:
        ytd_duration, current_year, first_date = dates_result
    else:
        # Fallback values if dates_functionality returns None
        from datetime import datetime
        current_year = datetime.now().year
        ytd_duration = 365
        first_date = datetime(current_year, 1, 1).date()

    # Determine date range for time filters
    today = datetime.now().date()
    start_date = today - timedelta(days=30)  # Default: Last 30 days
    if time_filter == "last_month":
        start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    elif time_filter == "last_year":
        start_date = today.replace(year=today.year - 1, month=1, day=1)
    elif time_filter == "all":
        start_date = None  # No filtering

    # Determine cashflow type: inflow or outflow
    if type == "inflow":
        print("Processing inflows")
        inflows = Inflow.objects.all()
        if start_date:
            inflows = inflows.filter(transaction_date__gte=start_date)
        inflows = inflows.order_by("-transaction_date")
        cashflows, form = filteroutflowsbydepartment(request, inflows)
        total_amount = sum(inflow.total_payment for inflow in cashflows) or Decimal(0)

    elif type == "outflow":
        print("Processing outflows")
        outflows = Transaction.objects.all()
        if start_date:
            outflows = outflows.filter(transaction_date__gte=start_date)
        outflows = outflows.order_by("-id")
        cashflows, form = filteroutflowsbydepartment(request, outflows)

        # Convert to Decimal to avoid type errors
        rate = Decimal(1.0)  # Replace with actual exchange rate or calculation
        total_op_outflows = sum(
            Decimal(transact.amount) * Decimal(transact.qty) for transact in cashflows
        )
        ytd_transactions = cashflows.filter(transaction_date__year=current_year)
        ytd_op_outflow = sum(
            Decimal(transact.amount) * Decimal(transact.qty)
            for transact in ytd_transactions
        )
        total_op_outflows_usd = total_op_outflows / rate
        ytd_op_outflow_usd = ytd_op_outflow / rate

        # Website totals
        web_obj = Requirement.objects.all()
        web_obj_done = Requirement.objects.filter(is_reviewed=False)
        ytd_requirements = Requirement.objects.filter(
            created_at__year=current_year, is_reviewed=False
        )
        ytd_web_outflow = sum(
            Decimal(req.duration) * Decimal(delta) * Decimal(webhour)
            for req in ytd_requirements
        )
        total_web_outflow = sum(
            Decimal(req.duration) * Decimal(delta) * Decimal(webhour)
            for req in web_obj_done
        )

        # Field totals
        field_obj = Field_Expense.objects.all()
        ytd_field_obj = Field_Expense.objects.filter(date__year=current_year)
        ytd_field_outflow = sum(
            Decimal(transact.transactions_amt) for transact in ytd_field_obj
        )
        total_field_outflow = sum(
            Decimal(transact.transactions_amt) for transact in field_obj
        )
        total_field_outflow_usd = total_field_outflow / rate
        ytd_field_outflow_usd = ytd_field_outflow / rate

        # Calculate total and YTD outflows
        total_outflows = (
            total_op_outflows_usd + total_web_outflow + total_field_outflow_usd
        )
        ytd_outflows = ytd_op_outflow_usd + ytd_web_outflow + ytd_field_outflow_usd

        # Averages
        avg_daily_expenditure = ytd_outflows / Decimal(ytd_duration)
        avg_monthly_expenditure = avg_daily_expenditure * Decimal(30)
        avg_quarterly_expenditure = avg_monthly_expenditure * Decimal(3)

        # Prepare data for summary
        data = [
            {
                "title": "Operations",
                "link": "/finance/transaction/operations",
                "value": total_op_outflows_usd,
            },
            {
                "title": "Web Development",
                "link": "/finance/coda_budget_estimation/all/",
                "value": total_web_outflow,
            },
            {
                "title": "Makutano Office",
                "link": "/finance/transaction/field",
                "value": total_field_outflow_usd,
            },
            {"title": "Year_To_Date", "link": "all", "value": ytd_outflows},
            {"title": "Quarterly", "link": "all", "value": avg_quarterly_expenditure},
            {"title": "Monthly", "link": "all", "value": avg_monthly_expenditure},
            {"title": "Daily", "link": "all", "value": avg_daily_expenditure},
        ]
    else:
        # Handle invalid type or default to inflows
        inflows = Inflow.objects.all().order_by("-transaction_date")
        cashflows, form = filteroutflowsbydepartment(request, inflows)
        total_amount = (
            cashflows.aggregate(total_payment=Sum("total_payment"))["total_payment"]
            or 0
        )

    # Context for rendering
    context = {
        "cashflows": cashflows,
        "total_amount": total_amount,
        "type": type,
        "data": data,
        "form": form,
        "webhour": webhour,
        "delta": delta,
    }
    return render(request, "finance/cashflows/cashflows.html", context)


@method_decorator(login_required, name="dispatch")
class UserInflowListView(ListView):
    model = Inflow
    template_name = "finance/cashflows/user_inflow.html"
    context_object_name = "inflows"
    ordering = ["-transaction_date"]


@method_decorator(login_required, name="dispatch")
class InflowUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Inflow
    success_url = "/finance/cashflows/inflow"
    fields = [
        "sender",
        "receiver",
        "phone",
        "category",
        "subcategory",
        "item",
        "method",
        "period",
        "qty",
        "amount",
        "transaction_cost",
        "description",
    ]

    def form_valid(self, form):
        form.instance.sender = self.request.user
        return super().form_valid(form)

    def test_func(self):
        # inflow = self.get_object()
        # if self.request.user == inflow.sender:
        if self.request.user:
            return True
        return False


@method_decorator(login_required, name="dispatch")
class InflowDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Inflow
    success_url = "/finance/inflow"

    def test_func(self):
        inflow = self.get_object()
        # if self.request.user == inflow.sender:
        if self.request.user.is_superuser:
            return True
        return False


# # ============LOAN VIEWS========================


@login_required
def loan_application_confirmation(request):
    """Shows confirmation message after loan application submission."""
    return render(request, "finance/loan_application_confirmation.html")


@login_required
def loan_detail(request, pk):
    """Shows detailed information about a specific loan application."""
    loan = get_object_or_404(LoanApplication, pk=pk, borrower=request.user)
    
    context = {
        'loan': loan,
        'user_currency': getattr(request.user, 'currency', 'USD'),
        'currency_symbol': '$' if getattr(request.user, 'currency', 'USD') == 'USD' else 'KSh' if getattr(request.user, 'currency', 'USD') == 'KSH' else '€',
    }
    
    return render(request, "finance/loan_detail.html", context)


@login_required
def collateral_form(request, loan_id):
    """Display collateral form for external users."""
    loan = get_object_or_404(LoanApplication, pk=loan_id, borrower=request.user)
    
    # Only external users need to fill collateral form
    if request.user.category == 2:  # Staff users don't need collateral
        return redirect("finance:loan-application-confirmation")
    
    context = {
        'loan_id': loan_id,
        'plan_id': loan.loan_product.id,
        'loan_amount': loan.amount_requested,
        'user_currency': getattr(request.user, 'currency', 'USD'),
        'currency_symbol': '$' if getattr(request.user, 'currency', 'USD') == 'USD' else 'KSh' if getattr(request.user, 'currency', 'USD') == 'KSH' else '€',
    }
    
    return render(request, "finance/collateral_form.html", context)


@login_required
def submit_collateral(request, loan_id):
    """Process collateral form submission."""
    print(f"🔍 DEBUG: submit_collateral called with method: {request.method}, loan_id: {loan_id}")
    
    if request.method != 'POST':
        print(f"🔍 DEBUG: Not POST method, redirecting to collateral form")
        return redirect("finance:collateral-form", loan_id=loan_id)
    
    loan = get_object_or_404(LoanApplication, pk=loan_id, borrower=request.user)
    
    print(f"🔍 DEBUG: POST data = {dict(request.POST)}")
    
    # Get form data
    collateral_type = request.POST.get('collateral_type')
    collateral_description = request.POST.get('collateral_description')
    estimated_value = request.POST.get('estimated_value')
    documentation = request.POST.get('documentation', '')
    collateral_location = request.POST.get('collateral_location')
    additional_info = request.POST.get('additional_info', '')
    
    # Validate required fields
    print(f"🔍 DEBUG: Validation - collateral_type: {collateral_type}, description length: {len(collateral_description) if collateral_description else 0}")
    
    if not all([collateral_type, collateral_description, estimated_value, collateral_location]):
        print(f"🔍 DEBUG: Missing required fields")
        messages.error(request, "Please fill in all required fields.")
        return redirect("finance:collateral-form", loan_id=loan_id)
    
    # Validate description length
    if len(collateral_description.strip()) < 50:
        print(f"🔍 DEBUG: Description too short: {len(collateral_description.strip())}")
        messages.error(request, "Collateral description must be at least 50 characters long.")
        return redirect("finance:collateral-form", loan_id=loan_id)
    
    try:
        # Create comprehensive collateral information
        collateral_info = f"""
COLLATERAL TYPE: {collateral_type}
DESCRIPTION: {collateral_description}
ESTIMATED VALUE: ${estimated_value}
LOCATION: {collateral_location}
DOCUMENTATION: {documentation}
ADDITIONAL INFO: {additional_info}
SUBMITTED: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        
        # Update loan application with collateral information
        loan.collateral = collateral_info
        loan.status = 'under_review'  # Move to review status
        loan.save()
        
        # Create smart collateral system integration
        try:
            from .services.smart_collateral_service import SmartCollateralService
            
            smart_collateral_service = SmartCollateralService()
            
            # Prepare collateral data for smart system
            collateral_data = {
                'collateral_type': collateral_type,
                'description': collateral_description,
                'estimated_value': estimated_value,
                'location': collateral_location,
                'coordinates': None,  # Would be populated from GPS
                'monitoring_frequency': 60,  # Check every hour
                'auto_enforcement': True,
                'deploy_smart_contract': True,
                'insurance_required': True,
                'iot_devices': [
                    {
                        'device_type': 'gps_tracker',
                        'serial_number': f'GPS-{loan.id}-001',
                        'manufacturer': 'SmartTrack',
                        'model': 'ST-2024',
                        'is_primary': True,
                        'capabilities': {
                            'gps_tracking': True,
                            'geofencing': True,
                            'tamper_detection': True,
                            'battery_monitoring': True
                        }
                    }
                ],
                'insurance_data': {
                    'provider': 'Smart Insurance Co.',
                    'policy_type': 'comprehensive',
                    'auto_claim': True,
                    'blockchain_verification': True
                }
            }
            
            # Create smart collateral
            smart_collateral = smart_collateral_service.create_smart_collateral(loan, collateral_data)
            
            messages.success(
                request, 
                "Smart collateral system activated! Your collateral is now being monitored 24/7 with IoT devices and blockchain verification."
            )
            
        except Exception as smart_error:
            print(f"🚨 Smart collateral creation failed: {smart_error}")
            messages.warning(
                request, 
                "Collateral information submitted successfully, but smart monitoring setup failed. Your loan is still under review."
            )
        
        return redirect("finance:loan-application-confirmation")
        
    except Exception as e:
        messages.error(request, f"Error submitting collateral information: {e}")
        return redirect("finance:collateral-form", loan_id=loan_id)


@login_required
def edit_loan(request, loan_id):
    """Display loan editing form for users and admins."""
    loan = get_object_or_404(LoanApplication, pk=loan_id)
    
    # Check permissions
    if not (request.user == loan.borrower or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to edit this loan.")
        return redirect("finance:user-loans")
    
    # Only allow editing if loan is pending or under review
    if loan.status not in ['pending', 'under_review', 'pending_guarantor']:
        messages.error(request, "This loan cannot be edited in its current status.")
        return redirect("finance:loan-detail", pk=loan_id)
    
    context = {
        'loan': loan,
        'user_currency': getattr(request.user, 'currency', 'USD'),
        'currency_symbol': '$' if getattr(request.user, 'currency', 'USD') == 'USD' else 'KSh' if getattr(request.user, 'currency', 'USD') == 'KSH' else '€',
        'is_admin': request.user.is_staff or request.user.is_superuser,
    }
    
    return render(request, "finance/edit_loan.html", context)


@login_required
def update_loan(request, loan_id):
    """Process loan update form submission."""
    if request.method != 'POST':
        return redirect("finance:edit-loan", loan_id=loan_id)
    
    loan = get_object_or_404(LoanApplication, pk=loan_id)
    
    # Check permissions
    if not (request.user == loan.borrower or request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to edit this loan.")
        return redirect("finance:user-loans")
    
    # Only allow editing if loan is pending or under review
    if loan.status not in ['pending', 'under_review', 'pending_guarantor']:
        messages.error(request, "This loan cannot be edited in its current status.")
        return redirect("finance:loan-detail", pk=loan_id)
    
    try:
        # Get form data
        amount_requested = request.POST.get('amount_requested')
        purpose = request.POST.get('purpose')
        duration = request.POST.get('duration')
        interest_rate = request.POST.get('interest_rate')
        collateral = request.POST.get('collateral', '')
        
        # Validate required fields
        if not all([amount_requested, purpose]):
            messages.error(request, "Please fill in all required fields.")
            return redirect("finance:edit-loan", loan_id=loan_id)
        
        # Update loan fields
        loan.amount_requested = Decimal(str(amount_requested))
        loan.purpose = purpose
        
        # Admin can edit interest rate and duration
        if request.user.is_staff or request.user.is_superuser:
            if duration:
                loan.duration = int(duration)
            if interest_rate:
                loan.interest_rate = Decimal(str(interest_rate))
        
        # Update collateral if provided
        if collateral.strip():
            loan.collateral = collateral.strip()
        
        # Recalculate financial terms
        if loan.loan_product:
            interest_amount = loan.amount_requested * (loan.interest_rate / 100)
            loan.total_payable = loan.amount_requested + interest_amount
            loan.monthly_payment = loan.loan_product.calculate_monthly_payment(loan.amount_requested, loan.duration)
        
        loan.save()
        
        messages.success(request, "Loan application updated successfully!")
        return redirect("finance:loan-detail", pk=loan_id)
        
    except Exception as e:
        messages.error(request, f"Error updating loan: {e}")
        return redirect("finance:edit-loan", loan_id=loan_id)


@login_required
def smart_collateral_dashboard(request):
    """Smart collateral dashboard with IoT, blockchain, and AI monitoring"""
    
    # Check if user is admin
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect("main:layout")
    
    # Mock data for demonstration - in reality would come from smart collateral service
    context = {
        'total_collateral_value': 2500000,
        'active_monitoring': 156,
        'risk_score': 87,
        'iot_health': 98,
        'active_contracts': 156,
        'blockchain_health': 99.9,
        'recent_alerts': [
            {
                'type': 'payment_missed',
                'message': 'Vehicle #VH-001 (2 hours ago)',
                'severity': 'warning'
            },
            {
                'type': 'location_anomaly',
                'message': 'Equipment #EQ-045 (1 hour ago)',
                'severity': 'info'
            },
            {
                'type': 'device_offline',
                'message': 'Camera #CAM-023 (30 minutes ago)',
                'severity': 'secondary'
            }
        ],
        'ai_insights': [
            {
                'type': 'market_trend',
                'message': 'Equipment values up 3.2% this month',
                'trend': 'up'
            },
            {
                'type': 'risk_prediction',
                'message': '2 items at high risk of default',
                'trend': 'warning'
            },
            {
                'type': 'recommendation',
                'message': 'Increase monitoring for Vehicle #VH-001',
                'trend': 'info'
            }
        ],
        'collateral_types': [
            {'name': 'Smart Vehicles', 'count': 45, 'icon': 'fas fa-car', 'color': 'primary'},
            {'name': 'Smart Properties', 'count': 32, 'icon': 'fas fa-home', 'color': 'success'},
            {'name': 'Smart Equipment', 'count': 67, 'icon': 'fas fa-tools', 'color': 'info'},
            {'name': 'Smart Vaults', 'count': 12, 'icon': 'fas fa-gem', 'color': 'warning'}
        ],
        'recent_activity': [
            {
                'time': '2 min ago',
                'event': 'Payment Received',
                'collateral': 'Vehicle #VH-001',
                'status': 'success'
            },
            {
                'time': '15 min ago',
                'event': 'Location Update',
                'collateral': 'Equipment #EQ-045',
                'status': 'info'
            },
            {
                'time': '1 hour ago',
                'event': 'Device Online',
                'collateral': 'Camera #CAM-023',
                'status': 'success'
            },
            {
                'time': '2 hours ago',
                'event': 'Smart Contract Executed',
                'collateral': 'Property #PR-012',
                'status': 'success'
            }
        ]
    }
    
    return render(request, "finance/smart_collateral_dashboard.html", context)


def loan_system_presentation(request):
    """Investor presentation for the smart loan system"""
    return render(request, "finance/loan_system_presentation.html")


@login_required
def user_collateral_status(request, loan_id):
    """User-specific collateral status page"""
    loan = get_object_or_404(LoanApplication, pk=loan_id, borrower=request.user)
    
    # Mock smart collateral data - in reality would come from smart collateral service
    context = {
        'loan': loan,
        'collateral_status': {
            'status': 'active',
            'risk_score': 85,
            'devices_online': 2,
            'total_devices': 2,
            'last_check': timezone.now(),
            'monitoring_active': True,
            'smart_contract_deployed': True,
            'blockchain_verified': True
        },
        'recent_events': [
            {
                'time': '2 hours ago',
                'event': 'GPS Tracker Activated',
                'status': 'success'
            },
            {
                'time': '1 hour ago',
                'event': 'Smart Contract Deployed',
                'status': 'success'
            },
            {
                'time': '30 minutes ago',
                'event': 'Location Verified',
                'status': 'info'
            }
        ],
        'iot_devices': [
            {
                'name': 'GPS Tracker #001',
                'type': 'GPS Tracker',
                'status': 'online',
                'battery': 95,
                'last_update': '2 minutes ago'
            },
            {
                'name': 'Smart Camera #001',
                'type': 'Security Camera',
                'status': 'online',
                'battery': 88,
                'last_update': '5 minutes ago'
            }
        ]
    }
    
    return render(request, "finance/user_collateral_status.html", context)


def admin_loan_data_modified(form, username, user_data):
    previous_balance_amount = user_data.order_by("-id")[0].balance_amount
    try:
        employee = CustomerUser.objects.get(username=username)
    except:
        employee = None
    data = form.cleaned_data
    if previous_balance_amount != data["balance_amount"]:
        loan_data = LoanApplication(
            user=employee,
            category="Debit",
            amount=data["amount"],
            # created_at,
            # updated_at=2022-10-10,
            # is_active,
            training_loan_amount=data["training_loan_amount"],
            total_earnings_amount=data["total_earnings_amount"],
            # deduction_date,
            deduction_amount=data["deduction_amount"],
            balance_amount=data["balance_amount"],
        )
        loan_data.save()
        return loan_data
    return None


class LoanUpdateView(UpdateView):
    model = LoanApplication
    success_url = "/finance/loans"
    fields = "__all__"

    def form_valid(self, form):
        # form.instance.user=self.request.user
        if self.request.user.is_superuser:
            # Legacy admin_loan_data_modified function removed - not compatible with new loan model
            # The new loan system handles applications differently
            return super().form_valid(form)
        else:
            return redirect("finance:trainingloans")
            # return render(request,"management/contracts/supportcontract_form.html")

    def test_func(self):
        # task = self.get_object()
        if self.request.user.is_superuser:
            return True
        # elif self.request.user == task.employee:
        #     return True
        return False


class LoanListView(ListView):
    model = LoanApplication
    template_name = "finance/payments/loans.html"
    context_object_name = "payments"
    ordering = ["created_at"]


@method_decorator(login_required, name="dispatch")
class userLoanListView(ListView):
    model = LoanApplication
    template_name = "finance/loan_applications_list.html"
    context_object_name = "loans"

    def get_queryset(self):
        """Get loan applications for the current user"""
        return LoanApplication.objects.filter(borrower=self.request.user).order_by(
            "-created_at"
        )

    def get_context_data(self, **kwargs):
        """Add eligibility data to context"""
        context = super().get_context_data(**kwargs)

        # Add eligibility check for the current user
        from finance.utils import check_user_loan_eligibility

        context["eligibility"] = check_user_loan_eligibility(self.request.user)

        return context


# ==================================TESTING FOOD VIEWS==========================
@method_decorator(login_required, name="dispatch")
class FoodCreateView(LoginRequiredMixin, CreateView):
    model = Food
    success_url = "/finance/food"
    fields = "__all__"

    def form_valid(self, form):
        if self.request.user:
            return super().form_valid(form)


class SupplierCreateView(LoginRequiredMixin, CreateView):
    model = Supplier
    success_url = "/finance/food"
    fields = "__all__"

    def form_valid(self, form):
        if self.request.user:
            return super().form_valid(form)


@method_decorator(login_required, name="dispatch")
class SupplierUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Supplier
    success_url = "/finance/food"
    # fields=['group','category','employee','activity_name','description','point','mxpoint','mxearning']
    fields = "__all__"

    def form_valid(self, form):
        # form.instance.author=self.request.user
        return super().form_valid(form)

    def test_func(self):
        Supplier = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user == Supplier.added_by:
            return True
        return redirect("finance:supplies")


@method_decorator(login_required, name="dispatch")
class FoodUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Food
    success_url = "/finance/food"
    fields = "__all__"

    def form_valid(self, form):
        # form.instance.author=self.request.user
        return super().form_valid(form)

    def test_func(self):
        Food = self.get_object()
        if self.request.user.is_superuser:
            return True
        # elif self.request.user == Food.added_by:
        elif self.request.user:
            return True
        return redirect("finance:supplies")


class SupplierListView(ListView):
    model = Supplier
    template_name = "finance/payments/food.html"

    context_object_name = "suppliers"
    ordering = ["-created_at"]


def foodlist(request):
    supplies = Food.objects.all().order_by("-id")
    supplies_Fs = FoodFilter(request.GET, queryset=supplies)

    total_amt = 0
    for supply in supplies_Fs.qs:
        total_amt = total_amt + supply.total_amount

    total_add_amount = 0
    for supply in supplies_Fs.qs:
        total_add_amount = total_add_amount + supply.additional_amount

    context = {
        "total_add_amount": total_add_amount,
        "total_amt": total_amt,
        "supplies": supplies,
        "supplies_Fs": supplies_Fs,
    }
    return render(request, "finance/payments/food.html", context)


def food_history_view(request):
    date_today = timezone.now()
    current_year = date_today.year
    current_month = date_today.month
    query = Q()

    selected_month = request.GET.get("month")
    selected_year = request.GET.get("year")
    selected_office_location = request.GET.get("office_location")

    if selected_month and selected_month.isdigit():
        query &= Q(history_date__month=selected_month)
    if selected_year and selected_year.isdigit():
        query &= Q(history_date__year=selected_year)
    if selected_office_location:
        query &= Q(office_location=selected_office_location)

    food_histories = FoodHistory.objects.filter(query).order_by("-history_date")
    total_amount = (
        FoodHistory.objects.filter(query).aggregate(
            total=Sum(F("unit_amt") * F("qty"))
        )["total"]
        or 0
    )

    unique_office_locations = (
        Food.objects.order_by("office_location")
        .values_list("office_location", flat=True)
        .distinct()
    )
    years = list(range(current_year - 5, current_year + 1))
    months = [(i, timezone.datetime(2000, i, 1).strftime("%B")) for i in range(1, 13)]

    context = {
        "food_histories": food_histories,
        "unique_office_locations": unique_office_locations,
        "months": months,
        "years": years,
        "selected_month": selected_month,
        "selected_year": selected_year,
        "total_amount": total_amount,
    }
    return render(request, "finance/payments/foodhistory.html", context)


def food_history_update(request, pk):
    food_histories = get_object_or_404(FoodHistory, pk=pk)
    if request.method == "POST":
        form = FoodHistoryForm(request.POST, instance=food_histories)
        if form.is_valid():
            form.save()
            return redirect("finance:foodhistory")
    else:
        form = FoodHistoryForm(instance=food_histories)
    return render(
        request,
        "finance/payments/foodhistory_update.html",
        {"form": form, "food_histories": food_histories},
    )


@login_required
def clientinflows(request, user=None, *args, **kwargs):
    try:
        client = get_object_or_404(User, username=kwargs.get("username"))
        transactions = DC48_Inflow.objects.filter(sender=client, is_active=True)
        total_members = transactions.count()
        paid_members = transactions.filter(has_paid=True).count()
        total_amt = 0
        total_paid = 0
        for transact in transactions:
            print("clients_category", transact.clients_category)
            total_amt += transact.total_payment
            if transact.has_paid:
                total_paid += transact.total_paid

        pledged = total_amt - total_paid
        amount_ksh = total_amt * rate  # Initialize amount_ksh outside the if block
        context = {
            "message": "Kindly contact adminstrator info@codanalytics.net",
            "transactions": transactions,
            "total_count": total_members,
            "paid_count": paid_members,
            "total_amt": total_amt,
            "amount_ksh": amount_ksh,
            "total_paid": total_paid,
            "pledged": pledged,
            "rate": rate,
            "remaining_days": remaining_days,
            "remaining_seconds ": int(remaining_seconds % 60),
            "remaining_minutes ": int(remaining_minutes % 60),
            "remaining_hours": int(remaining_hours % 24),
        }
        return render(request, "finance/payments/dcinflows.html", context)
    except:
        return render(request, "main/errors/template_error.html", context)


# views.py
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import LoanApplication
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


def MpesaPaymentView(request):
    context = {}

    if request.method == "POST":
        phone_number = request.POST.get("phone_number")

        user_email = (
            request.user.email
        )  # Replace with the actual path to the user's email
        print("user_email: ", user_email)
        otp = generate_and_send_otp(user_email)
        print("otp: ", otp)

        request.session["phone_number"] = phone_number

        request.session["payment_otp"] = otp
        return redirect("finance:otp_confirmation")
    else:
        payment_info = Payment_Information.objects.filter(
            customer_id=request.user.id
        ).first()
        downpayment = payment_info.down_payment
        paypal_charges = calculate_paypal_charges(downpayment)
        request.session["amount"] = downpayment

        reference = f"MPESA-{request.session.get('phone_number')}-{request.session.get('amount')}"
        request.session["reference"] = reference
        context = {
            "payment": payment_info,
            "paypal_charges": paypal_charges,
        }
        return render(request, "finance/payments/mpesa_payment.html", context)


# views.py
def verify_otp(request):
    if request.method == "POST":
        entered_otp = request.POST.get("otp")
        stored_otp = request.session.get("payment_otp")
        phone_number = request.session.get("phone_number")
        amount = request.session.get("amount")
        reference = request.session.get("reference")

        if entered_otp == stored_otp:
            print("_______correct")
            # If OTP is verified, proceed with payment initiation
            payment_data = []
            if not payment_data:
                print("____________________paymrnt_data", payment_data)
                response = initiate_payment(phone_number, amount, reference)
                print(response, "______________Response")
                if ("ResponseCode" in response) and (response["ResponseCode"] == "0"):
                    payment_info = Payment_Information.objects.get(
                        customer_id=request.user.id
                    )
                    Payment_History.objects.create(
                        customer=request.user,
                        payment_fees=payment_info.payment_fees,
                        down_payment=payment_info.down_payment,
                        student_bonus=payment_info.student_bonus,
                        plan=payment_info.plan,
                        # fee_balance=payment_info.fee_balance,
                        payment_method="M-pesa",
                        contract_submitted_date=payment_info.contract_submitted_date,
                        client_signature=payment_info.client_signature,
                        company_rep=payment_info.company_rep,
                        client_date=payment_info.client_date,
                        rep_date=payment_info.rep_date,
                    )
                if response.get("ResponseCode") == "0":
                    messages.success(request, "Payment initiated successfully.")
                    return redirect(
                        "finance:payment_success"
                    )  # Redirect to success page
                else:
                    messages.error(request, "Failed to initiate payment.")
                    return redirect("finance:payment_failed")  # Redirect to failed page
            else:
                messages.error(request, "Payment data not found. Please try again.")
                return redirect("finance:payment_failed")  # Redirect to failed page
        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return redirect("finance:payment_failed")  # Redirect to failed page

    return render(request, "finance/payments/otp_confirmation.html")


def payment_success(request):
    return render(request, "finance/payments/success.html")


def payment_failed(request):
    return render(request, "finance/payments/failed.html")


def get_existing_data():
    existing_assets = BalanceSheetCategory.objects.filter(category_type="Asset")
    existing_long_term_assets = BalanceSheetCategory.objects.filter(
        category_type="Long-term Asset"
    )
    existing_liabilities = BalanceSheetCategory.objects.filter(
        category_type="Liability"
    )
    existing_long_term_liabilities = BalanceSheetCategory.objects.filter(
        category_type="Long-term Liability"
    )

    total_current_assets = existing_assets.aggregate(Sum("amount"))["amount__sum"] or 0
    total_long_term_assets = (
        existing_long_term_assets.aggregate(Sum("amount"))["amount__sum"] or 0
    )
    total_current_liabilities = (
        existing_liabilities.aggregate(Sum("amount"))["amount__sum"] or 0
    )
    total_long_term_liabilities = (
        existing_long_term_liabilities.aggregate(Sum("amount"))["amount__sum"] or 0
    )

    return (
        existing_assets.exists()
        and existing_long_term_assets.exists()
        and existing_liabilities.exists()
        and existing_long_term_liabilities.exists(),
        existing_assets,
        existing_long_term_assets,
        existing_liabilities,
        existing_long_term_liabilities,
        total_current_assets,
        total_long_term_assets,
        total_current_liabilities,
        total_long_term_liabilities,
    )


def financial_statements():
    saved_Revenue = BalanceSheetCategory.objects.filter(category_type="Revenue")
    saved_Expenses = BalanceSheetCategory.objects.filter(category_type="Expenses")
    total_revenue = saved_Revenue.aggregate(Sum("amount"))["amount__sum"] or 0
    total_expenses = saved_Expenses.aggregate(Sum("amount"))["amount__sum"] or 0
    net_income = total_revenue - total_expenses
    return saved_Revenue, saved_Expenses, total_revenue, total_expenses, net_income


def calculate_revenue_and_expenses(request):
    """Calculate revenue and expenses data for the balance sheet view"""
    saved_Revenue, saved_Expenses, total_revenue, total_expenses, net_income = financial_statements()
    
    # This function is called when there's no existing data, so we just return the calculated values
    # The calling function should handle updating the context
    return saved_Revenue, saved_Expenses, total_revenue, total_expenses, net_income


def cashflowstatements():
    saved_inflow_investing = BalanceSheetCategory.objects.filter(
        category_type="Cash Inflows for Investing Activities"
    )
    saved_outflow_investing = BalanceSheetCategory.objects.filter(
        category_type="Cash Outflows for Investing Activities"
    )
    saved_inflow_financing = BalanceSheetCategory.objects.filter(
        category_type="Cash Inflows for Financing Activities"
    )
    saved_outflow_financing = BalanceSheetCategory.objects.filter(
        category_type="Cash Outflows for Financing Activities"
    )
    return (
        saved_inflow_investing,
        saved_outflow_investing,
        saved_inflow_financing,
        saved_outflow_financing,
    )


def openai_balancesheet(request):
    context = {}  # Initialize context variable

    try:
        # Existing data check
        (
            data_exists,
            existing_assets,
            existing_long_term_assets,
            existing_liabilities,
            existing_long_term_liabilities,
            total_current_assets,
            total_long_term_assets,
            total_current_liabilities,
            total_long_term_liabilities,
        ) = get_existing_data()

        # Check if data already exists in the model
        if data_exists:
            # Use existing data
            print("Using existing data")
            context.update(
                {
                    "company_name": "CODA",
                    "assets": existing_assets,
                    "long_term_assets": existing_long_term_assets,
                    "liabilities": existing_liabilities,
                    "long_term_liabilities": existing_long_term_liabilities,
                    "total_current_assets": total_current_assets,
                    "total_long_term_assets": total_long_term_assets,
                    "total_current_liabilities": total_current_liabilities,
                    "total_long_term_liabilities": total_long_term_liabilities,
                    "total_assets": total_current_assets + total_long_term_assets,
                    "total_liabilities": total_current_liabilities
                    + total_long_term_liabilities,
                }
            )
        else:
            # Use default empty data when no existing data is found
            context.update(
                {
                    "assets": [],
                    "long_term_assets": [],
                    "liabilities": [],
                    "long_term_liabilities": [],
                }
            )

    except Exception as e:
        # Handle other exceptions
        print(f"An unexpected error occurred: {e}")

    # Calculate total revenues
    # Get existing revenue and expenses data
    (saved_Revenve, saved_Expanses, total_revenue, total_expenses, net_income) = (
        financial_statements()
    )

    if saved_Revenve.exists() and saved_Expanses.exists():
        context.update(
            {
                "existing_revenue_data": saved_Revenve,
                "existing_expenses_data": saved_Expanses,
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "net_income": net_income,
            }
        )
    else:
        # Calculate revenue and expenses
        saved_Revenue, saved_Expenses, total_revenue, total_expenses, net_income = calculate_revenue_and_expenses(request)
        context.update(
            {
                "existing_revenue_data": saved_Revenue,
                "existing_expenses_data": saved_Expenses,
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "net_income": net_income,
            }
        )

    # Cash flow data
    (
        saved_inflow_investing,
        saved_outflow_investing,
        saved_inflow_financing,
        saved_outflow_financing,
    ) = cashflowstatements()

    # Check if data already exists in the model
    if (
        saved_inflow_investing.exists()
        and saved_outflow_investing.exists()
        and saved_inflow_financing.exists()
        and saved_outflow_financing.exists()
    ):
        # Use the stored data
        context.update(
            {
                "saved_inflow_investing": saved_inflow_investing,
                "saved_outflow_investing": saved_outflow_investing,
                "saved_outflow_financing": saved_outflow_financing,
                "saved_inflow_financing": saved_inflow_financing,
            }
        )
    # Render the template with the 'assets' variable
    return render(request, "finance/reports/openai.html", context)


class StatementsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = BalanceSheetCategory
    # success_url="/management/transaction"
    fields = "__all__"

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("finance:open_statements")

    def test_func(self):
        policy = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user == policy.staff:
            return True
        return False


def delete_bad_entry_in_payment_history(request):
    if request.user and request.user.is_superuser:
        delete_payment_history = Payment_History.objects.filter(customer__is_staff=True)
        for payment in delete_payment_history:
            DeletedPaymentHistory.objects.create(
                customer=payment.customer,
                payment_fees=payment.payment_fees,
                down_payment=payment.down_payment,
                student_bonus=payment.student_bonus,
                fee_balance=payment.fee_balance,
                plan=payment.plan,
                subplan=payment.subplan,
                pricing_plan=payment.pricing_plan,
                payment_method=payment.payment_method,
                contract_submitted_date=payment.contract_submitted_date,
                client_signature=payment.client_signature,
                company_rep=payment.company_rep,
                client_date=payment.client_date,
                rep_date=payment.rep_date,
            )
            payment.delete()

    previous_path = request.META.get("HTTP_REFERER", "")
    if previous_path:
        return redirect(previous_path)
    else:
        return redirect("main:layout")


@login_required
def add_budget_item(request):
    if request.method == "POST":
        form = BudgetForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            instance = form.save(commit=False)
            print(request.user)
            instance.budget_lead = request.user
            instance.save()
            return redirect("/finance/budget/")
    else:
        form = BudgetForm()
    return render(request, "finance/budgets/newbudget.html", {"form": form})


def filter_transactions_by_year_and_month(
    year=None, month=None, department_name=None, company_name="Coda", summary=False
):
    """
    Filters transactions based on the selected year, optionally by month, department, and company.
    Uses `Budget` for summary (`created_at`) and `CodaBudget` for detailed (`start_date`).
    """

    Model = Budget if summary else CodaBudget  # Choose the correct model
    date_field = "start_date__year" if summary else "created_at__year"

    # Default to current year and month if not provided
    current_year = datetime.now().year
    current_month = datetime.now().month

    year = year or current_year
    month = month or current_month

    filters = {date_field: str(year)}

    if month:
        filters[date_field.replace("year", "month")] = str(month)

    if department_name:
        filters["department__name"] = department_name

    # Get company object by name (Default to "Coda")
    try:
        company = Company.objects.get(name=company_name.upper())
        filters["company"] = company  # Use the company object in filtering
    except ObjectDoesNotExist:
        pass  # If the company doesn't exist, ignore the filter

    return Model.objects.filter(**filters).order_by("category")


def budget_projection(request, subtitle="summary"):
    path_list, sub_title, pre_sub_title = path_values(request)
    subtitle = path_list[2]
    departments = Department.objects.all()
    companies = Company.objects.all()

    # Default values to the current year and current month
    current_year = datetime.now().year
    current_month = datetime.now().month
    default_company = "Coda"
    selected_year = current_year
    selected_month = current_month
    selected_company = default_company

    total = 0
    budget_items = []

    if request.method == "POST":
        form = DepartmentFilterForm(
            request.POST, departments=departments, companies=companies
        )
        if form.is_valid():
            department_name = form.cleaned_data.get("name")
            selected_year = form.cleaned_data.get("year", current_year)
            selected_month = form.cleaned_data.get(
                "month", current_month
            )  # Default to current month
            selected_company = form.cleaned_data.get("company", default_company)

            # Retrieve filtered transactions from the correct model
            budget_items = filter_transactions_by_year_and_month(
                selected_year,
                selected_month,
                department_name,
                summary=(subtitle == "summary"),
            )

            total = sum(
                item.amount * item.qty
                for item in budget_items
                if hasattr(item, "amount") and hasattr(item, "qty")
            )
    else:
        form = DepartmentFilterForm(departments=departments, companies=companies)
        budget_items = filter_transactions_by_year_and_month(
            selected_year, selected_month, summary=(subtitle == "summary")
        )
        total = sum(
            item.amount * item.qty
            for item in budget_items
            if hasattr(item, "amount") and hasattr(item, "qty")
        )

    # Extract unique categories
    available_categories = budget_items.values_list(
        "category__name", flat=True
    ).distinct()

    # Prepare context
    context = {
        "form": form,
        "budget_items": budget_items,
        "total": total,
        "available_categories": available_categories,
        "selected_year": selected_year,
        "selected_month": selected_month,
        "selected_company": selected_company,
        "subtitle": subtitle,
    }

    return render(request, "finance/budgets/budget_projection.html", context)


@login_required
def automated_budget_estimation(request, company_slug="coda"):
    """
    Automated budget estimation view using historical transaction data
    """
    try:
        # Get company
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        return redirect("some_error_view")
    
    # Initialize services
    calculation_utils = CalculationUtils()
    filter_utils = FilterUtils()
    budget_service = BudgetEstimationService()
    consolidation_service = BudgetConsolidationService()
    
    # Get departments for filtering
    departments = Department.objects.all()
    selected_department = None
    
    if request.method == "POST":
        department_id = request.POST.get("department_id")
        if department_id:
            selected_department = Department.objects.get(id=department_id)
    
    # Get spending analysis
    spending_analysis = budget_service.analyze_spending_patterns(
        company=company,
        department=selected_department,
        months=3
    )
    
    # Get budget estimates
    budget_estimates = budget_service.estimate_next_month_budget(
        company=company,
        department=selected_department,
        method='average'
    )
    
    # Get variance analysis
    variance_analysis = budget_service.get_budget_variance_analysis(
        company=company,
        department=selected_department
    )
    
    # Get consolidated report
    consolidated_report = consolidation_service.get_unified_budget_report(
        company=company,
        department=selected_department
    )
    
    # Get recommendations
    recommendations = budget_service.get_budget_recommendations(
        company=company,
        department=selected_department
    )
    
    context = {
        "company": company,
        "departments": departments,
        "selected_department": selected_department,
        "spending_analysis": spending_analysis,
        "budget_estimates": budget_estimates,
        "variance_analysis": variance_analysis,
        "consolidated_report": consolidated_report,
        "recommendations": recommendations,
        "calculation_utils": calculation_utils,
        "filter_utils": filter_utils,
    }
    
    return render(request, "finance/budgets/automated_estimation.html", context)


@login_required
def budget_consolidation_dashboard(request, company_slug="coda"):
    """
    Budget consolidation dashboard showing unified view of all budget models
    """
    try:
        # Get company
        company = Company.objects.get(slug=company_slug)
    except Company.DoesNotExist:
        return redirect("some_error_view")
    
    # Initialize services
    consolidation_service = BudgetConsolidationService()
    budget_service = BudgetEstimationService()
    
    # Get departments for filtering
    departments = Department.objects.all()
    selected_department = None
    
    if request.method == "POST":
        department_id = request.POST.get("department_id")
        if department_id:
            selected_department = Department.objects.get(id=department_id)
    
    # Get consolidated view
    consolidated_view = consolidation_service.create_consolidated_view(
        company=company,
        department=selected_department
    )
    
    # Get model statistics
    model_statistics = consolidation_service.get_model_usage_statistics(
        company=company
    )
    
    # Get unified report
    unified_report = consolidation_service.get_unified_budget_report(
        company=company,
        department=selected_department
    )
    
    context = {
        "company": company,
        "departments": departments,
        "selected_department": selected_department,
        "consolidated_view": consolidated_view,
        "model_statistics": model_statistics,
        "unified_report": unified_report,
    }
    
    return render(request, "finance/budgets/consolidation_dashboard.html", context)


class CodaBudgetUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CodaBudget
    success_url = "/finance/budget/detailed/2024/"
    template_name = "main/snippets_templates/generalform.html"
    fields = "__all__"

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def test_func(self):
        if self.request.user:
            return True
        return False


class BudgetSummaryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Budget
    success_url = "/finance/budget_projection/summary/"
    template_name = "main/snippets_templates/generalform.html"
    fields = "__all__"

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def test_func(self):
        if self.request.user:
            return True
        return False


def determine_rejection_reason(loan_app):
    """
    Determine the rejection reason and category for a loan application

    Args:
        loan_app: LoanApplication object

    Returns:
        dict: Rejection reason with category, title, and description
    """
    try:
        from finance.utils import get_standard_rejection_reasons

        # Get standard rejection reasons
        standard_reasons = get_standard_rejection_reasons()

        # Check for specific rejection scenarios
        if loan_app.borrower.category == 2:  # Staff member
            if not loan_app.monthly_income or loan_app.monthly_income < 50:
                return standard_reasons["insufficient_income"]
            elif loan_app.amount_requested > loan_app.staff_cap:
                return standard_reasons["insufficient_income"]

        # Check for missing guarantor (if required)
        if loan_app.amount_requested > 500 and not loan_app.guarantor:
            return standard_reasons["missing_documents"]

        # Check for existing active loan
        existing_loan = (
            LoanApplication.objects.filter(
                borrower=loan_app.borrower, status__in=["approved", "active"]
            )
            .exclude(id=loan_app.id)
            .first()
        )

        if existing_loan:
            return standard_reasons["existing_active_loan"]

        # Default to permanent disqualification if no specific reason found
        return standard_reasons["permanent_disqualification"]

    except Exception as e:
        logger.error(f"Error determining rejection reason: {e}")
        return {
            "category": "unknown",
            "title": "Application rejected",
            "description": "Unable to determine specific rejection reason",
            "is_temporary": False,
        }


@login_required
def recompute_loan_application(request, pk):
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({"success": False, "error": "Forbidden"}, status=403)
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"}, status=405)
    app = get_object_or_404(LoanApplication, pk=pk)
    result = app.recompute_and_decide(decided_by=request.user)
    return JsonResponse(
        {
            "success": True,
            "status": result.get("status"),
            "monthly_income": (
                str(result.get("monthly_income"))
                if result.get("monthly_income") is not None
                else None
            ),
            "cap": str(result.get("cap")) if result.get("cap") is not None else None,
            "reason": result.get("reason"),
        }
    )


def loan_rejection(request):
    """Display loan rejection page with rejection details"""
    # Get rejection details from session or query params
    rejection_reason = request.session.get("loan_rejection_reason", "")
    max_borrowable_amount = request.session.get("loan_max_amount", "")
    monthly_income = request.session.get("loan_monthly_income", "")

    # Clear session data after displaying
    if "loan_rejection_reason" in request.session:
        del request.session["loan_rejection_reason"]
    if "loan_max_amount" in request.session:
        del request.session["loan_max_amount"]
    if "loan_monthly_income" in request.session:
        del request.session["loan_monthly_income"]

    context = {
        "rejection_reason": rejection_reason,
        "max_borrowable_amount": max_borrowable_amount,
        "monthly_income": monthly_income,
    }

    return render(request, "finance/loan_rejection.html", context)


@login_required
def guarantor_dashboard(request):
    """Dashboard for guarantors to view loans they're guaranteeing"""
    # Get all loans where user is guarantor
    guaranteed_loans = (
        LoanApplication.objects.filter(guarantor=request.user)
        .select_related("borrower", "loan_product")
        .order_by("-created_at")
    )

    context = {
        "guaranteed_loans": guaranteed_loans,
        "total_guaranteed": guaranteed_loans.count(),
        "pending_approvals": guaranteed_loans.filter(
            guarantor_approval_status="pending"
        ).count(),
        "approved_loans": guaranteed_loans.filter(
            guarantor_approval_status="approved"
        ).count(),
        "rejected_loans": guaranteed_loans.filter(
            guarantor_approval_status="rejected"
        ).count(),
    }

    return render(request, "finance/guarantor/dashboard.html", context)


@login_required
def get_guarantor_eligibility_scores(request):
    """AJAX endpoint to get guarantor eligibility scores - called when user needs them"""
    # Allow both GET and POST requests for flexibility
    if request.method not in ["GET", "POST"]:
        return JsonResponse({"error": "GET or POST method required"}, status=405)

    try:
        from finance.utils import get_eligible_staff_guarantors

        # Get eligibility scores (this is the heavy computation)
        suggested_guarantors = get_eligible_staff_guarantors(limit=5)

        # Format data for frontend
        guarantor_data = []
        for guarantor in suggested_guarantors:
            guarantor_data.append(
                {
                    "id": guarantor["staff"].id,
                    "first_name": guarantor["staff"].first_name,
                    "last_name": guarantor["staff"].last_name,
                    "email": guarantor["staff"].email,
                    "phone": guarantor["staff"].phone or "",
                    "eligibility_score": guarantor["eligibility_score"],
                    "avg_earnings": float(guarantor["avg_earnings"]),
                    "monthly_earnings": guarantor["monthly_earnings"],
                }
            )

        return JsonResponse({"success": True, "guarantors": guarantor_data})

    except Exception as e:
        logger.error(f"Error fetching guarantor eligibility scores: {e}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def notify_guarantor_available(request, pk):
    """Notify user when staff guarantors become available"""
    if not request.user.is_superuser and not request.user.is_staff:
        return JsonResponse({"success": False, "error": "Forbidden"}, status=403)
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "POST required"}, status=405)

    try:
        app = get_object_or_404(LoanApplication, pk=pk)

        # Check if this is a rejected application that can be reconsidered
        if app.status != "rejected":
            return JsonResponse(
                {"success": False, "error": "Application is not rejected"}, status=400
            )

        # Send notification to user
        try:
            from finance.utils import notify_user_of_guarantor_availability

            success = notify_user_of_guarantor_availability(app.borrower, app.id)

            if success:
                # Update application status to pending_guarantor
                app.status = "pending_guarantor"
                app.save()

                messages.success(
                    request, f"Notification sent to {app.borrower.get_full_name()}"
                )
                return JsonResponse(
                    {"success": True, "message": "Notification sent successfully"}
                )
            else:
                return JsonResponse(
                    {"success": False, "error": "Failed to send notification"},
                    status=500,
                )

        except Exception as e:
            logger.error(f"Error sending guarantor availability notification: {e}")
            return JsonResponse(
                {"success": False, "error": "Failed to send notification"}, status=500
            )

    except Exception as e:
        logger.error(f"Error in notify_guarantor_available: {e}")
        return JsonResponse(
            {"success": False, "error": "Internal server error"}, status=500
        )


# Analytics Dashboard Views


# ... existing code ...


# finance_dashboard function removed - functionality moved to unified dashboard

# Analytics Dashboard Views
@login_required
def analytics_dashboard(request):
    """Main analytics dashboard view"""
    try:
        # Get analytics services
        services = get_all_analytics_services()
        dashboard_service = services["dashboard"]

        # Get dashboard data
        dashboard_data = dashboard_service.get_dashboard_data()

        context = {
            "dashboard_data": dashboard_data,
            "page_title": "Analytics Dashboard",
            "active_tab": "analytics",
        }

        return render(request, "finance/analytics_dashboard.html", context)

    except Exception as e:
        context = {
            "error": str(e),
            "page_title": "Analytics Dashboard - Error",
            "active_tab": "analytics",
        }
        return render(request, "finance/analytics_dashboard.html", context)


@login_required
def loan_performance_analytics(request):
    """Loan performance analytics view"""
    try:
        services = get_all_analytics_services()
        loan_analytics = services["loan_analytics"]

        # Get performance data
        performance_data = loan_analytics.get_performance_dashboard_data()

        context = {
            "performance_data": performance_data,
            "page_title": "Loan Performance Analytics",
            "active_tab": "loan_analytics",
        }

        return render(request, "finance/loan_performance_analytics.html", context)

    except Exception as e:
        context = {
            "error": str(e),
            "page_title": "Loan Performance Analytics - Error",
            "active_tab": "loan_analytics",
        }
        return render(request, "finance/loan_performance_analytics.html", context)


@login_required
def kcc_optimization_analytics(request):
    """KCC optimization analytics view"""
    try:
        services = get_all_analytics_services()
        kcc_analytics = services["kcc_analytics"]

        # Get KCC optimization data
        kcc_data = kcc_analytics.generate_kcc_optimization_report()

        context = {
            "kcc_data": kcc_data,
            "page_title": "KCC Optimization Analytics",
            "active_tab": "kcc_analytics",
        }

        return render(request, "finance/kcc_optimization_analytics.html", context)

    except Exception as e:
        context = {
            "error": str(e),
            "page_title": "KCC Optimization Analytics - Error",
            "active_tab": "kcc_analytics",
        }
        return render(request, "finance/kcc_optimization_analytics.html", context)


@login_required
def analytics_export(request):
    """Export analytics data to CSV/Excel"""
    try:
        export_type = request.GET.get("type", "csv")
        date_range = request.GET.get("date_range", "12_months")

        services = get_all_analytics_services()
        dashboard_service = services["dashboard"]

        # Get dashboard data for export
        dashboard_data = dashboard_service.get_dashboard_data()

        if export_type.lower() == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = (
                f'attachment; filename="analytics_export_{date_range}.csv"'
            )

            # Create CSV writer
            writer = csv.writer(response)

            # Write headers
            writer.writerow(["Analytics Export", date_range])
            writer.writerow([])

            # Write overview metrics
            writer.writerow(["Overview Metrics"])
            overview = dashboard_data.get("overview_metrics", {})
            for key, value in overview.items():
                writer.writerow([key.replace("_", " ").title(), value])

            writer.writerow([])

            # Write performance charts data
            writer.writerow(["Performance Charts Data"])
            charts = dashboard_data.get("performance_charts", {})
            for chart_name, chart_data in charts.items():
                writer.writerow([chart_name.replace("_", " ").title()])
                if isinstance(chart_data, dict) and "labels" in chart_data:
                    for i, label in enumerate(chart_data["labels"]):
                        data_value = (
                            chart_data.get("data", [])[i]
                            if i < len(chart_data.get("data", []))
                            else ""
                        )
                        writer.writerow([label, data_value])
                writer.writerow([])

            return response

        else:
            # For now, default to CSV
            return analytics_export(request)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# API Views for AJAX calls
@csrf_exempt
@require_http_methods(["POST"])
def analytics_api(request):
    """API endpoint for analytics data"""
    try:
        data = json.loads(request.body)
        action = data.get("action")
        params = data.get("params", {})

        services = get_all_analytics_services()

        if action == "get_dashboard_data":
            dashboard_service = services["dashboard"]
            result = dashboard_service.get_dashboard_data(**params)

        elif action == "get_loan_performance":
            loan_analytics = services["loan_analytics"]
            result = loan_analytics.get_performance_dashboard_data(**params)

        elif action == "get_kcc_optimization":
            kcc_analytics = services["kcc_analytics"]
            result = kcc_analytics.generate_kcc_optimization_report(**params)

        elif action == "export_data":
            dashboard_service = services["dashboard"]
            result = dashboard_service.export_dashboard_data(**params)

        else:
            return JsonResponse({"error": "Invalid action"}, status=400)

        return JsonResponse({"success": True, "data": result})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


# ... existing code ...


class FoodListView(FilteredListViewMixin, ListView):
    """Consolidated food supplies list view using generic mixin"""

    model = Food
    template_name = "finance/payments/food.html"
    context_object_name = "supplies"
    order_by = "-id"

    def get_queryset(self):
        """Apply food-specific filtering"""
        queryset = super().get_queryset()
        return queryset.order_by(self.order_by)

    def get_context_data(self, **kwargs):
        """Add food-specific context data with aggregations"""
        context = super().get_context_data(**kwargs)

        # Apply filter
        supplies_filter = FoodFilter(self.request.GET, queryset=self.get_queryset())
        context["supplies_Fs"] = supplies_filter

        # Calculate totals
        total_amt = sum(supply.total_amount for supply in supplies_filter.qs)
        total_add_amount = sum(
            supply.additional_amount for supply in supplies_filter.qs
        )

        context.update(
            {
                "total_add_amount": total_add_amount,
                "total_amt": total_amt,
                "supplies": self.get_queryset(),
            }
        )

        return context
