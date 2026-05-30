def calculate_login_bonus(*args, **kwargs):
    """
    Placeholder for login bonus calculation logic.
    Returns 0 by default. Update with real logic as needed.
    """
    return 0
import requests
import csv
import logging
from pyexpat.errors import messages
import time
from django.db.models import Sum, F, Q, ExpressionWrapper, fields
from datetime import date, datetime
from decimal import Decimal
from django.db import transaction
from django.urls import reverse
from django.template.loader import render_to_string
from accounts.models import CustomerUser
from django.core.paginator import Paginator
from coda_project import settings
from django.conf import settings
from django.core.mail.backends.smtp import EmailBackend

logger = logging.getLogger(__name__)

"""
Utility functions for CustomerUser model
Computed user status functions to replace redundant boolean fields
"""


def get_job_applicant_redirect(user):
    """Determines the redirect URL for Job Applicants based on their profile section."""
    try:
        section_redirects = {
            "A": "application:section_a",
            "B": "application:section_b",
            "C": "application:policies",
        }

        return section_redirects.get(
            getattr(user, "profile", {}).get("section"),
            "application:interview",
        )

    except Exception as e:
        logger.error(f"Error in get_job_applicant_redirect: {str(e)}")
        return "application:interview"  # Default fallback


def agreement_data(request):
    contract_data = {}

    contract_data["first_name"] = request.POST.get("first_name")
    contract_data["last_name"] = request.POST.get("last_name")
    contract_data["address"] = request.POST.get("address")
    contract_data["category"] = request.POST.get("category")
    contract_data["sub_category"] = request.POST.get("sub_category")
    contract_data["username"] = request.POST.get("username")
    contract_data["password1"] = request.POST.get("password1")
    contract_data["password2"] = request.POST.get("password2")
    contract_data["email"] = request.POST.get("email")
    contract_data["phone"] = request.POST.get("phone")
    contract_data["gender"] = request.POST.get("gender")
    contract_data["city"] = request.POST.get("city")
    contract_data["state"] = request.POST.get("state")
    contract_data["country"] = request.POST.get("country")
    contract_data["resume_file"] = request.POST.get("resume_file")

    today = date.today()
    contract_date = today.strftime("%d %B, %Y")

    return contract_data, contract_date


def compute_default_fee(category, default_amounts, Default_Payment_Fees):
    if default_amounts:
        default_fee = default_amounts.first()
    else:
        default_fee = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=1000,
            job_plan_hours_per_month=40,
            student_down_payment_per_month=500,
            student_bonus_payment_per_month=100,
        )

    return default_fee


# ================================USERS========================================
def employees():
    active_employees = CustomerUser.objects.filter(
        Q(is_staff=True),
        Q(is_active=True),
    ).order_by("-date_joined")

    # former_employees = CustomerUser.objects.filter(
    #     Q(is_staff=True),
    #     Q(is_active=True),
    #     Q(sub_category=5)
    # ).order_by("-date_joined")

    employees_categories_list = CustomerUser.objects.values_list(
        "sub_category",
        flat=True,
    ).distinct()

    employees_categories = [
        subcat
        for subcat in employees_categories_list
        if subcat in (0, 1, 2, 3, 4, 5, 6)
    ]

    employee_subcategories = list(set(employees_categories))

    return employee_subcategories, active_employees


# ================================USERS========================================
def get_clients_time(current_info, history_info, trackers):
    # Payment Info
    payment_latest_record = current_info
    first_history_record = history_info

    history_time = first_history_record.plan if first_history_record else 0
    added_time = payment_latest_record.plan if payment_latest_record else 0

    # Examining Tracker
    num = trackers.count()

    Used = trackers.aggregate(Used_Time=Sum("duration"))
    Usedtime = Used.get("Used_Time") if Used.get("Used_Time") else 0

    plantime = history_time + added_time

    try:
        delta = round(plantime - Usedtime)
    except (TypeError, AttributeError):
        delta = 0

    return (
        plantime,
        history_time,
        added_time,
        Usedtime,
        delta,
        num,
    )


JOB_SUPPORT_CATEGORIES = [
    "Job_Support",
    "job_support",
    "jobsupport",
    "Jobsupport",
    "JobSupport",
    "Job Support",
    "Job support",
    "job support",
]

BASE_API_URL = "https://api.zerobounce.net/v2"


def validate_email(email, ip_address=""):
    params = {
        "api_key": settings.ZEROBOUNCE_API_KEY,
        "email": email,
        "ip_address": ip_address,
    }

    response = requests.get(
        f"{BASE_API_URL}/validate",
        params=params,
    )

    return response.json() if response.status_code == 200 else None


from django.core.mail import EmailMultiAlternatives, send_mail
from django.core.mail.backends.console import (
    EmailBackend as ConsoleBackend,
)
from django.core.mail.backends.locmem import (
    EmailBackend as LocMemBackend,
)

# from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site


