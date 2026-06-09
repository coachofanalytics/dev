import os
import json
import logging
try:
    import paypalrestsdk
except ImportError:
    paypalrestsdk = None
try:
    import stripe
except ImportError:
    stripe = None
from datetime import datetime

import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.db.models import Sum
from django.http import QueryDict, Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.utils.decorators import method_decorator
from decimal import Decimal,  ROUND_HALF_UP

from django.views.decorators.csrf import csrf_exempt
from mail.custom_email import send_email
from datetime import datetime
from django.utils.timezone import now as tz_now


from accounts.forms import UserForm
from accounts.models import CustomerUser, Membership
from .forms import BudgetForm, DepartmentFilterForm, InflowForm, PaymentForm
from .models import (
    Budget,
    CodaBudget,
    Payment_Information,
    Payment_History,
    Default_Payment_Fees,
    Transaction,
    Payment,
    Pricing,
    Opportunity,
    NewsLetterSubscriber,
)
from .forms import OpportunityForm
from .utils import get_exchange_rate
from main.utils import path_values
from django.contrib.admin.views.decorators import staff_member_required
from django.core.cache import cache
from django.core.mail import send_mail
from django.http import JsonResponse
import uuid


# Initialize Logger
logger = logging.getLogger(__name__)


# Payment and time details
def payment_details():
    phone_number = "123456789"
    email_info = "example@example.com"
    cashapp = "cashapp_tag"
    venmo = "venmo_tag"
    account_no = "account_number"
    return phone_number, email_info, cashapp, venmo, account_no


# ===================== FINANCE REPORT =====================
def finance_report(request):
    return render(request, "finance/reports/finance.html", {"title": "Finance"})


# ===================== SOLUTIONS PAGE =====================
def solutions(request):
    """Display detailed banking and investment solutions"""
    return render(request, "finance/solutions.html", {"title": "Solutions"})


# ===================== CONTRACT FORM SUBMISSION =====================
def contract_form_submission(request):
    try:
        if request.method == "POST":
            user_student_data = request.POST.get("usr_data")
            if not user_student_data:
                raise ValueError("Missing form data")

            student_dict_data = QueryDict(user_student_data)
            username = student_dict_data.get("username")

            # Retrieve customer and payment info
            customer = CustomerUser.objects.filter(username=username).first()
            payment = Payment_Information.objects.filter(
                customer_id=request.user.id
            ).first()

            # Handle new user form
            if not payment:
                form = UserForm(student_dict_data)
                if form.is_valid():
                    category = form.cleaned_data.get("category")
                    form.instance.is_applicant = category == 1
                    form.instance.is_staff = category == 2
                    form.instance.is_client = category == 3
                    form.instance.is_admin = category == 4
                    form.save()

            # Payment details
            payment_fees = int(request.POST.get("duration", 0)) * 1000
            down_payment = int(request.POST.get("down_payment", 0))
            student_bonus_amount = int(request.POST.get("bonus", 0))
            fee_balance = payment_fees - down_payment
            if request.POST.get("student_contract"):
                fee_balance -= student_bonus_amount

            # Save payment info
            payment_data = {
                "payment_fees": payment_fees,
                "down_payment": down_payment,
                "student_bonus": student_bonus_amount,
                "fee_balance": fee_balance,
                "plan": request.POST.get("duration"),
                "payment_method": request.POST.get("payment_type"),
                "client_signature": request.POST.get("client_sign"),
                "company_rep": request.POST.get("rep_name"),
                "client_date": request.POST.get("client_date"),
                "rep_date": request.POST.get("rep_date"),
            }

            if payment:
                Payment_Information.objects.filter(customer_id=customer.id).update(
                    **payment_data
                )
            else:
                Payment_Information.objects.create(
                    customer_id=customer.id, **payment_data
                )

            # Save payment history
            Payment_History.objects.create(customer=customer, **payment_data)

            messages.success(request, f"Added New Contract for {username}!")
            return redirect("finance:pay")

        # Render GET request
        return render(request, "finance/contract_form.html")

    except ValueError as ve:
        logger.error(f"Validation error in contract_form_submission: {ve}")
        messages.error(request, str(ve))
        return redirect("finance:contract_form")
    except Exception as e:
        logger.exception(f"Unexpected error in contract_form_submission: {e}")
        message = f"Hi {request.user}, there is an issue on our end. Kindly contact us directly at info@codanalytics.net."
        context = {"title": "CONTRACT", "message": message, "error_details": str(e)}
        return render(request, "main/errors/generalerrors.html", context)


# ===================== PAYMENTS =====================

@login_required
def pay(request, service=None):
    if not request.user.is_authenticated:
        return redirect(reverse("accounts:account-login"))

    user = request.user
    print(user)
    membership = get_object_or_404(Membership, member=user)
    fee_usd = membership.fee

    fee_kes = fee_usd * get_exchange_rate("USD", "KES")
    print(fee_kes)

    context = {
        "title": "PAYMENT",
        "membership": membership,
        "fee_kes": fee_kes,
        "user": request.user,
        "message": f"Hi {request.user}, you are yet to sign the contract with us. Kindly contact us at info@codanalytics.net.",
    }
    return render(request, "finance/payments/pay.html", context)

class PaymentCreateView(CreateView):
    model = Payment_Information
    fields = ["customer_id", "down_payment", "payment_method"]
    template_name = "finance/payments/payment_form.html"
    success_url = "/finance/pay/"


from django.shortcuts import get_object_or_404


@login_required
def mycontract(request, username):
    User = get_user_model()
    user = get_object_or_404(User, username=username)

    # Fetch contract details for the user
    contract = Payment_Information.objects.filter(customer_id=user.id).first()

    context = {
        "title": f"Contract for {user.username}",
        "contract": contract,
    }
    return render(request, "finance/contracts/mycontract.html", context)


from django.contrib.auth.decorators import login_required


@login_required
def another_view(request, method):
    context = {
        "title": f"Payment Method: {method}",
        "method": method,
    }
    return render(request, "finance/payments/another_view.html", context)


from django.contrib.auth.decorators import login_required
from .models import Payment_Information


@login_required
def payments(request):
    # Fetch payment information for the logged-in user
    payment_info = Payment_Information.objects.filter(
        customer_id=request.user.id
    ).last()

    context = {
        "title": "Payments",
        "payments": payment_info,
    }
    return render(request, "finance/payments/payments.html", context)


# def pay(request, service=None):
#     if not request.user.is_authenticated:
#         return redirect(reverse('accounts:account-login'))
#     payment_info = Payment_Information.objects.filter(customer_id=request.user).last()


#     context = {
#             "title": "PAYMENT",
#             "payments": payment_info,
#             "rate": rate,
#             'user': request.user,

#             "message": f"Hi {request.user}, you are yet to sign the contract with us. Kindly contact us at info@codanalytics.net.",

#             # "service": True,
#         }
#     return render(request, "finance/payments/pay.html", context)


def paymentComplete(request):
    if request.method == "POST":
        user = request.user
        membership = Membership.objects.get(member=user)

        # Get the amount entered by the user
        entered_amount = request.POST.get("amount")
        if entered_amount:
            try:
                # Update the membership fee with the new amount
                membership.fee = float(entered_amount)
                membership.save()
                # Redirect to payment gateway or success page
                return redirect("finance:payment_complete")
            except ValueError:
                # Handle invalid input
                return redirect(
                    "finance:payment_page"
                )  # Redirect back to payment page with error

    return redirect("payment_page")


def process_payment(request):
    if request.method == "POST":
        user = request.user
        membership = Membership.objects.get(member=user)

        # Get the amount entered by the user
        entered_amount = request.POST.get("amount")
        if entered_amount:
            try:
                # Update the membership fee with the new amount
                membership.fee = float(entered_amount)
                membership.status = "PAID"  # Update the payment status if applicable
                membership.save()
                return redirect("finance:payment_success")  # Redirect to success page
            except ValueError:
                # Handle invalid input
                return redirect(
                    "finance:payment_page"
                )  # Redirect back to payment page with error

    return redirect("finance:pay")

