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
            getattr(user, "profile", {}).get("section"), "application:interview"
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
        Q(is_staff=True), Q(is_active=True)
    ).order_by("-date_joined")

    # former_employees = CustomerUser.objects.filter(
    #                                          Q(is_staff=True),Q(is_active=True),Q(sub_category=5)
    #                                       ).order_by("-date_joined")

    employees_categories_list = CustomerUser.objects.values_list(
        "sub_category", flat=True
    ).distinct()

    # employees_categories = [subcat for subcat in employees_categories_list if subcat in (1,2,3)]
    # employees_categories = [subcat for subcat in employees_categories_list]
    employees_categories = [
        subcat
        for subcat in employees_categories_list
        if subcat in (0, 1, 2, 3, 4, 5, 6)
    ]
    employee_subcategories = list(set(employees_categories))
    return (employee_subcategories, active_employees)


# ================================USERS========================================
def get_clients_time(current_info, history_info, trackers):
    # Payment Infor
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
    return plantime, history_time, added_time, Usedtime, delta, num


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
    response = requests.get(f"{BASE_API_URL}/validate", params=params)
    return response.json() if response.status_code == 200 else None


from django.core.mail import EmailMultiAlternatives

# from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site


def send_verification_email(request, user, password=None):
    """
    Sends a verification email to the user with the verification URL using the info email configuration.
    """
    # current_site = Site.objects.get_current()
    # domain = current_site.domain
    site = get_current_site(request)
    domain = site.domain
    verification_token = user.verification_token
    # verification_url = request.build_absolute_uri(
    #     reverse('accounts:verify-email', kwargs={'token': str(verification_token)})
    # )

    # verification_url = f"https://{domain}{reverse('accounts:verify-email',  kwargs={'token': str(verification_token)})}"
    verification_url = request.build_absolute_uri(
        reverse("accounts:verify-email", kwargs={"token": str(verification_token)})
    )

    logger.info(f"Verification URL: {verification_url}")

    subject = "Email Verification"
    html_message = render_to_string(
        "accounts/verification_email.html",
        {
            "user": user,
            "verification_url": verification_url,
            "password": password,
        },
    )
    logger.info("Email message rendered.")

    try:
        # Create an email backend using the EMAIL_INFO configuration
        email_backend = EmailBackend(
            host=settings.EMAIL_INFO["HOST"],
            port=settings.EMAIL_INFO["PORT"],
            username=settings.EMAIL_INFO["USER"],
            password=settings.EMAIL_INFO["PASS"],
            use_tls=settings.EMAIL_INFO["USE_TLS"],
            use_ssl=settings.EMAIL_INFO["USE_SSL"],
        )
        logger.info("Opening email backend connection")
        # Explicitly open the connection
        email_backend.open()
        logger.info("Email backend connection opened")

        email = EmailMultiAlternatives(
            subject=subject,
            body=html_message,  # This will be used as plain text fallback
            from_email=settings.EMAIL_INFO["USER"],
            to=[user.email],
            connection=email_backend,
        )
        email.attach_alternative(html_message, "text/html")  # Attach the HTML version

        # Send the email
        email.send()
        logger.info(f"Verification email sent to {user.email}.")

        # Close the connection after sending the email
        email_backend.close()

    except Exception as e:
        logger.error(f"An error occurred while sending the email: {e}")


def send_email_to_applicant(instance):

    subject = "Update on Your Application Progress"
    html_message = render_to_string(
        "accounts/verification_applicant.html",
        {
            "user": instance,
        },
    )
    print("Email message rendered.job applicant")

    try:
        # Create an email backend using the EMAIL_INFO configuration
        email_backend = EmailBackend(
            host=settings.EMAIL_INFO["HOST"],
            port=settings.EMAIL_INFO["PORT"],
            username=settings.EMAIL_INFO["USER"],
            password=settings.EMAIL_INFO["PASS"],
            use_tls=settings.EMAIL_INFO["USE_TLS"] == "True",
            use_ssl=settings.EMAIL_INFO["USE_SSL"] == "True",
        )

        # Explicitly open the connection
        email_backend.open()

        email = EmailMultiAlternatives(
            subject=subject,
            body=html_message,  # This will be used as plain text fallback
            from_email=settings.EMAIL_INFO["USER"],
            to=[instance.email],
            connection=email_backend,
        )
        email.attach_alternative(html_message, "text/html")  # Attach the HTML version

        # Send the email
        email.send()
        print(f"Email to aplicant {instance.email}.")

        # Close the connection after sending the email
        email_backend.close()

    except Exception as e:
        print(f"An error occurred while sending the email: {e}")