def _build_verification_url(user, request=None, site_url=None):
    """
    Build verification URL with fallback if request is None.

    Args:
        user: The user object with verification_token
        request: Optional HTTP request object
        site_url: Optional fallback site URL

    Returns:
        The verification URL as a string
    """

    verification_token = user.verification_token

    if request:
        try:
            verification_url = request.build_absolute_uri(
                reverse(
                    "accounts:verify-email",
                    kwargs={"token": str(verification_token)},
                )
            )

            logger.info(
                f"Built verification URL from request: {verification_url}"
            )

            return verification_url

        except Exception as e:
            logger.warning(
                f"Failed to build URL from request: {e}, "
                "falling back to site_url"
            )

    # Fallback: use site_url or construct from settings
    if site_url:
        verification_url = (
            f"{site_url}"
            f"{reverse('accounts:verify-email', kwargs={'token': str(verification_token)})}"
        )
    else:
        site_url = getattr(settings, "SITE_URL", None)

        if not site_url:
            try:
                site = get_current_site(None)
                site_url = f"https://{site.domain}"

            except Exception as e:
                logger.warning(f"Could not determine site URL: {e}")
                site_url = "https://localhost:8000"

        verification_url = (
            f"{site_url}"
            f"{reverse('accounts:verify-email', kwargs={'token': str(verification_token)})}"
        )

    logger.info(f"Built verification URL (fallback): {verification_url}")

    return verification_url


def _validate_smtp_config():
    """
    Validate SMTP configuration and return backend configuration or fallback.

    Returns:
        tuple: (is_valid, config_dict_or_fallback_type)
    """

    try:
        required_fields = ["USER", "PASS", "HOST", "PORT"]

        missing_fields = [
            f
            for f in required_fields
            if not settings.EMAIL_INFO.get(f)
        ]

        if missing_fields:
            logger.warning(
                f"Missing EMAIL_INFO fields: {missing_fields}. "
                "Using console backend for testing."
            )

            return False, "console"

        # Try to connect to SMTP server
        backend = EmailBackend(
            host=settings.EMAIL_INFO["HOST"],
            port=settings.EMAIL_INFO["PORT"],
            username=settings.EMAIL_INFO["USER"],
            password=settings.EMAIL_INFO["PASS"],
            use_tls=settings.EMAIL_INFO.get("USE_TLS", False),
            use_ssl=settings.EMAIL_INFO.get("USE_SSL", False),
        )

        backend.open()
        backend.close()

        logger.info("SMTP configuration validated successfully")

        return True, None

    except Exception as e:
        logger.warning(
            f"SMTP validation failed: {e}. "
            "Will use console backend for testing."
        )

        return False, "console"


def send_verification_email(
    request=None,
    user=None,
    password=None,
    site_url=None,
):
    """
    Sends a verification email to the user with the verification URL.

    Handles multiple scenarios:
    - Called from view with request object
    - Called from signal with request=None
    - SMTP failure fallback

    Args:
        request: Optional HTTP request object
        user: The user object
        password: Optional temporary password
        site_url: Optional fallback site URL

    Returns:
        bool: True if email was sent successfully
    """

    if not user or not user.verification_token:
        logger.error(
            "send_verification_email called without user "
            "or verification_token"
        )
        return False

    try:
        # Build the verification URL
        verification_url = _build_verification_url(
            user,
            request,
            site_url,
        )

        logger.info(
            f"Verification URL built: {verification_url}"
        )

        # Render email template
        subject = "Email Verification - CODA"

        html_message = render_to_string(
            "accounts/verification_email.html",
            {
                "user": user,
                "verification_url": verification_url,
                "password": password,
            },
        )

        logger.info(
            f"Email template rendered for user {user.email}"
        )

        # Validate SMTP and get appropriate backend
        smtp_valid, fallback_type = _validate_smtp_config()

        if smtp_valid:
            logger.info(
                f"Sending verification email via SMTP "
                f"to {user.email}"
            )

            email_backend = EmailBackend(
                host=settings.EMAIL_INFO["HOST"],
                port=settings.EMAIL_INFO["PORT"],
                username=settings.EMAIL_INFO["USER"],
                password=settings.EMAIL_INFO["PASS"],
                use_tls=settings.EMAIL_INFO.get("USE_TLS", False),
                use_ssl=settings.EMAIL_INFO.get("USE_SSL", False),
            )

            email_backend.open()

            email = EmailMultiAlternatives(
                subject=subject,
                body=html_message,
                from_email=settings.EMAIL_INFO["USER"],
                to=[user.email],
                connection=email_backend,
            )

            email.attach_alternative(
                html_message,
                "text/html",
            )

            email.send()
            email_backend.close()

            logger.info(
                f"Verification email successfully sent "
                f"to {user.email}"
            )

        else:
            logger.warning(
                f"Using {fallback_type} backend "
                "as fallback for testing"
            )

            if fallback_type == "console":
                backend = ConsoleBackend()
            else:
                backend = LocMemBackend()

            email = EmailMultiAlternatives(
                subject=subject,
                body=html_message,
                from_email=getattr(
                    settings,
                    "DEFAULT_FROM_EMAIL",
                    "noreply@coda.local",
                ),
                to=[user.email],
                connection=backend,
            )

            email.attach_alternative(
                html_message,
                "text/html",
            )

            email.send()

            logger.info(
                f"Verification email sent via "
                f"{fallback_type} backend to {user.email}"
            )

        return True

    except Exception as e:
        logger.error(
            f"Failed to send verification email to "
            f"{user.email if user else 'unknown'}: {str(e)}",
            exc_info=True,
        )

        return False