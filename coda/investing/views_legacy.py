# Standard Library Imports
import os
import time
import json
import ast
from datetime import datetime, timedelta, date
from decimal import Decimal, DecimalException
from concurrent.futures import ThreadPoolExecutor, as_completed

# Third-Party Library Imports
# Optional import - removed during optimization to reduce slug size
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False
# Optional imports - removed during optimization to reduce slug size
try:
    import pandas as pd
    PANDAS_INVESTING_AVAILABLE = True
except ImportError:
    pd = None
    PANDAS_INVESTING_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    yf = None
    YFINANCE_AVAILABLE = False

import requests

try:
    import ta  # Technical Analysis Library
    TA_AVAILABLE = True
except ImportError:
    ta = None
    TA_AVAILABLE = False
from dateutil.relativedelta import relativedelta
from django.contrib.auth.mixins import LoginRequiredMixin

# Django Core Imports
from django.db.models import (
    Subquery,
    OuterRef,
    CharField,
    DecimalField,
    Sum,
    Q,
    Count,
    F,
    Case,
    When,
    Value,
)
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import user_passes_test
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.shortcuts import get_object_or_404, redirect, render
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib import messages
from django.views.generic import ListView, UpdateView, DetailView
from django.http import JsonResponse
from django import template
from accounts.mixins import FilteredListViewMixin

# Application Imports
from finance.models import Payment_Information, Transaction
from .models import (
    Investor_Information,
    Investment_rates,
    Investments,
    InvestmentContent,
    Ticker_Data,
    # credit_spread,  # DELETED Nov 5, 2025
    # OverBoughtSold,  # DELETED Nov 5, 2025
    # SavedResponses,  # DELETED Nov 5, 2025
    # Options_Returns,  # DELETED Nov 5, 2025
    # Cost_Basis,  # DELETED Nov 5, 2025
    InvestmentsStrategy,
    Returns_Balances,
    Daily_Trades,
    InvestmentReport,
    InvestmentUpgradeOffer,
)
from accounts.models import CustomerUser
from accounts.choices import UserCategory as CategoryChoices
from ai_services.models import Editable


# Utility Imports
from .utils import (
    risk_ratios,
    financial_categories,
    investment_rules,
    calculate_investor_returns,
)
from main.utils import (
    path_values,
    dates_functionality,
    generate_chatbot_response,
    today_date,
    date_converter,
)
from main.filters import ReturnsFilter
from main.context_processors import fetch_service_descriptions
# from .filters import PortfolioFilter  # DELETED Nov 5, 2025 - Portfolio model removed
from .forms import (
    # OptionsForm,  # DELETED Nov 5, 2025 - ShortPut model removed
    InvestmentForm,
    InvestmentRateForm,
    # PortfolioForm,  # DELETED Nov 5, 2025 - Portfolio model removed
    InvestmentsStrategyForm,
)

register = template.Library()
User = get_user_model

# ============================================================
# LEGACY MODEL PLACEHOLDERS (Nov 5, 2025)
# ============================================================
# These models were deleted but views_legacy.py still references them
# This prevents import errors. These views are DEPRECATED and should not be used.
# Use OptionsPosition and related services instead.
# 
# TODO: Refactor or remove views_legacy.py entirely
#
class ShortPut:
    """DEPRECATED - Placeholder to prevent import errors"""
    objects = None
    
class covered_calls:
    """DEPRECATED - Placeholder to prevent import errors"""
    objects = None
    
class Portfolio:
    """DEPRECATED - Placeholder to prevent import errors"""
    objects = None

class PortfolioForm:
    """DEPRECATED - Placeholder to prevent import errors"""
    pass

class PortfolioFilter:
    """DEPRECATED - Placeholder to prevent import errors"""
    pass

class OptionsForm:
    """DEPRECATED - Placeholder to prevent import errors"""
    pass

# Additional legacy models deleted Nov 5, 2025
class credit_spread:
    """DEPRECATED - Placeholder to prevent import errors"""
    objects = None

class OverBoughtSold:
    """DEPRECATED - Placeholder to prevent import errors"""
    objects = None

class SavedResponses:
    """DEPRECATED - Placeholder to prevent import errors"""
    objects = None

class Options_Returns:
    """DEPRECATED - Placeholder to prevent import errors"""
    objects = None

class Cost_Basis:
    """DEPRECATED - Placeholder to prevent import errors"""
    objects = None
# ============================================================


# Create your views here.
def home(request):
    return render(request, "main/home_templates/investing_home.html", {"title": "home"})


def training(request):
    return render(request, "investing/training.html", {"title": "training"})


@login_required
def newinvestment(request, plan_id=None):
    """
    Unified function to process new investments from forms or direct POST data.
    Handles both Revenue Sharing and Installment Models.
    """
    plan = None

    # Fetch investment plan from ID or API
    if plan_id:
        try:
            # Attempt to fetch from API
            response = requests.get(
                f"https://api.example.com/investment_plans/{plan_id}"
            )
            plan_data = response.json()
            plan = (
                Investment_rates.objects.get(id=plan_id) if not plan_data else plan_data
            )
        except (requests.exceptions.RequestException, Investment_rates.DoesNotExist):
            # Fallback to local DB if API fails
            plan = get_object_or_404(Investment_rates, id=plan_id, is_active=True)

    # Process direct POST request or form-based submission
    if request.method == "POST":
        form = InvestmentForm(request.POST) if not plan_id else None

        # Amount and duration handling
        amount = (
            Decimal(request.POST.get("amount"))
            if plan_id
            else Decimal(form.cleaned_data["amount"])
        )
        duration = (
            int(request.POST.get("duration"))
            if plan_id
            else int(request.POST.get("duration"))
        )

        # Calculate interest and returns dynamically
        if plan.get("investment_rate", None):
            # Revenue Sharing Model
            interest_amount = amount * Decimal(
                plan["investment_rate"]
                if isinstance(plan, dict)
                else plan.investment_rate
            )
            total_return = amount + interest_amount
            bi_weekly_returns = (total_return / duration) / 2
        else:
            # Installment Model
            installment_amount = amount / duration
            total_return = installment_amount * duration
            bi_weekly_returns = installment_amount / 2

        # Generate personalized investment summary (optional OpenAI call)
        user_message = (
            f"Create a personalized summary for {request.user.username} regarding their investment of "
            f"${amount} in the {plan['name'] if isinstance(plan, dict) else plan.name} plan. "
            f"Include key details like investment duration, returns, and next steps."
        )
        print(user_message)
        # investment_summary = generate_chatbot_response(user_message)
        # investment_summary = user_message  # Unused variable

        # Create Investor Information entry
        Investor_Information.objects.create(
            investor=request.user,
            total_amount=amount,
            amount_invested=amount,
            duration=duration,
            bi_weekly_returns=bi_weekly_returns,
        )

        messages.success(request, f"Investment of ${amount} successfully created!")

        # Redirect to contract signing page
        return redirect("finance:newoptioncontract", request.user)

    # GET request - show investment form
    return render(request, "investing/newinvestment.html", {"plan": plan})


@login_required
def newinvestmentrate(request):
    if request.method == "POST":
        form = InvestmentRateForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.save()
            return redirect("investing:investments")
    else:
        form = InvestmentRateForm()
    return render(request, "main/snippets_templates/generalform.html", {"form": form})


def get_or_create_investment_content():
    slug = "your-slug"
    try:
        investment_content = InvestmentContent.objects.filter(slug=slug).first()
        if investment_content and investment_content.description:
            # print("Using existing content from the database.")
            return investment_content.description
        else:
            raise InvestmentContent.DoesNotExist
    except InvestmentContent.DoesNotExist:
        context = fetch_service_descriptions()
        query = "Use the context as a example and generate a good overview."
        user_message = f"{context}\n\n{query}"
        generated_description = generate_chatbot_response(user_message)
        # Ensure we have a valid description
        if not generated_description:
            generated_description = "Welcome to our investment platform. We provide comprehensive investment solutions for all types of investors."
        
        investment_content = InvestmentContent.objects.filter(slug=slug).first()
        if investment_content:
            investment_content.description = generated_description
            investment_content.save()
        else:
            InvestmentContent.objects.create(
                slug=slug, title="Investment Platform Overview", description=generated_description
            )
        return generated_description
    except Exception as e:
        print(f"Error in get_or_create_investment_content: {e}")
        return "Welcome to our investment platform. We provide comprehensive investment solutions for all types of investors."


def InvestmentPlatformOverview(request):
    investment_content = get_or_create_investment_content()

    # Use the existing or generated content
    generated_content = (
        investment_content  # Assuming investment_content is the description field
    )

    data = []
    today = date.today()
    for year in range(2021, today.year + 1):
        year_data = {
            "year": year,
            "sales": Payment_Information.objects.filter(
                client_date__contains=str(year)
            ).aggregate(total_amount=Sum("payment_fees"))["total_amount"]
            or 0,
            "expenses": Transaction.objects.filter(
                transaction_date__year=year
            ).aggregate(total_amount=Sum("amount"))["total_amount"]
            or 0,
            "net_income": (
                Payment_Information.objects.filter(
                    client_date__contains=str(year)
                ).aggregate(total_amount=Sum("payment_fees"))["total_amount"]
                or 0
            )
            - (
                Transaction.objects.filter(transaction_date__year=year).aggregate(
                    total_amount=Sum("amount")
                )["total_amount"]
                or 0
            ),
        }
        data.append(year_data)
    # For pie graph
    # Get total active users
    total_active_users = CustomerUser.objects.filter(is_active=True).count()

    # Get active user counts by category
    active_user_counts = (
        CustomerUser.objects.filter(is_active=True)
        .values("category")
        .annotate(count=Count("id"))
    )

    # Creating a mapping from numerical values to English names
    category_mapping = dict(CategoryChoices.choices, Unknown="Unknown")

    active_user_counts_with_names = [
        {
            "category": category_mapping.get(entry["category"], "Unknown"),
            "count": entry["count"],
        }
        for entry in active_user_counts
    ]
    aggregated_counts = {}
    for entry in active_user_counts_with_names:
        category = entry["category"]
        count = entry["count"]
        if category not in aggregated_counts:
            aggregated_counts[category] = count
        else:
            aggregated_counts[category] += count

    # Create a list of dictionaries with unique category names and their counts
    categories_data = [
        {"category": category, "count": count}
        for category, count in aggregated_counts.items()
    ]

    # Print categories for debugging
    # category_names = [entry["category"] for entry in categories_data]  # Unused variable

    count_to_class = {2: "col-md-6", 3: "col-md-4", 4: "col-md-3"}
    # Fix privacy issue: Only show current user's investments
    if request.user.is_authenticated:
        investments = Investments.objects.filter(client=request.user)
    else:
        investments = Investments.objects.none()  # No investments for anonymous users

    selected_class = count_to_class.get(len(investments), "default-class")

    context = {
        "investments": investments,
        "selected_class": selected_class,
        "generated_content": generated_content,
        "chart_data": data,
        "total_active_users": total_active_users,
        "categories_data": categories_data,
    }
    return render(request, "investing/platformoverview.html", context)


