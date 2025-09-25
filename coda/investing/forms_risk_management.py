"""
Enhanced Risk Management Forms for Investing App
Uses optimized models and provides comprehensive form handling
"""

from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date, timedelta

from .models import (
    Investor_Information,
    RiskAssessment,
    RiskAlert,
    ComplianceRecord,
    InvestmentAnalytics,
    InvestorCommunication,
    NotificationPreference
)


class RiskAssessmentForm(forms.ModelForm):
    """
    Comprehensive risk assessment form
    Uses optimized models and provides intelligent validation
    """
    
    class Meta:
        model = RiskAssessment
        fields = [
            'market_risk_score',
            'credit_risk_score', 
            'liquidity_risk_score',
            'operational_risk_score',
            'mitigation_strategies',
            'notes'
        ]
        widgets = {
            'market_risk_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'step': 1
            }),
            'credit_risk_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'step': 1
            }),
            'liquidity_risk_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'step': 1
            }),
            'operational_risk_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 10,
                'step': 1
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional notes about the risk assessment...'
            })
        }
        labels = {
            'market_risk_score': 'Market Risk Score (1-10)',
            'credit_risk_score': 'Credit Risk Score (1-10)',
            'liquidity_risk_score': 'Liquidity Risk Score (1-10)',
            'operational_risk_score': 'Operational Risk Score (1-10)',
            'mitigation_strategies': 'Mitigation Strategies',
            'notes': 'Assessment Notes'
        }
    
    def clean(self):
        """Validate risk assessment data"""
        cleaned_data = super().clean()
        
        # Validate risk scores are within range
        for field_name in ['market_risk_score', 'credit_risk_score', 'liquidity_risk_score', 'operational_risk_score']:
            score = cleaned_data.get(field_name)
            if score is not None and (score < 1 or score > 10):
                raise ValidationError(f'{field_name.replace("_", " ").title()} must be between 1 and 10')
        
        # Check for extreme risk combinations
        scores = [
            cleaned_data.get('market_risk_score', 5),
            cleaned_data.get('credit_risk_score', 5),
            cleaned_data.get('liquidity_risk_score', 5),
            cleaned_data.get('operational_risk_score', 5)
        ]
        
        avg_score = sum(scores) / len(scores)
        high_scores = [s for s in scores if s >= 8]
        
        if avg_score >= 8:
            raise ValidationError('Average risk score is very high. Please review all risk factors.')
        
        if len(high_scores) >= 3:
            raise ValidationError('Too many high-risk factors. Consider mitigation strategies.')
        
        return cleaned_data


class ComplianceRecordForm(forms.ModelForm):
    """
    Compliance record form for tracking regulatory requirements
    """
    
    class Meta:
        model = ComplianceRecord
        fields = [
            'requirement_type',
            'due_date',
            'documents',
            'notes',
            'assigned_to'
        ]
        widgets = {
            'requirement_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'requirement_type': 'Compliance Requirement Type',
            'due_date': 'Due Date',
            'documents': 'Required Documents',
            'notes': 'Notes',
            'assigned_to': 'Assigned To'
        }
    
    def clean_due_date(self):
        """Validate due date"""
        due_date = self.cleaned_data.get('due_date')
        
        if due_date and due_date < date.today():
            raise ValidationError('Due date cannot be in the past')
        
        if due_date and due_date > date.today() + timedelta(days=365):
            raise ValidationError('Due date cannot be more than 1 year in the future')
        
        return due_date


class RiskAlertForm(forms.ModelForm):
    """
    Risk alert form for creating and managing alerts
    """
    
    class Meta:
        model = RiskAlert
        fields = [
            'alert_type',
            'severity',
            'message',
            'resolution_notes'
        ]
        widgets = {
            'alert_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'severity': forms.Select(attrs={
                'class': 'form-control'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'resolution_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            })
        }
        labels = {
            'alert_type': 'Alert Type',
            'severity': 'Severity Level',
            'message': 'Alert Message',
            'resolution_notes': 'Resolution Notes'
        }


