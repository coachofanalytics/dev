"""
Budget API views - RESTful API endpoints for budget operations.
"""

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg
from decimal import Decimal
import json
import logging

from ..core.base import BaseFinanceView, login_required_finance, company_required, json_response, error_json_response
from ...models import Budget, BudgetCategory, BudgetSubCategory, BudgetRequest, BudgetEstimateProjection
from ...services.budget.estimation import BudgetEstimationService
from ...services.budget.consolidation import BudgetConsolidationService

logger = logging.getLogger(__name__)


class BudgetAPIView(BaseFinanceView):
    """Base class for budget API views."""
    
    def __init__(self):
        super().__init__()
        self.estimation_service = BudgetEstimationService()
        self.consolidation_service = BudgetConsolidationService()


@require_http_methods(["GET"])
@login_required_finance
@company_required
def budget_list_api(request, company_slug, company=None):
    """
    API endpoint to list budgets for a company.
    """
    view = BudgetAPIView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        user_department = view.get_user_department(request, company)
        
        # Build query
        budget_query = Budget.objects.filter(company=company)
        if user_department:
            budget_query = budget_query.filter(department=user_department)
        
        # Apply filters
        category_id = request.GET.get('category_id')
        if category_id:
            budget_query = budget_query.filter(category_id=category_id)
        
        status = request.GET.get('status')
        if status:
            budget_query = budget_query.filter(status=status)
        
        # Get budgets
        budgets = budget_query.select_related('category', 'subcategory', 'budget_lead').order_by('-created_at')
        
        # Serialize data
        budget_data = []
        for budget in budgets:
            budget_data.append({
                'id': budget.id,
                'item_name': budget.item_name,
                'category': {
                    'id': budget.category.id,
                    'name': budget.category.name
                },
                'subcategory': {
                    'id': budget.subcategory.id,
                    'name': budget.subcategory.name
                } if budget.subcategory else None,
                'estimated_amount': float(budget.estimated_amount),
                'actual_spent': float(budget.actual_spent),
                'variance': float(budget.variance),
                'status': budget.status,
                'created_at': budget.created_at.isoformat(),
                'updated_at': budget.updated_at.isoformat()
            })
        
        return json_response({
            'budgets': budget_data,
            'total_count': len(budget_data),
            'company': company.name
        })
    
    except Exception as e:
        view.log_error("Error in budget list API", e)
        return error_json_response("Internal server error", 500)


@require_http_methods(["GET"])
@login_required_finance
@company_required
def budget_detail_api(request, company_slug, budget_id, company=None):
    """
    API endpoint to get budget details.
    """
    view = BudgetAPIView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        # Get budget
        budget = get_object_or_404(Budget, id=budget_id, company=company)
        
        # Serialize budget data
        budget_data = {
            'id': budget.id,
            'item_name': budget.item_name,
            'description': budget.description,
            'category': {
                'id': budget.category.id,
                'name': budget.category.name,
                'description': budget.category.description
            },
            'subcategory': {
                'id': budget.subcategory.id,
                'name': budget.subcategory.name,
                'description': budget.subcategory.description
            } if budget.subcategory else None,
            'estimated_amount': float(budget.estimated_amount),
            'actual_spent': float(budget.actual_spent),
            'variance': float(budget.variance),
            'quantity': float(budget.quantity),
            'unit_price': float(budget.unit_price),
            'cases': budget.cases,
            'status': budget.status,
            'notes': budget.notes,
            'created_at': budget.created_at.isoformat(),
            'updated_at': budget.updated_at.isoformat()
        }
        
        return json_response(budget_data)
    
    except Exception as e:
        view.log_error("Error in budget detail API", e)
        return error_json_response("Internal server error", 500)


@require_http_methods(["POST"])
@login_required_finance
@company_required
@csrf_exempt
def budget_create_api(request, company_slug, company=None):
    """
    API endpoint to create a new budget.
    """
    view = BudgetAPIView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        # Parse request data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return error_json_response("Invalid JSON data", 400)
        
        # Validate required fields
        required_fields = ['item_name', 'category_id', 'estimated_amount']
        for field in required_fields:
            if field not in data:
                return error_json_response("Missing required field: {}".format(field), 400)
        
        # Create budget
        budget = Budget.objects.create(
            company=company,
            item_name=data['item_name'],
            description=data.get('description', ''),
            category_id=data['category_id'],
            subcategory_id=data.get('subcategory_id'),
            estimated_amount=Decimal(str(data['estimated_amount'])),
            quantity=Decimal(str(data.get('quantity', 1))),
            unit_price=Decimal(str(data.get('unit_price', data['estimated_amount']))),
            cases=data.get('cases', 1),
            status=data.get('status', 'active'),
            notes=data.get('notes', ''),
            budget_lead=request.user
        )
        
        return json_response({
            'success': True,
            'budget_id': budget.id,
            'message': 'Budget created successfully'
        })
    
    except Exception as e:
        view.log_error("Error in budget create API", e)
        return error_json_response("Internal server error", 500)