def payment_success(request):
    return render(request, "finance/payments/payment_success.html")


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


# For payment purposes
class PaymentInformationUpdateView(UpdateView):
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
        #     return True
        # elif self.request.user == task.employee:
        if self.request.user:
            return True


# ----------------------CASH OUTFLOW CLASS-BASED VIEWS--------------------------------
@login_required
def transact(request):
    if request.method == "POST":
        form = InflowForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            instance = form.save(commit=False)
            instance.sender = request.user
            instance.save()
            return redirect("/finance/transaction/")
    else:
        form = InflowForm()
    return render(request, "finance/payments/transact.html", {"form": form})


class TransactionListView(ListView):
    model = Transaction
    template_name = "finance/payments/transactions.html"
    context_object_name = "transactions"
    # ordering=['-transaction_date']


@method_decorator(login_required, name="dispatch")
class TransanctionDetailView(DetailView):
    template_name = "finance/payments/transaction_detail.html"
    model = Transaction
    ordering = ["-transaction_date"]


class TransactionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Transaction
    # success_url="/finance/transaction"
    fields = [
        "sender",
        "receiver",
        "phone",
        "sender_phone",
        "department",
        "category",
        "type",
        "payment_method",
        "qty",
        "amount",
        "transaction_cost",
        "description",
        "receipt_link",
    ]

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("finance:transaction-list")

    def test_func(self):
        inflow = self.get_object()
        if self.request.user == inflow.sender:
            return True
        elif self.request.user.is_admin or self.request.user.is_superuser:
            return True
        return False


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

    # Fetch budgets for the company
    company_budgets = Budget.objects.all()

    # Calculate total budgets
    total_budget = sum(site.amount for site in company_budgets)

    # Construct link URL
    # link_url = reverse('finance:site_budget_with_subcategory', kwargs={'company_slug': company_slug, 'category': 'Web', 'subcategory': 'all'})

    # Prepare summary data
    summary = [
        {"title": "Total Budget", "value": total_budget, "link": ""},
    ]

    context = {
        "budget_obj": company_budgets,
        "data": summary,
    }
    return render(request, "finance/budgets/budget.html", context)


def filter_transactions_by_duration_and_department(duration, department_name=None):
    """
    Filters transactions based on the given duration and optionally by department name.
    """
    if duration > 12:
        year = duration - 1
        if department_name:
            return CodaBudget.objects.filter(
                department__name=department_name, created_at__year=str(year)
            ).order_by("category")
        else:
            return CodaBudget.objects.filter(created_at__year=str(year)).order_by(
                "category"
            )
    else:
        month = duration - 1
        year = 2024
        if department_name:
            # return CodaBudget.objects.filter(department__name=department_name, created_at__month=str(month)).order_by('category')
            return CodaBudget.objects.filter(
                department__name=department_name,
                created_at__year=str(year),
                created_at__month=str(month),
            ).order_by("category")
        else:
            return CodaBudget.objects.filter(
                created_at__year=str(year), created_at__month=str(month)
            ).order_by("category")


