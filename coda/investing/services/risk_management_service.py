"""
Enhanced Risk Management Service for Investing App
Uses optimized models and provides comprehensive risk analysis
"""

from datetime import datetime, timedelta, date
from decimal import Decimal
from django.db.models import Q, Avg, Count, Max, Min
from django.contrib.auth import get_user_model
from typing import Dict, List, Optional, Tuple

from ..models import (
    Investor_Information,
    RiskAssessment,
    RiskAlert,
    ComplianceRecord,
    AuditTrail,
    InvestmentAnalytics,
    InvestorCommunication,
    NotificationPreference
)

User = get_user_model()


class RiskManagementService:
    """
    Comprehensive risk management service
    Provides risk analysis, assessment, and monitoring capabilities
    """
    
    def __init__(self, user: User):
        self.user = user
        self.investments = Investor_Information.objects.filter(
            investor=user,
            is_active=True
        )
    
    def get_risk_summary(self) -> Dict:
        """
        Get comprehensive risk summary for user's investments
        """
        summary = {
            'total_investments': self.investments.count(),
            'high_risk_count': 0,
            'medium_risk_count': 0,
            'low_risk_count': 0,
            'active_alerts': 0,
            'compliance_issues': 0,
            'risk_score_average': 0,
            'risk_trend': 'stable'
        }
        
        # Analyze risk levels
        for investment in self.investments:
            risk_level = investment.get_risk_level()
            if risk_level == 'high':
                summary['high_risk_count'] += 1
            elif risk_level == 'medium':
                summary['medium_risk_count'] += 1
            else:
                summary['low_risk_count'] += 1
        
        # Count active alerts
        summary['active_alerts'] = RiskAlert.objects.filter(
            investment__in=self.investments,
            is_resolved=False
        ).count()
        
        # Count compliance issues
        summary['compliance_issues'] = ComplianceRecord.objects.filter(
            investment__in=self.investments,
            status__in=['pending', 'in_progress']
        ).count()
        
        # Calculate average risk score
        recent_assessments = RiskAssessment.objects.filter(
            investment__in=self.investments,
            assessment_date__gte=date.today() - timedelta(days=30)
        )
        
        if recent_assessments.exists():
            summary['risk_score_average'] = recent_assessments.aggregate(
                avg_score=Avg('average_risk_score')
            )['avg_score'] or 0
        
        # Determine risk trend
        summary['risk_trend'] = self._calculate_risk_trend()
        
        return summary
    
    def _calculate_risk_trend(self) -> str:
        """
        Calculate risk trend based on recent assessments
        """
        thirty_days_ago = date.today() - timedelta(days=30)
        sixty_days_ago = date.today() - timedelta(days=60)
        
        recent_assessments = RiskAssessment.objects.filter(
            investment__in=self.investments,
            assessment_date__gte=thirty_days_ago
        )
        
        older_assessments = RiskAssessment.objects.filter(
            investment__in=self.investments,
            assessment_date__gte=sixty_days_ago,
            assessment_date__lt=thirty_days_ago
        )
        
        if not recent_assessments.exists() or not older_assessments.exists():
            return 'stable'
        
        recent_avg = recent_assessments.aggregate(
            avg=Avg('average_risk_score')
        )['avg']
        
        older_avg = older_assessments.aggregate(
            avg=Avg('average_risk_score')
        )['avg']
        
        if recent_avg > older_avg + 0.5:
            return 'increasing'
        elif recent_avg < older_avg - 0.5:
            return 'decreasing'
        else:
            return 'stable'
    
    def create_automated_risk_assessment(self, investment: Investor_Information) -> RiskAssessment:
        """
        Create automated risk assessment based on investment characteristics
        """
        # Calculate risk scores based on investment characteristics
        market_risk = self._calculate_market_risk(investment)
        credit_risk = self._calculate_credit_risk(investment)
        liquidity_risk = self._calculate_liquidity_risk(investment)
        operational_risk = self._calculate_operational_risk(investment)
        
        # Calculate overall rating
        avg_score = (market_risk + credit_risk + liquidity_risk + operational_risk) / 4
        
        if avg_score <= 3:
            overall_rating = 'low'
        elif avg_score <= 7:
            overall_rating = 'medium'
        else:
            overall_rating = 'high'
        
        # Create assessment
        assessment = RiskAssessment.objects.create(
            investment=investment,
            assessment_date=date.today(),
            market_risk_score=market_risk,
            credit_risk_score=credit_risk,
            liquidity_risk_score=liquidity_risk,
            operational_risk_score=operational_risk,
            overall_risk_rating=overall_rating,
            mitigation_strategies=self._generate_mitigation_strategies(overall_rating, avg_score),
            notes=f'Automated risk assessment generated on {date.today()}',
            assessed_by=self.user
        )
        
        # Create audit trail
        self._create_audit_trail(
            investment=investment,
            action='auto_risk_assessment',
            new_values={
                'assessment_id': assessment.id,
                'overall_rating': overall_rating,
                'average_score': float(avg_score)
            },
            reason='Automated risk assessment completed'
        )
        
        return assessment
    
    def _calculate_market_risk(self, investment: Investor_Information) -> int:
        """Calculate market risk score"""
        score = 5  # Base score
        
        # Adjust based on investment type
        high_risk_types = ['options', 'vc_investment', 'private_equity']
        if investment.investment_type in high_risk_types:
            score += 3
        
        # Adjust based on amount
        if investment.amount_invested > Decimal('100000.00'):
            score += 2
        
        # Adjust based on duration
        if investment.duration and investment.duration > 24:
            score += 1
        
        return max(1, min(10, score))
    
    def _calculate_credit_risk(self, investment: Investor_Information) -> int:
        """Calculate credit risk score"""
        score = 5  # Base score
        
        # Adjust based on investor risk tolerance
        if investment.risk_tolerance == 'conservative':
            score -= 2
        elif investment.risk_tolerance == 'aggressive':
            score += 2
        
        # Adjust based on KYC status
        if investment.kyc_status == 'verified':
            score -= 1
        elif investment.kyc_status == 'rejected':
            score += 3
        
        return max(1, min(10, score))
    
    def _calculate_liquidity_risk(self, investment: Investor_Information) -> int:
        """Calculate liquidity risk score"""
        score = 5  # Base score
        
        # Adjust based on investment type
        illiquid_types = ['vc_investment', 'private_equity']
        if investment.investment_type in illiquid_types:
            score += 3
        
        # Adjust based on duration
        if investment.duration and investment.duration > 36:  # More than 3 years
            score += 2
        
        return max(1, min(10, score))
    
    def _calculate_operational_risk(self, investment: Investor_Information) -> int:
        """Calculate operational risk score"""
        score = 5  # Base score
        
        # Adjust based on compliance status
        if not investment.is_compliance_complete():
            score += 2
        
        # Adjust based on document completeness
        if len(investment.documents) == 0:
            score += 1
        
        return max(1, min(10, score))
    
    def _generate_mitigation_strategies(self, overall_rating: str, avg_score: float) -> List[Dict]:
        """Generate appropriate mitigation strategies"""
        strategies = []
        
        if overall_rating == 'high' or avg_score >= 7:
            strategies.extend([
                {'strategy': 'diversification', 'priority': 'high'},
                {'strategy': 'stop_loss', 'priority': 'high'},
                {'strategy': 'regular_monitoring', 'priority': 'high'},
                {'strategy': 'hedging', 'priority': 'medium'}
            ])
        elif overall_rating == 'medium' or avg_score >= 4:
            strategies.extend([
                {'strategy': 'diversification', 'priority': 'medium'},
                {'strategy': 'regular_monitoring', 'priority': 'medium'},
                {'strategy': 'position_sizing', 'priority': 'medium'}
            ])
        else:
            strategies.extend([
                {'strategy': 'regular_monitoring', 'priority': 'low'},
                {'strategy': 'performance_tracking', 'priority': 'low'}
            ])
        
        return strategies
    
    def create_risk_alert(self, investment: Investor_Information, alert_type: str, 
                         severity: str, message: str, **kwargs) -> RiskAlert:
        """
        Create a new risk alert
        """
        alert = RiskAlert.objects.create(
            investment=investment,
            alert_type=alert_type,
            severity=severity,
            message=message,
            triggered_by=kwargs.get('triggered_by', 'system'),
            data_snapshot=kwargs.get('data_snapshot', {})
        )
        
        # Send notification if enabled
        self._send_alert_notification(alert)
        
        return alert
    
    def _send_alert_notification(self, alert: RiskAlert):
        """Send notification for risk alert"""
        # Check if user has notifications enabled
        notification_prefs = NotificationPreference.objects.filter(
            investor=alert.investment.investor,
            notification_type='market_alert',
            enabled=True
        )
        
        if notification_prefs.exists():
            # Create communication record
            InvestorCommunication.objects.create(
                investment=alert.investment,
                communication_type='notification',
                subject=f'Risk Alert: {alert.get_alert_type_display()}',
                content=alert.message,
                sent_by=self.user,
                is_automated=True,
                template_used='risk_alert_notification'
            )
    
    def get_compliance_status(self) -> Dict:
        """
        Get comprehensive compliance status
        """
        compliance_records = ComplianceRecord.objects.filter(
            investment__in=self.investments
        )
        
        status = {
            'total_requirements': compliance_records.count(),
            'completed': compliance_records.filter(status='approved').count(),
            'pending': compliance_records.filter(status='pending').count(),
            'in_progress': compliance_records.filter(status='in_progress').count(),
            'overdue': compliance_records.filter(
                due_date__lt=date.today(),
                status__in=['pending', 'in_progress']
            ).count(),
            'completion_rate': 0
        }
        
        if status['total_requirements'] > 0:
            status['completion_rate'] = (status['completed'] / status['total_requirements']) * 100
        
        return status
    
    def create_compliance_record(self, investment: Investor_Information, 
                                requirement_type: str, due_date: date, **kwargs) -> ComplianceRecord:
        """
        Create a new compliance record
        """
        record = ComplianceRecord.objects.create(
            investment=investment,
            requirement_type=requirement_type,
            due_date=due_date,
            notes=kwargs.get('notes', ''),
            assigned_to=kwargs.get('assigned_to', self.user)
        )
        
        # Create audit trail
        self._create_audit_trail(
            investment=investment,
            action='compliance_record_created',
            new_values={
                'record_id': record.id,
                'requirement_type': requirement_type,
                'due_date': due_date.isoformat()
            },
            reason=f'Compliance record created for {requirement_type}'
        )
        
        return record
    
    def _create_audit_trail(self, investment: Investor_Information, action: str, 
                           new_values: Dict, old_values: Dict = None, reason: str = ''):
        """Create audit trail entry"""
        AuditTrail.objects.create(
            investment=investment,
            action=action,
            performed_by=self.user,
            old_values=old_values or {},
            new_values=new_values,
            reason=reason
        )
    
    def get_investment_analytics(self, investment: Investor_Information) -> Optional[InvestmentAnalytics]:
        """
        Get latest analytics for an investment
        """
        return InvestmentAnalytics.objects.filter(
            investment=investment
        ).order_by('-analysis_date').first()
    
    def create_investment_analytics(self, investment: Investor_Information, 
                                   analytics_data: Dict) -> InvestmentAnalytics:
        """
        Create new investment analytics
        """
        analytics = InvestmentAnalytics.objects.create(
            investment=investment,
            analysis_date=analytics_data.get('analysis_date', date.today()),
            sharpe_ratio=analytics_data.get('sharpe_ratio'),
            max_drawdown=analytics_data.get('max_drawdown'),
            volatility=analytics_data.get('volatility'),
            predicted_return=analytics_data.get('predicted_return'),
            confidence_score=analytics_data.get('confidence_score'),
            market_correlation=analytics_data.get('market_correlation'),
            beta=analytics_data.get('beta'),
            value_at_risk=analytics_data.get('value_at_risk'),
            expected_shortfall=analytics_data.get('expected_shortfall'),
            analysis_notes=analytics_data.get('analysis_notes', ''),
            calculated_by=self.user
        )
        
        return analytics
    
    def get_risk_trend_data(self, days: int = 180) -> List[Dict]:
        """
        Get risk trend data for charts
        """
        start_date = date.today() - timedelta(days=days)
        
        assessments = RiskAssessment.objects.filter(
            investment__in=self.investments,
            assessment_date__gte=start_date
        ).order_by('assessment_date')
        
        trend_data = []
        for assessment in assessments:
            trend_data.append({
                'date': assessment.assessment_date.isoformat(),
                'average_risk': float(assessment.average_risk_score),
                'overall_rating': assessment.overall_risk_rating,
                'market_risk': assessment.market_risk_score,
                'credit_risk': assessment.credit_risk_score,
                'liquidity_risk': assessment.liquidity_risk_score,
                'operational_risk': assessment.operational_risk_score
            })
        
        return trend_data
    
    def get_performance_metrics(self) -> Dict:
        """
        Get performance metrics for all investments
        """
        metrics = {
            'total_return': 0,
            'average_return_rate': 0,
            'best_performer': None,
            'worst_performer': None,
            'volatility': 0
        }
        
        if not self.investments.exists():
            return metrics
        
        # Calculate total return
        total_invested = sum(inv.amount_invested for inv in self.investments)
        total_current_value = sum(inv.current_value for inv in self.investments)
        
        if total_invested > 0:
            metrics['total_return'] = ((total_current_value - total_invested) / total_invested) * 100
        
        # Calculate average return rate
        return_rates = [inv.actual_return_rate for inv in self.investments if inv.actual_return_rate]
        if return_rates:
            metrics['average_return_rate'] = sum(return_rates) / len(return_rates)
        
        # Find best and worst performers
        if self.investments.exists():
            best_investment = max(self.investments, key=lambda x: x.actual_return_rate or 0)
            worst_investment = min(self.investments, key=lambda x: x.actual_return_rate or 0)
            
            metrics['best_performer'] = {
                'investment': best_investment,
                'return_rate': best_investment.actual_return_rate
            }
            
            metrics['worst_performer'] = {
                'investment': worst_investment,
                'return_rate': worst_investment.actual_return_rate
            }
        
        return metrics
