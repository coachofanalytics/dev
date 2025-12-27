
import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum
from django.http import QueryDict, Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import CreateView, ListView, UpdateView, DetailView
from django.utils.decorators import method_decorator
from .models import Payment_Information
from accounts.forms import UserForm
from accounts.models import CustomerUser, Membership
from .forms import BudgetForm, DepartmentFilterForm, InflowForm
from .models import (
    Budget, CodaBudget, Payment_Information, Payment_History,
    Default_Payment_Fees, Transaction
)
from .utils import (
    check_default_fee, get_exchange_rate, compute_amt, category_subcategory
)
from main.utils import path_values, countdown_in_month
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import CreateView
from .models import Payment_Information

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


# ===================== CONTRACT FORM SUBMISSION =====================
def contract_form_submission(request):
    try:
        if request.method == "POST":
            user_student_data = request.POST.get('usr_data')
            if not user_student_data:
                raise ValueError("Missing form data")

            student_dict_data = QueryDict(user_student_data)
            username = student_dict_data.get('username')

            # Retrieve customer and payment info
            customer = CustomerUser.objects.filter(username=username).first()
            payment = Payment_Information.objects.filter(customer_id=request.user.id).first()

            # Handle new user form
            if not payment:
                form = UserForm(student_dict_data)
                if form.is_valid():
                    category = form.cleaned_data.get('category')
                    form.instance.is_applicant = category == 1
                    form.instance.is_staff = category == 2
                    form.instance.is_client = category == 3
                    form.instance.is_admin = category == 4
                    form.save()

            # Payment details
            payment_fees = int(request.POST.get('duration', 0)) * 1000
            down_payment = int(request.POST.get('down_payment', 0))
            student_bonus_amount = int(request.POST.get('bonus', 0))
            fee_balance = payment_fees - down_payment
            if request.POST.get('student_contract'):
                fee_balance -= student_bonus_amount

            # Save payment info
            payment_data = {
                'payment_fees': payment_fees,
                'down_payment': down_payment,
                'student_bonus': student_bonus_amount,
                'fee_balance': fee_balance,
                'plan': request.POST.get('duration'),
                'payment_method': request.POST.get('payment_type'),
                'client_signature': request.POST.get('client_sign'),
                'company_rep': request.POST.get('rep_name'),
                'client_date': request.POST.get('client_date'),
                'rep_date': request.POST.get('rep_date'),
            }

            if payment:
                Payment_Information.objects.filter(customer_id=customer.id).update(**payment_data)
            else:
                Payment_Information.objects.create(customer_id=customer.id, **payment_data)

            # Save payment history
            Payment_History.objects.create(customer=customer, **payment_data)

            messages.success(request, f'Added New Contract for {username}!')
            return redirect('finance:pay')

        # Render GET request
        return render(request, "finance/contract_form.html")

    except ValueError as ve:
        logger.error(f"Validation error in contract_form_submission: {ve}")
        messages.error(request, str(ve))
        return redirect('finance:contract_form')
    except Exception as e:
        logger.exception(f"Unexpected error in contract_form_submission: {e}")
        message = f'Hi {request.user}, there is an issue on our end. Kindly contact us directly at info@codanalytics.net.'
        context = {"title": "CONTRACT", "message": message, "error_details": str(e)}
        return render(request, "main/errors/generalerrors.html", context)


# ===================== PAYMENTS =====================

@login_required
def pay(request, service=None):
    if not request.user.is_authenticated:
        return redirect(reverse('accounts:account-login'))

    user = request.user
    print(user)
    membership = get_object_or_404(Membership, member=user)
    fee_usd = membership.fee

    fee_kes = fee_usd * get_exchange_rate('USD', 'KES')
    print(fee_kes)
   

    context = {
        "title": "PAYMENT",
        "membership": membership,
        "fee_kes":fee_kes,
        "user": request.user,
        "message": f"Hi {request.user}, you are yet to sign the contract with us. Kindly contact us at info@codanalytics.net.",
    }
    return render(request, "finance/payments/pay.html", context)

class PaymentCreateView(CreateView):
    model = Payment_Information
    fields = ['customer_id', 'down_payment', 'payment_method']
    template_name = 'finance/payments/payment_form.html'
    success_url = '/finance/pay/'


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



@login_required
def another_view(request, method):
    context = {
        "title": f"Payment Method: {method}",
        "method": method,
    }
    return render(request, "finance/payments/another_view.html", context)



from django.shortcuts import render