def budget_projection(request, subtitle="summary", duration=2024):
    path_list, sub_title, pre_sub_title = path_values(request)
    subtitle = path_list[2]
    # departments = Department.objects.all()
    # categories = BudgetCategory.objects.all()

    # Validate and convert duration to an integer
    try:
        duration = int(duration)
    except ValueError:
        raise Http404("Invalid duration value")

    total = 0
    budget_items = []

    if request.method == "POST":
        form = DepartmentFilterForm(request.POST)
        if form.is_valid():
            department_name = form.cleaned_data.get("name")
            if department_name:
                budget_items = filter_transactions_by_duration_and_department(
                    duration, department_name
                )
            else:
                budget_items = filter_transactions_by_duration_and_department(duration)
            total = sum(item.amount * item.qty for item in budget_items)
    else:
        form = DepartmentFilterForm()
        budget_items = filter_transactions_by_duration_and_department(duration)
        total = sum(item.amount * item.qty for item in budget_items)

    # Aggregate data by month and category
    budget_summary = budget_items.values(
        "category__name", "subcategory__name"
    ).annotate(total_qty=Sum("qty"), total_amount=Sum("unit_price"))
    # Create a list of unique categories
    available_categories = budget_summary.values_list(
        "category__name", flat=True
    ).distinct()

    budget_months = list(range(1, 13))  # Months 1-12
    budget_years = [2024]  # Add relevant years
    rate = 1.0  # Exchange rate or conversion factor

    context = {
        # "departments": departments,
        "categories": available_categories,
        "summary": budget_summary,
        "budget_items": budget_items,
        "budget_months": budget_months,
        "budget_years": budget_years,
        "total_amt_ksh": total,
        "total_amt": total / rate if total else 0,
    }
    if subtitle == "detailed":
        return render(request, "finance/budgets/detailed_budget.html", context)
    else:
        return render(request, "finance/budgets/summary_budget.html", context)


# Including sending email
def payment_processing(request):
    url = "email/payment_confirm.html"
    user_category = "Ordinary"
    subject = "Payment Received"

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            # save in a JSON
            # we call the exchange rate API
            # we will also need to call send notification function to send an email
            # form.save()
            amount = form.cleaned_data["amount"]
            currency = form.cleaned_data["currency"]
            first_name = form.cleaned_data["first_name"]
            last_name = form.cleaned_data["last_name"]
            email = form.cleaned_data["email"]

            print(amount, currency, first_name, last_name, email)
            # we call the exchange rate API converting to USD
            exchange_rate = get_exchange_rate(currency, "USD")
            converted_amount_USD = amount / exchange_rate
            print(amount, exchange_rate, converted_amount_USD)

            # send_notification(request, email, first_name, last_name, amount)
            context = {
                "user_category": user_category,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "amount": amount,
                "subject": subject,
            }
            send_email(
                category=user_category,
                to_email=[email],
                subject=subject,
                html_template=url,
                context=context,
            )
            data = {
                "amount": str(amount),
                "currency": currency,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "exchange_rate": str(exchange_rate),
                "converted_amount_USD": str(converted_amount_USD),
            }
            file_path = os.path.join(settings.BASE_DIR, "payment_data.json")
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)

            # return HttpResponse("JSON file saved.")
            return redirect("main:layout")

    else:
        form = PaymentForm()

    # return render(request, "finance/online_payments.html", {"form": form})
    return render(request, "finance/online_payments_2.html", {"form": form})


@csrf_exempt
def paypal_checkout(request):
    if request.method == "GET":
        amount = request.GET.get("amount")
        purpose = request.GET.get('purpose')

        payment = paypalrestsdk.Payment(
            {
                "intent": "sale",
                "payer": {"payment_method": "paypal"},
                "redirect_urls": {
                    "return_url": request.build_absolute_uri("/finance/paypal/return/"),
                    "cancel_url": request.build_absolute_uri("/finance/paypal/cancel/"),
                },
                "transactions": [
                    {
                        "item_list": {
                            "items": [
                                {
                                    "name": purpose,
                                    "sku": "DC48K",
                                    "price": amount,
                                    "currency": "USD",
                                    "quantity": 1,
                                }
                            ]
                        },
                        "amount": {"total": amount, "currency": "USD"},
                        "description": purpose,
                    }
                ],
            }
        )

        if payment.create():
            for link in payment.links:
                if link.method == "REDIRECT":
                    return redirect(link.href)
        else:
            return render(
                request, "finance/payment_failed.html", {"error": payment.error}
            )