@require_http_methods(["PUT"])
@login_required_finance
@company_required
@csrf_exempt
def budget_update_api(request, company_slug, budget_id, company=None):
    """
    API endpoint to update a budget.
    """
    view = BudgetAPIView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        # Get budget
        budget = get_object_or_404(Budget, id=budget_id, company=company)
        
        # Parse request data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return error_json_response("Invalid JSON data", 400)
        
        # Update budget fields
        if 'item_name' in data:
            budget.item_name = data['item_name']
        if 'description' in data:
            budget.description = data['description']
        if 'category_id' in data:
            budget.category_id = data['category_id']
        if 'subcategory_id' in data:
            budget.subcategory_id = data['subcategory_id']
        if 'estimated_amount' in data:
            budget.estimated_amount = Decimal(str(data['estimated_amount']))
        if 'quantity' in data:
            budget.quantity = Decimal(str(data['quantity']))
        if 'unit_price' in data:
            budget.unit_price = Decimal(str(data['unit_price']))
        if 'cases' in data:
            budget.cases = data['cases']
        if 'status' in data:
            budget.status = data['status']
        if 'notes' in data:
            budget.notes = data['notes']
        
        budget.save()
        
        return json_response({
            'success': True,
            'budget_id': budget.id,
            'message': 'Budget updated successfully'
        })
    
    except Exception as e:
        view.log_error("Error in budget update API", e)
        return error_json_response("Internal server error", 500)


@require_http_methods(["DELETE"])
@login_required_finance
@company_required
def budget_delete_api(request, company_slug, budget_id, company=None):
    """
    API endpoint to delete a budget.
    """
    view = BudgetAPIView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        # Get budget
        budget = get_object_or_404(Budget, id=budget_id, company=company)
        
        # Delete budget
        budget.delete()
        
        return json_response({
            'success': True,
            'message': 'Budget deleted successfully'
        })
    
    except Exception as e:
        view.log_error("Error in budget delete API", e)
        return error_json_response("Internal server error", 500)


@require_http_methods(["GET"])
@login_required_finance
@company_required
def budget_categories_api(request, company_slug, company=None):
    """
    API endpoint to get budget categories.
    """
    view = BudgetAPIView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        # Get categories
        categories = BudgetCategory.objects.all().order_by('name')
        
        # Serialize data
        category_data = []
        for category in categories:
            # Get subcategories for this category
            subcategories = BudgetSubCategory.objects.filter(category=category).order_by('name')
            subcategory_data = [
                {
                    'id': sub.id,
                    'name': sub.name,
                    'description': sub.description
                }
                for sub in subcategories
            ]
            
            category_data.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'subcategories': subcategory_data
            })
        
        return json_response({
            'categories': category_data,
            'total_count': len(category_data)
        })
    
    except Exception as e:
        view.log_error("Error in budget categories API", e)
        return error_json_response("Internal server error", 500)


@require_http_methods(["GET"])
@login_required_finance
@company_required
def budget_statistics_api(request, company_slug, company=None):
    """
    API endpoint to get budget statistics.
    """
    view = BudgetAPIView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        user_department = view.get_user_department(request, company)
        
        # Build query
        budget_query = Budget.objects.filter(company=company)
        if user_department:
            budget_query = budget_query.filter(department=user_department)
        
        # Calculate statistics
        total_budgets = budget_query.count()
        total_estimated = budget_query.aggregate(Sum('estimated_amount'))['estimated_amount__sum'] or Decimal('0.00')
        total_actual = budget_query.aggregate(Sum('actual_spent'))['actual_spent__sum'] or Decimal('0.00')
        total_variance = total_actual - total_estimated
        
        # Status breakdown
        status_breakdown = budget_query.values('status').annotate(
            count=Count('id'),
            total_amount=Sum('estimated_amount')
        )
        
        # Category breakdown
        category_breakdown = budget_query.values('category__name').annotate(
            count=Count('id'),
            total_estimated=Sum('estimated_amount'),
            total_actual=Sum('actual_spent')
        )
        
        return json_response({
            'statistics': {
                'total_budgets': total_budgets,
                'total_estimated': float(total_estimated),
                'total_actual': float(total_actual),
                'total_variance': float(total_variance),
                'variance_percentage': float((total_variance / total_estimated * 100) if total_estimated > 0 else 0)
            },
            'status_breakdown': list(status_breakdown),
            'category_breakdown': list(category_breakdown)
        })
    
    except Exception as e:
        view.log_error("Error in budget statistics API", e)
        return error_json_response("Internal server error", 500)


@require_http_methods(["POST"])
@login_required_finance
@company_required
@csrf_exempt
def budget_estimation_api(request, company_slug, company=None):
    """
    API endpoint to generate budget estimations.
    """
    view = BudgetAPIView()
    
    try:
        if not company:
            company = view.get_company(request, company_slug)
            if not company:
                return error_json_response("Company not found", 404)
        
        # Parse request data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return error_json_response("Invalid JSON data", 400)
        
        # Get estimation parameters
        method = data.get('method', 'transaction_analysis')
        horizon = data.get('horizon', 'yearly')
        
        # Generate estimation
        estimation_result = view.estimation_service.generate_estimation(company, method, horizon)
        
        if estimation_result.get('success'):
            return json_response({
                'success': True,
                'estimation': estimation_result['estimation'],
                'message': 'Budget estimation generated successfully'
            })
        else:
            return error_json_response(estimation_result.get('error', 'Estimation failed'), 400)
    
    except Exception as e:
        view.log_error("Error in budget estimation API", e)
        return error_json_response("Internal server error", 500)