def payment(request, method):
    path_list, sub_title, pre_sub_title = path_values(request)
    subject = 'PAYMENT'
    url = 'email/payment/payment_method.html'

    # Define the account number based on the subtitle
    account_no = None  
    if sub_title == 'mpesa':
        account_no = '0100008710952'  
    
    context = {
        'subtitle': sub_title,
        'user': request.user.first_name,
        'cashapp': '$cmaghas',
        'venmo': '@codainfo',
        'email': 'info@codanalytics.net',
        'contact_message': 'info@codanalytics.net',
        'account_no': account_no,  
    }
    print(context)
    try:
        return render(request, "finance/payments/payment_method.html", context)
    except Exception as e:
        print(f"Error: {e}")  
        return render(request, "finance/payments/payment_method.html", context)

@login_required
def payments(request):
    # Fetch payment information for the logged-in user
    payment_info = Payment_Information.objects.filter(customer_id=request.user.id).last()

    context = {
        "title": "Payments",
        "payments": payment_info,
    }
    return render(request, "finance/payments/payments.html", context)

@login_required
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
                membership.status = 'PAID'  # Update the payment status if applicable
                membership.save()
                return redirect("finance:payment_success")  # Redirect to success page
            except ValueError:
                # Handle invalid input
                return redirect("finance:payment_page")  # Redirect back to payment page with error

    return redirect("finance:pay")

@login_required
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
            return render(request,"management/contracts/supportcontract_form.html")

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
    template_name="main/snippets_templates/generalform.html"
    
    # fields ="__all__"
    fields=['customer_id','down_payment']
    def form_valid(self, form):
        # form.instance.author=self.request.user
        # if self.request.user.is_superuser or self.request.user:
        if self.request.user is not None:
            return super().form_valid(form)
        else:
            # return redirect("management:tasks")
            return render(request,"main/snippets_templates/generalform.html")

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
            instance=form.save(commit=False)
            instance.sender=request.user
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
            instance=form.save(commit=False)
            print(request.user)
            instance.budget_lead=request.user
            instance.save()
            return redirect("finance:budget", company_slug="coda")
    else:
        form = BudgetForm()
    return render(request, "finance/budgets/newbudget.html", {"form": form})

def budget(request, company_slug='coda'):
   
    # Fetch budgets for the company
    company_budgets = Budget.objects.all()
  
    # Calculate total budgets
    total_budget = sum(site.amount for site in company_budgets)
   
    # Construct link URL
    #link_url = reverse('finance:site_budget_with_subcategory', kwargs={'company_slug': company_slug, 'category': 'Web', 'subcategory': 'all'})

    # Prepare summary data
    summary = [
        {"title": "Total Budget", "value": total_budget, "link": ''},
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
            return CodaBudget.objects.filter(department__name=department_name, created_at__year=str(year)).order_by('category')
        else:
            return CodaBudget.objects.filter(created_at__year=str(year)).order_by('category')
    else:
        month = duration-1
        year=2024
        if department_name:
            # return CodaBudget.objects.filter(department__name=department_name, created_at__month=str(month)).order_by('category')
            return CodaBudget.objects.filter(department__name=department_name, created_at__year=str(year), created_at__month=str(month)).order_by('category')
        else:
            return CodaBudget.objects.filter( created_at__year=str(year),created_at__month=str(month)).order_by('category')

def budget_projection(request,subtitle='summary',duration=2024):
    path_list, sub_title, pre_sub_title = path_values(request)
    subtitle=path_list[2]
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
            department_name = form.cleaned_data.get('name')
            if department_name:
                budget_items = filter_transactions_by_duration_and_department(duration, department_name)
            else:
                budget_items = filter_transactions_by_duration_and_department(duration)
            total = sum(item.amount * item.qty for item in budget_items)
    else:
        form = DepartmentFilterForm()
        budget_items = filter_transactions_by_duration_and_department(duration)
        total = sum(item.amount * item.qty for item in budget_items)




    # Aggregate data by month and category
    budget_summary = budget_items.values('category__name','subcategory__name').annotate(
        total_qty=Sum('qty'),
        total_amount=Sum('unit_price')

    )
    # Create a list of unique categories
    available_categories = budget_summary.values_list('category__name', flat=True).distinct()

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
    if subtitle=='detailed':
        return render(request, "finance/budgets/detailed_budget.html", context)
    else:
        return render(request, "finance/budgets/summary_budget.html", context)
    



def Payment_Review(request):
 
    # Simulated payment amount (dynamic logic here)
    pay_amount = 3500  # Replace this with your dynamic value or calculation logic

    # Calculate the divided amount (used for backend processing only)
    if 1000 < pay_amount <= 3000:
        divided_amount = pay_amount / 3
    elif pay_amount > 3000:
        divided_amount = pay_amount / 4
    else:
        divided_amount = pay_amount

    # You can still use divided_amount for other purposes if needed
    context = {
        'pay_amount': pay_amount,
    }

    
    return render(request,"finance/payments/Payment_Review.html",context)