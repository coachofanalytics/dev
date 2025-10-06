"""
Transaction entry views - basic transaction entry and management.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Sum, Count
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
from decimal import Decimal
import json
import logging

from main.models import Company
from ..core.base import BaseFinanceView, login_required_finance, company_required, json_response, error_json_response
from ...models import Transaction, BudgetCategory, BudgetSubCategory
from ...forms import forms as legacy_forms

logger = logging.getLogger(__name__)
User = get_user_model()


class TransactionEntryView(BaseFinanceView):
    """Base class for transaction entry views."""
    
    def __init__(self):
        super().__init__()


@login_required_finance
@company_required
def transaction_entry(request, company_slug, company=None):
    """
    Basic transaction entry form.
    """
    view = TransactionEntryView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        user_department = view.get_user_department(request, company)
        
        if request.method == 'POST':
            return view._handle_transaction_post(request, company, user_department)
        
        # Get form
        form = legacy_forms.TransactionForm()
        
        # Get categories for dropdown
        categories = BudgetCategory.objects.all().order_by('name')
        
        context = {
            'company': company,
            'user_department': user_department,
            'form': form,
            'categories': categories,
        }
        
        return render(request, 'finance/transactions/entry.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading transaction entry")
        return redirect('finance:unified-budget-dashboard', company_slug=company_slug)


def _handle_transaction_post(self, request, company, user_department):
    """Handle POST request for transaction entry."""
    try:
        form = legacy_forms.TransactionForm(request.POST)
        
        if form.is_valid():
            # Save transaction
            transaction = form.save(commit=False)
            transaction.sender = request.user
            transaction.department = user_department
            transaction.transaction_date = timezone.now()
            transaction.save()
            
            messages.success(request, "Transaction recorded successfully.")
            return redirect('finance:transaction-list', company_slug=company.slug)
        else:
            messages.error(request, "Please correct the errors below.")
    
    except Exception as e:
        self.handle_error(request, e, "Error processing transaction")
    
    # If we get here, there was an error
    categories = BudgetCategory.objects.all().order_by('name')
    context = {
        'company': company,
        'user_department': user_department,
        'form': form,
        'categories': categories,
    }
    return render(request, 'finance/transactions/entry.html', context)


# Add method to the class
TransactionEntryView._handle_transaction_post = _handle_transaction_post


@login_required_finance
@company_required
def transaction_list(request, company_slug, company=None):
    """
    List transactions for the user.
    """
    view = TransactionEntryView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        user_department = view.get_user_department(request, company)
        
        # Get user's transactions
        transactions = Transaction.objects.filter(
            sender=request.user
        ).select_related('category', 'subcategory', 'department').order_by('-transaction_date')
        
        # Get transaction statistics
        transaction_stats = {
            'total_transactions': transactions.count(),
            'total_amount': transactions.aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'),
            'avg_amount': transactions.aggregate(Sum('amount'))['amount__sum'] / transactions.count() if transactions.count() > 0 else Decimal('0.00'),
        }
        
        # Filter by category if provided
        category_filter = request.GET.get('category')
        if category_filter:
            transactions = transactions.filter(category_id=category_filter)
        
        # Filter by date range if provided
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        if date_from:
            transactions = transactions.filter(transaction_date__gte=date_from)
        if date_to:
            transactions = transactions.filter(transaction_date__lte=date_to)
        
        # Get categories for filter
        categories = BudgetCategory.objects.all().order_by('name')
        
        context = {
            'company': company,
            'user_department': user_department,
            'transactions': transactions,
            'transaction_stats': transaction_stats,
            'categories': categories,
            'selected_category': category_filter,
            'date_from': date_from,
            'date_to': date_to,
        }
        
        return render(request, 'finance/transactions/list.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading transaction list")
        return redirect('finance:unified-budget-dashboard', company_slug=company_slug)


@login_required_finance
@company_required
def transaction_detail(request, company_slug, transaction_id, company=None):
    """
    Detailed view of a transaction.
    """
    view = TransactionEntryView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        # Get transaction
        transaction = get_object_or_404(
            Transaction,
            id=transaction_id,
            sender=request.user
        )
        
        context = {
            'company': company,
            'transaction': transaction,
        }
        
        return render(request, 'finance/transactions/detail.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error loading transaction detail")
        return redirect('finance:transaction-list', company_slug=company_slug)


@login_required_finance
@company_required
def edit_transaction(request, company_slug, transaction_id, company=None):
    """
    Edit a transaction.
    """
    view = TransactionEntryView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return redirect('main:dashboard')
        
        # Get transaction
        transaction = get_object_or_404(
            Transaction,
            id=transaction_id,
            sender=request.user
        )
        
        if request.method == 'POST':
            form = legacy_forms.TransactionForm(request.POST, instance=transaction)
            if form.is_valid():
                form.save()
                messages.success(request, "Transaction updated successfully.")
                return redirect('finance:transaction-detail', 
                               company_slug=company.slug, transaction_id=transaction.id)
            else:
                messages.error(request, "Please correct the errors below.")
        else:
            form = legacy_forms.TransactionForm(instance=transaction)
        
        # Get categories for dropdown
        categories = BudgetCategory.objects.all().order_by('name')
        
        context = {
            'company': company,
            'transaction': transaction,
            'form': form,
            'categories': categories,
        }
        
        return render(request, 'finance/transactions/edit.html', context)
    
    except Exception as e:
        view.handle_error(request, e, "Error editing transaction")
        return redirect('finance:transaction-list', company_slug=company_slug)


@require_http_methods(["POST"])
@login_required_finance
@company_required
def delete_transaction(request, company_slug, transaction_id, company=None):
    """
    Delete a transaction.
    """
    view = TransactionEntryView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        # Get transaction
        transaction = get_object_or_404(
            Transaction,
            id=transaction_id,
            sender=request.user
        )
        
        # Delete the transaction
        transaction.delete()
        
        return json_response({
            'success': True,
            'message': 'Transaction deleted successfully',
            'transaction_id': transaction_id
        })
    
    except Exception as e:
        view.log_error("Error deleting transaction", e)
        return error_json_response("Internal server error", 500)


@require_http_methods(["GET"])
@login_required_finance
def transaction_api(request, company_slug):
    """
    API endpoint for transaction data.
    """
    view = TransactionEntryView()
    
    try:
        company = view.get_company(request, company_slug)
        if not company:
            return error_json_response("Company not found", 404)
        
        # Get user's transactions
        transactions = Transaction.objects.filter(
            sender=request.user
        ).values('id', 'receiver', 'amount', 'category__name', 'transaction_date', 'description')
        
        # Get transaction statistics
        transaction_stats = {
            'total_transactions': Transaction.objects.filter(sender=request.user).count(),
            'total_amount': Transaction.objects.filter(sender=request.user).aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00'),
        }
        
        data = {
            'transactions': list(transactions),
            'transaction_stats': transaction_stats,
        }
        
        return json_response(data)
    
    except Exception as e:
        view.log_error("Error in transaction API", e)
        return error_json_response("Internal server error", 500)