@login_required
def investments(request):
    """
    Display user investments with proper data type handling for both API and database sources.
    """
    try:
        # Try to fetch from API first
        response = requests.get(
            f"https://api.example.com/user_investments/{request.user.id}"
        )
        if response.status_code == 200:
            investments_data = response.json()
            is_api_data = True
        else:
            raise requests.exceptions.RequestException("API returned non-200 status")
    except (requests.exceptions.RequestException, ValueError, KeyError):
        # Fallback to database
        investments_data = Investments.objects.filter(client=request.user)
        is_api_data = False

    # Initialize variables
    total_invested = 0
    revenue_share_returns = 0
    installment_returns = 0

    if is_api_data:
        # Handle API data (list of dictionaries)
        if isinstance(investments_data, list):
            total_invested = sum(
                investment.get("amount", 0) for investment in investments_data
            )

            for investment in investments_data:
                plan = investment.get("investment_plan", {})
                amount = investment.get("amount", 0)

                if plan and plan.get("investment_rate"):
                    # Revenue Share: Calculate returns based on rate and amount
                    revenue_share_returns += amount * plan["investment_rate"]
                elif plan and plan.get("duration"):
                    # Installments: Calculate pending returns
                    installment_returns += amount / plan["duration"]
        else:
            # Handle single investment object
            total_invested = investments_data.get("amount", 0)
            plan = investments_data.get("investment_plan", {})
            if plan and plan.get("investment_rate"):
                revenue_share_returns = total_invested * plan["investment_rate"]
            elif plan and plan.get("duration"):
                installment_returns = total_invested / plan["duration"]
    else:
        # Handle database QuerySet
        if investments_data.exists():
            total_invested = (
                investments_data.aggregate(total=Sum("amount"))["total"] or 0
            )

            for investment in investments_data:
                # Assuming investment has related fields for plan information
                # Adjust field names based on your actual model structure
                try:
                    if (
                        hasattr(investment, "investment_plan")
                        and investment.investment_plan
                    ):
                        if (
                            hasattr(investment.investment_plan, "investment_rate")
                            and investment.investment_plan.investment_rate
                        ):
                            revenue_share_returns += (
                                investment.amount
                                * investment.investment_plan.investment_rate
                            )
                        elif (
                            hasattr(investment.investment_plan, "duration")
                            and investment.investment_plan.duration
                        ):
                            installment_returns += (
                                investment.amount / investment.investment_plan.duration
                            )
                except AttributeError:
                    # Handle case where investment plan relationship doesn't exist
                    continue

    # Generate Investment Report using OpenAI API (optional)
    # user_message = f"Generate an investment report for {request.user} based on their portfolio. The portfolio includes these investments: {investments_data}. Summarize the overall performance, potential returns, and risks."
    # investment_report = generate_chatbot_response(user_message)

    context = {
        "investments": investments_data,
        "total_invested": total_invested,
        "revenue_share_returns": revenue_share_returns,
        "installment_returns": installment_returns,
        "is_api_data": is_api_data,  # Useful for template logic
    }
    return render(request, "investing/clients_investments.html", context)


@login_required
def user_investments(request, username=None, *args, **kwargs):
    """
    Display user investments with proper calculation of returns.
    """
    try:
        # Get user or return 404
        user = get_object_or_404(CustomerUser, username=username)

        # Check if current user has permission to view this user's investments
        if not request.user.is_superuser and request.user.username != username:
            return redirect("investing:investments")  # Redirect to own investments

        # Get user's investments
        investments = Investor_Information.objects.filter(investor=user)
        # latest_investment_rates = Investment_rates.objects.order_by(
        #     "-created_date"
        # ).first()  # Unused variable

        # Initialize variables for calculations
        total_return = 0
        monthly_return = 0
        number_positions = 0
        total_invested = 0
        total_duration = 0
        total_rate = 0
        investment_count = 0

        if investments.exists():
            # Calculate returns for each investment
            for investment in investments:
                # Get investment details from model instance
                model_type = investment.model_type
                duration = investment.duration or 12
                rate = investment.revenue_share_percentage or 0.05
                amount = investment.amount_invested

                # Accumulate totals for averages
                total_invested += amount
                total_duration += duration
                total_rate += rate
                investment_count += 1

                # Convert model_type to lowercase for comparison
                model_type_lower = model_type.lower() if model_type else "installment"

                # Calculate returns for this investment
                try:
                    (inv_total_return, inv_monthly_return, inv_positions) = (
                        calculate_investor_returns(
                            request,
                            investments,
                            amount,  # This should be the investment amount, not latest_investment_rates
                            model_type_lower,
                            rate,
                            duration,
                            business_revenue=15000,  # This should be calculated from actual business data
                            investment_goal=100000,
                        )
                    )

                    # Accumulate totals
                    total_return += inv_total_return
                    monthly_return += inv_monthly_return
                    number_positions += inv_positions

                except Exception as e:
                    # Log error for debugging but continue processing other investments
                    print(
                        f"Error calculating returns for investment {investment.id}: {e}"
                    )
                    continue

        # Calculate averages
        average_duration = (
            total_duration / investment_count if investment_count > 0 else 0
        )
        average_rate = total_rate / investment_count if investment_count > 0 else 0

        context = {
            "investments": investments,
            "title": "User Investments",
            "amount": total_return,
            "monthly_return": monthly_return,
            "number_positions": number_positions,
            "total_invested": total_invested,
            "average_duration": average_duration,
            "average_rate": average_rate,
            "user": user,
        }

        return render(request, "investing/clients_investments.html", context)

    except CustomerUser.DoesNotExist:
        # Handle case where user doesn't exist
        context = {"error": f"User '{username}' not found.", "title": "User Not Found"}
        return render(request, "investing/clients_investments.html", context)

    except Exception as e:
        # Handle any other unexpected errors
        print(f"Error in user_investments view: {e}")
        context = {
            "error": "An error occurred while loading investments.",
            "title": "Error",
        }
        return render(request, "investing/clients_investments.html", context)


@login_required
def investment_plan_list(request, path="options"):
    """View to display all active and featured investment plans."""
    try:
        response = requests.get("https://api.example.com/investment_plans")
        plans_data = response.json()
        if not isinstance(plans_data, list):
            raise ValueError("Invalid API response format")
        is_api = True
    except (requests.exceptions.RequestException, ValueError):
        plans_data = Investment_rates.objects.filter(is_active=True, is_featured=True)
        is_api = False

    processed_plans = []
    start_date = date_converter(today_date)

    for plan in plans_data:
        # Handle API data as dictionaries
        if is_api:
            plan_name = plan.get("name", "No Name")
            share_price_min = plan.get("share_price_min", 1000)
            share_price_max = plan.get("share_price_max", 5000)
            duration = plan.get("duration", 12)
            interest_rate = plan.get("rate", 0.05)
            tax_rate = plan.get("tax_rate", 0.05)
            plan_description = plan.get("description", "No Description")
            advantages_list = (
                plan.get("advantages", "").split(",") if plan.get("advantages") else []
            )
        else:
            # Handle local database objects

            plan_name = plan.name
            share_price_min = plan.share_price_min
            share_price_max = plan.share_price_max
            duration = plan.duration or 12
            interest_rate = plan.rate
            tax_rate = plan.tax
            plan_description = plan.description or "No Description"
            advantages_list = plan.advantages.split(",") if plan.advantages else []
        return_dates = []
        for month in range(duration):
            return_date = start_date + relativedelta(months=month + 1)
            return_dates.append(return_date.date())

        latest_investment = (
            Investments.objects.filter(investment_plan=plan)
            .order_by("-investment_date")
            .first()
        )
        latest_returns = (
            latest_investment.amount * interest_rate if latest_investment else 0
        )

        processed_plans.append(
            {
                "plan": {
                    "id": plan.get("id") if is_api else plan.id,
                    "name": plan_name,
                    "share_price_min": share_price_min,
                    "share_price_max": share_price_max,
                    "duration": duration,
                },
                "plan_description": plan_description,
                "advantages_list": advantages_list,
                "interest_rate": interest_rate,
                "tax_rate": tax_rate,
                "return_dates": return_dates[:1],
                "latest_returns": latest_returns,
            }
        )
    return render(
        request, "investing/investment_plans.html", {"plans": processed_plans}
    )


