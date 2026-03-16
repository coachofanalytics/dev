"""
Enhanced Risk Management Views for Investing App
Uses optimized models and avoids duplications
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib import messages
from django.db.models import Q, Avg, Count, Max
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta, date
from decimal import Decimal 


from .models import (
    Investor_Information,
    RiskAssessment,
    RiskAlert,
    ComplianceRecord,
    AuditTrail,
    InvestmentAnalytics
)
from .forms_risk_management import (
    RiskAssessmentForm,
    ComplianceRecordForm,
    RiskAlertForm
)


class RiskManagementDashboardView(LoginRequiredMixin, ListView):
    """
    Comprehensive risk management dashboard
    Uses optimized models and provides real-time risk insights
    """
    template_name = 'investing/risk_management_dashboard.html'
    context_object_name = 'risk_summary'
    
    def get_queryset(self):
        """Get risk summary data for the dashboard"""
        user = self.request.user
        
        # Get user's investments
        investments = Investor_Information.objects.filter(
            investor=user,
            is_active=True
        )
        
        # Calculate risk metrics
        risk_summary = {
            'total_investments': investments.count(),
            'high_risk_investments': 0,
            'medium_risk_investments': 0,
            'low_risk_investments': 0,
            'active_alerts': 0,
            'compliance_issues': 0,
            'risk_trend': 'stable'
        }
        
        # Analyze each investment's risk level
        for investment in investments:
            risk_level = investment.get_risk_level()
            if risk_level == 'high':
                risk_summary['high_risk_investments'] += 1
            elif risk_level == 'medium':
                risk_summary['medium_risk_investments'] += 1
            else:
                risk_summary['low_risk_investments'] += 1
        
        # Count active risk alerts
        risk_summary['active_alerts'] = RiskAlert.objects.filter(
            investment__in=investments,
            is_resolved=False
        ).count()
        
        # Count compliance issues
        risk_summary['compliance_issues'] = ComplianceRecord.objects.filter(
            investment__in=investments,
            status__in=['pending', 'in_progress']
        ).count()
        
        return risk_summary
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get recent risk assessments
        context['recent_assessments'] = RiskAssessment.objects.filter(
            investment__investor=user
        ).order_by('-assessment_date')[:5]
        
        # Get active alerts
        context['active_alerts'] = RiskAlert.objects.filter(
            investment__investor=user,
            is_resolved=False
        ).order_by('-created_at')[:10]
        
        # Get compliance status
        context['compliance_records'] = ComplianceRecord.objects.filter(
            investment__investor=user
        ).order_by('due_date')[:10]
        
        # Get risk trend data
        context['risk_trend_data'] = self.get_risk_trend_data(user)
        
        return context
    
    def get_risk_trend_data(self, user):
        """Get risk trend data for charts"""
        # Get risk assessments from the last 6 months
        six_months_ago = date.today() - timedelta(days=180)
        
        assessments = RiskAssessment.objects.filter(
            investment__investor=user,
            assessment_date__gte=six_months_ago
        ).order_by('assessment_date')
        
        trend_data = []
        for assessment in assessments:
            trend_data.append({
                'date': assessment.assessment_date.isoformat(),
                'average_risk': assessment.average_risk_score,
                'overall_rating': assessment.overall_risk_rating
            })
        
        return trend_data


class RiskAssessmentCreateView(LoginRequiredMixin, CreateView):
    """
    Create new risk assessment
    Uses optimized models and provides comprehensive risk analysis
    """
    model = RiskAssessment
    form_class = RiskAssessmentForm
    template_name = 'investing/risk_assessment_form.html'
    
    def form_valid(self, form):
        """Validate and save risk assessment"""
        # Get the investment
        investment_id = self.kwargs.get('investment_id')
        investment = get_object_or_404(
            Investor_Information,
            id=investment_id,
            investor=self.request.user
        )
        
        # Set the investment and assessor
        form.instance.investment = investment
        form.instance.assessed_by = self.request.user
        
        # Calculate overall risk rating based on scores
        avg_score = (
            form.instance.market_risk_score +
            form.instance.credit_risk_score +
            form.instance.liquidity_risk_score +
            form.instance.operational_risk_score
        ) / 4
        
        if avg_score <= 3:
            form.instance.overall_risk_rating = 'low'
        elif avg_score <= 7:
            form.instance.overall_risk_rating = 'medium'
        else:
            form.instance.overall_risk_rating = 'high'
        
        # Create audit trail
        AuditTrail.objects.create(
            investment=investment,
            action='risk_assessment_created',
            performed_by=self.request.user,
            new_values={
                'risk_assessment_id': form.instance.id,
                'overall_risk_rating': form.instance.overall_risk_rating,
                'average_score': float(avg_score)
            },
            reason=f'Risk assessment created with {form.instance.overall_risk_rating} rating'
        )
        
        messages.success(
            self.request,
            f'Risk assessment created successfully. Overall rating: {form.instance.overall_risk_rating.title()}'
        )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return f'/investing/risk-dashboard/'


class ComplianceTrackingView(LoginRequiredMixin, ListView):
    """
    Compliance tracking view
    Uses optimized models for comprehensive compliance management
    """
    template_name = 'investing/compliance_tracking.html'
    context_object_name = 'compliance_records'
    
    def get_queryset(self):
        """Get compliance records for the user"""
        return ComplianceRecord.objects.filter(
            investment__investor=self.request.user
        ).order_by('due_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get compliance statistics
        records = self.get_queryset()
        context['compliance_stats'] = {
            'total_requirements': records.count(),
            'completed': records.filter(status='approved').count(),
            'pending': records.filter(status='pending').count(),
            'overdue': records.filter(
                due_date__lt=date.today(),
                status__in=['pending', 'in_progress']
            ).count()
        }
        
        return context


class RiskAlertManagementView(LoginRequiredMixin, ListView):
    """
    Risk alert management view
    Provides comprehensive alert management capabilities
    """
    template_name = 'investing/risk_alerts.html'
    context_object_name = 'risk_alerts'
    
    def get_queryset(self):
        """Get risk alerts for the user"""
        return RiskAlert.objects.filter(
            investment__investor=self.request.user
        ).order_by('-created_at')
    
    def post(self, request, *args, **kwargs):
        """Handle alert resolution"""
        alert_id = request.POST.get('alert_id')
        resolution_notes = request.POST.get('resolution_notes')
        
        if alert_id:
            alert = get_object_or_404(
                RiskAlert,
                id=alert_id,
                investment__investor=request.user
            )
            
            alert.is_resolved = True
            alert.resolved_date = timezone.now()
            alert.resolved_by = request.user
            alert.resolution_notes = resolution_notes
            alert.save()
            
            messages.success(request, 'Risk alert resolved successfully')
        
        return redirect('investing:risk-alerts')


@login_required
def risk_analytics_api(request):
    """
    API endpoint for risk analytics data
    Provides JSON data for charts and analytics
    """
    user = request.user
    
    # Get investments
    investments = Investor_Information.objects.filter(
        investor=user,
        is_active=True
    )
    
    # Calculate risk distribution
    risk_distribution = {
        'low': 0,
        'medium': 0,
        'high': 0
    }
    
    for investment in investments:
        risk_level = investment.get_risk_level()
        risk_distribution[risk_level] += 1
    
    # Get compliance completion rate
    compliance_records = ComplianceRecord.objects.filter(
        investment__in=investments
    )
    
    compliance_rate = 0
    if compliance_records.exists():
        completed = compliance_records.filter(status='approved').count()
        total = compliance_records.count()
        compliance_rate = (completed / total) * 100
    
    # Get recent risk trend
    recent_assessments = RiskAssessment.objects.filter(
        investment__in=investments,
        assessment_date__gte=date.today() - timedelta(days=30)
    ).order_by('assessment_date')
    
    risk_trend = []
    for assessment in recent_assessments:
        risk_trend.append({
            'date': assessment.assessment_date.isoformat(),
            'score': float(assessment.average_risk_score),
            'rating': assessment.overall_risk_rating
        })
    
    return JsonResponse({
        'risk_distribution': risk_distribution,
        'compliance_rate': compliance_rate,
        'risk_trend': risk_trend,
        'total_investments': investments.count(),
        'active_alerts': RiskAlert.objects.filter(
            investment__in=investments,
            is_resolved=False
        ).count()
    })


@login_required
def auto_risk_assessment(request, investment_id):
    """
    Automated risk assessment based on investment data
    Uses AI-like logic to assess risk automatically
    """
    investment = get_object_or_404(
        Investor_Information,
        id=investment_id,
        investor=request.user
    )
    
    # Calculate automated risk scores
    market_risk = 5  # Default medium risk
    credit_risk = 5
    liquidity_risk = 5
    operational_risk = 5
    
    # Adjust based on investment characteristics
    if investment.amount_invested > Decimal('100000.00'):
        market_risk += 2
        liquidity_risk += 1
    
    if investment.investment_type in ['options', 'vc_investment', 'private_equity']:
        market_risk += 3
        operational_risk += 2
    
    if investment.duration and investment.duration > 24:  # More than 2 years
        market_risk += 1
        liquidity_risk += 2
    
    # Adjust based on risk tolerance
    if investment.risk_tolerance == 'conservative':
        market_risk -= 1
        credit_risk -= 1
    elif investment.risk_tolerance == 'aggressive':
        market_risk += 1
        operational_risk += 1
    
    # Ensure scores are within 1-10 range
    market_risk = max(1, min(10, market_risk))
    credit_risk = max(1, min(10, credit_risk))
    liquidity_risk = max(1, min(10, liquidity_risk))
    operational_risk = max(1, min(10, operational_risk))
    
    # Calculate overall rating
    avg_score = (market_risk + credit_risk + liquidity_risk + operational_risk) / 4
    if avg_score <= 3:
        overall_rating = 'low'
    elif avg_score <= 7:
        overall_rating = 'medium'
    else:
        overall_rating = 'high'
    
    # Create automated risk assessment
    assessment = RiskAssessment.objects.create(
        investment=investment,
        assessment_date=date.today(),
        market_risk_score=market_risk,
        credit_risk_score=credit_risk,
        liquidity_risk_score=liquidity_risk,
        operational_risk_score=operational_risk,
        overall_risk_rating=overall_rating,
        mitigation_strategies=[
            {'strategy': 'diversification', 'priority': 'high'},
            {'strategy': 'regular_monitoring', 'priority': 'medium'},
            {'strategy': 'stop_loss', 'priority': 'high' if overall_rating == 'high' else 'medium'}
        ],
        notes=f'Automated risk assessment generated on {date.today()}',
        assessed_by=request.user
    )
    
    # Create audit trail
    AuditTrail.objects.create(
        investment=investment,
        action='auto_risk_assessment',
        performed_by=request.user,
        new_values={
            'assessment_id': assessment.id,
            'overall_rating': overall_rating,
            'average_score': float(avg_score)
        },
        reason='Automated risk assessment completed'
    )
    
    messages.success(
        request,
        f'Automated risk assessment completed. Overall rating: {overall_rating.title()}'
    )
    
    return redirect('investing:risk-dashboard')
