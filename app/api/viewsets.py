"""
API ViewSets

This module contains ViewSets for all major functionality in the CODA application,
integrating with service layers for business logic and providing comprehensive API endpoints.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from accounts.models import Department
from finance.models import LoanProduct, LoanApplication, Payment_Information, Budget
from investing.models import Investment_rates, Investor_Information
from management.models import Task, Meetings
from ai_services.models import DiasporaAnalysisData, AnalysisSession
from professional_services.models import ClientAssessment, JobRoles

# Import service layers
from finance.services import LoanService, PaymentService, BudgetService, FinancialAnalyticsService
from investing.services import InvestmentService
from management.services import ManagementService
from ai_services.services import AIAnalyticsService
from professional_services.services import TrainingService
from accounts.services import UserService
from main.services import CoreService

# Import serializers
from .serializers import (
    UserSerializer, UserProfileSerializer, DepartmentSerializer, GroupSerializer,
    LoanProductSerializer, LoanApplicationSerializer, PaymentInformationSerializer,
    BudgetSerializer, InvestmentRatesSerializer, InvestorInformationSerializer,
    EmployeeSerializer, TaskSerializer, MeetingSerializer, AIAnalysisSerializer,
    StockAnalysisSerializer, TrainingProgramSerializer, AssessmentSerializer,
    DetailedLoanApplicationSerializer, DetailedPaymentSerializer, DetailedInvestmentSerializer,
    UserSummarySerializer, LoanSummarySerializer, PaymentSummarySerializer, InvestmentSummarySerializer
)

# Import core services
from core.caching import cache_result, CacheKeyGenerator
from core.rate_limiting import rate_limit, api_rate_limit
from core.performance_monitoring import monitor_performance

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User management."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'is_staff', 'category']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['date_joined', 'last_login', 'username']
    ordering = ['-date_joined']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'retrieve':
            return UserProfileSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    @rate_limit('user_general')
    @monitor_performance
    def me(self, request):
        """Get current user profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    @rate_limit('user_general')
    def activate(self, request, pk=None):
        """Activate a user."""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({'status': 'User activated'})
    
    @action(detail=True, methods=['post'])
    @rate_limit('user_general')
    def deactivate(self, request, pk=None):
        """Deactivate a user."""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({'status': 'User deactivated'})


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Department management."""
    
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Group management (read-only)."""
    
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticated]


class LoanProductViewSet(viewsets.ModelViewSet):
    """ViewSet for LoanProduct management."""
    
    queryset = LoanProduct.objects.all()
    serializer_class = LoanProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'interest_rate', 'max_amount']
    ordering = ['name']


class LoanApplicationViewSet(viewsets.ModelViewSet):
    """ViewSet for LoanApplication management."""
    
    queryset = LoanApplication.objects.all()
    serializer_class = LoanApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'user', 'loan_product']
    search_fields = ['purpose', 'notes']
    ordering_fields = ['application_date', 'amount', 'status']
    ordering = ['-application_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['retrieve', 'update', 'partial_update']:
            return DetailedLoanApplicationSerializer
        return LoanApplicationSerializer
    
    @action(detail=True, methods=['post'])
    @rate_limit('api_loan')
    @monitor_performance
    def approve(self, request, pk=None):
        """Approve a loan application."""
        loan_application = self.get_object()
        loan_service = LoanService()
        
        try:
            result = loan_service.approve_loan_application(loan_application.id, request.user.id)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    @rate_limit('api_loan')
    @monitor_performance
    def reject(self, request, pk=None):
        """Reject a loan application."""
        loan_application = self.get_object()
        loan_service = LoanService()
        
        try:
            result = loan_service.reject_loan_application(loan_application.id, request.user.id)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    @rate_limit('api_loan')
    def my_applications(self, request):
        """Get current user's loan applications."""
        applications = LoanApplication.objects.filter(user=request.user)
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data)


class PaymentInformationViewSet(viewsets.ModelViewSet):
    """ViewSet for Payment_Information management."""
    
    queryset = Payment_Information.objects.all()
    serializer_class = PaymentInformationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'user']
    search_fields = ['reference', 'description']
    ordering_fields = ['payment_date', 'amount', 'status']
    ordering = ['-payment_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['retrieve', 'update', 'partial_update']:
            return DetailedPaymentSerializer
        return PaymentInformationSerializer
    
    @action(detail=False, methods=['get'])
    @rate_limit('api_payment')
    def my_payments(self, request):
        """Get current user's payments."""
        payments = Payment_Information.objects.filter(user=request.user)
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    @rate_limit('api_payment')
    @monitor_performance
    def process_payment(self, request):
        """Process a new payment."""
        payment_service = PaymentService()
        
        try:
            result = payment_service.process_payment(
                user_id=request.user.id,
                amount=request.data.get('amount'),
                payment_method=request.data.get('payment_method'),
                description=request.data.get('description', '')
            )
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BudgetViewSet(viewsets.ModelViewSet):
    """ViewSet for Budget management."""
    
    queryset = Budget.objects.all()
    serializer_class = BudgetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'category', 'user']
    search_fields = ['name', 'description']
    ordering_fields = ['start_date', 'amount', 'created_at']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    @rate_limit('user_general')
    def my_budgets(self, request):
        """Get current user's budgets."""
        budgets = Budget.objects.filter(user=request.user)
        serializer = self.get_serializer(budgets, many=True)
        return Response(serializer.data)


class InvestmentRatesViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Investment_rates (read-only)."""
    
    queryset = Investment_rates.objects.all()
    serializer_class = InvestmentRatesSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'investment_type']
    search_fields = ['investment_type']
    ordering_fields = ['rate', 'min_amount', 'max_amount']
    ordering = ['investment_type']


class InvestorInformationViewSet(viewsets.ModelViewSet):
    """ViewSet for Investor_Information management."""
    
    queryset = Investor_Information.objects.all()
    serializer_class = InvestorInformationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'investment_type', 'user']
    search_fields = ['investment_type']
    ordering_fields = ['investment_date', 'investment_amount', 'status']
    ordering = ['-investment_date']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['retrieve', 'update', 'partial_update']:
            return DetailedInvestmentSerializer
        return InvestorInformationSerializer
    
    @action(detail=False, methods=['get'])
    @rate_limit('user_general')
    def my_investments(self, request):
        """Get current user's investments."""
        investments = Investor_Information.objects.filter(user=request.user)
        serializer = self.get_serializer(investments, many=True)
        return Response(serializer.data)


class EmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet for User management (used as Employee)."""
    
    queryset = User.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'department']
    search_fields = ['employee_id', 'position']
    ordering_fields = ['hire_date', 'salary']
    ordering = ['employee_id']


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for Task management."""
    
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'priority', 'assigned_to']
    search_fields = ['title', 'description']
    ordering_fields = ['due_date', 'created_at', 'priority']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['get'])
    @rate_limit('user_general')
    def my_tasks(self, request):
        """Get current user's tasks."""
        tasks = Task.objects.filter(assigned_to=request.user)
        serializer = self.get_serializer(tasks, many=True)
        return Response(serializer.data)


class MeetingViewSet(viewsets.ModelViewSet):
    """ViewSet for Meeting management."""
    
    queryset = Meetings.objects.all()
    serializer_class = MeetingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'meeting_type', 'organizer']
    search_fields = ['title', 'description']
    ordering_fields = ['meeting_date', 'created_at']
    ordering = ['-meeting_date']


class AIAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet for DiasporaAnalysisData management."""
    
    queryset = DiasporaAnalysisData.objects.all()
    serializer_class = AIAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['analysis_type', 'user']
    search_fields = ['analysis_type']
    ordering_fields = ['created_at', 'confidence_score']
    ordering = ['-created_at']
    
    @action(detail=False, methods=['post'])
    @rate_limit('api_general')
    @monitor_performance
    def analyze_data(self, request):
        """Perform AI analysis on provided data."""
        ai_service = AIAnalyticsService()
        
        try:
            result = ai_service.analyze_data(
                analysis_type=request.data.get('analysis_type'),
                input_data=request.data.get('input_data'),
                user_id=request.user.id
            )
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class StockAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet for AnalysisSession management."""
    
    queryset = AnalysisSession.objects.all()
    serializer_class = StockAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['symbol', 'analysis_type', 'user']
    search_fields = ['symbol']
    ordering_fields = ['analysis_date', 'confidence']
    ordering = ['-analysis_date']


class TrainingProgramViewSet(viewsets.ModelViewSet):
    """ViewSet for JobRoles management."""
    
    queryset = JobRoles.objects.all()
    serializer_class = TrainingProgramSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'instructor']
    search_fields = ['name', 'description']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-created_at']


class AssessmentViewSet(viewsets.ModelViewSet):
    """ViewSet for ClientAssessment management."""
    
    queryset = ClientAssessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'user', 'training_program']
    search_fields = ['feedback']
    ordering_fields = ['assessment_date', 'score']
    ordering = ['-assessment_date']


# Dashboard ViewSets for summary data
class DashboardViewSet(viewsets.ViewSet):
    """ViewSet for dashboard summary data."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    @rate_limit('user_general')
    @monitor_performance
    def summary(self, request):
        """Get dashboard summary data."""
        try:
            # Get summary data using service layers
            loan_service = LoanService()
            payment_service = PaymentService()
            investment_service = InvestmentService()
            
            # Get user's summary data
            user_loans = LoanApplication.objects.filter(user=request.user)[:5]
            user_payments = Payment_Information.objects.filter(user=request.user)[:5]
            user_investments = Investor_Information.objects.filter(user=request.user)[:5]
            
            summary_data = {
                'loans': LoanSummarySerializer(user_loans, many=True).data,
                'payments': PaymentSummarySerializer(user_payments, many=True).data,
                'investments': InvestmentSummarySerializer(user_investments, many=True).data,
                'total_loans': LoanApplication.objects.filter(user=request.user).count(),
                'total_payments': Payment_Information.objects.filter(user=request.user).count(),
                'total_investments': Investor_Information.objects.filter(user=request.user).count(),
            }
            
            return Response(summary_data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    @rate_limit('user_general')
    def analytics(self, request):
        """Get analytics data."""
        try:
            analytics_service = FinancialAnalyticsService()
            result = analytics_service.get_user_analytics(request.user.id)
            return Response(result)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