class InvestmentPlanListView(FilteredListViewMixin, ListView):
    """Display active and featured investment plans with fallback to DB."""

    model = Investment_rates
    template_name = "investing/investment_plans.html"
    context_object_name = "plans"
    order_by = "-created_at"

    def get_queryset(self):
        try:
            response = requests.get("https://api.example.com/investment_plans")
            plans_data = response.json()
            if isinstance(plans_data, list):
                return plans_data  # handled in context
        except Exception:
            pass
        return Investment_rates.objects.filter(is_active=True, is_featured=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        is_api = isinstance(context["plans"], list)
        processed_plans = []
        start_date = date_converter(today_date)
        for plan in context["plans"]:
            if is_api:
                plan_name = plan.get("name", "No Name")
                share_price_min = plan.get("share_price_min", 1000)
                share_price_max = plan.get("share_price_max", 5000)
                duration = plan.get("duration", 12)
                interest_rate = plan.get("rate", 0.05)
                tax_rate = plan.get("tax_rate", 0.05)
                plan_description = plan.get("description", "No Description")
                advantages_list = (
                    plan.get("advantages", "").split(",")
                    if plan.get("advantages")
                    else []
                )
                plan_id = plan.get("id")
            else:
                plan_name = plan.name
                share_price_min = plan.share_price_min
                share_price_max = plan.share_price_max
                duration = plan.duration or 12
                interest_rate = plan.rate
                tax_rate = plan.tax
                plan_description = plan.description or "No Description"
                advantages_list = plan.advantages.split(",") if plan.advantages else []
                plan_id = plan.id
            return_dates = []
            for month in range(duration):
                return_date = start_date + relativedelta(months=month + 1)
                return_dates.append(return_date.date())
            latest_investment = (
                Investments.objects.filter(
                    investment_plan=plan if not is_api else plan_id
                )
                .order_by("-investment_date")
                .first()
            )
            latest_returns = (
                latest_investment.amount * interest_rate if latest_investment else 0
            )
            processed_plans.append(
                {
                    "plan": {
                        "id": plan_id,
                        "name": plan_name,
                        "share_price_min": share_price_min,
                        "share_price_max": share_price_max,
                        "duration": duration,
                    },
                    "plan_description": plan_description,
                    "advantages_list": advantages_list,
                    "interest_rate": interest_rate,
                    "tax_rate": tax_rate,
                    "return_dates": return_dates[:1],
                    "latest_returns": latest_returns,
                }
            )
        context["plans"] = processed_plans
        return context


class OptionListView(FilteredListViewMixin, ListView):
    """Render option data page with a title parameter."""

    template_name = "main/snippets_templates/output_snippets/option_data.html"
    context_object_name = "objects"
    model = ShortPut  # placeholder; not used directly
    order_by = "-on_date"  # Override the default date_joined with on_date which exists in ShortPut

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        default_title = "creditspread"
        # Get title from URL path parameter, not query parameter
        title = self.kwargs.get("title", default_title)
        context.update({
            "title": title,
            "subtitle": title,  # Add subtitle for template compatibility
        })
        return context


def investment_plan_detail(request, pk):
    """View to display details of a selected investment plan."""
    plan = get_object_or_404(Investment_rates, pk=pk)
    return render(request, "investing/detail.html", {"plan": plan})


class Investment_Update_View(UpdateView):
    # model = Oversold
    model = Investments
    # success_url = "/investing/overboughtsold/None"
    fields = "__all__"
    # fields = ['symbol','comment','is_featured']
    template_name = "main/snippets_templates/generalform.html"

    def form_valid(self, form):
        # form.instance.author=self.request.user
        return super().form_valid(form)

    def test_func(self):
        # if self.request.user.is_superuser:
        if self.request.user:
            return True
        return False


def optionlist(request):
    default_title = "creditspread"
    title = request.GET.get("title", default_title)
    return render(
        request,
        "main/snippets_templates/output_snippets/option_data.html",
        {"title": title},
    )


FMP_API_KEY = os.environ.get("FMP_API_KEY")


# Fetch the top 1000 symbols from the FMP API
def fetch_symbols_from_fmp(exchange, limit=1000):
    url = f"https://financialmodelingprep.com/api/v3/stock-screener?exchange={exchange}&limit={limit}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200 and data:
            filtered_symbols = []
            symbols_not_meeting_criteria = []
            for company in data:
                symbol = company.get("symbol")
                beta = company.get("beta")
                volume = company.get("volume")
                if beta is not None and volume is not None:
                    if beta > 0 and volume > 1000:
                        filtered_symbols.append(symbol)
                    else:
                        symbols_not_meeting_criteria.append(symbol)
                else:
                    symbols_not_meeting_criteria.append(symbol)
            # Print symbols that don't meet the criteria
            if symbols_not_meeting_criteria:
                print(f"Symbols not meeting beta and volume criteria for {exchange}:")
                print(", ".join(symbols_not_meeting_criteria))
            return filtered_symbols
        else:
            print(f"No data received for exchange {exchange}")
    except Exception as e:
        print(f"Error fetching symbols from {exchange}: {e}")
    return []


FMP_API_KEY1 = os.environ.get("FMP_API_KEY1")


def fetch_rsi_from_fmp(symbols):
    rsi_data = {}
    for symbol in symbols:
        url = f"https://financialmodelingprep.com/api/v3/technical_indicator/1day/{symbol}?type=rsi&period=14&apikey={FMP_API_KEY1}"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data:
                # Get the latest RSI value
                rsi = data[1].get("rsi")
                if rsi is not None:
                    rsi_data[symbol] = rsi
                else:
                    print(f"No RSI data available for symbol {symbol}")
            else:
                print(f"No data returned for symbol {symbol}")
        else:
            print(
                f"Error fetching data for symbol {symbol} (Status Code: {response.status_code})"
            )

    # Ensure it returns an empty dictionary if no RSI data is found
    return rsi_data if rsi_data else {}


def fetch_historical_data(symbols, period="6mo"):
    try:
        hist_data = yf.download(
            tickers=symbols,
            period=period,
            group_by="ticker",
            threads=True,
            progress=False,
        )
        return hist_data
    except Exception as e:
        print(f"Error fetching historical data: {e}")
        return None


def save_shortput_data(filtered_data):
    """
    Save or update ShortPut data.
    """
    one_day_ago = timezone.now() - timedelta(days=3)

    # Delete records older than a day
    old_records = ShortPut.objects.filter(on_date__lt=one_day_ago)

    # Debug: print records to be deleted
    print("Records to be deleted:", old_records)

    # Delete old records
    old_records.delete()
    shortput_objects = []
    for symbol_data in filtered_data:
        # Check if the data already exists for the symbol
        shortput, created = ShortPut.objects.update_or_create(
            symbol=symbol_data["symbol"],
            defaults={
                "expiry": symbol_data["expiry"],
                "industry": symbol_data["industry"],
                "strike_price": symbol_data["strike_price"],
                "implied_volatility_rank": symbol_data["rank"],
                "earnings_date": symbol_data["earnings_date"],
                "stock_price": symbol_data["stock_price"],
                "annualized_return": symbol_data["annualized_return"],
                "on_date": timezone.now(),  # Update the on_date when saving or updating
            },
        )
        shortput_objects.append(shortput)
    return shortput_objects


@login_required
def optiondata(request, title=None, symbol=None, *arg, **kwargs):
    start_time = time.time()
    path_list, sub_title, pre_sub_title = path_values(request)

    # Check for existing data
    existing_data = ShortPut.objects.all()

    if existing_data.exists():
        filtered_data = []
        for obj in existing_data:
            symbol_data = {
                "symbol": obj.symbol,
                "stock_price": obj.stock_price,
                "strike_price": obj.strike_price,
                "industry": obj.industry,
                "return": None,
                "annualized_return": obj.annualized_return,
                "rank": obj.implied_volatility_rank,
                "expiry": obj.expiry,
                "earnings_date": obj.earnings_date,
            }
            filtered_data.append(symbol_data)
    else:
        # Fetch new data if no existing data is found
        exchanges = ["NYSE"]
        symbols = []
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(fetch_symbols_from_fmp, exchange, limit=500)
                for exchange in exchanges
            ]
            for future in as_completed(futures):
                symbols += future.result()

        symbols = symbols[:100]
        print("Fetched symbols:", symbols)

        rsi_data = fetch_rsi_from_fmp(symbols)

        filtered_rsi_data = {
            symbol: rsi for symbol, rsi in rsi_data.items() if rsi < 20 or rsi > 80
        }

        if not filtered_rsi_data:
            return render(
                request,
                "main/snippets_templates/output_snippets/option_data.html",
                {"error": "No symbols found with RSI < 20 or RSI > 80."},
            )

        # Fetch stock data
        def fetch_stock_data(symbol):
            try:
                stock = yf.Ticker(symbol)
                stock_info = stock.info
                return {
                    "symbol": symbol,
                    "industry": stock_info.get("industry", "N/A"),
                    "stock_price": stock_info.get("previousClose", "N/A"),
                    "strike_price": stock_info.get("strikePrice"),
                    "return": None,
                    "annualized_return": stock_info.get("trailingAnnualDividendYield"),
                    "rank": None,
                    "expiry": None,
                    "earnings_date": stock_info.get("earningsDate"),
                    "financials": "More",
                    "charting": "Chart",
                    "edit": "Edit",
                }
            except Exception as e:
                print(f"Error fetching data for {symbol}: {e}")
                return None

        with ThreadPoolExecutor() as executor:
            stock_results = list(
                executor.map(fetch_stock_data, filtered_rsi_data.keys())
            )

        filtered_data = [result for result in stock_results if result]
        print("Filtered data:", filtered_data)

        if not filtered_data:
            return render(
                request,
                "main/snippets_templates/output_snippets/option_data.html",
                {"error": "No valid stock data found."},
            )

        # Save or update the ShortPut data using the new function
        save_shortput_data(filtered_data)

    title_mapping = {
        "covered_calls": "COVERED CALLS",
        "shortputdata": "SHORT PUT",
    }
    page_title = title_mapping.get(sub_title, "Option Data")
    description = None

    context = {
        "data": filtered_data,
        "days_to_expiration": 0,
        "subtitle": sub_title,
        "pre_sub_title": pre_sub_title,
        "title": page_title,
        "get_edit_url": "",
        "url_name": "",
    }

    if request.method == "POST":
        condition_list = request.POST.getlist("selected_conditions")
        data = "symbol rank(Implied Volatility) days_to_expiry earning_date return\n"
        for stock_data in context["data"]:
            data += f"{stock_data['symbol']} {stock_data.get('rank', 'N/A')} {stock_data.get('days_to_expiry', 'N/A')} {stock_data.get('earnings_date', 'N/A')} {stock_data.get('return', 'N/A')}\n"
        question = (
            data
            + "\n"
            + "On the above data, list the top 5 symbols considering the following fields in priority order: "
            + ", ".join(condition_list)
            + """
            Output format example: {
            description: "Why you chose these five",
            symbols: ["ENPH", "PYPL"]
            }, and do not include any extra strings in the output.
            """
        )
        message_dict = [
            {"role": "system", "content": question},
        ]
        try:
            answer = generate_chatbot_response(None, user_message_dict=message_dict)
            data_dict = json.loads(answer)
            description = data_dict["description"]
            symbols = data_dict["symbols"]
            context["data"] = [v for v in context["data"] if v["symbol"] in symbols]
        except Exception as e:
            print(e)
            description = "Try again!!!"

    context.update(
        {
            "categories": investment_rules,
            "subtitle": sub_title,
            "pre_sub_title": pre_sub_title,
            "title": page_title,
            "ai_message": description,
        }
    )

    end_time = time.time()
    print(f"Total execution time: {end_time - start_time} seconds")

    return render(
        request, "main/snippets_templates/output_snippets/option_data.html", context
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def shortput_update(request, pk):
    path_list, subtitle, pre_sub_title = path_values(request)
    shortput = get_object_or_404(ShortPut, pk=pk)
    success_url = reverse("investing:option_list", kwargs={"title": "shortputdata"})

    if request.method == "POST":
        form = OptionsForm(request.POST, instance=shortput)
        if form.is_valid():
            form.save()
            return redirect(success_url)
    else:
        form = OptionsForm(instance=shortput)

    context = {
        "form": form,
        "title": "Update Short Put",
    }
    return render(request, "main/snippets_templates/generalform.html", context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def covered_update(request, pk):
    path_list, subtitle, pre_sub_title = path_values(request)
    covered = get_object_or_404(covered_calls, pk=pk)

    # Check if the object exists
    if not covered:
        context = {
            "title": "STOCKS ERROR",
            "message": "Hi, No covered_calls matches the given query.",
        }
        return render(request, "main/errors/generalerrors.html", context)

    success_url = reverse("investing:option_list", kwargs={"title": "covered_calls"})

    if request.method == "POST":
        form = OptionsForm(request.POST, instance=covered)
        if form.is_valid():
            form.save()
            return redirect(success_url)
    else:
        form = OptionsForm(instance=covered)

    context = {
        "form": form,
        "title": "Update covered Calls",
    }
    return render(request, "main/snippets_templates/generalform.html", context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def credit_spread_update(request, pk):
    spread = get_object_or_404(credit_spread, pk=pk)
    success_url = reverse("investing:option_list", kwargs={"title": "credit_spread"})

    if request.method == "POST":
        form = OptionsForm(request.POST, instance=spread)
        if form.is_valid():
            form.save()
            return redirect(success_url)
    else:
        form = OptionsForm(instance=spread)

    context = {
        "form": form,
        "title": "Update Credit spread",
    }
    return render(request, "main/snippets_templates/generalform.html", context)


def calculate_remaining_amount(query_set, username, exclude_symbol=None):

    total_amount = 20000
    investment_threshold = 10

    if exclude_symbol:
        query_set = query_set.exclude(symbol=exclude_symbol)

    investor = Investor_Information.objects.filter(investor__username=username)
    if not investor.exists():
        default_value = Editable.objects.filter(name="investor_default")

        if default_value.exists():
            try:
                default_value = default_value.first()
                total_amount = default_value.get("investment_total_amount", 20000)
                investment_threshold = default_value.get("investment_threshold", 10)
            except Exception:
                pass
    else:

        total_amount = investor.first().total_amount
        investment_threshold = investor.first().investment_threshold

    invested_amount = (
        query_set.filter(is_active=True).aggregate(total_amount=Sum("amount"))[
            "total_amount"
        ]
        if query_set.aggregate(total_amount=Sum("amount"))["total_amount"]
        else 0
    )
    threshold_amount = total_amount * investment_threshold / 100

    return (
        total_amount,
        investment_threshold,
        invested_amount,
        threshold_amount,
        Decimal(threshold_amount) - Decimal(invested_amount),
    )


@login_required
def portfolioCreate(request):
    if request.method == "POST":
        data = request.POST
        condition_dict = {
            "-1": "neutral",
            "1": "oversold",
            "0": "overbought",
        }
        query_set = Portfolio.objects.filter(user=request.user)
        (
            total_amount,
            investment_threshold,
            invested_amount,
            threshold_amount,
            remaining_investment_amount,
        ) = calculate_remaining_amount(query_set, request.user.username, data["symbol"])
        form = PortfolioForm(data)
        reversed_condition_dict = {value: key for key, value in condition_dict.items()}
        # import pdb; pdb.set_trace()
        if form.is_valid():

            if (
                not form.instance.is_active
                or form.instance.amount <= remaining_investment_amount
            ):
                form.instance.condition = reversed_condition_dict[
                    form.instance.condition
                ]

                form.instance.user = request.user

                form.save()
                success_url = reverse("investing:my_portfolio")
            else:

                form.add_error(
                    None,
                    f"You exceed your limit of investment(max limit:{threshold_amount}). try to reduce this investment amount or close another investment.",
                )
                return render(
                    request, "main/snippets_templates/generalform.html", {"form": form}
                )

        else:
            # Form is not valid
            return render(
                request, "main/snippets_templates/generalform.html", {"form": form}
            )

        return redirect(success_url)

    else:
        form = PortfolioForm(initial={"create": True})
        context = {
            "form": form,
        }

        return render(request, "main/snippets_templates/generalform.html", context)


@login_required
def portfolio(request, symbol):
    model = request.GET.get("model")
    model_mapping = {
        "covered_calls": {"model": covered_calls},
        "shortputdata": {"model": ShortPut},
        "credit_spread": {"model": credit_spread},
    }
    stock_model = model_mapping.get(model, None)
    symbol_in_portfolio = Portfolio.objects.filter(user=request.user, symbol=symbol)
    initial_values = None
    # amount = 0  # Unused variable
    # max_reward = 0  # Unused variable
    strategy_type = None
    condition_dict = {
        "-1": "neutral",
        "1": "oversold",
        "0": "overbought",
    }
    if request.method == "POST":
        data = request.POST

        query_set = Portfolio.objects.filter(user=request.user)
        (
            total_amount,
            investment_threshold,
            invested_amount,
            threshold_amount,
            remaining_investment_amount,
        ) = calculate_remaining_amount(query_set, request.user.username, symbol)
        form = PortfolioForm(data)
        reversed_condition_dict = {value: key for key, value in condition_dict.items()}

        if form.is_valid():

            if (
                not form.instance.is_active
                or form.instance.amount <= remaining_investment_amount
            ):
                form.instance.condition = reversed_condition_dict[
                    form.instance.condition
                ]

                if symbol_in_portfolio:
                    form = PortfolioForm(data, instance=symbol_in_portfolio.first())

                else:
                    form.instance.user = request.user
                # form.instance.amount=form.instance.long_strike-form.instance.short_strike

                try:
                    difference_legs = (
                        form.instance.long_strike - form.instance.short_strike
                    )
                    # Determine the action type
                    action_type = form.instance.action.lower()

                    # Check for 'put' or 'call' actions and set strategy_type and max_reward
                    if (action_type == "put" and difference_legs > 0) or (
                        action_type == "call" and difference_legs < 0
                    ):
                        # max_reward = difference_legs - form.instance.amount  # Unused variable
                        strategy_type = "debit"
                    else:
                        # max_reward = difference_legs  # Unused variable
                        form.instance.amount = difference_legs
                        strategy_type = "credit"

                except Exception as e:
                    print(f"Error: {e}")

                # Set calculated values in the form instance
                form.instance.strategy = strategy_type
                form.save()
                success_url = reverse("investing:my_portfolio")
            else:

                form.add_error(
                    None,
                    f"you exceed your limit of investment(max limit:{threshold_amount}). try to reduce this investment amount or close another investment.",
                )
                return render(
                    request, "main/snippets_templates/generalform.html", {"form": form}
                )

        else:
            # Form is not valid
            return render(
                request, "main/snippets_templates/generalform.html", {"form": form}
            )

        return redirect(success_url)

    else:
        condition = OverBoughtSold.objects.filter(symbol=symbol)
        if symbol_in_portfolio.exists():

            symbol_in_portfolio = symbol_in_portfolio.first()

            symbol_in_portfolio.condition = (
                condition_dict[str(condition.first().condition_integer)]
                if condition.exists()
                else condition_dict["-1"]
            )

            # Pass the initial values to the form when creating an instance
            form = PortfolioForm(instance=symbol_in_portfolio)

        else:

            if stock_model:
                subquery = Ticker_Data.objects.filter(symbol=OuterRef("symbol")).values(
                    "industry"
                )[:1]
                symbol_data = (
                    stock_model["model"]
                    .objects.filter(symbol=symbol)
                    .annotate(
                        industry=Subquery(subquery, output_field=CharField()),
                    )
                )
                if symbol_data and symbol_data.exists():
                    symbol_data = symbol_data.first()
                    initial_values = {
                        "symbol": symbol,
                        "industry": symbol_data.industry,
                        "condition": (
                            condition_dict[str(condition.first().condition_integer)]
                            if condition.exists()
                            else condition_dict["-1"]
                        ),
                        "strike_price": (
                            symbol_data.strike_price
                            if stock_model["model"] != "credit_spread"
                            else symbol_data.sell_strike
                        ),
                        "expiry": symbol_data.expiry,
                        # 'user': request.user,
                        "action": (
                            symbol_data.action
                            if stock_model["model"] != "credit_spread"
                            else symbol_data.strategy
                        ),
                        "implied_volatility_rank": (
                            symbol_data.implied_volatility_rank
                            if stock_model["model"] != "credit_spread"
                            else symbol_data.rank
                        ),
                        "earnings_date": symbol_data.earnings_date,
                        "strategy": model,
                    }
            # Pass the initial values to the form when creating an instance
            form = PortfolioForm(initial=initial_values)

        # import pdb; pdb.set_trace()
        context = {
            "form": form,
        }

        return render(request, "main/snippets_templates/generalform.html", context)


@method_decorator(login_required, name="dispatch")
class PortfolioListView(ListView):
    model = Portfolio
    template_name = "investing/portfolioList.html"
    context_object_name = "portfolio"
    ordering = ["created_at"]
    # filterset_class = PortfolioFilter

    def get_queryset(self):
        username = self.request.user.username
        if self.request.user.is_superuser:
            username = self.request.GET.get("username", None)
        # Combine the custom query with the existing queryset
        query = (
            super()
            .get_queryset()
            .annotate(
                condition_name=Case(
                    When(Q(condition=1), then=Value("overbought")),
                    When(Q(condition=0), then=Value("oversold")),
                    When(Q(condition=-1), then=Value("neutral")),
                    default=F("condition"),  # Default case, adjust as needed
                    output_field=CharField(),
                ),
                difference_legs=(F("long_strike") - F("short_strike")) * 100,
            )
            .annotate(
                max_reward=Case(
                    # For put spreads, calculate reward as 70% of the difference between legs
                    When(
                        Q(action="put") & Q(long_strike__gt=F("short_strike")),
                        then=F("difference_legs") - F("amount"),
                    ),
                    # For call spreads, calculate reward as the difference between legs
                    When(
                        Q(action="call") & Q(long_strike__gt=F("short_strike")),
                        then=F("difference_legs"),
                    ),
                    # Default case if none of the above conditions are met
                    default=F("difference_legs"),
                    output_field=DecimalField(),
                )
            )
        )

        if self.request.user.is_superuser and username is None:
            return query
        else:
            return query.filter(user__username=username)

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get the default context
        context = super().get_context_data(**kwargs)
        query_set = self.get_queryset()
        username = self.request.user.username
        if self.request.user.is_superuser:
            username = self.request.GET.get("username", self.request.user.username)

        (
            total_amount,
            investment_threshold,
            invested_amount,
            threshold_amount,
            remaining_investment_amount,
        ) = calculate_remaining_amount(query_set, username)
        remaining_amount = total_amount - invested_amount
        total_theta = query_set.aggregate(
            total_theta=Sum(
                (F("long_leg_theta") - F("short_leg_theta")) * F("number_of_contract")
            )
        )["total_theta"]
        total_delta = query_set.aggregate(
            total_delta=Sum(
                (F("long_leg_delta") - F("short_leg_delta")) * F("number_of_contract")
            )
        )["total_delta"]
        context["total_amount"] = total_amount
        context["invested_amount"] = invested_amount if invested_amount else 0
        context["remaining_amount"] = remaining_amount
        context["threshold_amount"] = threshold_amount
        context["investment_threshold"] = investment_threshold
        context["total_theta"] = total_theta if total_theta else 0
        context["total_delta"] = total_delta if total_delta else 0
        context["hide_summary"] = (
            False
            if self.request.user.is_superuser
            and self.request.GET.get("username") is None
            else True
        )

        filter = PortfolioFilter(self.request.GET, query_set)
        context["filter"] = filter
        query_set = filter.qs
        context["portfolio"] = query_set
        return context


class oversold_update(UpdateView):
    # model = Oversold
    model = OverBoughtSold
    success_url = "/investing/overboughtsold/None"
    fields = "__all__"
    # fields = ['symbol','comment','is_featured']
    template_name = "main/snippets_templates/generalform.html"

    def form_valid(self, form):
        # form.instance.author=self.request.user
        return super().form_valid(form)

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        return False


@register.filter
def subtract_dates(date1, date2):
    return date1 - date2


@login_required
def options_returns(request, title="daily_trades"):
    values, sub_title, pre_sub_title = path_values(request)
    # date_today = datetime.now(timezone.utc)  # Unused variable
    ytd_duration, current_year, first_date = dates_functionality()
    ytd_weeks = int(ytd_duration / 7)
    ytd_bi_weekly = int(ytd_duration / 14)
    ytd_month = int(ytd_duration / 30)

    total_returns_on_options = 0
    total_returns_on_stocks = 0
    transactions = 0
    total_proceeds = 0
    wash_amount = 0
    days_to_expiration = 0
    # total_credit = 0  # Unused variable
    # total_debit = 0  # Unused variable
    # total_returns = 0  # Unused variable
    opening_balance = 0
    closing_balance = 0
    options_returns = 0
    percentage_returns = 0
    # date = date_today  # Unused variable
    # Extract the selected date from the request
    selected_date = request.GET.get("date")
    print(selected_date)

    if sub_title == "daily_trades":
        stockdata = Daily_Trades.objects.all()
        balances = Returns_Balances.objects.all()
        ReturnsFilters = ReturnsFilter(request.GET, queryset=stockdata)
        balances = Returns_Balances.objects.filter(closing_date=selected_date)
        # balances = Returns_Balances.objects.filter(closing_date='2024-02-29')
        if balances.exists():
            single_balance = balances.first()
            # date = single_balance.closing_date  # Unused variable
            opening_balance = float(single_balance.opening)
            closing_balance = float(single_balance.closing)
            options_returns = float(single_balance.balances)
            percentage_returns = float(options_returns / opening_balance) * 100

        # print("Balances=====>",date,closing_balance,opening_balance,options_returns,percentage_returns)

    else:
        washdata = Options_Returns.objects.filter(event="Wash")
        stockdata = Options_Returns.objects.all()
        ReturnsFilters = ReturnsFilter(request.GET, queryset=stockdata)
        for amt in stockdata:
            total_proceeds += amt.proceeds
            transactions += amt.qty
            total_returns_on_options += amt.ST_GL
            total_returns_on_stocks += amt.LT_GL
        for amt in washdata:
            wash_amount += amt.ST_GL

        # Formatting
    total_proceeds = float(total_proceeds)
    total_returns_on_options = float(total_returns_on_options)
    total_returns_on_stocks = float(total_returns_on_stocks)
    net_returns = total_returns_on_options + total_returns_on_stocks
    monthly_returns = net_returns / ytd_month
    ytd_bi_weekly_returns = net_returns / ytd_bi_weekly
    weekly_returns = net_returns / ytd_weeks

    context = {
        "title": "CODA INVESTMENT PORTAL",
        "sub_title": sub_title,
        "data": ReturnsFilters,
        "days_to_expiration": days_to_expiration,
        "total_proceeds": total_proceeds,
        "transactions": transactions,
        "options_amount": total_returns_on_options,
        "stocks_amount": total_returns_on_stocks,
        "wash_amount": wash_amount,
        "net_returns": net_returns,
        "monthly_returns": monthly_returns,
        "bi_weekly_returns": ytd_bi_weekly_returns,
        "weekly_returns": weekly_returns,
        "duration": ytd_month,
        "opening_balance": opening_balance,
        "closing_balance": closing_balance,
        "options_returns": options_returns,
        "percentage_returns": percentage_returns,
        # "total_credit": total_credit,
        # "total_debit": total_debit,
        # "total_returns": total_returns,
    }

    return render(request, "investing/company_returns.html", context)


@login_required
def cost_basis(request):
    ytd_duration, current_year, first_date = dates_functionality()
    # date_today = datetime.now(timezone.utc)  # Unused variable
    ytd_days = ytd_duration
    # ytd_weeks = int(ytd_days / 7)  # Unused variable
    # ytd_bi_weekly = int(ytd_days / 14)  # Unused variable
    ytd_month = int(ytd_days / 30)

    stockdata = Cost_Basis.objects.all()

    context = {
        "title": "COST BASIS ANALYSIS",
        "data": stockdata,
        "duration": ytd_month,
    }
    return render(request, "investing/cost_basis.html", context)


def ticker_measures(request):
    # Get current datetime with UTC timezone
    ticker_data = Ticker_Data.objects.all()
    context = {
        "ticker_data": ticker_data,
    }
    return render(request, "investing/ticker_data.html", context)


def calculate_rsi(symbol):
    """Calculates the Relative Strength Index (RSI)."""
    url = f"https://financialmodelingprep.com/api/v3/technical_indicator/1day/{symbol}?type=rsi&period=14&apikey={FMP_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            # Get the latest RSI value
            rsi = data[1].get("rsi")
            if rsi is not None:
                return rsi
            else:
                print(f"No RSI data available for symbol {symbol}")
        else:
            print(f"No data returned for symbol {symbol}")
    else:
        print(
            f"Error fetching data for symbol {symbol} (Status Code: {response.status_code})"
        )


def calculate_rs(data, window=14):
    """Calculates the Relative Strength Index (RSI)."""
    delta = data.diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_bollinger_bands(series, window=20, num_std=2):
    rolling_mean = series.rolling(window=window).mean()
    rolling_std = series.rolling(window=window).std()
    upper_band = rolling_mean + (rolling_std * num_std)
    lower_band = rolling_mean - (rolling_std * num_std)
    return upper_band, lower_band


def calculate_cci(data, window=20):
    tp = (data["High"] + data["Low"] + data["Close"]) / 3  # Typical Price
    matp = tp.rolling(window=window).mean()  # Moving Average of Typical Price
    mean_dev = tp.rolling(window=window).apply(
        lambda x: np.mean(np.abs(x - np.mean(x))), raw=True
    )
    cci = (tp - matp) / (0.015 * mean_dev)
    return cci


@login_required
def oversoldpositions(request, symbol=None):
    # current_date_str = timezone.now().strftime("%Y-%m-%d")  # Unused variable

    overboughtsold_records = OverBoughtSold.objects.all()

    context = {
        "overboughtsold": overboughtsold_records,
        "title": "Click On a Symbol",
        "financial_categories": financial_categories,
        "risk_ratios": risk_ratios,
    }
    if symbol is not None:
        try:
            today = datetime.datetime.today().date()
            start_date = today.replace(day=1)
            ticker = yf.Ticker(symbol)
            hist_data = ticker.history(start=start_date, end=today, interval="1d")
            ticker_info = ticker.info
            selected_industry = ticker_info.get("industry", None)
            selected_market_cap = ticker_info.get("marketCap", None)

            # print(hist_data)
            # rsi_indicator = ta.momentum.RSIIndicator(hist_data['Close'], window=14)  # 10-day window for RSI
            # rsi_series = rsi_indicator.rsi()

            # rsi = rsi_series.iloc[1]

            rsi = calculate_rsi(symbol)
            print("rsi using api", rsi)
            # Bollinger Bands
            bollinger_bands = ta.volatility.BollingerBands(
                hist_data["Close"], window=14, window_dev=2
            )
            bollinger_upper_band = bollinger_bands.bollinger_hband().iloc[
                -1
            ]  # Upper Band
            bollinger_lower_band = bollinger_bands.bollinger_lband().iloc[
                -1
            ]  # Lower Band
            latest_ma_26 = bollinger_bands.bollinger_mavg().iloc[
                -1
            ]  # Moving Average (Middle Band)

            # CCI (Commodity Channel Index)
            cci_indicator = ta.trend.CCIIndicator(
                hist_data["High"], hist_data["Low"], hist_data["Close"], window=14
            )
            cci_series = cci_indicator.cci()
            cci = cci_series.iloc[-1]  # Latest CCI value

            # Print the values
            print(f"RSI: {rsi}")
            print(f"Bollinger Upper Band: {bollinger_upper_band}")
            print(f"Bollinger Middle Band (MAVG): {latest_ma_26}")
            print(f"Bollinger Lower Band: {bollinger_lower_band}")
            print(f"CCI: {cci}")

            trend = (
                (hist_data["Close"].iloc[-1] - hist_data["Close"].iloc[0])
                / hist_data["Close"].iloc[0]
            ) * 100

            if rsi < 20:
                stock_status = "Oversold"
                percentage = 20 - rsi  # How much below 20%
            elif rsi > 80:
                stock_status = "Overbought"
                percentage = rsi - 80  # How much above 80%
            else:
                stock_status = "Neutral"
                percentage = 0
            latest_close = hist_data["Close"].iloc[-1]
            print(latest_close)

            # Tony Zac Signal logic
            if cci is not None and latest_ma_26 is not None:
                if cci > 0 and latest_close > latest_ma_26:
                    stock_status = "Bullish"
                elif cci < 0 and latest_close < latest_ma_26:
                    stock_status = "Bearish"
                else:
                    stock_status = "Neutral"

                if cci > 0 and latest_close < latest_ma_26:
                    tony_zac_signal = "New Buy Signal"
                    condition = "Oversold"
                elif cci < 0 and latest_close > latest_ma_26:
                    tony_zac_signal = "New Sell Signal"
                    condition = "Overbought"
                else:
                    tony_zac_signal = "no signal"
                    # Do not reset condition here
            else:
                tony_zac_signal = "Data insufficient for Tony Zac Signal"

            # Coda Signal logic
            if len(hist_data) >= 14:
                if rsi > 80 and latest_close > bollinger_upper_band:
                    coda_signal = "Overbought - Sell"

                elif rsi < 20 and latest_close < bollinger_lower_band:
                    coda_signal = "Oversold - Buy"

                else:
                    coda_signal = "Neutral"
                    # Do not reset condition here
            else:
                coda_signal = "Not enough data for Coda method"

            # prompt = f"""
            # You are an AI assistant that helps analyze stock signals and provide trading recommendations.
            # Given the following signals for the stock symbol {symbol}:
            # - RSI: {rsi:.2f}
            # - Stock Status: {stock_status}
            # - Tony Zac Signal: {tony_zac_signal}
            # - Coda Signal: {coda_signal}

            # Based on these indicators, should an investor consider buying, selling, or holding the stock?
            # Provide a concise recommendation with a brief explanation.
            # """
            # print('tony',tony_zac_signal)

            # openai_recommendation = generate_chatbot_response(prompt)
            # print('openai',openai_recommendation)
            # Prepare different prompts based on stock status
            indicators_text = {
                "rsi": f"{rsi:.2f}",
                "stock_status": stock_status,
                "tony_zac_signal": tony_zac_signal,
                "coda_signal": coda_signal,
            }

            # Initialize OpenAI recommendation
            # Initialize OpenAI recommendation
            openai_recommendation = None

            if rsi > 80 or rsi < 20:
                if rsi > 80:
                    condition = "80"
                if rsi < 20:
                    condition = "20"
                print("condition", condition)
                standard_response_entry = SavedResponses.objects.filter(
                    condition=condition
                ).first()

                if standard_response_entry:
                    print("using exiting")
                    # Standard response exists, replace placeholders
                    standard_response = standard_response_entry.standard_response

                    openai_recommendation = standard_response.format(**indicators_text)
                    print(openai_recommendation)
                else:
                    # Standard response doesn't exist, generate it
                    prompt = f"""
                    You are an AI assistant that helps analyze stock signals and provide trading recommendations.
                    Given the following signals for the stock symbol {symbol}:
                    - RSI: {rsi:.2f}
                    - Stock Status: {stock_status}
                    - Tony Zac Signal: {tony_zac_signal}
                    - Coda Signal: {coda_signal}

                    Based on these indicators, should an investor consider buying, selling, or holding the stock?
                    Provide a concise recommendation with a brief explanation.
                     Note: This is a standard response template for {condition} conditions.SO for instead of using valuse for rsi and other use brackets{'rsi'} and in use rsi and soon.it is jus the template.do use any other text.
                    """

                    openai_response = generate_chatbot_response(prompt)

                    # Save the standard response with placeholders to the database
                    SavedResponses.objects.create(
                        condition=condition, standard_response=openai_response
                    )

                    # Replace placeholders with current values
                    openai_recommendation = openai_response.format(**indicators_text)
            else:
                # If the RSI is between 20 and 80, provide a neutral response
                openai_recommendation = "The stock is currently in a neutral state based on RSI and other indicators."

            # Fetch global market data (as before)
            # global_markets = {  # Unused variable
            #     "NYSE": symbol,
            #     "LSE": f"{symbol}.L",
            #     "FRA": f"{symbol}.F",
            # }

            global_market_info = {}
            # market_dfs = {}  # Unused variable
            # Options Data:
            FMP_API_KEY = os.environ.get("FMP_API_KEY")
            selected_industry = ticker_info.get("industry", None)
            selected_market_cap = ticker_info.get("marketCap", None)

            if not selected_industry:
                context["error"] = f"Industry information not available for {symbol}."
                return render(request, "investing/oversold.html", context)

            if not selected_market_cap:
                context["error"] = (
                    f"Market capitalization information not available for {symbol}."
                )
                return render(request, "investing/oversold.html", context)

            # Define the exchanges
            exchanges = ["NYSE", "LSE", "FRA", "TSX"]
            exchange_params = "&".join(
                [f"exchange={exchange}" for exchange in exchanges]
            )

            # Fetch companies from the specified exchanges
            fmp_url = f"https://financialmodelingprep.com/api/v3/stock-screener?{exchange_params}&limit=1000&apikey={FMP_API_KEY}"
            response = requests.get(fmp_url)
            if response.status_code == 200:
                companies_list = response.json()
                available_industries = set(
                    company.get("industry")
                    for company in companies_list
                    if company.get("industry")
                )
            else:
                context["error"] = "Failed to fetch companies data."
                return render(request, "investing/oversold.html", context)

            # Construct the prompt for OpenAI
            prompt = f"""
            You are an AI assistant that helps match/find industries. Given a selected industry and a list of available industries in different exchanges, return a list of industries that are relevant or similar to the selected industry.
            

            Selected Industry: "{selected_industry}"

            Available Industries:
            {', '.join(available_industries)}

            Provide the list of matching industries give only 04 industories as a Python list of strings. Do not include any other text or quotes, just provide the list.
            """

            # Call the OpenAI API
            response = generate_chatbot_response(prompt)
            # print(f"OpenAI response: {response}")

            try:
                # Parse the response as a Python list
                matching_industries = ast.literal_eval(response)

                if not isinstance(matching_industries, list):
                    raise ValueError("Response is not a list.")
            except Exception as e:
                context["error"] = f"Error parsing OpenAI response: {e}"
                return render(request, "investing/oversold.html", context)

            if not matching_industries:
                context["error"] = (
                    f"No matching industries found for {selected_industry}."
                )
                return render(request, "investing/oversold.html", context)

            # Filter the companies_list using the matching industries
            companies = [
                company
                for company in companies_list
                if company.get("industry") in matching_industries
            ]
            companies = companies[:4]
            if not companies:
                context["error"] = "No companies found in the matching industries."
                return render(request, "investing/oversold.html", context)

            # Proceed with filtering companies
            top_symbols_data = []
            markets_seen = set()
            for company in companies:
                try:
                    company_symbol = company.get("symbol")
                    company_market_cap = company.get("marketCap")
                    company_exchange = company.get("exchangeShortName")
                    print(company_exchange)
                    # Skip if same symbol
                    if company_symbol == symbol:
                        continue

                    try:
                        company_market_cap = float(company_market_cap)
                    except (TypeError, ValueError):
                        continue
                    company_ticker = yf.Ticker(company_symbol)
                    company_hist_data = company_ticker.history(period="6mo")
                    if company_hist_data.empty:
                        continue
                    company_hist_data.reset_index(inplace=True)
                    chart_data = {
                        "dates": company_hist_data["Date"]
                        .dt.strftime("%Y-%m-%d")
                        .tolist(),
                        "prices": company_hist_data["Close"].round(2).tolist(),
                    }
                    top_symbols_data.append(
                        {
                            "symbol": company_symbol,
                            "market": company_exchange,
                            "marketCap": company_market_cap,
                            "chart_data": chart_data,
                            "company_name": company.get("companyName", company_symbol),
                        }
                    )
                    markets_seen.add(company_exchange)

                    # Limit to top 3 symbols
                    if len(markets_seen) >= 3:
                        break

                except Exception as e:
                    print(f"Error fetching data for {company_symbol}: {e}")
                    continue

            print("Top symbols data:", top_symbols_data)
            if not top_symbols_data:
                context["error"] = (
                    "No top symbols found in the same industry with larger market cap."
                )
                # return render(request, "investing/oversold.html", context)

            options_dates = ticker.options  # List of expiration dates
            today = datetime.date.today()
            next_month = (
                (today.replace(day=28) + datetime.timedelta(days=4))
                .replace(day=1)
                .month
            )

            # Filter options_dates to only include dates in the next month
            next_month_options_dates = [
                date_str
                for date_str in options_dates
                if datetime.datetime.strptime(date_str, "%Y-%m-%d").date().month
                == next_month
            ]

            # Fetch options chain for next month's dates
            options_data = []
            for date in next_month_options_dates:
                try:
                    opt = ticker.option_chain(date)
                    calls = opt.calls.copy()
                    puts = opt.puts.copy()

                    # Add 'type' field to distinguish calls and puts
                    calls["type"] = "Call"
                    puts["type"] = "Put"

                    # Add 'expirationDate' field
                    calls["expirationDate"] = date
                    puts["expirationDate"] = date

                    # Append to options_data
                    options_data.append(calls)
                    options_data.append(puts)
                except Exception as e:
                    print(f"Error fetching options for {date}: {e}")

            if options_data:
                # Concatenate all options dataframes
                options_df = pd.concat(options_data, ignore_index=True)

                # Adjust implied volatility
                options_df["impliedVolatility"] = options_df["impliedVolatility"] * 100

                # Apply Open Interest filter (>100)
                options_df = options_df[options_df["openInterest"] > 100]

                # **Sort options by open interest (highest to lowest)**
                options_df = options_df.sort_values(by="openInterest", ascending=False)

                # Handle filters from user input
                expiration_filter = request.GET.get("expirationDate")
                strike_filter = request.GET.get("strike")
                option_type_filter = request.GET.get("type")  # 'Call' or 'Put'

                if expiration_filter:
                    options_df = options_df[
                        options_df["expirationDate"] == expiration_filter
                    ]
                if strike_filter:
                    try:
                        strike_value = float(strike_filter)
                        options_df = options_df[options_df["strike"] == strike_value]
                    except ValueError:
                        pass  # Invalid strike filter
                if option_type_filter:
                    options_df = options_df[options_df["type"] == option_type_filter]

                # Convert options_df to dictionary for template
                options_list = options_df.to_dict(orient="records")

                # Paginate the options_list
                page = request.GET.get("page", 1)
                paginator = Paginator(options_list, 15)  # Show 15 options per page

                try:
                    options_page = paginator.page(page)
                except PageNotAnInteger:
                    options_page = paginator.page(1)
                except EmptyPage:
                    options_page = paginator.page(paginator.num_pages)
            else:
                options_page = None  # No options data

            # Sliding window logic for pagination display
            if options_page:
                index = options_page.number - 1
                max_index = len(paginator.page_range)
                start_index = index - 2 if index >= 2 else 0
                end_index = index + 3 if index <= max_index - 3 else max_index

                page_range = list(paginator.page_range)[start_index:end_index]

                # Add first and last pages with ellipsis
                if start_index > 0:
                    page_range.insert(0, 1)
                    if start_index > 1:  # Add ellipsis
                        page_range.insert(1, "...")
                if end_index < max_index:
                    if end_index < max_index - 1:  # Add ellipsis
                        page_range.append("...")
                    page_range.append(max_index)
            else:
                page_range = []
                # options_dates = ticker.options  # List of expiration dates
            options_dates = ticker.options  # List of expiration dates
            today = datetime.date.today()
            next_month = (
                (today.replace(day=28) + datetime.timedelta(days=4))
                .replace(day=1)
                .month
            )

            new_options = False
            upcoming_options = []

            for date_str in options_dates:
                date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                if date_obj.month == next_month:
                    new_options = True
                    upcoming_options.append(date_str)
            # Prepare a message if new options are detected
            if new_options:
                options_message = f"Options expiration date(s) for next month: {', '.join(upcoming_options)}"
            else:
                options_message = "No options available for next month."

            # Prepare a message if new options are detected
            if new_options:
                options_message = f"New options expiration date(s) available: {', '.join(upcoming_options)}"
            else:
                options_message = ""
            context.update(
                {
                    "ticker_data": ticker_measures,
                    "title": f"Fetched Financial Data (Yahoo) - {symbol}",
                    "symbol_info": {
                        "symbol": symbol,
                        "trend": trend,
                        "rsi": rsi,
                        "status": stock_status,
                        "percentage": percentage,
                    },
                    "global_market_info": global_market_info,
                    "chart_data": chart_data,
                    "top_symbols_data": top_symbols_data,
                    "openai_recommendation": openai_recommendation,
                    "tony_zac_signal": tony_zac_signal,
                    "coda_signal": coda_signal,
                    "options_page": options_page,
                    "options_dates": options_dates,
                    "new_options": new_options,
                    "options_message": options_message,
                    "page_obj": options_page,
                    "page_range": page_range,
                }
            )

        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            context["error"] = (
                f"Could not retrieve data for {symbol}. Please try again later."
            )

    return render(request, "investing/oversold.html", context)


def list_investment_strategies(request):
    investment_strategies = InvestmentsStrategy.objects.all()
    return render(
        request,
        "investing/investstrategies.html",
        {"investment_strategies": investment_strategies},
    )


def create_investment_strategies(request):
    if request.method == "POST":
        form = InvestmentsStrategyForm(request.POST)
        if form.is_valid:
            form.save()
            return redirect("investing:investstrategy")
    else:
        form = InvestmentsStrategyForm()
        return render(request, "investing/investment_form.html", {"form": form})


def update_investment_strategies(request, pk):
    investment_strategy = get_object_or_404(InvestmentsStrategy, pk=pk)
    if request.method == "POST":
        form = InvestmentsStrategyForm(request.POST, instance=investment_strategy)
        if form.is_valid:
            form.save()
            return redirect("investstrategy")
    else:
        form = InvestmentsStrategyForm(instance=investment_strategy)
        return render(request, "investing/investment_form.html", {"form": form})


def delete_investment_strategy(request, pk):
    investment_strategy = get_object_or_404(InvestmentsStrategy, pk=pk)
    if request.strategy == "POST":
        investment_strategy.delete()
        return redirect("investing:investstrategy")
    return render(request, "", {"investment_strategy": delete_investment_strategy})


class IndividualInvestmentListView(LoginRequiredMixin, ListView):
    """View for listing individual investments"""

    model = Investor_Information
    template_name = "investing/individual_investments.html"
    context_object_name = "investments"
    paginate_by = 10

    def get_queryset(self):
        # Only show investments for the current user
        return Investor_Information.objects.filter(investor=self.request.user).order_by(
            "-investment_date"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Calculate summary statistics
        investments = self.get_queryset()
        context["total_invested"] = investments.aggregate(total=Sum("amount_invested"))[
            "total"
        ] or Decimal("0.00")

        context["total_current_value"] = investments.aggregate(
            total=Sum("current_value")
        )["total"] or Decimal("0.00")

        context["total_returns_paid"] = investments.aggregate(
            total=Sum("total_returns_paid")
        )["total"] or Decimal("0.00")

        # Calculate overall return percentage
        if context["total_invested"] > 0:
            context["overall_return_percentage"] = (
                (context["total_current_value"] - context["total_invested"])
                / context["total_invested"]
                * 100
            )
        else:
            context["overall_return_percentage"] = 0

        return context


class IndividualInvestmentDetailView(LoginRequiredMixin, DetailView):
    """Detailed view of an individual investment"""

    model = Investor_Information
    template_name = "investing/individual_investment_detail.html"
    context_object_name = "investment"

    def get_queryset(self):
        return Investor_Information.objects.filter(investor=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        investment = self.object

        # Note: Investor_Information model doesn't have separate performance records, reports, milestones, or upgrade offers
        # These features would need to be implemented separately if needed

        # Set empty context for template compatibility
        context["performance_records"] = []
        context["recent_reports"] = []
        context["milestones"] = []
        context["upgrade_offers"] = []

        # Use model's direct fields for performance metrics
        context["latest_return_percentage"] = investment.actual_return_rate
        context["latest_period_return"] = investment.total_returns_paid

        return context


@login_required
def create_individual_investment(request):
    """Create a new individual investment"""
    if request.method == "POST":
        # Extract and validate form data
        amount_invested_str = request.POST.get("amount_invested")
        if not amount_invested_str:
            messages.error(request, "Investment amount is required.")
            return render(request, "investing/create_individual_investment.html")

        try:
            amount_invested = Decimal(amount_invested_str)
        except (ValueError, TypeError, DecimalException):
            messages.error(
                request, "Invalid investment amount. Please enter a valid number."
            )
            return render(request, "investing/create_individual_investment.html")

        investment_type = request.POST.get("investment_type")
        expected_return_rate_str = request.POST.get("expected_return_rate", "8.00")
        try:
            expected_return_rate = (
                Decimal(expected_return_rate_str)
                if expected_return_rate_str
                else Decimal("8.00")
            )
        except (ValueError, TypeError, DecimalException):
            expected_return_rate = Decimal("8.00")

        investment_purpose = request.POST.get("investment_purpose", "")
        maturity_months_str = request.POST.get("maturity_months", "12")
        try:
            maturity_months = int(maturity_months_str) if maturity_months_str else 12
        except (ValueError, TypeError):
            maturity_months = 12

        # Validate required fields
        if not investment_type:
            messages.error(request, "Investment type is required.")
            return render(request, "investing/create_individual_investment.html")

        # Calculate maturity date
        maturity_date = date.today() + timedelta(days=maturity_months * 30)

        try:
            print(
                f"🔍 DEBUG: Attempting to create investment with amount: {amount_invested}"
            )
            # Create investment
            investment = Investor_Information.objects.create(
                investor=request.user,
                amount_invested=amount_invested,
                investment_type=investment_type,
                expected_return_rate=expected_return_rate,
                investment_purpose=investment_purpose,
                maturity_date=maturity_date,
                current_value=amount_invested,  # Start with initial amount
                contract_signed=True,
                contract_signed_date=date.today(),
            )
            print(f"✅ DEBUG: Investment created successfully with ID: {investment.pk}")
        except Exception as e:
            print(f"❌ DEBUG: Failed to create investment: {e}")
            messages.error(request, f"Error creating investment: {str(e)}")
            return render(request, "investing/create_individual_investment.html")

        # Note: Investor_Information model doesn't have separate performance records
        # Performance tracking is handled through the model's fields directly

        try:
            # Send welcome email
            send_investment_welcome_email(investment)
        except Exception:
            # Don't fail the whole process for this - email is not critical
            messages.warning(
                request,
                "Investment created successfully, but welcome email could not be sent.",
            )

        print("🎉 DEBUG: Investment creation completed successfully!")
        messages.success(
            request,
            f"Investment of ${amount_invested} created successfully! "
            f"You will receive monthly reports and updates.",
        )

        print(
            f"🔍 DEBUG: About to redirect to individual_investment_detail with pk: {investment.pk}"
        )
        try:
            redirect_url = redirect(
                "investing:individual_investment_detail", pk=investment.pk
            )
            print(f"✅ DEBUG: Redirect object created successfully: {redirect_url}")
            return redirect_url
        except Exception as e:
            print(f"❌ DEBUG: Redirect failed: {e}")
            messages.error(request, f"Investment created but redirect failed: {str(e)}")
            return render(request, "investing/create_individual_investment.html")

    # GET request - show form
    return render(request, "investing/create_individual_investment.html")


@login_required
def update_investment_performance(request, investment_id):
    """Update investment performance (admin function)"""
    investment = get_object_or_404(Investor_Information, id=investment_id)

    if request.method == "POST":
        # Extract performance data
        new_value = Decimal(request.POST.get("current_value"))
        # revenue = Decimal(request.POST.get("revenue_generated", "0.00"))  # Unused variable
        # expenses = Decimal(request.POST.get("expenses_incurred", "0.00"))  # Unused variable
        key_achievements = request.POST.get("key_achievements", "")
        # challenges = request.POST.get("challenges_faced", "")  # Unused variable
        # next_goals = request.POST.get("next_period_goals", "")  # Unused variable

        # Update Investor_Information model directly
        previous_value = investment.current_value

        # Calculate period return
        period_return = new_value - previous_value
        period_return_percentage = (
            (period_return / previous_value * 100) if previous_value > 0 else 0
        )

        # Update investment fields directly
        investment.current_value = new_value
        investment.actual_return_rate = period_return_percentage
        investment.total_returns_paid += period_return
        investment.notes = f"Updated on {date.today()}: {key_achievements}"
        investment.save()

        # Note: Monthly reports and upgrade opportunities would need separate implementation
        # for Investor_Information model

        messages.success(request, "Investment performance updated successfully!")
        return redirect("investing:individual_investment_detail", pk=investment.pk)

    return render(
        request,
        "investing/update_investment_performance.html",
        {"investment": investment},
    )


def send_investment_welcome_email(investment):
    """Send welcome email to new investor"""
    subject = (
        f"Welcome to CODA Investment Program - ${investment.amount_invested} Investment"
    )

    context = {
        "investment": investment,
        "investor": investment.investor,
    }

    html_message = render_to_string("investing/emails/investment_welcome.html", context)

    send_mail(
        subject=subject,
        message=f"Welcome to CODA Investment Program! Your ${investment.amount_invested} investment is now active.",
        from_email="investments@codanalytics.net",
        recipient_list=[investment.investor.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_monthly_investment_report(investment):
    """Send monthly investment report to investor"""
    # Get latest performance record
    latest_performance = investment.performance_records.first()
    if not latest_performance:
        return

    subject = f"CODA Investment Report - {latest_performance.performance_date.strftime('%B %Y')}"

    context = {
        "investment": investment,
        "performance": latest_performance,
        "investor": investment.investor,
    }

    html_message = render_to_string(
        "investing/emails/monthly_investment_report.html", context
    )

    # Create report record
    report = InvestmentReport.objects.create(
        investment=investment,
        report_type="monthly",
        period_start=latest_performance.period_start,
        period_end=latest_performance.period_end,
        subject=subject,
        content=html_message,
    )

    try:
        send_mail(
            subject=subject,
            message=f"Your monthly investment report is ready. Current value: ${investment.current_value}",
            from_email="reports@codanalytics.net",
            recipient_list=[investment.investor.email],
            html_message=html_message,
            fail_silently=False,
        )

        report.sent_date = timezone.now()
        report.delivery_status = "sent"
        report.save()

    except Exception:
        report.delivery_status = "failed"
        report.save()


def check_upgrade_opportunities(investment):
    """Check if investor is eligible for upgrade offers"""
    # Check if investment is performing well and investor could invest more
    if investment.current_return_percentage >= investment.expected_return_rate:

        # Check if investor hasn't received an upgrade offer recently
        recent_offers = investment.upgrade_offers.filter(
            created_at__gte=timezone.now() - timedelta(days=90)
        ).count()

        if recent_offers == 0:
            # Create upgrade offer based on investment amount
            if investment.amount_invested < Decimal("10000.00"):
                create_upgrade_offer(
                    investment,
                    "tier_upgrade",
                    minimum_additional=Decimal("5000.00"),
                    bonus_rate=Decimal("1.00"),
                )
            elif investment.amount_invested < Decimal("25000.00"):
                create_upgrade_offer(
                    investment,
                    "equity_bonus",
                    minimum_additional=Decimal("15000.00"),
                    bonus_equity=Decimal("0.50"),
                )


def create_upgrade_offer(
    investment, offer_type, minimum_additional, bonus_rate=None, bonus_equity=None
):
    """Create an upgrade offer for the investor"""
    offer_titles = {
        "tier_upgrade": f"Upgrade to Premium Tier - Additional ${minimum_additional}",
        "equity_bonus": f"Equity Bonus Offer - Additional ${minimum_additional}",
        "bonus_rate": f"Bonus Interest Rate - Additional ${minimum_additional}",
    }

    offer_descriptions = {
        "tier_upgrade": "Upgrade your investment to our Premium Tier with additional benefits and higher returns.",
        "equity_bonus": "Receive additional equity percentage in CODA with your increased investment.",
        "bonus_rate": "Get a bonus interest rate on your additional investment.",
    }

    InvestmentUpgradeOffer.objects.create(
        investment=investment,
        offer_type=offer_type,
        title=offer_titles.get(offer_type, "Special Upgrade Offer"),
        description=offer_descriptions.get(
            offer_type, "Special offer for valued investors."
        ),
        minimum_additional_investment=minimum_additional,
        bonus_rate=bonus_rate,
        bonus_equity=bonus_equity,
        valid_until=date.today() + timedelta(days=30),
    )


@login_required
def accept_upgrade_offer(request, offer_id):
    """Accept an upgrade offer"""
    offer = get_object_or_404(
        InvestmentUpgradeOffer, id=offer_id, investment__investor=request.user
    )

    if request.method == "POST":
        additional_amount = Decimal(request.POST.get("additional_amount"))

        if additional_amount >= offer.minimum_additional_investment:
            # Update the original investment
            investment = offer.investment
            investment.amount_invested += additional_amount
            investment.current_value += additional_amount

            # Apply bonus rate if applicable
            if offer.bonus_rate:
                investment.expected_return_rate += offer.bonus_rate

            investment.save()

            # Mark offer as accepted
            offer.investor_response = "accepted"
            offer.response_date = timezone.now()
            offer.save()

            # Send confirmation email
            send_upgrade_confirmation_email(investment, offer, additional_amount)

            messages.success(
                request,
                f"Upgrade accepted! Your investment is now ${investment.amount_invested}",
            )

            return redirect("investing:individual_investment_detail", pk=investment.pk)
        else:
            messages.error(
                request,
                f"Additional amount must be at least ${offer.minimum_additional_investment}",
            )

    return render(request, "investing/accept_upgrade_offer.html", {"offer": offer})


def send_upgrade_confirmation_email(investment, offer, additional_amount):
    """Send confirmation email for accepted upgrade"""
    subject = f"Investment Upgrade Confirmed - ${additional_amount} Added"

    context = {
        "investment": investment,
        "offer": offer,
        "additional_amount": additional_amount,
        "investor": investment.investor,
    }

    html_message = render_to_string(
        "investing/emails/upgrade_confirmation.html", context
    )

    send_mail(
        subject=subject,
        message=f"Your investment upgrade has been confirmed. Additional ${additional_amount} added.",
        from_email="upgrades@codanalytics.net",
        recipient_list=[investment.investor.email],
        html_message=html_message,
        fail_silently=False,
    )


@login_required
def investment_dashboard(request):
    """Dashboard view for all investor types using Investor_Information model"""
    from .models import Investor_Information, ManagedTradingAccount
    from decimal import Decimal
    from django.db.models import Count, Q
    from django.utils import timezone

    # Get user's investments from Investor_Information model (System 1: Invest IN CODA)
    investments = Investor_Information.objects.filter(investor=request.user).order_by(
        "-created_at"
    )

    # Calculate summary statistics for equity investments
    total_invested = sum(inv.amount_invested for inv in investments)
    total_current_value = sum(inv.current_value for inv in investments)
    total_returns_paid = sum(inv.total_returns_paid for inv in investments)

    # Calculate overall return percentage
    if total_invested > 0:
        overall_return_percentage = (total_returns_paid / total_invested) * 100
    else:
        overall_return_percentage = Decimal("0.00")

    # Get active investments count
    active_investments = investments.filter(status="active").count()

    # Get recent milestones (temporarily disabled until data exists)
    recent_milestones = []
    
    # NEW: Get managed trading accounts (System 2: CODA Manages Client Money)
    from .models import ManagedTradingApplication, PositionBatch
    
    managed_accounts = ManagedTradingAccount.objects.filter(
        client=request.user
    ).annotate(
        open_positions_count=Count('positions', filter=Q(positions__status='open'))
    )
    
    # Calculate managed trading summary
    has_managed_accounts = managed_accounts.exists()
    managed_accounts_count = managed_accounts.count()
    managed_total_balance = sum([acc.current_balance for acc in managed_accounts])
    managed_total_pnl = sum([acc.total_profit_loss for acc in managed_accounts])
    
    # Get pending applications
    applications = ManagedTradingApplication.objects.filter(
        user=request.user
    ).order_by('-applied_date')
    has_application = applications.exists()
    
    # Get pending batches (URGENT - needs approval)
    now = timezone.now()
    pending_batches = PositionBatch.objects.filter(
        managed_account__client=request.user,
        status='pending',
        approval_deadline__gt=now
    ).order_by('approval_deadline')

    expired_batches = PositionBatch.objects.filter(
        managed_account__client=request.user,
        status='pending',
        approval_deadline__lte=now
    ).order_by('-approval_deadline')

    context = {
        # Equity investments (System 1)
        "investments": investments,
        "total_invested": total_invested,
        "total_current_value": total_current_value,
        "total_returns_paid": total_returns_paid,
        "overall_return_percentage": overall_return_percentage,
        "active_investments": active_investments,
        "recent_milestones": recent_milestones,
        "recent_performance": [],
        "active_offers": [],
        "user_type": "individual",
        
        # Managed trading (System 2) - NEW
        "has_managed_accounts": has_managed_accounts,
        "managed_accounts": managed_accounts,
        "managed_accounts_count": managed_accounts_count,
        "managed_total_balance": managed_total_balance,
        "managed_total_pnl": managed_total_pnl,
        "has_application": has_application,
        "applications": applications,
        "pending_batches": pending_batches,
        "expired_batches": expired_batches,
    }

    return render(request, "investing/investment_dashboard.html", context)


@login_required
def apply_for_investment(request):
    """Unified investment application view for all investor types"""
    from .services import InvestmentService

    if request.method == "POST":
        investment_service = InvestmentService()

        # Extract and validate form data
        investment_data = {
            "investment_plan": request.POST.get("investment_plan"),
            "duration": request.POST.get("duration"),
            "investment_purpose": request.POST.get("investment_purpose", ""),
            "model_type": request.POST.get("model_type", "Installment"),
        }

        # Convert amount_invested to Decimal
        amount_str = request.POST.get("amount_invested")
        if amount_str:
            try:
                investment_data["amount_invested"] = Decimal(amount_str)
            except (ValueError, TypeError, DecimalException):
                messages.error(
                    request, "Invalid investment amount. Please enter a valid number."
                )
                return redirect("investing:apply_for_investment")

        # Convert revenue_share_percentage to Decimal
        revenue_str = request.POST.get("revenue_share_percentage")
        if revenue_str:
            try:
                investment_data["revenue_share_percentage"] = Decimal(revenue_str)
            except (ValueError, TypeError, DecimalException):
                # Use default if invalid
                investment_data["revenue_share_percentage"] = Decimal("8.00")

        # Create investment using service
        result = investment_service.create_investment(request.user, investment_data)

        if result["status"] == "success":
            messages.success(
                request, "Your investment application has been submitted successfully!"
            )
            return redirect("investing:investment_dashboard")
        else:
            error_message = result.get(
                "message",
                result.get(
                    "error",
                    "An error occurred while processing your investment application.",
                ),
            )
            messages.error(request, error_message)

    # GET request - show form
    investment_service = InvestmentService()
    plans_result = investment_service.get_investment_plans_for_user(request.user)

    if plans_result["status"] == "success":
        investment_plans = plans_result["plans"]
        investor_type = plans_result["investor_type"]
    else:
        investment_plans = []
        investor_type = "individual"

    context = {
        "investment_plans": investment_plans,
        "investor_type": investor_type,
        "user": request.user,
    }

    return render(request, "investing/apply_for_investment.html", context)


def investment_analytics_api(request):
    """API endpoint for investment analytics data"""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    investments = Investor_Information.objects.filter(investor=request.user)

    # Performance over time (simplified for Investor_Information model)
    performance_data = []
    for investment in investments:
        performance_data.append(
            {
                "date": investment.investment_date.strftime("%Y-%m"),
                "value": float(investment.current_value),
                "return_percentage": float(investment.actual_return_rate),
                "investment_id": investment.id,
            }
        )

    # Summary statistics
    summary = {
        "total_invested": float(
            investments.aggregate(total=Sum("amount_invested"))["total"] or 0
        ),
        "total_current_value": float(
            investments.aggregate(total=Sum("current_value"))["total"] or 0
        ),
        "total_returns_paid": float(
            investments.aggregate(total=Sum("total_returns_paid"))["total"] or 0
        ),
        "active_investments": investments.filter(status="active").count(),
        "completed_investments": investments.filter(status="completed").count(),
    }

    return JsonResponse({"performance_data": performance_data, "summary": summary})
