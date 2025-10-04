# -*- coding: utf-8 -*-
"""
Loan-Budget Integration Views - Phase 3 Implementation
Integrates loan system with budget availability and limits
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q, F
from decimal import Decimal
import json

from ...models import (
    BudgetCategory, BudgetSubCategory, Budget,
    LoanApplication, LoanProduct, BudgetRequest
)
from ...services.loan_service import LoanService
from ...services.automation_service import BudgetRequestService


@login_required
def loan_eligibility_check(request, company_slug):
    """
    Check loan eligibility based on budget availability
    """
    from main.models import Company
    company = get_object_or_404(Company, slug=company_slug)
    user_department = getattr(request.user, 'department', None)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            loan_amount = Decimal(str(data.get('loan_amount', 0)))
            loan_purpose = data.get('purpose', '')
            
            if loan_amount <= 0:
                return JsonResponse({'error': 'Invalid loan amount'}, status=400)
            
            # Calculate budget availability
            budget_availability = calculate_budget_availability(company, user_department)
            
            # Check loan eligibility
            eligibility_result = check_loan_eligibility(
                request.user, loan_amount, loan_purpose, budget_availability
            )
            
            return JsonResponse(eligibility_result)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # GET request - show eligibility form
    # Get available loan products
    loan_products = LoanProduct.objects.filter(is_active=True).order_by('name')
    
    # Get budget summary for context
    budget_summary = get_budget_summary(company, user_department)
    
    context = {
        'company': company,
        'loan_products': loan_products,
        'budget_summary': budget_summary,
        'user_department': user_department,
    }
    
    return render(request, 'finance/loans/loan_eligibility_check.html', context)


@login_required
def loan_application_with_budget(request, company_slug):
    """
    Enhanced loan application that considers budget constraints
    """
    from main.models import Company
    company = get_object_or_404(Company, slug=company_slug)
    user_department = getattr(request.user, 'department', None)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                data = json.loads(request.body)
                
                # Validate loan data
                loan_amount = Decimal(str(data.get('loan_amount', 0)))
                loan_product_id = data.get('loan_product_id')
                purpose = data.get('purpose', '')
                
                if loan_amount <= 0:
                    return JsonResponse({'error': 'Invalid loan amount'}, status=400)
                
                # Get loan product
                loan_product = get_object_or_404(LoanProduct, id=loan_product_id, is_active=True)
                
                # Check budget constraints
                budget_availability = calculate_budget_availability(company, user_department)
                max_loan_amount = budget_availability.get('available_for_loans', 0)
                
                if loan_amount > max_loan_amount:
                    return JsonResponse({
                        'error': f'Loan amount exceeds budget availability. Maximum: ${max_loan_amount:,.2f}',
                        'max_amount': float(max_loan_amount),
                        'budget_availability': budget_availability
                    }, status=400)
                
                # Create loan application
                loan_service = LoanService()
                loan_data = {
                    'loan_amount': float(loan_amount),
                    'loan_product_id': loan_product_id,
                    'purpose': purpose,
                    'duration': loan_product.term_months,
                    'interest_rate': float(loan_product.interest_rate),
                }
                
                result = loan_service.create_loan_application(request.user, loan_data)
                
                if result['success']:
                    # Create budget allocation for loan repayment
                    create_loan_budget_allocation(
                        company, user_department, loan_amount, 
                        loan_product, result['loan_application']
                    )
                    
                    messages.success(
                        request, 
                        f'Loan application submitted successfully. Application #: {result["loan_application"]["application_number"]}'
                    )
                    
                    return JsonResponse({
                        'success': True,
                        'loan_application': result['loan_application'],
                        'budget_impact': {
                            'allocated_amount': float(loan_amount),
                            'remaining_budget': float(max_loan_amount - loan_amount)
                        }
                    })
                else:
                    return JsonResponse({'error': result['error']}, status=400)
                    
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # GET request - show application form
    loan_products = LoanProduct.objects.filter(is_active=True).order_by('name')
    budget_summary = get_budget_summary(company, user_department)
    
    context = {
        'company': company,
        'loan_products': loan_products,
        'budget_summary': budget_summary,
        'user_department': user_department,
    }
    
    return render(request, 'finance/loans/loan_application_with_budget.html', context)


@login_required
def loan_budget_dashboard(request, company_slug):
    """
    Dashboard showing loan-budget integration status
    """
    from main.models import Company
    company = get_object_or_404(Company, slug=company_slug)
    user_department = getattr(request.user, 'department', None)
    
    # Get budget summary
    budget_summary = get_budget_summary(company, user_department)
    
    # Get active loans
    active_loans = LoanApplication.objects.filter(
        borrower=request.user,
        status__in=['active', 'approved']
    ).select_related('loan_product').order_by('-approved_at')
    
    # Get pending loan applications
    pending_loans = LoanApplication.objects.filter(
        borrower=request.user,
        status__in=['submitted', 'under_review', 'pending_guarantor']
    ).select_related('loan_product').order_by('-submitted_at')
    
    # Calculate loan impact on budget
    total_monthly_loan_payments = sum(
        loan.monthly_payment or 0 
        for loan in active_loans 
        if loan.monthly_payment
    )
    
    # Get budget categories with loan allocations
    budget_categories = BudgetCategory.objects.all()
    category_details = []
    
    for category in budget_categories:
        category_budgets = Budget.objects.filter(
            company=company,
            department=user_department,
            category=category
        )
        
        total_estimated = category_budgets.aggregate(
            total=Sum('estimated_amount')
        )['total'] or Decimal('0.00')
        
        total_actual = category_budgets.aggregate(
            total=Sum('actual_spent')
        )['total'] or Decimal('0.00')
        
        # Check if this category has loan-related items
        has_loan_items = category_budgets.filter(
            item_name__icontains='loan'
        ).exists()
        
        category_details.append({
            'category': category,
            'total_estimated': total_estimated,
            'total_actual': total_actual,
            'has_loan_items': has_loan_items,
            'variance': total_actual - total_estimated
        })
    
    context = {
        'company': company,
        'budget_summary': budget_summary,
        'active_loans': active_loans,
        'pending_loans': pending_loans,
        'total_monthly_loan_payments': total_monthly_loan_payments,
        'category_details': category_details,
        'user_department': user_department,
    }
    
    return render(request, 'finance/loans/loan_budget_dashboard.html', context)


@login_required
def budget_loan_impact_analysis(request, company_slug):
    """
    Analyze the impact of loans on budget categories
    """
    from main.models import Company
    company = get_object_or_404(Company, slug=company_slug)
    user_department = getattr(request.user, 'department', None)
    
    # Get all loans for the user
    user_loans = LoanApplication.objects.filter(
        borrower=request.user
    ).select_related('loan_product').order_by('-created_at')
    
    # Analyze budget impact by category
    impact_analysis = []
    
    for loan in user_loans:
        if loan.status in ['active', 'approved'] and loan.monthly_payment:
            # Find related budget categories
            related_budgets = Budget.objects.filter(
                company=company,
                department=user_department,
                item_name__icontains='loan'
            )
            
            for budget in related_budgets:
                impact_analysis.append({
                    'loan': loan,
                    'budget': budget,
                    'monthly_impact': loan.monthly_payment,
                    'annual_impact': loan.monthly_payment * 12,
                    'category': budget.category.name,
                    'subcategory': budget.subcategory.name
                })
    
    # Calculate total impact
    total_monthly_impact = sum(item['monthly_impact'] for item in impact_analysis)
    total_annual_impact = sum(item['annual_impact'] for item in impact_analysis)
    
    context = {
        'company': company,
        'user_loans': user_loans,
        'impact_analysis': impact_analysis,
        'total_monthly_impact': total_monthly_impact,
        'total_annual_impact': total_annual_impact,
        'user_department': user_department,
    }
    
    return render(request, 'finance/loans/budget_loan_impact_analysis.html', context)


def calculate_budget_availability(company, department):
    """
    Calculate available budget for loans
    """
    # Get total budget allocations
    total_budget = Budget.objects.filter(
        company=company,
        department=department,
        status='active'
    ).aggregate(
        total=Sum('estimated_amount')
    )['total'] or Decimal('0.00')
    
    # Get total actual spending
    total_actual = Budget.objects.filter(
        company=company,
        department=department,
        status='active'
    ).aggregate(
        total=Sum('actual_spent')
    )['total'] or Decimal('0.00')
    
    # Get existing loan allocations
    loan_allocations = Budget.objects.filter(
        company=company,
        department=department,
        item_name__icontains='loan'
    ).aggregate(
        total=Sum('estimated_amount')
    )['total'] or Decimal('0.00')
    
    # Calculate available amount
    available_budget = total_budget - total_actual
    available_for_loans = max(Decimal('0.00'), available_budget - loan_allocations)
    
    return {
        'total_budget': total_budget,
        'total_actual': total_actual,
        'available_budget': available_budget,
        'existing_loan_allocations': loan_allocations,
        'available_for_loans': available_for_loans,
        'utilization_percentage': (total_actual / total_budget * 100) if total_budget > 0 else 0
    }


def check_loan_eligibility(user, loan_amount, purpose, budget_availability):
    """
    Check if user is eligible for a loan based on budget constraints
    """
    # Basic eligibility checks
    max_loan_amount = budget_availability.get('available_for_loans', 0)
    
    eligibility = {
        'eligible': loan_amount <= max_loan_amount,
        'max_loan_amount': float(max_loan_amount),
        'requested_amount': float(loan_amount),
        'budget_availability': budget_availability,
        'recommendations': []
    }
    
    if loan_amount > max_loan_amount:
        eligibility['recommendations'].append(
            f"Reduce loan amount to ${max_loan_amount:,.2f} or less"
        )
    
    # Check if user has existing loans
    existing_loans = LoanApplication.objects.filter(
        borrower=user,
        status__in=['active', 'approved']
    )
    
    if existing_loans.exists():
        total_existing_payments = sum(
            loan.monthly_payment or 0 for loan in existing_loans
        )
        eligibility['existing_loan_payments'] = float(total_existing_payments)
        eligibility['recommendations'].append(
            f"You have existing loan payments of ${total_existing_payments:,.2f}/month"
        )
    
    # Calculate debt-to-income ratio (simplified)
    if hasattr(user, 'monthly_income') and user.monthly_income:
        estimated_monthly_payment = loan_amount * Decimal('0.1')  # Rough estimate
        debt_ratio = (estimated_monthly_payment / user.monthly_income) * 100
        
        if debt_ratio > 40:
            eligibility['recommendations'].append(
                "High debt-to-income ratio. Consider reducing loan amount."
            )
    
    return eligibility


def get_budget_summary(company, department):
    """
    Get budget summary for loan eligibility
    """
    budgets = Budget.objects.filter(
        company=company,
        department=department,
        status='active'
    )
    
    total_estimated = budgets.aggregate(total=Sum('estimated_amount'))['total'] or Decimal('0.00')
    total_actual = budgets.aggregate(total=Sum('actual_spent'))['total'] or Decimal('0.00')
    
    # Get top categories
    top_categories = budgets.values('category__name').annotate(
        estimated=Sum('estimated_amount'),
        actual=Sum('actual_spent')
    ).order_by('-estimated')[:5]
    
    return {
        'total_estimated': total_estimated,
        'total_actual': total_actual,
        'available': total_estimated - total_actual,
        'utilization_percentage': (total_actual / total_estimated * 100) if total_estimated > 0 else 0,
        'top_categories': list(top_categories)
    }


def create_loan_budget_allocation(company, department, loan_amount, loan_product, loan_application):
    """
    Create budget allocation for loan repayment
    """
    # Find or create loan-related budget category
    loan_category, created = BudgetCategory.objects.get_or_create(
        name='Loan Repayments',
        defaults={'description': 'Budget allocations for loan repayments'}
    )
    
    # Find or create loan subcategory
    loan_subcategory, created = BudgetSubCategory.objects.get_or_create(
        category=loan_category,
        name='Staff Loans',
        defaults={'description': 'Staff loan repayments'}
    )
    
    # Create budget allocation
    Budget.objects.create(
        company=company,
        department=department,
        category=loan_category,
        subcategory=loan_subcategory,
        item_name=f'Loan #{loan_application["application_number"]} - {loan_product.name}',
        estimated_amount=loan_amount,
        actual_spent=Decimal('0.00'),
        currency='USD',
        fiscal_year=timezone.now().year,
        status='active',
        requires_approval=False,
        description=f'Budget allocation for loan application #{loan_application["application_number"]}'
    )