class InvestmentAnalyticsForm(forms.ModelForm):
    """
    Investment analytics form for performance tracking
    """
    
    class Meta:
        model = InvestmentAnalytics
        fields = [
            'analysis_date',
            'sharpe_ratio',
            'max_drawdown',
            'volatility',
            'predicted_return',
            'confidence_score',
            'market_correlation',
            'beta',
            'value_at_risk',
            'expected_shortfall',
            'analysis_notes'
        ]
        widgets = {
            'analysis_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'sharpe_ratio': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001'
            }),
            'max_drawdown': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001'
            }),
            'volatility': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001'
            }),
            'predicted_return': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001'
            }),
            'confidence_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': '0.01'
            }),
            'market_correlation': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': -1,
                'max': 1,
                'step': '0.001'
            }),
            'beta': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.001'
            }),
            'value_at_risk': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'expected_shortfall': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
            'analysis_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            })
        }
    
    def clean_confidence_score(self):
        """Validate confidence score"""
        confidence = self.cleaned_data.get('confidence_score')
        if confidence is not None and (confidence < 0 or confidence > 100):
            raise ValidationError('Confidence score must be between 0 and 100')
        return confidence
    
    def clean_market_correlation(self):
        """Validate market correlation"""
        correlation = self.cleaned_data.get('market_correlation')
        if correlation is not None and (correlation < -1 or correlation > 1):
            raise ValidationError('Market correlation must be between -1 and 1')
        return correlation


class InvestorCommunicationForm(forms.ModelForm):
    """
    Investor communication form for tracking interactions
    """
    
    class Meta:
        model = InvestorCommunication
        fields = [
            'communication_type',
            'subject',
            'content',
            'is_automated',
            'template_used'
        ]
        widgets = {
            'communication_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': 200
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6
            }),
            'is_automated': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'template_used': forms.TextInput(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'communication_type': 'Communication Type',
            'subject': 'Subject',
            'content': 'Content',
            'is_automated': 'Automated Communication',
            'template_used': 'Template Used'
        }


class NotificationPreferenceForm(forms.ModelForm):
    """
    Notification preference form for investor settings
    """
    
    class Meta:
        model = NotificationPreference
        fields = [
            'notification_type',
            'frequency',
            'delivery_method',
            'enabled',
            'quiet_hours_start',
            'quiet_hours_end',
            'timezone'
        ]
        widgets = {
            'notification_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'frequency': forms.Select(attrs={
                'class': 'form-control'
            }),
            'delivery_method': forms.Select(attrs={
                'class': 'form-control'
            }),
            'enabled': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'quiet_hours_start': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'quiet_hours_end': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'timezone': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def clean(self):
        """Validate notification preferences"""
        cleaned_data = super().clean()
        
        quiet_start = cleaned_data.get('quiet_hours_start')
        quiet_end = cleaned_data.get('quiet_hours_end')
        
        if quiet_start and quiet_end and quiet_start >= quiet_end:
            raise ValidationError('Quiet hours start time must be before end time')
        
        return cleaned_data


class BulkRiskAssessmentForm(forms.Form):
    """
    Bulk risk assessment form for multiple investments
    """
    
    RISK_FACTORS = [
        ('market_volatility', 'Market Volatility'),
        ('credit_rating', 'Credit Rating'),
        ('liquidity_concerns', 'Liquidity Concerns'),
        ('operational_issues', 'Operational Issues'),
        ('regulatory_changes', 'Regulatory Changes'),
        ('economic_conditions', 'Economic Conditions')
    ]
    
    risk_factor = forms.ChoiceField(
        choices=RISK_FACTORS,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Risk Factor'
    )
    
    impact_level = forms.ChoiceField(
        choices=[
            ('low', 'Low Impact'),
            ('medium', 'Medium Impact'),
            ('high', 'High Impact')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Impact Level'
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        }),
        required=False,
        label='Additional Notes'
    )
    
    def clean_impact_level(self):
        """Validate impact level"""
        impact = self.cleaned_data.get('impact_level')
        if impact not in ['low', 'medium', 'high']:
            raise ValidationError('Invalid impact level selected')
        return impact


class RiskMitigationStrategyForm(forms.Form):
    """
    Risk mitigation strategy form
    """
    
    STRATEGY_TYPES = [
        ('diversification', 'Diversification'),
        ('hedging', 'Hedging'),
        ('stop_loss', 'Stop Loss'),
        ('position_sizing', 'Position Sizing'),
        ('regular_monitoring', 'Regular Monitoring'),
        ('stress_testing', 'Stress Testing'),
        ('insurance', 'Insurance'),
        ('liquidity_management', 'Liquidity Management')
    ]
    
    strategy_type = forms.ChoiceField(
        choices=STRATEGY_TYPES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Strategy Type'
    )
    
    priority = forms.ChoiceField(
        choices=[
            ('low', 'Low Priority'),
            ('medium', 'Medium Priority'),
            ('high', 'High Priority')
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Priority'
    )
    
    implementation_date = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False,
        label='Implementation Date'
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3
        }),
        label='Strategy Description'
    )
    
    def clean_implementation_date(self):
        """Validate implementation date"""
        impl_date = self.cleaned_data.get('implementation_date')
        if impl_date and impl_date < date.today():
            raise ValidationError('Implementation date cannot be in the past')
        return impl_date
