from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from .models import (
    Budget, CodaBudget, Payment_Information, Payment_History,
    FinancialServiceRequest, Default_Payment_Fees, Transaction
)
from .forms import BudgetForm, DepartmentFilterForm, InflowForm, FinancialServiceRequestForm

# Stubbing minimal views to prevent import errors and support basic functionality.
# Real implementations for old views are lost but can be stubbed.

def budget(request):
    return render(request, 'finance/budget.html', {})

def budget_projection(request, subtitle, duration):
    return render(request, 'finance/budget_projection.html', {})

def pay(request, service=None):
    return render(request, 'finance/pay.html', {})

def payment(request, method):
    return render(request, 'finance/payment.html', {})

def payments(request):
    return render(request, 'finance/payments.html', {})

def contract_form_submission(request):
    return render(request, 'finance/contract.html', {})

def mycontract(request, username):
    return render(request, 'finance/mycontract.html', {})

def Payment_Review(request):
    return render(request, 'finance/payment_review.html', {})

def transact(request):
    return render(request, 'finance/transact.html', {})
    
def process_payment(request):
    return redirect('finance:payments')

def payment_success(request):
    return render(request, 'finance/success.html', {})

class TransactionListView(ListView):
    model = Transaction
    template_name = 'finance/transaction_list.html'

class TransanctionDetailView(DetailView):
    model = Transaction
    template_name = 'finance/transaction_detail.html'

class TransactionUpdateView(UpdateView):
    model = Transaction
    fields = '__all__'
    template_name = 'finance/transaction_update.html'

class DefaultPaymentListView(ListView):
    model = Default_Payment_Fees
    template_name = 'finance/default_fees.html'
    
class DefaultPaymentUpdateView(UpdateView):
    model = Default_Payment_Fees
    fields = '__all__'
    template_name = 'finance/default_fee_update.html'

class PaymentCreateView(CreateView):
    model = Payment_Information
    fields = '__all__'
    template_name = 'finance/payment_create.html'

class PaymentInformationUpdateView(UpdateView):
    model = Payment_Information
    fields = '__all__'
    template_name = 'finance/payment_update.html'

# ===================== FINANCIAL PLANNING CRUD =====================

# @login_required
def financial_planning_list(request):
    """
    Displays the Financial Planning dashboard:
    - Lists the 4 key services.
    - Lists the user's active/past requests (if logged in).
    - Modal or section to create a new request.
    """
    if request.user.is_authenticated:
        user_requests = FinancialServiceRequest.objects.filter(user=request.user).order_by('-created_at')
    else:
        # For anonymous users, we can't show "their" history easily without session tracking.
        # For now, show empty list or maybe generic info.
        user_requests = FinancialServiceRequest.objects.none()

    if request.method == 'POST':
        form = FinancialServiceRequestForm(request.POST)
        if form.is_valid():
            service_request = form.save(commit=False)
            if request.user.is_authenticated:
                service_request.user = request.user
            else:
                service_request.user = None # Explicitly set None for anonymous
            service_request.save()
            messages.success(request, f"Your request for {service_request.get_service_type_display()} has been submitted.")
            return redirect('finance:planning_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = FinancialServiceRequestForm()

    context = {
        'title': 'Financial Planning',
        'requests': user_requests,
        'form': form,
    }
    return render(request, 'finance/planning.html', context)

@login_required
def financial_planning_update(request, pk):
    service_request = get_object_or_404(FinancialServiceRequest, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = FinancialServiceRequestForm(request.POST, instance=service_request)
        if form.is_valid():
            form.save()
            messages.success(request, "Request updated successfully.")
            return redirect('finance:planning_list')
    else:
        form = FinancialServiceRequestForm(instance=service_request)
    
    context = {
        'title': 'Update Request',
        'form': form,
        'is_update': True
    }
    return render(request, 'finance/request_form.html', context)

@login_required
def financial_planning_delete(request, pk):
    service_request = get_object_or_404(FinancialServiceRequest, pk=pk, user=request.user)
    if request.method == 'POST':
        service_request.delete()
        messages.success(request, "Request cancelled successfully.")
        return redirect('finance:planning_list')
    
    context = {
        'title': 'Cancel Request',
        'item': service_request
    }
    return render(request, 'finance/request_confirm_delete.html', context)
