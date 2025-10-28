"""
Analytics views for GoToMeeting integration.

PHASE 3 FEATURE: Meeting analytics dashboard with insights and trends.

Provides:
- Meeting statistics (total, by type, by date range)
- Top attendees (participation metrics)
- Department participation trends
- Meeting duration analysis
- Task points awarded tracking
"""

from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
import logging

from ai_services.models import Meeting, MeetingAttendee, MeetingActivityMapping

logger = logging.getLogger(__name__)


def is_staff_or_superuser(user):
    """Check if user is staff or superuser"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_staff_or_superuser)
def meeting_analytics_dashboard(request):
    """
    Analytics dashboard for GoToMeeting data.
    
    PHASE 3 FEATURE: Comprehensive meeting analytics.
    """
    # Date range filter (default: last 30 days)
    days_back = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days_back)
    
    # Overall statistics
    total_meetings = Meeting.objects.count()
    total_attendees = MeetingAttendee.objects.count()
    meetings_in_period = Meeting.objects.filter(start_time__gte=start_date).count()
    
    # Meeting type breakdown
    meeting_by_type = Meeting.objects.filter(
        start_time__gte=start_date
    ).values('meeting_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Top attendees
    top_attendees = MeetingAttendee.objects.filter(
        meeting__start_time__gte=start_date
    ).values(
        'attendee_name', 'attendee_email'
    ).annotate(
        meeting_count=Count('meeting'),
        total_minutes=Sum('duration_minutes'),
        avg_duration=Avg('duration_minutes'),
    ).order_by('-meeting_count')[:10]
    
    # Task points awarded
    points_awarded = MeetingAttendee.objects.filter(
        meeting__start_time__gte=start_date,
        task_points_awarded=True
    ).count()
    
    # Average meeting duration
    avg_meeting_duration = Meeting.objects.filter(
        start_time__gte=start_date
    ).aggregate(Avg('duration_minutes'))['duration_minutes__avg'] or 0
    
    # Average attendance per meeting
    avg_attendees_per_meeting = MeetingAttendee.objects.filter(
        meeting__start_time__gte=start_date
    ).values('meeting').annotate(
        attendee_count=Count('id')
    ).aggregate(Avg('attendee_count'))['attendee_count__avg'] or 0
    
    # Meetings with recordings
    recorded_meetings = Meeting.objects.filter(
        start_time__gte=start_date,
        is_recorded=True
    ).count()
    recording_rate = (recorded_meetings / meetings_in_period * 100) if meetings_in_period > 0 else 0
    
    # Meeting trends (by week)
    weekly_trends = []
    for i in range(4):
        week_start = timezone.now() - timedelta(weeks=i+1)
        week_end = timezone.now() - timedelta(weeks=i)
        count = Meeting.objects.filter(
            start_time__gte=week_start,
            start_time__lt=week_end
        ).count()
        weekly_trends.append({
            'week': f'Week {i+1}',
            'count': count
        })
    
    context = {
        'total_meetings': total_meetings,
        'total_attendees': total_attendees,
        'meetings_in_period': meetings_in_period,
        'meeting_by_type': meeting_by_type,
        'top_attendees': top_attendees,
        'points_awarded': points_awarded,
        'avg_meeting_duration': round(avg_meeting_duration, 1),
        'avg_attendees_per_meeting': round(avg_attendees_per_meeting, 1),
        'recorded_meetings': recorded_meetings,
        'recording_rate': round(recording_rate, 1),
        'weekly_trends': weekly_trends,
        'days_back': days_back,
    }
    
    return render(request, 'ai_services/meeting_analytics_dashboard.html', context)


@login_required
@user_passes_test(is_staff_or_superuser)
def meeting_participation_report(request):
    """
    Detailed participation report.
    
    Shows who attended which meetings and task points awarded.
    """
    from django.db.models import Prefetch
    
    days_back = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days_back)
    
    # Get meetings with attendees
    meetings = Meeting.objects.filter(
        start_time__gte=start_date
    ).prefetch_related(
        Prefetch(
            'attendees',
            queryset=MeetingAttendee.objects.select_related('user')
        )
    ).order_by('-start_time')
    
    context = {
        'meetings': meetings,
        'days_back': days_back,
    }
    
    return render(request, 'ai_services/meeting_participation_report.html', context)


@login_required
def my_meeting_stats(request):
    """
    Personal meeting statistics for logged-in user.
    
    PHASE 3 FEATURE: Individual user can see their own stats.
    """
    days_back = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days_back)
    
    # Get user's attendances
    my_attendances = MeetingAttendee.objects.filter(
        user=request.user,
        meeting__start_time__gte=start_date
    ).select_related('meeting')
    
    # Statistics
    total_meetings_attended = my_attendances.count()
    total_minutes = my_attendances.aggregate(Sum('duration_minutes'))['duration_minutes__avg'] or 0
    avg_duration = my_attendances.aggregate(Avg('duration_minutes'))['duration_minutes__avg'] or 0
    points_earned = my_attendances.filter(task_points_awarded=True).count()
    
    # Recent meetings
    recent_meetings = my_attendances.order_by('-meeting__start_time')[:10]
    
    context = {
        'total_meetings_attended': total_meetings_attended,
        'total_minutes': round(total_minutes, 0),
        'avg_duration': round(avg_duration, 1),
        'points_earned': points_earned,
        'recent_meetings': recent_meetings,
        'days_back': days_back,
    }
    
    return render(request, 'ai_services/my_meeting_stats.html', context)

