import os
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from datetime import date

import requests
from accounts.choices import CategoryChoices
from coda_project import settings
from finance.utils import DYCDefaultPayments


from django.contrib.auth.decorators import login_required

# def get_default_sender():
#     # Custom logic to determine the default sender
#     return User.objects.get(username="default_sender")

@login_required
def user_categories(user,UserCategory):
    # get the current logged in user
    # user = request.user

    # filter UserCategory objects by the current user
    user_categories = UserCategory.objects.filter(user=user)

    # create an empty dictionary to store the category and subcategory names
    categories = {}

    # iterate over the user_categories queryset and populate the categories dictionary
    for category in user_categories:
        category_name = UserCategory.Category(category.category).name
        subcategory_name = UserCategory.SubCategory(category.sub_category).name if category.sub_category else ""
        categories[category_name] = subcategory_name

    # render the categories in a template or return a JSON response
    return categories

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
    # contract_data["city"] = request.POST.get("city")
    # contract_data["state"] = request.POST.get("state")
    # contract_data["country"] = request.POST.get("country")
    # contract_data["resume_file"] = request.POST.get("resume_file")
    today = date.today()
    contract_date = today.strftime("%d %B, %Y")
    return contract_data,contract_date

def compute_default_fee(category, default_amounts,Default_Payment_Fees):
    if default_amounts:
        default_fee = default_amounts.first()
    else:
        if category == "4" : #and subcategory == "1":
            default_fee = Default_Payment_Fees.objects.create(
                job_down_payment_per_month=1000,
                job_plan_hours_per_month=40,
                student_down_payment_per_month=500,
                student_bonus_payment_per_month=100,
            )
        else:
            default_fee = Default_Payment_Fees.objects.create(
                job_down_payment_per_month=1000,
                job_plan_hours_per_month=40,
                student_down_payment_per_month=500,
                student_bonus_payment_per_month=100,
            )
    return default_fee

# ============================FDYC===========================================
def dyc_compute_default_fee(category,subcategory,dyc_default_amounts, Default_Payment_Fees):
    if dyc_default_amounts:
        dyc_default_fee = dyc_default_amounts.first()
    else:
        # if category == "4" and subcategory == "7":
        #     default_fee = Default_Payment_Fees.objects.create(
        #         job_down_payment_per_month=1000,
        #         job_plan_hours_per_month=40,
        #         student_down_payment_per_month=500,
        #         student_bonus_payment_per_month=100,
        #     )
        # else:
        default_fee = Default_Payment_Fees.objects.create(
            job_down_payment_per_month=1000,
            job_plan_hours_per_month=40,
            student_down_payment_per_month=500,
            student_bonus_payment_per_month=100,
        )
    return default_fee

CATEGORY_FEES = {
    CategoryChoices.ORDINARY_MEMBER: 0.0,
    CategoryChoices.ACTIVE_MEMBER: 1000.0,
    CategoryChoices.EXECUTIVE_MEMBER: 10000.0,
    CategoryChoices.FBO_ORDINARY: 0.0,
    CategoryChoices.ACTIVE_ORGANIZATION: 10000.0,
    CategoryChoices.ROYAL_ORGANIZATION: 20000.0,
}

def convert_kes_to_usd(amount_kes):
    """
    Converts KES to USD using an external API or a predefined rate.
    """
    try:
        # Use an exchange rate API (e.g., exchangerate.host)
        response = requests.get("https://api.exchangerate.host/latest?base=KES&symbols=USD")
        response.raise_for_status()  # Raise exception for HTTP errors
        rate = response.json()["rates"]["USD"]
    except Exception as e:
        # Fallback to a predefined rate if API fails
        print(f"Error fetching exchange rate: {e}")
        rate = 0.0077  # Example: 1 KES = 0.0088 USD

    # Convert and return the amount
    return round(amount_kes * rate, 2)
def get_exchange_rate(base, target):
    """
    Fetches the exchange rate between base and target currencies using OpenExchangeRates API.

    Args:
        base (str): Base currency code (e.g., 'USD').
        target (str): Target currency code (e.g., 'KES').

    Returns:
        float: Exchange rate between base and target currencies.
    """
    exchange_api_key = '19312eb3c8014755b32a7fdad5a7b1cc'  # API key from environment variables
    
    try:
        # OpenExchangeRates endpoint
        url = f'https://openexchangerates.org/api/latest.json?app_id={exchange_api_key}'
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        
        data = response.json()
        
        # Extract rates
        rates = data.get('rates', {})
        
        # Calculate rate relative to the base currency
        if base == 'USD':
            rate = rates.get(target)
        else:
            rate = rates.get(target) / rates.get(base)
        
        if rate is None:
            raise ValueError("Target or base currency not found in API response.")
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        # Fallback rate
        rate = 139.00  # Default fallback exchange rate
    
    return rate
# ================================USERS========================================

from django.core.mail import EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.core.mail.backends.smtp import EmailBackend
def send_verification_email(user,password=None):
    """
    Sends a verification email to the user with the verification URL using the info email configuration.
    """
    verification_token = user.verification_token
   
    verification_url = f"https://dc48k-19fc8ecbc388.herokuapp.com{reverse('accounts:verify-email',  kwargs={'token': str(verification_token)})}"
    print(verification_url)
    subject = "Email Verification"
    html_message = render_to_string('accounts/verification_email.html', {
        'user': user,
        'verification_url': verification_url,
        'password': password,
    })
    print("Email message rendered.")

    try:
        # Create an email backend using the EMAIL_INFO configuration
        email_backend = EmailBackend(
            host=settings.EMAIL_INFO['HOST'],
            port=settings.EMAIL_INFO['PORT'],
            username=settings.EMAIL_INFO['USER'],
            password=settings.EMAIL_INFO['PASS'],
            use_tls=settings.EMAIL_INFO['USE_TLS'] == 'True',
            use_ssl=settings.EMAIL_INFO['USE_SSL'] == 'True',
        )
        
        # Explicitly open the connection
        email_backend.open()
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=html_message,  # This will be used as plain text fallback
            from_email=settings.EMAIL_INFO['USER'],
            to=[user.email],
            connection=email_backend
        )
        email.attach_alternative(html_message, "text/html")  # Attach the HTML version
        
        # Send the email
        email.send()
        print(f"Verification email sent to {user.email}.")

        # Close the connection after sending the email
        email_backend.close()

    except Exception as e:
        print(f"An error occurred while sending the email: {e}")