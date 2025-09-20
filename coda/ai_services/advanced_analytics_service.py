"""
Advanced Analytics Service for AI Platform
Provides comprehensive behavioral insights and predictive analytics
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from django.core.cache import cache

from .models import (
    UserBehaviorAnalytics, AnalysisSession, DiasporaAnalysisData,
    DiasporaAnalysisTypes, AIModelTypes
)

logger = logging.getLogger(__name__)

class AdvancedAnalyticsService:
    """Advanced analytics service with behavioral insights and predictive analytics"""
    
    def __init__(self):
        self.cache_timeout = 600  # 10 minutes cache
        self.analytics_cache_prefix = "advanced_analytics"
    
    def get_comprehensive_dashboard_data(self, days: int = 30) -> Dict:
        """Get comprehensive dashboard data with advanced analytics"""
        cache_key = f"{self.analytics_cache_prefix}_dashboard_{days}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            analytics_data = {
                'period': {
                    'days': days,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'overview_metrics': self._get_overview_metrics(start_date, end_date),
                'user_behavior_insights': self._get_user_behavior_insights(start_date, end_date),
                'ai_performance_analytics': self._get_ai_performance_analytics(start_date, end_date),
                'conversion_funnel': self._get_conversion_funnel(start_date, end_date),
                'predictive_insights': self._get_predictive_insights(start_date, end_date),
                'recommendations': self._get_analytics_recommendations(start_date, end_date)
            }
            
            # Cache the data
            cache.set(cache_key, analytics_data, self.cache_timeout)
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"Error getting comprehensive dashboard data: {e}")
            return {
                'error': str(e),
                'period': {'days': days, 'start_date': None, 'end_date': None},
                'overview_metrics': {},
                'user_behavior_insights': {},
                'ai_performance_analytics': {},
                'conversion_funnel': {},
                'predictive_insights': {},
                'recommendations': []
            }
    
    def _get_overview_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get comprehensive overview metrics"""
        try:
            total_sessions = AnalysisSession.objects.filter(start_time__gte=start_date).count()
            total_analyses = DiasporaAnalysisData.objects.filter(
                created_at__gte=start_date, is_active=True
            ).count()
            total_events = UserBehaviorAnalytics.objects.filter(timestamp__gte=start_date).count()
            
            unique_users = UserBehaviorAnalytics.objects.filter(
                timestamp__gte=start_date, user__isnull=False
            ).values('user').distinct().count()
            
            return {
                'total_sessions': total_sessions,
                'total_analyses': total_analyses,
                'total_events': total_events,
                'unique_users': unique_users,
                'avg_analyses_per_session': round(total_analyses / total_sessions, 2) if total_sessions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting overview metrics: {e}")
            return {}
    
    def _get_user_behavior_insights(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get detailed user behavior insights"""
        try:
            events = UserBehaviorAnalytics.objects.filter(timestamp__gte=start_date)
            
            # Device patterns
            device_patterns = events.values('device_type').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Browser patterns
            browser_patterns = events.values('browser').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            return {
                'device_patterns': list(device_patterns),
                'browser_patterns': list(browser_patterns),
                'engagement_levels': self._analyze_engagement_levels(start_date, end_date)
            }
            
        except Exception as e:
            logger.error(f"Error getting user behavior insights: {e}")
            return {}
    
    def _get_ai_performance_analytics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get comprehensive AI performance analytics"""
        try:
            analyses = DiasporaAnalysisData.objects.filter(
                created_at__gte=start_date, is_active=True
            )
            
            # Model performance comparison
            model_performance = analyses.values('model_used').annotate(
                count=Count('id'),
                avg_confidence=Avg('confidence_score'),
                avg_processing_time=Avg('processing_time')
            ).order_by('-count')
            
            # Analysis type performance
            type_performance = analyses.values('analysis_type').annotate(
                count=Count('id'),
                avg_confidence=Avg('confidence_score'),
                avg_processing_time=Avg('processing_time')
            ).order_by('-count')
            
            return {
                'model_performance': list(model_performance),
                'type_performance': list(type_performance),
                'quality_trends': self._analyze_quality_trends(start_date, end_date)
            }
            
        except Exception as e:
            logger.error(f"Error getting AI performance analytics: {e}")
            return {}
    
    def _get_conversion_funnel(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get conversion funnel analysis"""
        try:
            events = UserBehaviorAnalytics.objects.filter(timestamp__gte=start_date)
            
            # Define funnel stages
            funnel_stages = {
                'page_view': events.filter(event_type='page_view').count(),
                'form_start': events.filter(event_type='form_start').count(),
                'form_submit': events.filter(event_type='form_submit').count(),
                'analysis_complete': events.filter(event_type='analysis_complete').count(),
                'result_view': events.filter(event_type='result_view').count()
            }
            
            # Calculate conversion rates
            conversion_rates = {}
            stages = list(funnel_stages.keys())
            for i in range(1, len(stages)):
                prev_stage = stages[i-1]
                current_stage = stages[i]
                if funnel_stages[prev_stage] > 0:
                    conversion_rates[f"{prev_stage}_to_{current_stage}"] = round(
                        (funnel_stages[current_stage] / funnel_stages[prev_stage]) * 100, 2
                    )
            
            return {
                'funnel_stages': funnel_stages,
                'conversion_rates': conversion_rates,
                'optimization_opportunities': self._identify_funnel_optimizations(funnel_stages)
            }
            
        except Exception as e:
            logger.error(f"Error getting conversion funnel: {e}")
            return {}
    
    def _get_predictive_insights(self, start_date: datetime, end_date: datetime) -> Dict:
        """Get predictive insights and trends"""
        try:
            # Usage trend prediction
            usage_trends = self._predict_usage_trends(start_date, end_date)
            
            # Capacity planning
            capacity_forecast = self._forecast_capacity_needs(start_date, end_date)
            
            return {
                'usage_trends': usage_trends,
                'capacity_forecast': capacity_forecast,
                'risk_assessment': self._assess_risks(start_date, end_date)
            }
            
        except Exception as e:
            logger.error(f"Error getting predictive insights: {e}")
            return {}
    
    def _get_analytics_recommendations(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get actionable analytics recommendations"""
        try:
            recommendations = []
            
            # Get data for analysis
            overview = self._get_overview_metrics(start_date, end_date)
            funnel = self._get_conversion_funnel(start_date, end_date)
            
            # Conversion optimization recommendations
            if funnel.get('conversion_rates', {}).get('form_start_to_form_submit', 0) < 70:
                recommendations.append({
                    'category': 'Conversion Optimization',
                    'priority': 'High',
                    'title': 'Improve Form Completion Rate',
                    'description': 'Form completion rate is below 70%. Consider simplifying forms.',
                    'impact': 'High',
                    'effort': 'Medium'
                })
            
            # Performance optimization recommendations
            performance = self._get_ai_performance_analytics(start_date, end_date)
            if performance.get('model_performance'):
                avg_processing_time = sum(
                    model['avg_processing_time'] for model in performance['model_performance']
                ) / len(performance['model_performance'])
                
                if avg_processing_time > 3.0:
                    recommendations.append({
                        'category': 'Performance Optimization',
                        'priority': 'Medium',
                        'title': 'Optimize AI Processing Times',
                        'description': 'Average processing time is above 3 seconds.',
                        'impact': 'Medium',
                        'effort': 'High'
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting analytics recommendations: {e}")
            return []
    
    # Helper methods
    def _analyze_engagement_levels(self, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze user engagement levels"""
        try:
            sessions = AnalysisSession.objects.filter(start_time__gte=start_date)
            
            engagement_levels = {
                'low': 0,    # 1-2 analyses
                'medium': 0, # 3-5 analyses
                'high': 0    # 6+ analyses
            }
            
            for session in sessions:
                if session.total_analyses <= 2:
                    engagement_levels['low'] += 1
                elif session.total_analyses <= 5:
                    engagement_levels['medium'] += 1
                else:
                    engagement_levels['high'] += 1
            
            return engagement_levels
            
        except Exception as e:
            logger.error(f"Error analyzing engagement levels: {e}")
            return {}
    
    def _analyze_quality_trends(self, start_date: datetime, end_date: datetime) -> Dict:
        """Analyze quality trends over time"""
        try:
            # Daily quality trends
            daily_quality = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                day_analyses = DiasporaAnalysisData.objects.filter(
                    created_at__gte=current_date,
                    created_at__lt=next_date,
                    is_active=True
                )
                
                if day_analyses.exists():
                    avg_confidence = day_analyses.aggregate(
                        avg_confidence=Avg('confidence_score')
                    )['avg_confidence'] or 0
                    
                    daily_quality.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'avg_confidence': round(avg_confidence, 3),
                        'analysis_count': day_analyses.count()
                    })
                
                current_date = next_date
            
            return {
                'daily_trends': daily_quality,
                'overall_trend': 'stable'  # Simplified for now
            }
            
        except Exception as e:
            logger.error(f"Error analyzing quality trends: {e}")
            return {}
    
    def _identify_funnel_optimizations(self, funnel_stages: Dict) -> List[Dict]:
        """Identify funnel optimization opportunities"""
        optimizations = []
        
        stages = list(funnel_stages.keys())
        for i in range(1, len(stages)):
            prev_stage = stages[i-1]
            current_stage = stages[i]
            
            if funnel_stages[prev_stage] > 0:
                conversion_rate = (funnel_stages[current_stage] / funnel_stages[prev_stage]) * 100
                
                if conversion_rate < 50:  # Low conversion rate
                    optimizations.append({
                        'stage': f"{prev_stage} → {current_stage}",
                        'conversion_rate': round(conversion_rate, 2),
                        'opportunity': 'High',
                        'suggestion': f'Improve {current_stage} conversion from {prev_stage}'
                    })
        
        return optimizations
    
    def _predict_usage_trends(self, start_date: datetime, end_date: datetime) -> Dict:
        """Predict usage trends (simplified)"""
        try:
            # Get daily usage for trend analysis
            daily_usage = []
            current_date = start_date
            
            while current_date <= end_date:
                next_date = current_date + timedelta(days=1)
                
                day_sessions = AnalysisSession.objects.filter(
                    start_time__gte=current_date,
                    start_time__lt=next_date
                ).count()
                
                daily_usage.append(day_sessions)
                current_date = next_date
            
            # Simple trend calculation
            if len(daily_usage) >= 2:
                trend = 'increasing' if daily_usage[-1] > daily_usage[0] else 'decreasing'
            else:
                trend = 'stable'
            
            return {
                'current_trend': trend,
                'daily_usage': daily_usage,
                'predicted_next_week': sum(daily_usage[-7:]) if len(daily_usage) >= 7 else sum(daily_usage)
            }
            
        except Exception as e:
            logger.error(f"Error predicting usage trends: {e}")
            return {}
    
    def _forecast_capacity_needs(self, start_date: datetime, end_date: datetime) -> Dict:
        """Forecast capacity needs (simplified)"""
        try:
            total_analyses = DiasporaAnalysisData.objects.filter(
                created_at__gte=start_date, is_active=True
            ).count()
            
            days = (end_date - start_date).days
            daily_average = total_analyses / days if days > 0 else 0
            
            return {
                'current_daily_capacity': round(daily_average, 2),
                'projected_monthly_capacity': round(daily_average * 30, 0),
                'capacity_status': 'adequate' if daily_average < 100 else 'needs_scaling'
            }
            
        except Exception as e:
            logger.error(f"Error forecasting capacity needs: {e}")
            return {}
    
    def _assess_risks(self, start_date: datetime, end_date: datetime) -> Dict:
        """Assess potential risks (simplified)"""
        try:
            analyses = DiasporaAnalysisData.objects.filter(
                created_at__gte=start_date, is_active=True
            )
            
            fallback_rate = analyses.filter(is_real_ai=False).count() / analyses.count() * 100 if analyses.count() > 0 else 0
            
            risks = []
            if fallback_rate > 30:
                risks.append({
                    'type': 'High Fallback Usage',
                    'severity': 'Medium',
                    'description': f'{fallback_rate:.1f}% of analyses using fallback data'
                })
            
            return {
                'fallback_rate': round(fallback_rate, 2),
                'identified_risks': risks,
                'overall_risk_level': 'Low' if fallback_rate < 20 else 'Medium'
            }
            
        except Exception as e:
            logger.error(f"Error assessing risks: {e}")
            return {}