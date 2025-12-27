import os
import calendar
import requests
from datetime import datetime
from decimal import Decimal
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Sum


# ===================== Category and Sub-Category =====================
def category_subcategory(user_categories):
    """
    Extract the category and sub-category from user categories.
    """
    category, sub_category = None, None
    for cat in user_categories:
        category = cat.category
        sub_category = cat.sub_category
    return category, sub_category


# ===================== Default Fee Check =====================
def check_default_fee(Default_Payment_Fees, username):
    """
    Check if a default fee exists for the given user.
    If not, create a default payment fee.
    """
    try:
        default_fee = get_object_or_404(Default_Payment_Fees, user=username)
    except:
        default_payment_fees = Default_Payment_Fees(
            job_down_payment_per_month=500,
            job_plan_hours_per_month=40,
            student_down_payment_per_month=500,
            student_bonus_payment_per_month=100,
        )
        default_payment_fees.save()
        default_fee = Default_Payment_Fees.objects.get(id=1)
    return default_fee


# ===================== Exchange Rate =====================
def get_exchange_rate(base, target):
    """
    Fetch exchange rate between base and target currency.
    Fallback to a hardcoded value if the API fails.
    """
    exchange_api_key = '19312eb3c8014755b32a7fdad5a7b1cc'
    url = f"https://openexchangerates.org/api/latest.json?app_id={exchange_api_key}&base={base}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        rate = data["rates"].get(target, 139.00)  # Fallback to 139.00 if target not found
    except requests.RequestException as e:
        print(f"Error fetching exchange rate: {e}")
        rate = 139.00  # Fallback rate
    return round(Decimal(rate), 2)


# ===================== Compute Amount =====================
def compute_amt(VisaService, transactions, rate, user_categories):
    """
    Compute the total amount, balance, and receipt URL for a given user and service.
    """
    category, sub_category = category_subcategory(user_categories)
    total_amt, total_paid, receipt_url = Decimal(0), Decimal(0), None
    reg_fee = Decimal("19.99")
    try:
        service = VisaService.objects.filter(sub_category=sub_category).first()
        total_price = (service.price + reg_fee) * float(rate) if service else reg_fee
        total_price = round(Decimal(total_price), 2)
    except AttributeError:  # Handle if `VisaService` or `sub_category` is invalid
        service, total_price = None, reg_fee

    for transact in transactions:
        total_amt += transact.total_payment
        total_paid += transact.total_paid if transact.has_paid else Decimal(0)
        receipt_url = transact.receipturl or receipt_url

    if not receipt_url:
        return redirect("main:404error")

    balance = round(total_price - total_amt, 2)
    return total_price, total_amt, balance, receipt_url


# ===================== Default Payments =====================
def DYCDefaultPayments():
    """
    Provide default payment information for various user types.
    """
    context_dict = {
        "student": {"total_amount": 5000, "down_payment": 500, "early_registration_bonus": 100},
        "business": {"total_amount": 10000, "down_payment": 500, "early_registration_bonus": 100},
        "greencard": {"total_amount": 20000, "down_payment": 500, "early_registration_bonus": 100},
    }
    for usertype, values in context_dict.items():
        if usertype == "student":
            return values["total_amount"], values["down_payment"], values["early_registration_bonus"]
    return 0, 0, 0  # Fallback values


# ===================== Budget Months and Years =====================
def get_budget_periods():
    """
    Generate the previous, current, and next month with names and years.
    """
    today = datetime.now()
    budget_months = [
        {"month_num": (today.month - 1) % 12 or 12, "month_name": calendar.month_name[(today.month - 1) % 12 or 12]},
        {"month_num": today.month, "month_name": calendar.month_name[today.month]},
        {"month_num": (today.month + 1) % 12 or 12, "month_name": calendar.month_name[(today.month + 1) % 12 or 12]},
    ]
    budget_years = [
        {"budget_year": str(today.year - 1)},
        {"budget_year": str(today.year)},
        {"budget_year": str(today.year + 1)},
    ]
    return budget_months, budget_years
