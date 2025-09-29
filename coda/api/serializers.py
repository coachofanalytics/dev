"""
API Serializers

This module contains serializers for all major models in the CODA application,
providing comprehensive API data serialization and validation.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from accounts.models import Department
from finance.models import LoanProduct, LoanApplication, Payment_Information, Budget, BudgetRequest, ApprovalPolicy, DisbursementRequest, AutomationAuditLog
from investing.models import Investment_rates, Investor_Information
from management.models import Task, Meetings
from ai_services.models import DiasporaAnalysisData, AnalysisSession
from professional_services.models import ClientAssessment, JobRoles

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'date_joined', 'is_active', 'is_staff', 'category',
            'last_login', 'email_verified'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for User profile information."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'user', 'email', 'first_name', 'last_name',
            'phone_number', 'address', 'city', 'country',
            'date_of_birth', 'gender', 'profile_picture'
        ]


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model."""
    
    class Meta:
        model = Department
        fields = [
            'id', 'name', 'description', 'manager', 'created_at',
            'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GroupSerializer(serializers.ModelSerializer):
    """Serializer for Group model."""
    
    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']


class LoanProductSerializer(serializers.ModelSerializer):
    """Serializer for LoanProduct model."""
    
    class Meta:
        model = LoanProduct
        fields = [
            'id', 'name', 'description', 'interest_rate', 'max_amount',
            'min_amount', 'term_months', 'is_active', 'created_at',
            'updated_at', 'eligibility_criteria'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LoanApplicationSerializer(serializers.ModelSerializer):
    """Serializer for LoanApplication model."""
    
    user = UserSerializer(read_only=True)
    loan_product = LoanProductSerializer(read_only=True)
    guarantor = UserSerializer(read_only=True)
    
    class Meta:
        model = LoanApplication
        fields = [
            'id', 'user', 'loan_product', 'amount', 'term_months',
            'purpose', 'status', 'application_date', 'approval_date',
            'guarantor', 'guarantor_approved', 'notes', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'application_date', 'created_at', 'updated_at']


class PaymentInformationSerializer(serializers.ModelSerializer):
    """Serializer for Payment_Information model."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Payment_Information
        fields = [
            'id', 'user', 'amount', 'payment_method', 'payment_date',
            'status', 'transaction_id', 'reference', 'description',
            'currency', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer for Budget model."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Budget
        fields = [
            'id', 'user', 'name', 'description', 'amount', 'category',
            'start_date', 'end_date', 'is_active', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InvestmentRatesSerializer(serializers.ModelSerializer):
    """Serializer for Investment_rates model."""
    
    class Meta:
        model = Investment_rates
        fields = [
            'id', 'investment_type', 'rate', 'min_amount', 'max_amount',
            'term_months', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InvestorInformationSerializer(serializers.ModelSerializer):
    """Serializer for Investor_Information model."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Investor_Information
        fields = [
            'id', 'user', 'investment_amount', 'investment_type',
            'expected_return', 'risk_level', 'investment_date',
            'maturity_date', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer for User model (used as Employee)."""
    
    department = DepartmentSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for Task model."""
    
    assigned_to = UserSerializer(read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'assigned_to', 'created_by',
            'status', 'priority', 'due_date', 'completed_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MeetingSerializer(serializers.ModelSerializer):
    """Serializer for Meeting model."""
    
    organizer = UserSerializer(read_only=True)
    attendees = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = Meetings
        fields = [
            'id', 'title', 'description', 'organizer', 'attendees',
            'meeting_date', 'duration', 'location', 'meeting_type',
            'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AIAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for DiasporaAnalysisData model."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = DiasporaAnalysisData
        fields = [
            'id', 'user', 'analysis_type', 'input_data', 'result',
            'confidence_score', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StockAnalysisSerializer(serializers.ModelSerializer):
    """Serializer for AnalysisSession model."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = AnalysisSession
        fields = [
            'id', 'user', 'session_name', 'analysis_type', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TrainingProgramSerializer(serializers.ModelSerializer):
    """Serializer for JobRoles model."""
    
    instructor = UserSerializer(read_only=True)
    
    class Meta:
        model = JobRoles
        fields = [
            'id', 'name', 'description', 'instructor', 'duration_hours',
            'start_date', 'end_date', 'max_participants', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AssessmentSerializer(serializers.ModelSerializer):
    """Serializer for ClientAssessment model."""
    
    user = UserSerializer(read_only=True)
    training_program = TrainingProgramSerializer(read_only=True)
    
    class Meta:
        model = ClientAssessment
        fields = [
            'id', 'user', 'training_program', 'score', 'max_score',
            'assessment_date', 'status', 'feedback', 'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Nested serializers for detailed views
class DetailedLoanApplicationSerializer(serializers.ModelSerializer):
    """Detailed serializer for LoanApplication with nested data."""
    
    user = UserSerializer(read_only=True)
    loan_product = LoanProductSerializer(read_only=True)
    guarantor = UserSerializer(read_only=True)
    
    class Meta:
        model = LoanApplication
        fields = [
            'id', 'user', 'loan_product', 'amount', 'term_months',
            'purpose', 'status', 'application_date', 'approval_date',
            'guarantor', 'guarantor_approved', 'notes', 'created_at',
            'updated_at'
        ]


class DetailedPaymentSerializer(serializers.ModelSerializer):
    """Detailed serializer for Payment with nested data."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Payment_Information
        fields = [
            'id', 'user', 'amount', 'payment_method', 'payment_date',
            'status', 'transaction_id', 'reference', 'description',
            'currency', 'created_at', 'updated_at'
        ]


class DetailedInvestmentSerializer(serializers.ModelSerializer):
    """Detailed serializer for Investment with nested data."""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Investor_Information
        fields = [
            'id', 'user', 'investment_amount', 'investment_type',
            'expected_return', 'risk_level', 'investment_date',
            'maturity_date', 'status', 'created_at', 'updated_at'
        ]


# Summary serializers for dashboard views
class UserSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for User dashboard."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']


class LoanSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for Loan dashboard."""
    
    user = UserSummarySerializer(read_only=True)
    
    class Meta:
        model = LoanApplication
        fields = ['id', 'user', 'amount', 'status', 'application_date']


class PaymentSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for Payment dashboard."""
    
    user = UserSummarySerializer(read_only=True)
    
    class Meta:
        model = Payment_Information
        fields = ['id', 'user', 'amount', 'payment_method', 'status', 'payment_date']


class InvestmentSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for Investment dashboard."""
    
    user = UserSummarySerializer(read_only=True)
    
    class Meta:
        model = Investor_Information
        fields = ['id', 'user', 'investment_amount', 'investment_type', 'status', 'investment_date']


# =============================================================================
# AUTOMATION SYSTEM SERIALIZERS
# =============================================================================

class BudgetRequestSerializer(serializers.ModelSerializer):
    """Serializer for BudgetRequest model"""
    
    requester_name = serializers.CharField(source='requester.get_full_name', read_only=True)
    department_name = serializers.CharField(source='department.name', read_only=True)
    budget_category_name = serializers.CharField(source='budget_category.name', read_only=True)
    current_approver_name = serializers.CharField(source='current_approver.get_full_name', read_only=True)
    approval_policy_name = serializers.CharField(source='approval_policy.name', read_only=True)
    is_overdue = serializers.SerializerMethodField()
    
    class Meta:
        model = BudgetRequest
        fields = [
            'id', 'requester', 'requester_name', 'amount', 'currency', 'purpose',
            'department', 'department_name', 'budget_category', 'budget_category_name',
            'request_date', 'required_date', 'priority', 'status', 'rejection_reason',
            'approval_policy', 'approval_policy_name', 'current_approver', 'current_approver_name',
            'approval_chain', 'cost_center', 'attachments', 'is_overdue',
            'created_at', 'updated_at', 'created_by', 'last_modified_by'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by', 'last_modified_by',
            'approval_chain', 'current_approver', 'approval_policy'
        ]
    
    def get_is_overdue(self, obj):
        """Check if request is overdue"""
        return obj.is_overdue()
    
    def create(self, validated_data):
        """Create budget request with proper user assignment"""
        validated_data['created_by'] = self.context['request'].user
        validated_data['last_modified_by'] = self.context['request'].user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Update budget request with proper user assignment"""
        validated_data['last_modified_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ApprovalPolicySerializer(serializers.ModelSerializer):
    """Serializer for ApprovalPolicy model"""
    
    applicable_departments_names = serializers.StringRelatedField(
        source='applicable_departments', many=True, read_only=True
    )
    applicable_categories_names = serializers.StringRelatedField(
        source='applicable_categories', many=True, read_only=True
    )
    
    class Meta:
        model = ApprovalPolicy
        fields = [
            'id', 'name', 'description', 'is_active', 'min_amount', 'max_amount',
            'approver_roles', 'approval_chain', 'auto_approve', 'requires_otp',
            'applicable_departments', 'applicable_departments_names',
            'applicable_categories', 'applicable_categories_names',
            'applicable_user_types', 'max_approval_days', 'escalation_days',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class DisbursementRequestSerializer(serializers.ModelSerializer):
    """Serializer for DisbursementRequest model"""
    
    budget_request_id = serializers.IntegerField(source='budget_request.id', read_only=True)
    budget_request_purpose = serializers.CharField(source='budget_request.purpose', read_only=True)
    requester_name = serializers.CharField(source='budget_request.requester.get_full_name', read_only=True)
    is_otp_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = DisbursementRequest
        fields = [
            'id', 'budget_request', 'budget_request_id', 'budget_request_purpose',
            'requester_name', 'disbursement_method', 'recipient_name', 'recipient_phone',
            'recipient_email', 'bank_account', 'amount', 'currency', 'exchange_rate',
            'status', 'payment_reference', 'transaction_id', 'otp_code', 'otp_expires_at',
            'otp_verified', 'is_otp_expired', 'disbursement_date', 'completion_date',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'otp_code', 'otp_expires_at', 'otp_verified', 'is_otp_expired',
            'disbursement_date', 'completion_date', 'created_at', 'updated_at'
        ]
    
    def get_is_otp_expired(self, obj):
        """Check if OTP has expired"""
        return obj.is_otp_expired()


class AutomationAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AutomationAuditLog model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    content_type_name = serializers.CharField(source='content_type.name', read_only=True)
    
    class Meta:
        model = AutomationAuditLog
        fields = [
            'id', 'action', 'action_type', 'description', 'user', 'user_name',
            'ip_address', 'user_agent', 'content_type', 'content_type_name',
            'object_id', 'object_repr', 'details', 'old_values', 'new_values',
            'success', 'error_message', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at'
        ]


class BudgetRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating budget requests"""
    
    class Meta:
        model = BudgetRequest
        fields = [
            'amount', 'currency', 'purpose', 'department', 'budget_category',
            'required_date', 'priority', 'cost_center', 'attachments'
        ]
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
    
    def validate_required_date(self, value):
        """Validate required date is in the future"""
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Required date must be in the future")
        return value


class BudgetRequestUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating budget requests"""
    
    class Meta:
        model = BudgetRequest
        fields = [
            'amount', 'currency', 'purpose', 'department', 'budget_category',
            'required_date', 'priority', 'cost_center', 'attachments'
        ]
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
    
    def validate_required_date(self, value):
        """Validate required date is in the future"""
        from django.utils import timezone
        if value < timezone.now().date():
            raise serializers.ValidationError("Required date must be in the future")
        return value


class DisbursementRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating disbursement requests"""
    
    class Meta:
        model = DisbursementRequest
        fields = [
            'budget_request', 'disbursement_method', 'recipient_name',
            'recipient_phone', 'recipient_email', 'bank_account', 'amount', 'currency'
        ]
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
    
    def validate_recipient_phone(self, value):
        """Validate phone number format"""
        if value and not value.isdigit():
            raise serializers.ValidationError("Phone number must contain only digits")
        return value


class OTPVerificationSerializer(serializers.Serializer):
    """Serializer for OTP verification"""
    
    otp_code = serializers.CharField(max_length=10, min_length=6)
    
    def validate_otp_code(self, value):
        """Validate OTP code format"""
        if not value.isdigit():
            raise serializers.ValidationError("OTP code must contain only digits")
        return value


class ApprovalActionSerializer(serializers.Serializer):
    """Serializer for approval actions"""
    
    decision = serializers.ChoiceField(choices=['approved', 'rejected'])
    comments = serializers.CharField(required=False, allow_blank=True)
    reason = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validate approval action data"""
        decision = data.get('decision')
        comments = data.get('comments', '')
        reason = data.get('reason', '')
        
        if decision == 'rejected' and not reason:
            raise serializers.ValidationError("Reason is required for rejection")
        
        return data


class PolicyApplicabilitySerializer(serializers.Serializer):
    """Serializer for checking policy applicability"""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    department = serializers.IntegerField(required=False)
    category = serializers.IntegerField(required=False)
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value


