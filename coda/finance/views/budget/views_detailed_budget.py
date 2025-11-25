"""
Detailed Budget Estimation Views

Views for detailed budget item breakdown and user editing
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from decimal import Decimal
import json

from shared_core.models import Company
from shared_core.users import Department
from finance.models import BudgetCategory, BudgetEstimateProjection
from finance.models import BudgetItemDetail, BudgetEstimateItem
from finance.services.data_quality_service import DataQualityService
from finance.services.ai_budget_suggestion_service import AIBudgetSuggestionService
from finance.services.smart_data_correction_service import SmartDataCorrectionService


@login_required
def detailed_budget_breakdown(request, projection_id):
    """
    Show detailed breakdown of a budget projection with item-level editing
    """
    projection = get_object_or_404(BudgetEstimateProjection, id=projection_id)
    
    # Get or create budget item details for each category
    categories = BudgetCategory.objects.all()
    item_details = {}
    
    for category in categories:
        items = BudgetItemDetail.objects.filter(
            category=category,
            is_active=True
        ).order_by('item_name')
        item_details[category.name] = items
    
    # Get existing estimates for this projection
    existing_estimates = {
        item.item_detail.id: item for item in 
        BudgetEstimateItem.objects.filter(projection=projection)
    }
    
    # Get AI-powered intelligent suggestions
    ai_suggestion_service = AIBudgetSuggestionService()
    ai_suggestions = ai_suggestion_service.get_intelligent_suggestions(
        company=projection.company,
        department=projection.department,
        horizon=projection.horizon
    )
    
    # Get smart data correction suggestions
    correction_service = SmartDataCorrectionService()
    data_corrections = correction_service.analyze_and_correct_data(
        company=projection.company,
        department=projection.department
    )
    
    context = {
        'projection': projection,
        'categories': categories,
        'item_details': item_details,
        'existing_estimates': existing_estimates,
        'ai_suggestions': ai_suggestions,
        'data_corrections': data_corrections,
    }
    
    return render(request, 'finance/detailed_budget_breakdown.html', context)


@login_required
@require_http_methods(["POST"])
def save_item_estimate(request, projection_id):
    """
    Save user's estimate for a specific budget item
    """
    projection = get_object_or_404(BudgetEstimateProjection, id=projection_id)
    
    try:
        item_detail_id = request.POST.get('item_detail_id')
        estimated_quantity = Decimal(request.POST.get('estimated_quantity', 0))
        estimated_unit_cost = Decimal(request.POST.get('estimated_unit_cost', 0))
        notes = request.POST.get('notes', '')
        
        item_detail = get_object_or_404(BudgetItemDetail, id=item_detail_id)
        
        # Create or update estimate item
        estimate_item, created = BudgetEstimateItem.objects.get_or_create(
            projection=projection,
            item_detail=item_detail,
            defaults={
                'estimated_quantity': estimated_quantity,
                'estimated_unit_cost': estimated_unit_cost,
                'notes': notes,
            }
        )
        
        if not created:
            estimate_item.estimated_quantity = estimated_quantity
            estimate_item.estimated_unit_cost = estimated_unit_cost
            estimate_item.notes = notes
            estimate_item.save()
        
        # Update projection total
        update_projection_total(projection)
        
        return JsonResponse({
            'success': True,
            'message': 'Estimate saved successfully',
            'estimated_total': float(estimate_item.estimated_total),
            'variance_percentage': float(estimate_item.variance_percentage)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error saving estimate: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def submit_detailed_estimate(request, projection_id):
    """
    Submit detailed budget estimate for approval
    """
    projection = get_object_or_404(BudgetEstimateProjection, id=projection_id)
    
    try:
        # Update projection with detailed estimates
        estimate_items = BudgetEstimateItem.objects.filter(projection=projection)
        
        # Calculate totals by category
        category_totals = {}
        total_estimate = Decimal('0.00')
        
        for item in estimate_items:
            category_name = item.item_detail.category.name
            if category_name not in category_totals:
                category_totals[category_name] = Decimal('0.00')
            
            category_totals[category_name] += item.estimated_total
            total_estimate += item.estimated_total
        
        # Update projection
        projection.estimates = {k: float(v) for k, v in category_totals.items()}
        projection.total_estimate = float(total_estimate)
        projection.status = 'submitted'
        projection.submitted_at = timezone.now()
        projection.save()
        
        messages.success(request, f'Detailed budget estimate submitted for approval. Total: ${total_estimate:,.2f}')
        return redirect('finance:projections-list')
        
    except Exception as e:
        messages.error(request, f'Error submitting estimate: {str(e)}')
        return redirect('finance:detailed-budget-breakdown', projection_id=projection_id)


@login_required
def create_detailed_projection(request):
    """
    Create a new detailed budget projection
    """
    if request.method == 'POST':
        company_id = request.POST.get('company_id')
        department_id = request.POST.get('department_id')
        horizon = request.POST.get('horizon', 'monthly')
        
        if not company_id:
            messages.error(request, "Please select a company.")
            return redirect('finance:estimates-wizard')
        
        company = Company.objects.get(id=company_id)
        department = Department.objects.get(id=department_id) if department_id else Department.objects.first()
        
        # Create projection
        projection = BudgetEstimateProjection.objects.create(
            company=company,
            department=department,
            horizon=horizon,
            method='detailed',
            estimates={},
            total_estimate=0.0,
            created_by=getattr(request.user, "customeruser", None),
            status='draft'
        )
        
        # Initialize with default item details
        initialize_default_items(projection)
        
        return redirect('finance:detailed-budget-breakdown', projection_id=projection.id)
    
    # GET request - show form
    companies = Company.objects.all()
    departments = Department.objects.all()
    
    context = {
        'companies': companies,
        'departments': departments,
    }
    
    return render(request, 'finance/create_detailed_projection.html', context)


def update_projection_total(projection):
    """Update projection total based on estimate items"""
    estimate_items = BudgetEstimateItem.objects.filter(projection=projection)
    
    category_totals = {}
    total_estimate = Decimal('0.00')
    
    for item in estimate_items:
        category_name = item.item_detail.category.name
        if category_name not in category_totals:
            category_totals[category_name] = Decimal('0.00')
        
        category_totals[category_name] += item.estimated_total
        total_estimate += item.estimated_total
    
    projection.estimates = {k: float(v) for k, v in category_totals.items()}
    projection.total_estimate = float(total_estimate)
    projection.save()


def initialize_default_items(projection):
    """Initialize projection with default budget items"""
    categories = BudgetCategory.objects.all()
    
    for category in categories:
        # Create default items for each category
        default_items = get_default_items_for_category(category)
        
        for item_data in default_items:
            BudgetItemDetail.objects.get_or_create(
                category=category,
                item_name=item_data['item_name'],
                defaults={
                    'description': item_data['description'],
                    'unit_cost': item_data['unit_cost'],
                    'quantity': item_data['quantity'],
                    'frequency': item_data['frequency'],
                    'is_recurring': item_data['is_recurring'],
                    'is_essential': item_data['is_essential'],
                    'created_by': projection.created_by,
                }
            )


def get_default_items_for_category(category):
    """Get default items for a category - all start with zero values"""
    defaults = {
        'Salaries and Wages': [
            {
                'item_name': 'Base Salaries',
                'description': 'Monthly base salaries for all employees',
                'unit_cost': 0.00,  # Start with zero
                'quantity': 0,       # Start with zero
                'frequency': 'monthly',
                'is_recurring': True,
                'is_essential': True,
            },
            {
                'item_name': 'Bonuses',
                'description': 'Performance bonuses and incentives',
                'unit_cost': 0.00,   # Start with zero
                'quantity': 0,       # Start with zero
                'frequency': 'quarterly',
                'is_recurring': True,
                'is_essential': False,
            }
        ],
        'Utilities': [
            {
                'item_name': 'Electricity',
                'description': 'Monthly electricity bills',
                'unit_cost': 0.00,   # Start with zero
                'quantity': 0,       # Start with zero
                'frequency': 'monthly',
                'is_recurring': True,
                'is_essential': True,
            },
            {
                'item_name': 'Water',
                'description': 'Monthly water bills',
                'unit_cost': 0.00,   # Start with zero
                'quantity': 0,       # Start with zero
                'frequency': 'monthly',
                'is_recurring': True,
                'is_essential': True,
            }
        ],
        'Office Supplies': [
            {
                'item_name': 'Stationery',
                'description': 'Pens, paper, notebooks, etc.',
                'unit_cost': 0.00,   # Start with zero
                'quantity': 0,       # Start with zero
                'frequency': 'monthly',
                'is_recurring': True,
                'is_essential': True,
            }
        ],
        'IT and Software': [
            {
                'item_name': 'Software Licenses',
                'description': 'Monthly software subscription fees',
                'unit_cost': 0.00,   # Start with zero
                'quantity': 0,       # Start with zero
                'frequency': 'monthly',
                'is_recurring': True,
                'is_essential': True,
            }
        ]
    }
    
    return defaults.get(category.name, [])

