"""
Budget Estimation API for CODA Finance System

REST API endpoints for budget estimation and analysis including:
- Budget estimation endpoints
- Spending pattern analysis
- Variance analysis
- Budget consolidation
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.shortcuts import get_object_or_404
import logging

from ..models import Company, Department, BudgetCategory, BudgetEstimationTemplate, BudgetEstimateProjection
from ..services.budget_estimation_service import BudgetEstimationService
from ..services.budget_consolidation_service import BudgetConsolidationService
from ..utils.filter_utils import FilterUtils

logger = logging.getLogger(__name__)


class BudgetEstimationAPIView(viewsets.ModelViewSet):
    """API endpoint for budget estimation and analysis"""
    
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.budget_service = BudgetEstimationService()
        self.consolidation_service = BudgetConsolidationService()
        self.filter_utils = FilterUtils()
    
    @action(detail=False, methods=['get'])
    def list_templates(self, request):
        try:
            templates = BudgetEstimationTemplate.objects.filter(is_active=True).order_by('name')
            data = [
                {
                    'id': t.id,
                    'name': t.name,
                    'budget_type': t.budget_type,
                    'estimation_config': t.estimation_config,
                } for t in templates
            ]
            return Response({'templates': data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error listing templates: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def estimate_for_horizon(self, request):
        """Estimate for a specific horizon: monthly, two_year, five_year"""
        try:
            company_id = request.data.get('company_id')
            department_id = request.data.get('department_id')
            horizon = request.data.get('horizon', 'monthly')
            method = request.data.get('method', 'average')
            template_id = request.data.get('template_id')
            
            if not company_id:
                return Response({'error': 'company_id is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            company = get_object_or_404(Company, id=company_id)
            department = get_object_or_404(Department, id=department_id) if department_id else None
            template = get_object_or_404(BudgetEstimationTemplate, id=template_id) if template_id else None
            
            if horizon == 'monthly':
                est = self.budget_service.estimate_next_month_budget(company=company, department=department, method=method)
            else:
                annual = self.budget_service.estimate_annual_budget(company=company, department=department, method='ytd_average')
                factor = 2 if horizon == 'two_year' else 5
                est = {
                    'estimates': annual.get('estimates', {}),
                    'total_estimate': (annual.get('total_estimate') or 0) * factor,
                    'method': f"ytd_average_x{factor}"
                }
            
            return Response({
                'horizon': horizon,
                'template_id': template.id if template else None,
                'estimate': est,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error in estimate_for_horizon: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def save_projection(self, request):
        try:
            user = request.user
            company_id = request.data.get('company_id')
            department_id = request.data.get('department_id')
            template_id = request.data.get('template_id')
            horizon = request.data.get('horizon', 'monthly')
            method = request.data.get('method', 'average')
            estimates = request.data.get('estimates') or {}
            total_estimate = request.data.get('total_estimate') or 0
            
            company = get_object_or_404(Company, id=company_id)
            department = get_object_or_404(Department, id=department_id)
            template = get_object_or_404(BudgetEstimationTemplate, id=template_id) if template_id else None
            
            proj = BudgetEstimateProjection.objects.create(
                company=company,
                department=department,
                template=template,
                horizon=horizon,
                method=method,
                estimates=estimates,
                total_estimate=total_estimate,
                created_by=getattr(user, 'customeruser', None) or None,
            )
            return Response({'id': proj.id, 'status': proj.status}, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error saving projection: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def submit_projection(self, request):
        try:
            proj_id = request.data.get('projection_id')
            proj = get_object_or_404(BudgetEstimateProjection, id=proj_id)
            proj.status = 'submitted'
            from django.utils import timezone
            proj.submitted_at = timezone.now()
            proj.save(update_fields=['status', 'submitted_at'])
            return Response({'id': proj.id, 'status': proj.status}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error submitting projection: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def list_projections(self, request):
        try:
            company_id = request.query_params.get('company_id')
            department_id = request.query_params.get('department_id')
            qs = BudgetEstimateProjection.objects.all()
            if company_id:
                qs = qs.filter(company_id=company_id)
            if department_id:
                qs = qs.filter(department_id=department_id)
            data = [{
                'id': p.id,
                'company': p.company.name,
                'department': p.department.name,
                'template': p.template.name if p.template else None,
                'horizon': p.horizon,
                'method': p.method,
                'total_estimate': str(p.total_estimate),
                'status': p.status,
                'created_at': p.created_at.isoformat(),
            } for p in qs.order_by('-created_at')[:100]]
            return Response({'projections': data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error listing projections: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def estimate_budget(self, request):
        """Get automated budget estimate"""
        try:
            company_id = request.query_params.get('company_id')
            department_id = request.query_params.get('department_id')
            method = request.query_params.get('method', 'average')
            months = int(request.query_params.get('months', 3))
            
            if not company_id:
                return Response(
                    {'error': 'company_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            company = get_object_or_404(Company, id=company_id)
            department = get_object_or_404(Department, id=department_id) if department_id else None
            
            estimate = self.budget_service.estimate_next_month_budget(
                company=company,
                department=department,
                method=method
            )
            
            return Response(estimate, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in budget estimation API: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def estimate_annual_budget(self, request):
        """Get annual budget estimate"""
        try:
            company_id = request.query_params.get('company_id')
            department_id = request.query_params.get('department_id')
            method = request.query_params.get('method', 'ytd_average')
            
            if not company_id:
                return Response(
                    {'error': 'company_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            company = get_object_or_404(Company, id=company_id)
            department = get_object_or_404(Department, id=department_id) if department_id else None
            
            estimate = self.budget_service.estimate_annual_budget(
                company=company,
                department=department,
                method=method
            )
            
            return Response(estimate, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in annual budget estimation API: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def analyze_spending_patterns(self, request):
        """Get spending pattern analysis"""
        try:
            company_id = request.query_params.get('company_id')
            department_id = request.query_params.get('department_id')
            months = int(request.query_params.get('months', 3))
            
            if not company_id:
                return Response(
                    {'error': 'company_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            company = get_object_or_404(Company, id=company_id)
            department = get_object_or_404(Department, id=department_id) if department_id else None
            
            analysis = self.budget_service.analyze_spending_patterns(
                company=company,
                department=department,
                months=months
            )
            
            return Response(analysis, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in spending pattern analysis API: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def get_variance_analysis(self, request):
        """Get budget variance analysis"""
        try:
            company_id = request.query_params.get('company_id')
            department_id = request.query_params.get('department_id')
            category_id = request.query_params.get('category_id')
            
            if not company_id:
                return Response(
                    {'error': 'company_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            company = get_object_or_404(Company, id=company_id)
            department = get_object_or_404(Department, id=department_id) if department_id else None
            category = get_object_or_404(BudgetCategory, id=category_id) if category_id else None
            
            analysis = self.budget_service.get_budget_variance_analysis(
                company=company,
                department=department,
                category=category
            )
            
            return Response(analysis, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in variance analysis API: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def get_recommendations(self, request):
        """Get budget recommendations"""
        try:
            company_id = request.query_params.get('company_id')
            department_id = request.query_params.get('department_id')
            
            if not company_id:
                return Response(
                    {'error': 'company_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            company = get_object_or_404(Company, id=company_id)
            department = get_object_or_404(Department, id=department_id) if department_id else None
            
            recommendations = self.budget_service.get_budget_recommendations(
                company=company,
                department=department
            )
            
            return Response(recommendations, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in budget recommendations API: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def consolidate_budgets(self, request):
        """Get consolidated budget data"""
        try:
            company_id = request.query_params.get('company_id')
            department_id = request.query_params.get('department_id')
            
            if not company_id:
                return Response(
                    {'error': 'company_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            company = get_object_or_404(Company, id=company_id)
            department = get_object_or_404(Department, id=department_id) if department_id else None
            
            consolidated = self.consolidation_service.get_unified_budget_report(
                company=company,
                department=department
            )
            
            return Response(consolidated, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in budget consolidation API: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def get_consolidated_view(self, request):
        """Get consolidated view of budget data"""
        try:
            company_id = request.query_params.get('company_id')
            department_id = request.query_params.get('department_id')
            
            if not company_id:
                return Response(
                    {'error': 'company_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            company = get_object_or_404(Company, id=company_id)
            department = get_object_or_404(Department, id=department_id) if department_id else None
            
            consolidated_view = self.consolidation_service.create_consolidated_view(
                company=company,
                department=department
            )
            
            return Response(consolidated_view, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in consolidated view API: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def get_model_statistics(self, request):
        """Get budget model usage statistics"""
        try:
            company_id = request.query_params.get('company_id')
            
            if not company_id:
                return Response(
                    {'error': 'company_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            company = get_object_or_404(Company, id=company_id)
            
            statistics = self.consolidation_service.get_model_usage_statistics(
                company=company
            )
            
            return Response(statistics, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in model statistics API: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def migrate_budget_data(self, request):
        """Migrate budget data between models"""
        try:
            company_id = request.data.get('company_id')
            target_model = request.data.get('target_model', 'consolidated')
            
            if not company_id:
                return Response(
                    {'error': 'company_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            company = get_object_or_404(Company, id=company_id)
            
            migration_results = self.consolidation_service.migrate_budget_data(
                company=company,
                target_model=target_model
            )
            
            return Response(migration_results, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in budget migration API: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def get_budget_analytics(self, request):
        """Get comprehensive budget analytics"""
        try:
            company_id = request.query_params.get('company_id')
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            
            if not company_id:
                return Response(
                    {'error': 'company_id is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            company = get_object_or_404(Company, id=company_id)
            
            # Get spending analysis
            spending_analysis = self.budget_service.analyze_spending_patterns(company)
            
            # Get variance analysis
            variance_analysis = self.budget_service.get_budget_variance_analysis(company)
            
            # Get consolidated report
            consolidated_report = self.consolidation_service.get_unified_budget_report(company)
            
            # Get recommendations
            recommendations = self.budget_service.get_budget_recommendations(company)
            
            analytics = {
                'spending_analysis': spending_analysis,
                'variance_analysis': variance_analysis,
                'consolidated_report': consolidated_report,
                'recommendations': recommendations,
                'summary': {
                    'company': company.name,
                    'analysis_date': timezone.now().isoformat(),
                    'status': 'success'
                }
            }
            
            return Response(analytics, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in budget analytics API: {str(e)}")
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )

