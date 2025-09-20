"""
API Serializers

This module contains serializers for all major models in the CODA application,
providing comprehensive API data serialization and validation.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from accounts.models import Department
from finance.models import LoanProduct, LoanApplication, Payment_Information, Budget
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


