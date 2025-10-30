"""
Async views for GoToMeeting integration.

PHASE 2 IMPROVEMENT: Background processing views that queue Celery tasks
instead of blocking requests.

These views provide instant responses and email users when complete.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
import logging

from ai_services.forms import MeetingForm
from ai_services.tasks import fetch_meetings_task, download_recording_task

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def async_meeting_fetch_view(request):
    """
    Async version of meetingFormView - queues background task instead of blocking.
    
    PHASE 2 IMPROVEMENT: Instant response, email when complete.
    """
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['startDate']
            end_date = form.cleaned_data['endDate']
            
            # Check rate limiting
            rate_limit_key = f'meeting_fetch_rate_limit_{request.user.id}'
            recent_fetches = cache.get(rate_limit_key, 0)
            
            if recent_fetches >= 10:  # Max 10 fetches per hour
                messages.error(request, "⚠️ Rate limit exceeded. Please wait before fetching more meetings.")
                return render(request, 'ai_services/meetingForm.html', {'form': form})
            
            # Queue background task
            task = fetch_meetings_task.delay(
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d'),
                request.user.id
            )
            
            # Increment rate limit counter
            cache.set(rate_limit_key, recent_fetches + 1, 3600)  # 1 hour
            
            messages.success(
                request,
                f"✅ Meeting fetch queued! You'll receive an email when complete. Task ID: {task.id}"
            )
            
            return render(request, 'ai_services/meetingForm.html', {
                'form': form,
                'task_id': task.id,
                'processing': True,
            })
    else:
        form = MeetingForm()
    
    return render(request, 'ai_services/meetingForm.html', {'form': form})


@login_required
@require_http_methods(["GET"])
def task_status_api(request, task_id):
    """
    API endpoint to check task status.
    
    PHASE 2 FEATURE: Real-time progress tracking.
    
    Returns:
        JSON with task status
    """
    from celery.result import AsyncResult
    
    result = AsyncResult(task_id)
    
    response_data = {
        'task_id': task_id,
        'status': result.state,
        'ready': result.ready(),
    }
    
    if result.ready():
        if result.successful():
            response_data['result'] = result.result
        else:
            response_data['error'] = str(result.info)
    
    return JsonResponse(response_data)


@login_required
@require_http_methods(["POST"])
def async_download_recording_view(request):
    """
    Async version of recording download - queues background task.
    
    PHASE 2 IMPROVEMENT: Streaming download, no memory issues.
    """
    selected_meeting_ids = request.POST.getlist('selected_meetings')
    
    if not selected_meeting_ids:
        messages.warning(request, "No recordings selected for download.")
        return redirect('getdata:download_upload_recordings')
    
    # Queue download tasks
    task_ids = []
    for meeting_id in selected_meeting_ids:
        from ai_services.models import Meeting
        
        try:
            meeting = Meeting.objects.get(meeting_id=meeting_id)
            
            if meeting.download_url:
                task = download_recording_task.delay(
                    meeting_id,
                    meeting.download_url,
                    request.user.id
                )
                task_ids.append(task.id)
            else:
                logger.warning(f"Meeting {meeting_id} has no download URL")
        
        except Meeting.DoesNotExist:
            logger.error(f"Meeting {meeting_id} not found")
    
    messages.success(
        request,
        f"✅ Queued {len(task_ids)} recording downloads. You'll receive an email when complete."
    )
    
    return render(request, 'ai_services/download_upload_recordings.html', {
        'task_ids': task_ids,
        'processing': True,
    })


# Rate limiting decorator
def rate_limit(requests_per_hour=100):
    """
    Decorator to rate limit API calls.
    
    PHASE 2 IMPROVEMENT: Prevent API quota exhaustion.
    """
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            # Use user ID + function name as cache key
            cache_key = f'rate_limit_{func.__name__}_{request.user.id if hasattr(request, 'user') else "anon"}'
            
            # Get current count
            count = cache.get(cache_key, 0)
            
            if count >= requests_per_hour:
                from django.http import HttpResponse
                return HttpResponse("Rate limit exceeded. Please try again later.", status=429)
            
            # Increment and set/extend cache
            cache.set(cache_key, count + 1, 3600)  # 1 hour window
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


@rate_limit(requests_per_hour=50)
@login_required
def rate_limited_meeting_fetch(request):
    """
    Rate-limited version of meeting fetch.
    
    PHASE 2 IMPROVEMENT: Max 50 fetches per user per hour.
    """
    # ... implementation uses async_meeting_fetch_view logic
    return async_meeting_fetch_view(request)

