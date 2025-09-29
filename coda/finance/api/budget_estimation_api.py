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

from ..models import Company, Department, BudgetCategory
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

