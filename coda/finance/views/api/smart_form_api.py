"""
Smart Form API endpoints for auto-populating budget request fields
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json

from finance.services.smart_form_service import SmartFormService

@login_required
@require_http_methods(["POST"])
@csrf_exempt
def get_form_suggestions(request):
    """
    API endpoint to get smart form suggestions based on purpose and department
    """
    try:
        data = json.loads(request.body)
        purpose = data.get('purpose', '')
        department_name = data.get('department', '')
        amount = data.get('amount')
        
        service = SmartFormService()
        suggestions = service.suggest_fields(purpose, department_name, amount)
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
def get_department_defaults(request):
    """
    API endpoint to get smart defaults for a department
    """
    try:
        department_name = request.GET.get('department', '')
        service = SmartFormService()
        defaults = service.get_smart_defaults(department_name)
        
        return JsonResponse({
            'success': True,
            'defaults': defaults
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
