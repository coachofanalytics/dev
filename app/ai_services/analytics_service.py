"""
Enhanced Analytics Service for AI Platform
Tracks user behavior, generates insights, and provides comprehensive analytics
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.db.models import Count, Avg, Q, F
from django.utils import timezone
from django.core.cache import cache
from django.http import HttpRequest
from user_agents import parse as parse_user_agent

from .models import (
    UserBehaviorAnalytics, AnalysisSession, DiasporaAnalysisData,
    DiasporaAnalysisTypes, AIModelTypes
)

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Enhanced analytics service for user behavior tracking and insights"""
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutes cache for analytics data
    
    def track_event(self, request: HttpRequest, event_type: str, 
                   analysis_type: str = None, event_data: Dict = None) -> None:
        """Track user behavior event"""
        try:
            session_id = request.session.get('analysis_session_id')
            if not session_id:
                logger.warning("No session ID found for analytics tracking")
                return
            
            # Parse user agent
            user_agent_string = request.META.get('HTTP_USER_AGENT', '')
            user_agent = parse_user_agent(user_agent_string)
            
            # Determine device type
            device_type = 'desktop'
            if user_agent.is_mobile:
                device_type = 'mobile'
            elif user_agent.is_tablet:
                device_type = 'tablet'
            
            # Get browser info
            browser = f"{user_agent.browser.family} {user_agent.browser.version_string}"
            
            # Create analytics record
            UserBehaviorAnalytics.objects.create(
                session_id=session_id,
                user=request.user if request.user.is_authenticated else None,
                event_type=event_type,
                page_url=request.build_absolute_uri(),
                analysis_type=analysis_type,
                event_data=event_data or {},
                ip_address=self._get_client_ip(request),
                user_agent=user_agent_string,
                country=self._get_country_from_ip(request),
                device_type=device_type,
                browser=browser
            )
            
            logger.info(f"Tracked event: {event_type} for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error tracking analytics event: {e}")
    
    def get_user_journey(self, session_id: str) -> List[Dict]:
        """Get complete user journey for a session"""
        events = UserBehaviorAnalytics.objects.filter(
            session_id=session_id
        ).order_by('timestamp')
        
        journey = []
        for event in events:
            journey.append({
                'event_type': event.event_type,
                'timestamp': event.timestamp,
                'page_url': event.page_url,
                'analysis_type': event.analysis_type,
                'event_data': event.event_data,
                'device_type': event.device_type,
                'browser': event.browser
            })
        
        return journey
    
    def get_analytics_dashboard_data(self) -> Dict:
        """Get comprehensive analytics data for dashboard"""
        cache_key = "analytics_dashboard_data"
        cached_data = cache.get(cache_key)
        if cached_data:
            return cached_data
        
        # Time ranges
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Basic metrics
        total_sessions = AnalysisSession.objects.count()
        total_analyses = DiasporaAnalysisData.objects.filter(is_active=True).count()
        total_events = UserBehaviorAnalytics.objects.count()
        
        # Recent activity
        recent_sessions_24h = AnalysisSession.objects.filter(start_time__gte=last_24h).count()
        recent_analyses_24h = DiasporaAnalysisData.objects.filter(
            created_at__gte=last_24h, is_active=True
        ).count()
        
        # User behavior metrics
        page_views = UserBehaviorAnalytics.objects.filter(event_type='page_view').count()
        form_starts = UserBehaviorAnalytics.objects.filter(event_type='form_start').count()
        form_submissions = UserBehaviorAnalytics.objects.filter(event_type='form_submit').count()
        analysis_completions = UserBehaviorAnalytics.objects.filter(event_type='analysis_complete').count()
        
        # Conversion rates
        form_conversion_rate = (form_submissions / form_starts * 100) if form_starts > 0 else 0
        analysis_conversion_rate = (analysis_completions / form_submissions * 100) if form_submissions > 0 else 0
        
        # Analysis type breakdown
        analysis_breakdown = {}
        for analysis_type, _ in DiasporaAnalysisTypes.choices:
            count = DiasporaAnalysisData.objects.filter(
                analysis_type=analysis_type, is_active=True
            ).count()
            analysis_breakdown[analysis_type] = count
        
        # Device and browser analytics
        device_breakdown = UserBehaviorAnalytics.objects.values('device_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        browser_breakdown = UserBehaviorAnalytics.objects.values('browser').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Geographic distribution
        country_breakdown = UserBehaviorAnalytics.objects.values('country').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Time-based analytics (last 7 days)
        daily_analytics = []
        for i in range(7):
            date = now - timedelta(days=i)
            day_start = date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_sessions = AnalysisSession.objects.filter(
                start_time__gte=day_start, start_time__lt=day_end
            ).count()
            
            day_analyses = DiasporaAnalysisData.objects.filter(
                created_at__gte=day_start, created_at__lt=day_end, is_active=True
            ).count()
            
            daily_analytics.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'sessions': day_sessions,
                'analyses': day_analyses
            })
        
        # AI model performance
        ai_performance = DiasporaAnalysisData.objects.values('model_used').annotate(
            count=Count('id'),
            avg_confidence=Avg('confidence_score'),
            avg_processing_time=Avg('processing_time')
        ).order_by('-count')
        
        # Real AI vs Fallback usage
        real_ai_count = DiasporaAnalysisData.objects.filter(is_real_ai=True).count()
        fallback_count = DiasporaAnalysisData.objects.filter(is_real_ai=False).count()
        
        # User engagement metrics
        avg_session_duration = self._calculate_avg_session_duration()
        avg_analyses_per_session = total_analyses / total_sessions if total_sessions > 0 else 0
        
        # Top performing pages
        top_pages = UserBehaviorAnalytics.objects.filter(
            event_type='page_view'
        ).values('page_url').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Error tracking
        error_events = UserBehaviorAnalytics.objects.filter(event_type='error').count()
        error_rate = (error_events / total_events * 100) if total_events > 0 else 0
        
        analytics_data = {
            'overview': {
                'total_sessions': total_sessions,
                'total_analyses': total_analyses,
                'total_events': total_events,
                'recent_sessions_24h': recent_sessions_24h,
                'recent_analyses_24h': recent_analyses_24h,
            },
            'conversion_metrics': {
                'form_conversion_rate': round(form_conversion_rate, 2),
                'analysis_conversion_rate': round(analysis_conversion_rate, 2),
                'page_views': page_views,
                'form_starts': form_starts,
                'form_submissions': form_submissions,
                'analysis_completions': analysis_completions,
            },
            'analysis_breakdown': analysis_breakdown,
            'device_breakdown': list(device_breakdown),
            'browser_breakdown': list(browser_breakdown),
            'country_breakdown': list(country_breakdown),
            'daily_analytics': daily_analytics,
            'ai_performance': list(ai_performance),
            'ai_usage': {
                'real_ai_count': real_ai_count,
                'fallback_count': fallback_count,
                'real_ai_percentage': round(real_ai_count / (real_ai_count + fallback_count) * 100, 2) if (real_ai_count + fallback_count) > 0 else 0
            },
            'engagement_metrics': {
                'avg_session_duration': avg_session_duration,
                'avg_analyses_per_session': round(avg_analyses_per_session, 2),
                'error_rate': round(error_rate, 2),
            },
            'top_pages': list(top_pages),
            'generated_at': now.isoformat()
        }
        
        # Cache the data
        cache.set(cache_key, analytics_data, self.cache_timeout)
        
        return analytics_data
    
    def get_user_analytics(self, user_id: int) -> Dict:
        """Get analytics data for a specific user"""
        user_sessions = AnalysisSession.objects.filter(user_id=user_id)
        user_analyses = DiasporaAnalysisData.objects.filter(user_id=user_id, is_active=True)
        user_events = UserBehaviorAnalytics.objects.filter(user_id=user_id)
        
        # User journey analysis
        user_journeys = []
        for session in user_sessions:
            journey = self.get_user_journey(session.session_id)
            if journey:
                user_journeys.append({
                    'session_id': session.session_id,
                    'start_time': session.start_time,
                    'total_analyses': session.total_analyses,
                    'journey': journey
                })
        
        # Analysis preferences
        analysis_preferences = {}
        for analysis_type, _ in DiasporaAnalysisTypes.choices:
            count = user_analyses.filter(analysis_type=analysis_type).count()
            analysis_preferences[analysis_type] = count
        
        # Device preferences
        device_preferences = user_events.values('device_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'user_id': user_id,
            'total_sessions': user_sessions.count(),
            'total_analyses': user_analyses.count(),
            'total_events': user_events.count(),
            'analysis_preferences': analysis_preferences,
            'device_preferences': list(device_preferences),
            'user_journeys': user_journeys,
            'avg_confidence_score': user_analyses.aggregate(
                avg_confidence=Avg('confidence_score')
            )['avg_confidence'] or 0,
            'last_activity': user_events.order_by('-timestamp').first().timestamp if user_events.exists() else None
        }
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_country_from_ip(self, request: HttpRequest) -> Optional[str]:
        """Get country from IP address (simplified implementation)"""
        # In a real implementation, you'd use a service like GeoIP2
        # For now, return None or implement basic country detection
        return None
    
    def _calculate_avg_session_duration(self) -> float:
        """Calculate average session duration in minutes"""
        sessions_with_end = AnalysisSession.objects.filter(
            end_time__isnull=False
        ).exclude(end_time=F('start_time'))
        
        if not sessions_with_end.exists():
            return 0.0
        
        total_duration = 0
        for session in sessions_with_end:
            duration = session.end_time - session.start_time
            total_duration += duration.total_seconds()
        
        avg_seconds = total_duration / sessions_with_end.count()
        return round(avg_seconds / 60, 2)  # Convert to minutes
    
    def get_heatmap_data(self, analysis_type: str = None) -> Dict:
        """Get heatmap data for user interactions"""
        # This would integrate with a frontend heatmap library
        # For now, return page interaction data
        events = UserBehaviorAnalytics.objects.filter(event_type='page_view')
        
        if analysis_type:
            events = events.filter(analysis_type=analysis_type)
        
        page_interactions = events.values('page_url').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'page_interactions': list(page_interactions),
            'total_interactions': events.count(),
            'analysis_type': analysis_type
        }
    
    def export_analytics_data(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Export analytics data for external analysis"""
        events = UserBehaviorAnalytics.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        ).select_related('user')
        
        export_data = []
        for event in events:
            export_data.append({
                'timestamp': event.timestamp.isoformat(),
                'session_id': event.session_id,
                'user_id': event.user.id if event.user else None,
                'event_type': event.event_type,
                'page_url': event.page_url,
                'analysis_type': event.analysis_type,
                'device_type': event.device_type,
                'browser': event.browser,
                'country': event.country,
                'ip_address': event.ip_address,
                'event_data': event.event_data
            })
        
        return export_data