# Save Paypal payment to DB
def paypal_return(request):
    payment_id = request.GET.get("paymentId")
    payer_id = request.GET.get("PayerID")

    payment = paypalrestsdk.Payment.find(payment_id)

    if payment.execute({"payer_id": payer_id}):

        customer_email = payment.payer.payer_info.email
        existing_member = CustomerUser.objects.filter(email=customer_email).first()

        if existing_member:
            Payment.objects.create(
                user=CustomerUser.objects.filter(email=customer_email).first(),
                transaction_id=payment.id,
                amount=float(payment.transactions[0].amount.total),
                status=payment.state,
                payment_purpose=payment.transactions[0]["description"],
                payment_method = "paypal",
            )
        else:
            CustomerUser.objects.create(
                email=payment.payer.payer_info.email,
                first_name=payment.payer.payer_info.first_name,
                last_name=payment.payer.payer_info.last_name,
                city=payment.transactions[0]["item_list"]["shipping_address"]["city"],
                state=payment.transactions[0]["item_list"]["shipping_address"]["state"],
                country=payment.transactions[0]["item_list"]["shipping_address"]["country_code"],
                username=uuid.uuid4(),
            )
            # Save to DB
            Payment.objects.create(
                user=CustomerUser.objects.order_by("-id").first(),
                transaction_id=payment.id,
                amount=float(payment.transactions[0].amount.total),
                status=payment.state,
                payment_purpose=payment.transactions[0]["description"],
                payment_method = "paypal",
            )

        return render(request, "finance/payment_success.html")
    else:
        return render(request, "finance/payment_failed.html", {"error": payment.error})
    


if stripe:
    stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_checkout(request):
    if request.method != "GET":
        return HttpResponse(status=405)

    amount_str       = request.GET.get("amount", "0")
    purpose          = (request.GET.get("purpose") or "").strip()
    original_amount  = (request.GET.get("total_amount") or "").strip()  # optional cap for purpose
    source           = (request.GET.get("source") or "partial_payment").strip()

    try:
        amount = Decimal(amount_str)
    except Exception:
        amount = Decimal("0")

    if amount <= 0:
        return render(request, "finance/payment_failed.html", {"error": "Invalid amount"})

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(amount * 100),
                    "product_data": {"name": f"DC48K {purpose or 'Payment'}"},
                },
                "quantity": 1,
            }],
            success_url=request.build_absolute_uri(reverse("finance:stripe_success")),
            cancel_url=request.build_absolute_uri(reverse("finance:stripe_cancel")),
            customer_email=request.user.email if request.user.is_authenticated else None,
            metadata={
                "purpose": purpose,
                "original_amount": original_amount,  # the cap for this purpose (0/blank for uncapped e.g. donation)
                "source": source,
            },
        )
        return redirect(session.url)
    except Exception as e:
        return render(request, "finance/payment_failed.html", {"error": str(e)})
    


def stripe_payment_success(request):
    return render(request, "finance/payment_success.html")


def stripe_payment_cancel(request):
    return render(request, "finance/payment_failed.html")




# Stripe Webhook
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET 