# Zero Bounce View
def validate_emails_view(request):
    active_emails = []
    users = CustomerUser.objects.all()
    paginator = Paginator(users, 10)  # Process 20 users at a time to avoid timeouts

    for page_number in paginator.page_range:
        page = paginator.page(page_number)
        try:
            for user in page.object_list:
                email = user.email
                print(f"Validating email: {email}")  # Print the email being validated

                validation_result = validate_email(email)
                print(
                    f"Validation result for {email}: {validation_result}"
                )  # Print the result from ZeroBounce API

                if validation_result is not None:
                    # Check if 'status' key exists in the response
                    if "status" in validation_result:
                        if validation_result["status"] == "valid":
                            active_emails.append(email)
                            user.is_active = True  # Set user account as active
                            print(
                                f"Email {email} is valid and account is set to active."
                            )  # Print confirmation if email is valid
                        else:
                            user.is_active = False  # Set user account as inactive
                            print(
                                f"Email {email} is not valid and account is set to inactive."
                            )  # Print if email is not valid
                    else:
                        messages.warning(
                            request,
                            f"No 'status' key found in the response for {email}.",
                        )
                        print(
                            f"No 'status' key found in the response for {email}."
                        )  # Print warning if 'status' key is missing
                else:
                    # Set user account as inactive if validation fails
                    messages.error(
                        request,
                        f"Failed to validate {email}. API did not return a valid response.",
                    )
                    print(
                        f"Failed to validate {email}. API did not return a valid response."
                    )  # Print error if validation fails

                user.save()  # Save the updated user status
            transaction.commit()  # Commit the transaction after processing the batch
            time.sleep(1)  # Sleep for a second to avoid hitting API rate limits
        except Exception as e:
            messages.error(request, f"Error processing batch {page_number}: {e}")
            print(
                f"Error processing batch {page_number}: {e}"
            )  # Print the error and continue

    # Define the CSV file path
    csv_file_path = "active_emails.csv"

    # Write the active emails to a CSV file
    with open(csv_file_path, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Email"])
        for email in active_emails:
            writer.writerow([email])

    # Add a success message
    messages.success(
        request,
        f"Successfully generated {csv_file_path} with {len(active_emails)} active emails and updated user accounts.",
    )
    print(
        f"Successfully generated {csv_file_path} with {len(active_emails)} active emails and updated user accounts."
    )  # Print success message

    # Render the response page
    # return render(request, 'validate_emails.html')


def calculate_login_bonus(
    user,
    selected_month=None,
    selected_year=None,
    threshold=Decimal(20.00),
    hourly_rate=Decimal(5),
):
    """
    Calculate login bonus based on valid login hours and identify invalid entries.
    Parameters:
    - user: User object
    - selected_month: Month to calculate login hours (default: current month)
    - selected_year: Year to calculate login hours (default: current year)
    - threshold: Minimum login hours to qualify for bonus (default: 40 hours)
    - hourly_rate: Bonus amount per login hour after reaching the threshold (default: $1.5)
    Returns:
    - total_login_hours: Decimal
    - login_bonus: Decimal
    - invalid_entries: List of dictionaries containing invalid days and their hours
    """
    from .models import LoginHistory  # Local import to avoid circular dependency

    # Default to last month and year if not provided
    current_date = datetime.now()
    if selected_month is None or selected_year is None:
        selected_month = current_date.month
        selected_year = current_date.year
        # if current_date.month == 1:
        #     selected_month = 12  # Previous month is December
        #     selected_year = current_date.year - 1  # Adjust year
        # else:
        #     selected_month = current_date.month - 1  # Previous month
        #     selected_year = current_date.year  # Same year

    # Fetch login history for the given month and year
    login_history = LoginHistory.objects.filter(
        user=user,
        login_time__isnull=False,
        logout_time__isnull=False,
        login_time__month=selected_month,
        login_time__year=selected_year,
    ).annotate(
        total_duration=ExpressionWrapper(
            F("logout_time") - F("login_time"), output_field=fields.DurationField()
        )
    )
    total_login_hours = Decimal(0)
    invalid_entries = []  # Collect invalid days

    for entry in login_history:
        if entry.total_duration:
            total_seconds = entry.total_duration.total_seconds()
            total_hours = Decimal(total_seconds / 3600).quantize(Decimal("0.01"))
            day = entry.login_time.date() if entry.login_time else "Unknown Day"

            # print(f"Entry: {day}, Total Hours: {total_hours}")

            # Validate hours: >1 and <12
            if Decimal(1.0) <= total_hours <= Decimal(12.0):
                # print(f"Valid Hours: {total_hours}")
                total_login_hours += total_hours
            else:
                invalid_entries.append({"day": day, "logged_hours": total_hours})

    # Calculate bonus based on threshold and hourly rate
    login_bonus = Decimal(0)
    if total_login_hours >= threshold:
        login_bonus = total_login_hours * hourly_rate

    # print(f"Final Total Login Hours: {total_login_hours}, Login Bonus: {login_bonus}")
    return total_login_hours, login_bonus, invalid_entries
