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
from finance.models import LoanProduct, LoanApplication, Payment_Information, Budget, BudgetRequest, ApprovalPolicy, DisbursementRequest, AutomationAuditLog
from investing.models import Investment_rates, Investor_Information
from management.models import Task, Meetings
from ai_services.models import DiasporaAnalysisData, AnalysisSession
from professional_services.models import ClientAssessment, JobRoles

# Import service layers
from finance.services import LoanService, PaymentService, BudgetService, FinancialAnalyticsService
from finance.services.automation_service import BudgetRequestService, ApprovalEngineService, DisbursementService, AutomationAuditService
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
    UserSummarySerializer, LoanSummarySerializer, PaymentSummarySerializer, InvestmentSummarySerializer,
    BudgetRequestSerializer, ApprovalPolicySerializer, DisbursementRequestSerializer, AutomationAuditLogSerializer
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


# =============================================================================
# AUTOMATION SYSTEM VIEWSETS
# =============================================================================

class BudgetRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for budget request management"""
    
    queryset = BudgetRequest.objects.all()
    serializer_class = BudgetRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['purpose', 'requester__username', 'department__name']
    ordering_fields = ['request_date', 'required_date', 'amount', 'created_at']
    ordering = ['-request_date']
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # If user is not staff, only show their own requests
        if not self.request.user.is_staff:
            queryset = queryset.filter(requester=self.request.user)
        
        return queryset.select_related(
            'requester', 'department', 'budget_category', 
            'current_approver', 'approval_policy'
        )
    
    @action(detail=True, methods=['post'])
    def submit_for_approval(self, request, pk=None):
        """Submit budget request for approval"""
        try:
            service = BudgetRequestService()
            budget_request = service.submit_for_approval(pk, request.user, request)
            
            serializer = self.get_serializer(budget_request)
            return Response({
                'success': True,
                'message': 'Request submitted for approval successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve budget request"""
        try:
            service = ApprovalEngineService()
            budget_request = service.process_approval(
                pk, 
                request.user, 
                'approved',
                request.data.get('comments', ''),
                request
            )
            
            serializer = self.get_serializer(budget_request)
            return Response({
                'success': True,
                'message': 'Request approved successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject budget request"""
        try:
            service = ApprovalEngineService()
            budget_request = service.process_approval(
                pk, 
                request.user, 
                'rejected',
                request.data.get('reason', ''),
                request
            )
            
            serializer = self.get_serializer(budget_request)
            return Response({
                'success': True,
                'message': 'Request rejected successfully',
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def escalate(self, request, pk=None):
        """Escalate budget request"""
        try:
            service = ApprovalEngineService()
            budget_request = service.escalate_request(pk, request.user, request)
            
            serializer = self.get_serializer(budget_request)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_requests(self, request):
        """Get current user's budget requests"""
        queryset = self.get_queryset().filter(requester=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending_approvals(self, request):
        """Get requests pending approval by current user"""
        queryset = self.get_queryset().filter(
            current_approver=request.user,
            status='under_review'
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ApprovalPolicyViewSet(viewsets.ModelViewSet):
    """ViewSet for approval policy management"""
    
    queryset = ApprovalPolicy.objects.all()
    serializer_class = ApprovalPolicySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'auto_approve', 'requires_otp']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'min_amount', 'created_at']
    ordering = ['min_amount']
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # Only staff can manage policies
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        return queryset.prefetch_related(
            'applicable_departments', 'applicable_categories'
        )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate approval policy"""
        try:
            policy = self.get_object()
            policy.is_active = True
            policy.save()
            
            serializer = self.get_serializer(policy)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate approval policy"""
        try:
            policy = self.get_object()
            policy.is_active = False
            policy.save()
            
            serializer = self.get_serializer(policy)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def applicable_policies(self, request):
        """Get policies applicable to a specific request"""
        try:
            amount = request.query_params.get('amount')
            department = request.query_params.get('department')
            category = request.query_params.get('category')
            
            if not amount:
                return Response({'error': 'Amount is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create a mock request object for policy matching
            class MockRequest:
                def __init__(self, amount, department, category):
                    self.amount = float(amount)
                    self.department_id = department
                    self.budget_category_id = category
            
            mock_request = MockRequest(amount, department, category)
            
            service = ApprovalEngineService()
            policy = service.get_applicable_policy(mock_request)
            
            if policy:
                serializer = self.get_serializer(policy)
                return Response(serializer.data)
            else:
                return Response({'message': 'No applicable policy found'})
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class DisbursementRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for disbursement request management"""
    
    queryset = DisbursementRequest.objects.all()
    serializer_class = DisbursementRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'disbursement_method', 'currency']
    search_fields = ['recipient_name', 'recipient_email', 'transaction_id', 'payment_reference']
    ordering_fields = ['created_at', 'disbursement_date', 'amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # If user is not staff, only show their own disbursements
        if not self.request.user.is_staff:
            queryset = queryset.filter(budget_request__requester=self.request.user)
        
        return queryset.select_related(
            'budget_request', 'budget_request__requester'
        )
    
    @action(detail=True, methods=['post'])
    def process_disbursement(self, request, pk=None):
        """Process disbursement request"""
        try:
            service = DisbursementService()
            disbursement_request = service.process_disbursement(pk, request.user, request)
            
            serializer = self.get_serializer(disbursement_request)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def verify_otp(self, request, pk=None):
        """Verify OTP for disbursement"""
        try:
            otp_code = request.data.get('otp_code')
            if not otp_code:
                return Response({'error': 'OTP code is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            service = DisbursementService()
            disbursement_request = service.verify_otp(pk, otp_code, request.user, request)
            
            serializer = self.get_serializer(disbursement_request)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def resend_otp(self, request, pk=None):
        """Resend OTP for disbursement"""
        try:
            disbursement_request = self.get_object()
            disbursement_request.generate_otp()
            
            service = DisbursementService()
            service.otp_service.send_otp_email(
                disbursement_request.budget_request.requester,
                disbursement_request.otp_code,
                disbursement_request
            )
            
            serializer = self.get_serializer(disbursement_request)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel disbursement request"""
        try:
            disbursement_request = self.get_object()
            disbursement_request.status = 'cancelled'
            disbursement_request.save()
            
            serializer = self.get_serializer(disbursement_request)
            return Response(serializer.data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_disbursements(self, request):
        """Get current user's disbursement requests"""
        queryset = self.get_queryset().filter(budget_request__requester=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class AutomationAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for automation audit log viewing (read-only)"""
    
    queryset = AutomationAuditLog.objects.all()
    serializer_class = AutomationAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['action_type', 'success', 'user', 'created_at']
    search_fields = ['action', 'description', 'user__username', 'object_repr']
    ordering_fields = ['created_at', 'action']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter queryset based on user permissions"""
        queryset = super().get_queryset()
        
        # If user is not staff, only show their own audit logs
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)
        
        return queryset.select_related('user', 'content_type')
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export audit logs to CSV"""
        try:
            import csv
            from django.http import HttpResponse
            
            queryset = self.get_queryset()
            
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
            
            writer = csv.writer(response)
            writer.writerow([
                'ID', 'Action', 'Action Type', 'User', 'Object', 
                'Success', 'Created At', 'IP Address'
            ])
            
            for log in queryset:
                writer.writerow([
                    log.id, log.action, log.action_type, log.user.username,
                    log.object_repr, log.success, log.created_at, log.ip_address
                ])
            
            return response
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get audit log statistics"""
        try:
            from django.db.models import Count
            
            queryset = self.get_queryset()
            
            stats = {
                'total_logs': queryset.count(),
                'successful_actions': queryset.filter(success=True).count(),
                'failed_actions': queryset.filter(success=False).count(),
                'action_types': queryset.values('action_type').annotate(
                    count=Count('id')
                ).order_by('-count'),
                'recent_activity': queryset.order_by('-created_at')[:10]
            }
            
            return Response(stats)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