def _to_2dp(value: Decimal) -> Decimal:
    return (value or Decimal("0")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _resolve_cap_for_purpose(user, purpose, md_cap: Decimal) -> Decimal:
    """
    Return the cap (original_amount) for this user+purpose.
    Priority: metadata cap if > 0; else last nonzero cap saved for that user+purpose; else 0.
    """
    if md_cap and md_cap > 0:
        return _to_2dp(md_cap)
    last_cap = (
        Payment.objects.filter(user_id=user, payment_purpose__icontains=purpose)
        .exclude(original_amount=0)
        .order_by("-created_at")
        .values_list("original_amount", flat=True)
        .first()
    )
    return _to_2dp(last_cap or Decimal("0"))

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except Exception:
        return HttpResponse(status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        # ---- Core values from session ----
        email = ((session.get("customer_details") or {}).get("email")) or ""
        amount_paid = _to_2dp(Decimal(session.get("amount_total", 0)) / 100)
        payment_intent_id = session.get("payment_intent")
        payment_status = (session.get("payment_status") or "").lower()  # 'paid' expected

        md = session.get("metadata") or {}
        purpose = (md.get("purpose") or "").strip()
        md_original_amount = _to_2dp(Decimal(md.get("original_amount") or "0"))
        source = (md.get("source") or "").strip()

        # ---- Expand for method details + receipt url ----
        card_brand, card_last4, receipt_url = "", "", None
        try:
            if payment_intent_id:
                pi = stripe.PaymentIntent.retrieve(payment_intent_id, expand=["payment_method", "charges"])
                pm = pi.get("payment_method")
                if pm and pm.get("type") == "card":
                    card = pm.get("card") or {}
                    card_brand = (card.get("brand") or "").title()
                    card_last4 = card.get("last4") or ""
                charges = (pi.get("charges") or {}).get("data") or []
                if charges:
                    receipt_url = charges[0].get("receipt_url")
        except Exception:
            pass

        # ---- Ensure user exists ----
        user = CustomerUser.objects.filter(email=email).first()
        if not user:
            name = ((session.get("customer_details") or {}).get("name") or "").strip()
            parts = name.split(" ", 1)
            first = parts[0] if parts else ""
            last  = parts[1] if len(parts) > 1 else ""
            username = (f"{first}_{last}".strip() or f"user_{int(tz_now().timestamp())}").lower()
            user = CustomerUser.objects.create(
                email=email,
                first_name=first,
                last_name=last,
                username=username,
                is_active=True,
            )

        # ---- Determine cap for this user+purpose ----
        cap_for_purpose = _resolve_cap_for_purpose(user, purpose, md_original_amount)  # may be 0 (uncapped)

        # ---- Upsert payment row (idempotent on transaction_id) ----
        payment_obj, created = Payment.objects.get_or_create(
            transaction_id=payment_intent_id,
            defaults={
                "user_id": user,
                "payment_purpose": purpose or "Payment",
                "amount": amount_paid,
                "original_amount": cap_for_purpose,  # store the cap reference we resolved
                "payment_method": "stripe",
                "status": "paid" if payment_status == "paid" else payment_status,
                "receipt_url": receipt_url,
            },
        )

        # If it existed (retry), make sure critical fields are up to date
        if not created:
            updated = False
            if payment_obj.status != ("paid" if payment_status == "paid" else payment_status):
                payment_obj.status = "paid" if payment_status == "paid" else payment_status
                updated = True
            if payment_obj.receipt_url != receipt_url and receipt_url:
                payment_obj.receipt_url = receipt_url
                updated = True
            if payment_obj.original_amount != cap_for_purpose:
                payment_obj.original_amount = cap_for_purpose
                updated = True
            if updated:
                payment_obj.save(update_fields=["status", "receipt_url", "original_amount", "updated_at"])

        # ---- Compute running balance for this user+purpose (independent payments) ----
        # If cap is 0 (uncapped e.g. donations), we set balance to 0.
        if cap_for_purpose > 0:
            total_paid_for_purpose = (
                Payment.objects.filter(
                    user_id=user,
                    payment_purpose__icontains=purpose,
                    status__in=["paid", "succeeded", "Completed", "Paid"],
                ).aggregate(total=Sum("amount"))["total"]
                or Decimal("0.00")
            )
            balance_now = _to_2dp(cap_for_purpose - _to_2dp(total_paid_for_purpose))
            if balance_now < 0:
                balance_now = Decimal("0.00")
        else:
            balance_now = Decimal("0.00")

        # Save balance on the *current* row
        if payment_obj.balance != balance_now:
            payment_obj.balance = balance_now
            payment_obj.save(update_fields=["balance", "updated_at"])

        # ---- Email receipt ----
        brand_last4 = f"{card_brand}-{card_last4}" if card_brand and card_last4 else "Card"
        context = {
            "amount_paid": amount_paid,
            "purpose": purpose or "Payment",
            "receipt_number": payment_obj.pk,  # you can switch to payment_obj.pk if desired
            "payment_method": brand_last4,
            "email": email,
            "date_paid": datetime.now().strftime("%B %d, %Y"),
            "subject": "Receipt from DC48K",
        }
        try:
            send_email(
                category="dc48k_payments",
                to_email=[email],
                subject=context["subject"],
                html_template="email/payment_receipt.html",
                context=context,
            )
        except Exception as e:
            # Don't fail webhook on email problems
            print(f"[Webhook] Email send failed: {e}")

    return HttpResponse(status=200)




def donation(request):
    return render(request, "finance/donation.html")



@login_required
def pay_online(request):
    global_executive = (Pricing.objects.filter(title="Global Executive").order_by("-id").first())
    regional_administration = (Pricing.objects.filter(title="Regional Administration").order_by("-id").first())
    county_assembly = (Pricing.objects.filter(title="County Assembly").order_by("-id").first())

    # Global Executive Committe --> title & price
    global_executive_title = global_executive.title
    global_executive_price = int(global_executive.price)
    global_executive_description = global_executive.description

    # Regional Administration --> title & price
    regional_administration_title = regional_administration.title
    regional_administration_price = int(regional_administration.price)
    regional_administration_description = regional_administration.description

    # County Assembly --> title & price
    county_assembly_title = county_assembly.title
    county_assembly_price = int(county_assembly.price)
    county_assembly_description = county_assembly.description

    print(global_executive_price, global_executive_title)

    context = {
        "global_executive_title": global_executive_title,
        "global_executive_price": global_executive_price,
        "global_executive_description": global_executive_description,
        "regional_administration_title": regional_administration_title,
        "regional_administration_price": regional_administration_price,
        "regional_administration_description": regional_administration_description,
        "county_assembly_title": county_assembly_title,
        "county_assembly_price": county_assembly_price,
        "county_assembly_description": county_assembly_description
    }

    return render(request, "finance/pay_online.html", context)



@login_required
def partial_payment(request):
    purpose = request.GET.get("purpose", "").strip()
    total_amount_str = request.GET.get("total_amount", "0").strip()

    try:
        total_amount = Decimal(total_amount_str)
    except Exception:
        total_amount = Decimal("0")

    # Sum prior successful payments for this user (optionally filtered by purpose)
    paid_qs = Payment.objects.filter(
        user_id=request.user,
        status__in=["succeeded", "Succeeded", "Completed", "paid", "Paid"]
    )
    # If you want to track per-membership/category, also filter by purpose:
    if purpose:
        paid_qs = paid_qs.filter(payment_purpose__icontains=purpose)

    amount_paid = paid_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    # Remaining balance cannot go below 0
    balance = total_amount - amount_paid
    if balance < 0:
        balance = Decimal("0")

    context = {
        "purpose": purpose,
        "total_amount": total_amount,
        "amount_paid": amount_paid,
        "balance": balance,
    }
    return render(request, "finance/partial_payment.html", context)


# ===================== FINANCIAL SERVICES HOMEPAGE =====================
def homepage(request):
    return render(request, "finance/homepage/homepage.html")


# ===================== SOLUTIONS PAGE =====================
def solutions(request):
    """Display detailed banking and investment solutions"""
    return render(request, "finance/solutions.html", {"title": "Solutions"})


# ===================== INVESTMENT DIRECTORY =====================
def finance_directory(request):
    opportunities = Opportunity.approved.all()
    count = opportunities.count()

    if request.method == 'POST':
        user_ip = request.META.get('REMOTE_ADDR')
        cache_key = f"limit_sub_{user_ip}"

        if cache.get(cache_key):
            messages.error(request, "Please wait a minute before submitting another opportunity.")
            return redirect('finance:directory')

        form = OpportunityForm(request.POST)
        if form.is_valid():
            opportunity = form.save(commit=False)

            # --- AUTOMATION: SPAM LOGIC ---
            banned_keywords = ['crypto', 'guaranteed', 'whatsapp me', 'bitcoin']
            content = (opportunity.description + " " + opportunity.title).lower()

            # Reset flag before check
            opportunity.is_suspicious = False

            if any(word in content for word in banned_keywords) or len(opportunity.description) < 20:
                opportunity.is_suspicious = True

            opportunity.status = 'PENDING'
            opportunity.save()

            cache.set(cache_key, True, 60)

            messages.success(request, "Thank you! Your submission is under review.")
            return redirect('finance:directory')
    else:
        form = OpportunityForm()

    return render(request, "finance/investment/directory.html", {
        'opportunities': opportunities,
        'count': count,
        'form': form
    })


# ===================== NEWSLETTER SUBSCRIPTION =====================
def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()

        if not email:
            return JsonResponse({'success': False, 'message': 'Email is required.'}, status=400)

        subscriber, created = NewsLetterSubscriber.objects.get_or_create(email=email)

        if not created and subscriber.is_verified:
            return JsonResponse({
                'success': False,
                'exists': True,
                'message': 'You are already a verified subscriber!'
            })

        verify_url = request.build_absolute_uri(
            reverse('finance:verify_email', args=[subscriber.id])
        )

        try:
            send_mail(
                "Verify your Subscription",
                f"Welcome! Please click the link below to verify your email and start receiving alerts:\n\n{verify_url}\n\nIf you didn't request this, you can safely ignore this email.",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return JsonResponse({
                'success': True,
                'exists': False,
                'message': 'Subscription pending. Please check your inbox to verify!'
            })
        except Exception as e:
            logger.error(f"SMTP Error: {e}")
            return JsonResponse({
                'success': False,
                'message': 'System is busy. We saved your email, but verification might be delayed.'
            })


def verify_email(request, subscriber_id):
    subscriber = get_object_or_404(NewsLetterSubscriber, id=subscriber_id)

    if not subscriber.is_verified:
        subscriber.is_verified = True
        subscriber.save()

    return render(request, "finance/investment/verified_success.html", {
        "email": subscriber.email,
        "title": "Verified Successfully"
    })


@staff_member_required
def admin_send_newsletter(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        subscribers = NewsLetterSubscriber.objects.filter(is_verified=True)
        recipient_list = [s.email for s in subscribers]

        if recipient_list:
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipient_list,
                    fail_silently=False,
                )
                messages.success(request, f"Successfully sent to {len(recipient_list)} subscribers!")
            except Exception as e:
                messages.error(request, f"Mail Error: {e}")
        else:
            messages.warning(request, "No verified subscribers to send to.")

    return redirect('finance:moderation_queue')


# ===================== MODERATION QUEUE =====================
@staff_member_required
def moderation_queue(request):
    all_items = Opportunity.objects.all().order_by('-created_at')
    subscribers_count = NewsLetterSubscriber.objects.filter(is_verified=True).count()

    return render(request, 'finance/investment/moderation.html', {
        'all_items': all_items,
        'subscribers_count': subscribers_count
    })


@staff_member_required
def approve_opportunity(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk)
    opportunity.status = 'APPROVED'
    opportunity.save()
    return redirect('finance:moderation_queue')


@staff_member_required
def reject_opportunity(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk)
    opportunity.status = 'REJECTED'
    opportunity.save()
    return redirect('finance:moderation_queue')

@staff_member_required
def delete_opportunity(request, pk):
    opportunity = get_object_or_404(Opportunity, pk=pk)
    if request.method == 'POST':
        opportunity.delete()
        messages.success(request, "Opportunity has been permanently deleted.")
    return redirect('finance:moderation_queue')


# ===================== PAYMENT REVIEW =====================
def Payment_Review(request):
    pay_amount = 3500

    if 1000 < pay_amount <= 3000:
        divided_amount = pay_amount / 3
    elif pay_amount > 3000:
        divided_amount = pay_amount / 4
    else:
        divided_amount = pay_amount

    context = {
        'pay_amount': pay_amount,
    }

    return render(request, "finance/payments/Payment_Review.html", context)
