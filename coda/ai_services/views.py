# imports added below
import csv
import io
import os
import json
import requests
from decimal import *
from django.db.utils import DataError
from datetime import datetime, timezone
from django.http import JsonResponse
from accounts.models import TaskGroups
from coda_project import settings
from management.models import Task, TaskCategory, TaskLinks
# Conditional import for selenium (not available in production)
try:
    from selenium import webdriver
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
import threading
import logging
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.cache import cache

from django.db.models import Q
from django.utils.text import slugify
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from django.core.files.base import ContentFile
from io import BytesIO
logger = logging.getLogger('management')
import json
from datetime import datetime, time
import mimetypes
from django.core.mail import send_mail
from .utils import activity_mapping
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseRedirect, Http404, JsonResponse,HttpResponse,HttpResponseBadRequest
from django.contrib import admin, messages
from django.urls import path, reverse
from django.contrib.auth.decorators import login_required
from django.views.generic import (ListView,DetailView,CreateView,DetailView)
from main.utils import (App_Categories,Automation,Stocks,General,
						all_applications,generate_chatbot_response,
						openai_user_message)
from finance.utils import update_link
from ai_services.forms import OpenaiForm,UseCaseForm
from ai_services.utils import (
					download_recording, fetch_and_insert_data,populate_table_from_json_file,
					convert_excel_dates,move_questions_to_user_answer_status, process_excel_file,
					table_contents,Hardware_Software_Req,company_details,
					transfer_transactions_to_codabudget,populate_budget_categories,
    				populate_budget_subcategories, upload_to_google_drive
)
from finance.models import (Transaction, Payment_History)

from investing.models import Daily_Trades  # Options_Returns, OverBoughtSold DELETED Nov 5, 2025
from marketing.models import Whatsapp_Groups
from main.models import Pricing

#importing Options play funcationality

from .models import (
			CashappMail, DynamicExcelData,OpenaiPrompt,GotoMeetings,Logs,
			UseCase,CaseCategory
) 

from django.contrib.auth import get_user_model
from .forms import CsvImportForm, ExcelUploadForm, MeetingForm, UpworkConnectsForm
from coda_project.settings import EMAIL_INFO,source_target

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, user_passes_test

# User=settings.AUTH_USER_MODEL
User = get_user_model()
__smtp_user = EMAIL_INFO


# top level variables declaration
# views on ratings data.
def index(request):
	return render(request, 'ai_services/index.html', {'title': 'index'})

def getrating(request):
	
    # return render(request, 'ai_services/getrating.html', {'title': 'getrating'})
    return render(request, 'ai_services/openai.html', {'title': 'getrating'})

@login_required
def enter_prompt(request):
    if request.method == "POST":
        form = OpenaiForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
        else:
            # Form is not valid, print errors
            logger.debug("Form is not valid. Errors:")
            for field, errors in form.errors.items():
                logger.debug(f"Field: {field}")
                for error in errors:
                    logger.debug(f"- {error}")
    else:
        form = OpenaiForm()
    return render(request, "ai_services/openai_form.html", {"form": form})

@login_required
def fetch_whatsapp_groups(request):
    file_path='media/marketing/whatsapp_groups/Whatsapp_Groups_11232023_v1.txt'
    populate_table_from_json_file(file_path)
    return redirect('marketing:whatsapp_list')
	

def uploaddata(request):  
	# context = {"posts": posts}
	context = {
        "App_Categories": App_Categories,
	}
	return render(request,"ai_services/uploaddata.html", context) 


# def update_link(service_array, user_payment_history, service_categories):
# 	updated_automation = []
# 	for automation_service in service_array:
		
# 		if automation_service['service_category_slug'] and automation_service['service_category_slug'] in service_categories.keys():

# 			# import pdb; pdb.set_trace()
# 			if user_payment_history.filter(plan = service_categories[automation_service['service_category_slug']]).exists():
				
# 				updated_automation.append(automation_service)	
			
# 			else:

# 				automation_service['link'] = automation_service['service_url']
# 				updated_automation.append(automation_service)
			
# 		else:
# 			updated_automation.append(automation_service)
# 	return updated_automation


@login_required
def bigdata(request):
	if request.user.category != 2:
		payment_history = Payment_History.objects.filter(customer_id=request.user)
		
		pricing_serial_list = dict(Pricing.objects.values_list('serial', 'id'))
		
		context={
			"title":  "data",
			"Automation": update_link(Automation, payment_history, pricing_serial_list),
			"Stocks":Stocks,
			"General":update_link(General	, payment_history, pricing_serial_list),
		}
	else:
		context={
			"title": "data",
			"Automation":Automation,
			"Stocks":Stocks,
			"General":General,
		}
		
	return render(request, "ai_services/bigdata.html",context)


def bigdata_presentation(request):
	"""
	Enhanced Big Data presentation board showcasing all AI use cases
	Similar to diaspora dashboard but for budget system intelligence
	"""
	context = {
		"title": "CODA AI Platform - Big Data & Analytics Use Cases",
	}
	return render(request, "ai_services/bigdata_presentation.html", context)


# ========================. DISPLAY/LIST VIEWS============================
# class CashappListView(ListView):
#     queryset = CashappMail.objects.all()
#     template_name = "main/snippets_templates/interview_snippets/result.html"

class CashappListView(ListView):
	model = CashappMail
	template_name = "main/snippets_templates/interview_snippets/result.html"
	context_object_name = "cashappdata"

class CashappMailDetailSlugView(DetailView):
	queryset = CashappMail.objects.all()
	template_name = "ai_services/detail.html"
 
	def get_context_data(self, *args, **kwargs):
		context = super(CashappMailDetailSlugView, self).get_context_data(*args, **kwargs)
		return context
 
	def get_object(self, *args, **kwargs):
		request = self.request
		slug = self.kwargs.get('slug')
 
		#instance = get_object_or_404(CashappMail, slug=slug, active=True)
		try:
			instance = CashappMail.objects.get(slug=slug, active=True)
		except CashappMail.DoesNotExist:
			raise Http404("Not found..")
		except CashappMail.MultipleObjectsReturned:
			qs = CashappMail.objects.filter(slug=slug, active=True)
			instance = qs.first()
		except:
			raise Http404("Uhhmmm ")
		return instance

# # ==================GOTOMEETING===========================

API_CLIENT_ID = os.environ.get("API_CLIENT_ID")
API_CLIENT_SECRET = os.environ.get("API_CLIENT_SECRET")
API_AUTHORIZATION_URL="https://authentication.logmeininc.com/oauth/authorize"
API_TOKEN_URL="https://authentication.logmeininc.com/oauth/token"
TOKEN_CACHE_KEY = 'api_access_token'
REFRESH_TOKEN_CACHE_KEY = 'api_refresh_token'

def get_oauth_redirect_uri():
    """
    Get OAuth redirect URI based on environment.
    
    PHASE 1 IMPROVEMENT: Environment-aware redirect URIs.
    """
    from django.conf import settings
    
    environment = getattr(settings, 'ENVIRONMENT', 'local')
    
    if environment == 'production':
        return "https://www.codanalytics.net/management/oauth/callback/"
    elif environment == 'staging':
        return "https://codamakutano.herokuapp.com/management/oauth/callback/"
    else:  # local/development
        return "http://localhost:8000/management/oauth/callback/"

# For backward compatibility (will be replaced in views)
API_REDIRECT_URI = get_oauth_redirect_uri()

def get_authorization_url():
    """
    Constructs the authorization URL to redirect the user.
    
    PHASE 1 IMPROVEMENT: Uses dynamic redirect URI based on environment.
    """
    params = {
        'client_id': API_CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': get_oauth_redirect_uri(),  # Dynamic based on environment
        'state': 'random_state_string',  # Use a random string for security
    }
    from urllib.parse import urlencode
    url = f"{API_AUTHORIZATION_URL}?{urlencode(params)}"
    return url

def exchange_code_for_tokens(auth_code):
    """
    Exchanges the authorization code for access and refresh tokens.
    
    PHASE 1 IMPROVEMENT: Uses dynamic redirect URI and secure token storage.
    """
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': get_oauth_redirect_uri(),  # Dynamic based on environment
    }
    # Use HTTP Basic Auth with client_id and client_secret
    auth = (API_CLIENT_ID, API_CLIENT_SECRET)
    
    try:
        response = requests.post(API_TOKEN_URL, headers=headers, data=data, auth=auth, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in', 3600)  # Default to 1 hour

        if not access_token or not refresh_token:
            logger.error("OAuth response missing tokens")
            return False

        # Cache the tokens with expiry (still using cache for now - will move to DB in token service)
        cache.set(TOKEN_CACHE_KEY, access_token, timeout=expires_in)
        cache.set(REFRESH_TOKEN_CACHE_KEY, refresh_token, timeout=86400)  # Refresh token valid for 1 day
        
        logger.info("✅ Successfully exchanged auth code for tokens")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"OAuth exchange failed: {e}", exc_info=True)
        return False
    except ValueError as e:
        logger.error(f"Invalid OAuth response JSON: {e}", exc_info=True)
        return False

def refresh_access_token():
    """
    Uses the refresh token to obtain a new access token.
    
    PHASE 1 IMPROVEMENT: Better error handling and logging.
    """
    refresh_token = cache.get(REFRESH_TOKEN_CACHE_KEY)
    if not refresh_token:
        logger.warning("No refresh token available - user needs to re-authenticate")
        return False

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
    }
    # Use HTTP Basic Auth with client_id and client_secret
    auth = (API_CLIENT_ID, API_CLIENT_SECRET)
    
    try:
        response = requests.post(API_TOKEN_URL, headers=headers, data=data, auth=auth, timeout=10)
        response.raise_for_status()
        
        token_data = response.json()
        access_token = token_data.get('access_token')
        new_refresh_token = token_data.get('refresh_token', refresh_token)  # Some APIs return a new refresh token

        if not access_token:
            logger.error("Token refresh response missing access_token")
            return False

        expires_in = token_data.get('expires_in', 3600)  # Default to 1 hour

        # Update the cached tokens
        cache.set(TOKEN_CACHE_KEY, access_token, timeout=expires_in)
        cache.set(REFRESH_TOKEN_CACHE_KEY, new_refresh_token, timeout=86400)
        
        logger.info("✅ Successfully refreshed access token")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Token refresh failed: {e}", exc_info=True)
        return False
    except ValueError as e:
        logger.error(f"Invalid token refresh response: {e}", exc_info=True)
        return False

def get_access_token():
    """
    Retrieves a valid access token, refreshing it if necessary.
    """
    access_token = cache.get(TOKEN_CACHE_KEY)
    if access_token:
        return access_token
    else:
        # Attempt to refresh the token
        if refresh_access_token():
            return cache.get(TOKEN_CACHE_KEY)
        else:
            return None


# ## Get response

def getmeetingresponse(startDate, endDate):
    """
    Fetch meetings from GoToMeeting API for date range.
    
    PHASE 1 IMPROVEMENT: Better error handling, timeouts, and logging.
    
    Args:
        startDate: Start date string (YYYY-MM-DD)
        endDate: End date string (YYYY-MM-DD)
    
    Returns:
        List of meeting dicts with attendee info, or empty list on error
    """
    startDateTime = f"{startDate}T00:00:00Z"
    endDateTime = f"{endDate}T23:59:00Z"

    access_token = get_access_token()
    if not access_token:
        logger.warning("No access token available - redirecting to OAuth")
        return []

    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    urlGotoMeeting = "https://api.getgo.com/G2M/rest/historicalMeetings?startDate={}&endDate={}"
    urlMeeting = urlGotoMeeting.format(startDateTime, endDateTime)

    try:
        response = requests.get(url=urlMeeting, headers=headers, timeout=30)
        response.raise_for_status()
        
        jsonResponse = response.json()
        myCleanResponse = []
        
        logger.info(f"📊 Fetched {len(jsonResponse)} meetings from API for {startDate} to {endDate}")

        for meeting in jsonResponse:
            try:
                meeting_id = meeting.get('meetingId')
                if not meeting_id:
                    logger.warning("Meeting missing meetingId, skipping")
                    continue
                
                recording = meeting.get('recording', {})
                download_url = recording.get('downloadUrl') if recording else None

                meeting_dict = {
                    'meetingId': meeting_id,
                    'downloadUrl': download_url or '',
                    'subject': meeting.get('subject', 'Untitled Meeting'),
                    'meetingType': meeting.get('meetingType', ''),
                    'recording': recording.get('shareUrl') if recording else '',
                    'startTime': meeting.get('startTime', ''),
                    'endTime': meeting.get('endTime', ''),
                    'duration': meeting.get('duration', 0),
                    'email': meeting.get('email', ''),
                    'attendeeNames': [],
                    'attendee_Info': []
                }
                myCleanResponse.append(meeting_dict)

                # Fetch attendee information
                try:
                    urlGotoOneMeetingDetail = f"https://api.getgo.com/G2M/rest/meetings/{meeting_id}/attendees"
                    meeting_response = requests.get(url=urlGotoOneMeetingDetail, headers=headers, timeout=10)
                    
                    if meeting_response.status_code == 200:
                        attendees_response = meeting_response.json()
                        attendee_names = [attendee.get("attendeeName", "Unknown") for attendee in attendees_response]
                        attendee_info = [
                            {
                                "attendee_duration": attendee.get("duration", 0),
                                "attendee_email": attendee.get("attendeeEmail", ''),
                                "attendee_name": attendee.get("attendeeName", attendee.get("attendeeEmail", "Unknown"))
                            }
                            for attendee in attendees_response
                            if attendee.get("startTime", '').startswith(startDate)
                        ]

                        # Update the last appended meeting with attendee info
                        myCleanResponse[-1]['attendeeNames'] = attendee_names
                        myCleanResponse[-1]['attendee_Info'] = attendee_info
                        
                        logger.debug(f"✅ Fetched {len(attendee_info)} attendees for meeting {meeting_id}")
                    else:
                        logger.warning(f"Failed to fetch attendees for meeting {meeting_id}: HTTP {meeting_response.status_code}")
                
                except requests.exceptions.RequestException as e:
                    logger.error(f"Error fetching attendees for meeting {meeting_id}: {e}")
                    # Continue processing other meetings even if one fails
                    continue
            
            except Exception as e:
                logger.error(f"Error processing meeting {meeting_id}: {e}", exc_info=True)
                continue

        logger.info(f"✅ Successfully processed {len(myCleanResponse)} meetings")
        return myCleanResponse
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error("OAuth token expired or invalid - user needs to re-authenticate")
        else:
            logger.error(f"HTTP error fetching meetings: {e}")
        return []
    
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout fetching meetings from GoToMeeting API: {e}")
        return []
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching meetings: {e}", exc_info=True)
        return []
    
    except ValueError as e:
        logger.error(f"Invalid JSON response from GoToMeeting API: {e}")
        return []
    
    except Exception as e:
        logger.error(f"Unexpected error in getmeetingresponse: {e}", exc_info=True)
        return []

	
def save_meeting_data(meeting_data):
    """
    Persist meeting data using normalized Meeting + MeetingAttendee models.
    Accepts list of dicts or list of JSON bytes.
    
    PHASE 1 IMPROVEMENT: Uses normalized models with duplicate prevention.
    """
    import json
    from django.utils import timezone
    from django.utils.dateparse import parse_datetime
    from ai_services.models import Meeting, MeetingAttendee
    
    meetings_created = 0
    meetings_updated = 0
    attendees_created = 0
    attendees_updated = 0
    
    for meeting_info in meeting_data:
        try:
            # Normalize input: decode bytes -> str -> json -> dict
            if isinstance(meeting_info, (bytes, bytearray)):
                try:
                    meeting_info = json.loads(meeting_info.decode('utf-8', errors='ignore'))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to decode meeting bytes: {e}")
                    continue
            elif isinstance(meeting_info, str):
                try:
                    meeting_info = json.loads(meeting_info)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse meeting JSON: {e}")
                    continue
            
            if not isinstance(meeting_info, dict):
                logger.warning(f"Unexpected meeting data type: {type(meeting_info)}")
                continue
            
            # Extract meeting data
            meeting_id = meeting_info.get('meetingId', '')
            if not meeting_id:
                logger.warning("Meeting missing meetingId, skipping")
                continue
            
            meeting_topic = meeting_info.get('subject', 'Untitled Meeting')
            meeting_type = meeting_info.get('meetingType', '')
            recording = meeting_info.get('recording', '')
            download_url = meeting_info.get('downloadUrl', '')
            
            # Parse datetime strings properly
            start_time_str = meeting_info.get('startTime', '')
            end_time_str = meeting_info.get('endTime', '')
            
            start_time = parse_datetime(start_time_str) if start_time_str else timezone.now()
            end_time = parse_datetime(end_time_str) if end_time_str else start_time
            
            # Make timezone-aware if naive
            if start_time and timezone.is_naive(start_time):
                start_time = timezone.make_aware(start_time)
            if end_time and timezone.is_naive(end_time):
                end_time = timezone.make_aware(end_time)
            
            # Calculate duration in minutes
            if start_time and end_time and end_time > start_time:
                duration_minutes = int((end_time - start_time).total_seconds() / 60)
            else:
                duration_minutes = int(meeting_info.get('duration', 0))
            
            # Create or update Meeting (DUPLICATE PREVENTION)
            meeting, created = Meeting.objects.get_or_create(
                meeting_id=meeting_id,
                defaults={
                    'topic': meeting_topic,
                    'meeting_type': meeting_type,
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_minutes': duration_minutes,
                    'recording_url': recording,
                    'download_url': download_url,
                    'is_recorded': bool(recording),
                }
            )
            
            if created:
                meetings_created += 1
                logger.info(f"✅ Created meeting: {meeting_topic} ({meeting_id})")
            else:
                meetings_updated += 1
                # Update existing meeting with new data
                Meeting.objects.filter(meeting_id=meeting_id).update(
                    topic=meeting_topic,
                    meeting_type=meeting_type,
                    recording_url=recording or meeting.recording_url,
                    download_url=download_url or meeting.download_url,
                    is_recorded=bool(recording) or meeting.is_recorded,
                )
                logger.info(f"⏭️ Updated existing meeting: {meeting_topic} ({meeting_id})")
            
            # Process attendees
            attendee_info = meeting_info.get('attendee_Info', [])
            task_category, _ = TaskCategory.objects.get_or_create(
                title='Meetings',
                defaults={'description': 'Tasks related to meetings'}
            )
            
            for attendee_data in attendee_info:
                attendee_name = attendee_data.get('attendee_name', '').strip()
                attendee_email = attendee_data.get('attendee_email', '').strip()
                attendee_duration = int(attendee_data.get('attendee_duration', 0))
                
                if not attendee_email:
                    logger.debug(f"Skipping attendee with no email: {attendee_name}")
                    continue
                
                # Try to match to CODA user by email (better than username matching)
                user = None
                try:
                    user = User.objects.filter(Q(email__iexact=attendee_email)).first()
                    if not user:
                        # Fallback: try username match
                        user = User.objects.filter(Q(username__iexact=attendee_name.lower())).first()
                except Exception as e:
                    logger.debug(f"User lookup error for {attendee_email}: {e}")
                
                # Create or update MeetingAttendee (DUPLICATE PREVENTION)
                attendee, attendee_created = MeetingAttendee.objects.get_or_create(
                    meeting=meeting,
                    attendee_email=attendee_email,
                    defaults={
                        'user': user,
                        'attendee_name': attendee_name or attendee_email,
                        'duration_minutes': attendee_duration,
                        'is_organizer': False,
                    }
                )
                
                if attendee_created:
                    attendees_created += 1
                else:
                    attendees_updated += 1
                    # Update existing attendee
                    MeetingAttendee.objects.filter(id=attendee.id).update(
                        attendee_name=attendee_name or attendee.attendee_name,
                        duration_minutes=attendee_duration,
                        user=user or attendee.user,
                    )
                
                # Task integration (only if attended >3 minutes and not already awarded)
                if attendee.qualifies_for_points and not attendee.task_points_awarded:
                    try:
                        # Use MeetingActivityMapping if available, fallback to hardcoded dict
                        from ai_services.models import MeetingActivityMapping
                        mapping = MeetingActivityMapping.objects.filter(
                            meeting_id_pattern=meeting_id,
                            is_active=True
                        ).first()
                        
                        if mapping:
                            activity_name = mapping.activity_name
                            min_duration = mapping.min_duration_minutes
                        else:
                            # Fallback to hardcoded mapping
                            activity_name = activity_mapping.get(meeting_id)
                            min_duration = 3
                        
                        if activity_name and attendee_duration >= min_duration and user:
                            tasks = Task.objects.filter(activity_name=activity_name)
                            
                            for task in tasks:
                                # Create TaskLink
                                TaskLinks.objects.get_or_create(
                                    task=task,
                                    added_by=user,
                                    link_name=slugify(f"{meeting_topic}_{attendee_name}"),
                                    defaults={
                                        'description': f"Attended meeting '{meeting_topic}' with ID {meeting_id}.",
                                        'link': recording,
                                        'linkpassword': 'No Password Needed',
                                        'drive_link': None,
                                        'is_active': True,
                                        'is_featured': True,
                                    }
                                )
                                
                                # Award points
                                task_values = Task.objects.filter(id=task.id).values("point", "mxpoint").first()
                                if task_values:
                                    points = task_values["point"]
                                    Task.objects.filter(id=task.id).update(point=points + 1)
                                
                                # Mark as awarded
                                attendee.task_points_awarded = True
                                attendee.save(update_fields=['task_points_awarded'])
                                
                                logger.info(f"✅ Awarded task points to {attendee_name} for {meeting_topic}")
                        else:
                            logger.debug(f"No task mapping for meeting {meeting_id}")
                    
                    except Exception as e:
                        logger.error(f"Error awarding task points for {attendee_name}: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Error processing meeting: {e}", exc_info=True)
            continue
    
    # Log summary
    logger.info(f"📊 Meeting save summary: {meetings_created} created, {meetings_updated} updated, "
                f"{attendees_created} attendees created, {attendees_updated} attendees updated")        
   

@login_required
def meetingFormView(request):
    """
    View for fetching and displaying GoToMeeting data.
    
    PHASE 1 IMPROVEMENT: Uses normalized Meeting + MeetingAttendee models.
    """
    if request.method == 'POST':
        form = MeetingForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['startDate'] 
            end_date = form.cleaned_data['endDate']     
            start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

            # Check for existing meetings in NEW normalized model (with efficient query)
            from ai_services.models import Meeting, MeetingAttendee
            existing_meetings = Meeting.objects.filter(
                start_time__gte=start_datetime,
                start_time__lte=end_datetime
            ).prefetch_related('attendees__user')
            
            access_token = get_access_token()
            if not access_token:
               return redirect('management:oauth_login')

            if existing_meetings.exists():
                # Format data for template
                allDataJsons = []
                for meeting in existing_meetings:
                    meeting_dict = {
                        'meeting_id': meeting.meeting_id,
                        'meeting_topic': meeting.topic,
                        'meeting_type': meeting.meeting_type,
                        'meeting_start_time': meeting.start_time.isoformat(),
                        'meeting_end_time': meeting.end_time.isoformat(),
                        'meeting_duration': meeting.duration_minutes,
                        'recording': meeting.recording_url,
                        'download_url': meeting.download_url,
                        'is_recorded': meeting.is_recorded,
                        'attendee_count': meeting.attendee_count,
                        'attendees': [
                            {
                                'attendee_name': att.attendee_name,
                                'attendee_email': att.attendee_email,
                                'attendee_duration': att.duration_minutes,
                                'attendance_percentage': att.attendance_percentage,
                                'task_points_awarded': att.task_points_awarded,
                            }
                            for att in meeting.attendees.all()
                        ]
                    }
                    allDataJsons.append(meeting_dict)
                
                message = f"Meetings between {start_date} and {end_date} fetched from the database ({existing_meetings.count()} meetings)."
            else:
                # Fetch from API
                allDataJsons = getmeetingresponse(
                    start_date.strftime('%Y-%m-%d'),
                    end_date.strftime('%Y-%m-%d')
                )
                if not allDataJsons:
                    message = "No meetings found for the selected period."
                else:
                    # Save fetched data to the database (using new models)
                    save_meeting_data(allDataJsons)
                    
                    # Retrieve the newly saved data from new models
                    existing_meetings = Meeting.objects.filter(
                        start_time__gte=start_datetime,
                        start_time__lte=end_datetime
                    ).prefetch_related('attendees__user')
                    
                    # Format for template
                    allDataJsons = []
                    for meeting in existing_meetings:
                        meeting_dict = {
                            'meeting_id': meeting.meeting_id,
                            'meeting_topic': meeting.topic,
                            'meeting_type': meeting.meeting_type,
                            'meeting_start_time': meeting.start_time.isoformat(),
                            'meeting_end_time': meeting.end_time.isoformat(),
                            'meeting_duration': meeting.duration_minutes,
                            'recording': meeting.recording_url,
                            'download_url': meeting.download_url,
                            'is_recorded': meeting.is_recorded,
                            'attendee_count': meeting.attendee_count,
                            'attendees': [
                                {
                                    'attendee_name': att.attendee_name,
                                    'attendee_email': att.attendee_email,
                                    'attendee_duration': att.duration_minutes,
                                    'attendance_percentage': att.attendance_percentage,
                                    'task_points_awarded': att.task_points_awarded,
                                }
                                for att in meeting.attendees.all()
                            ]
                        }
                        allDataJsons.append(meeting_dict)
                    
                    message = f"Meetings between {start_date} and {end_date} fetched from the API and saved to the database ({existing_meetings.count()} meetings)."

            # Prepare context for the template
            context = {
                'data': allDataJsons,
                'message': message,
                'startDate': start_date,
                'endDate': end_date,
                'meeting_count': len(allDataJsons),
            }

            return render(request, 'ai_services/meetingList.html', context)
    else:
        form = MeetingForm()

    return render(request, 'ai_services/meetingForm.html', {'form': form})


## For downloading and uploading

@login_required
def download_and_upload_recordings(request):
    """
    View to handle downloading selected recordings and uploading them to Google Drive.
    """
    if request.method == 'POST':
        # Get list of selected meeting IDs from the form
        selected_meeting_ids = request.POST.getlist('selected_meetings')
        logger.debug('id',selected_meeting_ids)
        if not selected_meeting_ids:
            messages.warning(request, "No recordings selected for upload.")
            return redirect('getdata:download_upload_recordings')  # Adjust redirect as needed

        creds = Credentials(
            token=os.environ.get('GOOGLE_ACCESS_TOKEN'),
            refresh_token=os.environ.get('GOOGLE_REFRESH_TOKEN'),
            client_id=os.environ.get('GOOGLE_CLIENT_ID'),
            client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
            token_uri="https://oauth2.googleapis.com/token",
            scopes=['https://www.googleapis.com/auth/drive.file']

        )
        service = build('drive', 'v3', credentials=creds)
        if not service:
            messages.error(request, "Google Drive is not authorized. Please authorize first.")
            return redirect('getdata:authorize_google_drive')

        for meeting_id in selected_meeting_ids:
            try:
                logger.debug('going')
                logger.debug(meeting_id)
                meeting = GotoMeetings.objects.get(meeting_id=meeting_id)
                logger.debug('not ok')
                for meetings in meeting:
                    logger.debug(meeting)
                
                download_url = meeting.download_url
                logger.debug(download_url)
                if not download_url:
                    messages.warning(request, f"No download URL available for meeting ID {meeting_id}.")
                    continue
                # Download the recording
                file_content = download_recording(download_url)
                if not file_content:
                    messages.error(request, f"Failed to download recording for meeting ID {meeting_id}.")
                    continue

             # Determine filename
                filename = f"{meeting.meeting_topic or 'Meeting'}_{meeting_id}.mp4"

                # Optionally, specify the folder ID where to upload the file
                folder_id = '1PvJu6CX7DxrGO5-7eYdz_Pujpl9ViSQo'  # Replace with your Google Drive folder ID or set to None to upload to root

                # Upload to Google Drive
                file_id = upload_to_google_drive(service, file_content, filename, folder_id)
                if file_id:
                    messages.success(request, f"Uploaded recording for meeting ID {meeting_id} to Google Drive.")
                else:
                    messages.error(request, f"Failed to upload recording for meeting ID {meeting_id} to Google Drive.")

            except GotoMeetings.DoesNotExist:
                messages.error(request, f"Meeting with ID {meeting_id} does not exist.")
                continue
            except Exception as e:
                logger.error(f"Error uploading recording for meeting ID {meeting_id}: {e}")
                messages.error(request, f"Error uploading recording for meeting ID {meeting_id}.")
                continue

        return redirect('getdata:download_upload_recordings')  # Adjust redirect as needed

    else:
        # For GET requests, display the list of recordings with checkboxes
        # Fetch yesterday's meetings as per original code
        # today = timezone.now().date()
        # yesterday = today - timedelta(days=1)

        # # Define datetime range for yesterday
        # start_datetime = timezone.make_aware(datetime.combine(yesterday, datetime.min.time()))
        # end_datetime = timezone.make_aware(datetime.combine(yesterday, datetime.max.time()))
    
        meetings = GotoMeetings.objects.all()
    
        context = {
            'meetings': meetings,
        }
    
        return render(request, 'ai_services/download_upload_recordings.html', context)    


### Daily meetings record check    
from django.utils.timezone import now
def add_today_meetings(request):
    """
    View to add today's meetings to the GotoMeetings model.
    When accessed, fetches the data for today's date and saves it.
    """
    today = now().date()  
    yesterday = today - timedelta(days=1)  

    start_date_str = yesterday.strftime('%Y-%m-%d')
    end_date_str = yesterday.strftime('%Y-%m-%d')

    start_datetime = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(today, datetime.max.time()))
    
    # Check if meetings for today already exist
    existing_meetings = GotoMeetings.objects.filter(
        meeting_start_time__startswith=start_date_str,
        meeting_end_time__startswith=end_date_str
    )
    logger.debug(existing_meetings)
    if existing_meetings.exists():
        message = f"Meetings for today ({today}) already exist in the database."
        allDataJsons = list(existing_meetings.values())
        logger.debug(message)
        # Early return if data exists
        return render(request, 'ai_services/todayMeetingList.html', {
            'data': allDataJsons,
            'message': message,
            'date': today,
        })
    else:
    # Fetch data from the API if no meetings exist
        allDataJsons = getmeetingresponse(start_date_str, end_date_str)
        if not allDataJsons:
            message = "No meetings found for today."
        else:
            # Save fetched data to the database
            save_meeting_data(allDataJsons)
            # Retrieve the newly saved data
            existing_meetings = GotoMeetings.objects.filter(
                meeting_start_time__gte=start_datetime,
                meeting_end_time__lte=end_datetime
            )
            allDataJsons = list(existing_meetings.values())
            message = f"Meetings for today ({today}) fetched from the API and saved to the database."

        # Prepare context for the template
        context = {
            'data': allDataJsons,
            'message': message,
            'date': today,
        }

        return render(request, 'ai_services/todayMeetingList.html', context)
	
# ========================================UPLOADING DATA SECTION========================

def get_urls(self):
	urls = super().get_urls()
	new_urls = [
		path("upload-csv/", self.upload_csv),
	]
	return new_urls + urls


def upload_csv(request):
	if request.method == "POST":
		csv_file = request.FILES["csv_upload"]

		if not csv_file.name.endswith(".csv"):
			messages.warning(
				request, "The wrong file type was uploaded, it should be a csv file"
			)
			return render(request, "ai_services/uploaddata.html")
			# return HttpResponseRedirect(request.path_info)

		# file= csv_file.read().decode("utf-8")
		file = csv_file.read().decode("ISO-8859-1")
		file_data = file.split("\n")
		csv_data = [line for line in file_data if line.strip() != ""]
		logger.debug(csv_data)
		for x in csv_data:
			fields = x.split(",")
			created = Transaction.objects.update_or_create(
				transaction_date=fields[0],
				sender=fields[1],
				receiver=fields[2],
				phone=fields[3],
				qty=fields[4],
				amount=fields[5],
				payment_method=fields[6],
				department=fields[7],
				category=fields[8],
				type=fields[9],
				description=fields[10],
				receipt_link=fields[11],
			)
		url = reverse("main:layout")
		return HttpResponseRedirect(url)
	form = CsvImportForm()
	data = {"form": form}
	return render(request, "ai_services/uploaddata.html", data)

import decimal
from datetime import datetime, date

# Define the date formats to try
date_formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m/%d/%Y"] 

def upload_daily_trades(request):
	if request.method == "POST":
		csv_file = request.FILES["csv_upload"]

		if not csv_file.name.endswith(".csv"):
			messages.warning(
				request, "The wrong file type was uploaded, it should be a csv file"
			)
			return render(request, "ai_services/uploaddata.html")
			# return HttpResponseRedirect(request.path_info)

		# file= csv_file.read().decode("utf-8")
		file = csv_file.read().decode("ISO-8859-1")
		file_data = file.split("\n")
		csv_data = [line for line in file_data if line.strip() != ""]

		for x in csv_data:
			fields = x.split(",") 
			date_str = fields[4].strip() if fields[4] else None
			expiry_str = fields[5].strip() if fields[5] else None
			final_date,expiry_date=convert_excel_dates(date_str,expiry_str)
			logger.debug("Dates=====>", final_date,expiry_date)

			# Convert decimal fields to Decimal objects
			price = decimal.Decimal(fields[1]) if fields[1] else decimal.Decimal('0.00')
			strike_price = decimal.Decimal(fields[2]) if fields[2] else decimal.Decimal('0.00')
			credit = decimal.Decimal(fields[8]) if fields[8] else decimal.Decimal('0.00')
			debit = decimal.Decimal(fields[9]) if fields[9] else decimal.Decimal('0.00')

   			# Convert date fields to datetime objects or set default to today
			date = None
			expiry = None
			
			for format in date_formats:
				try:

					date = datetime.strptime(date_str, format).date() if date_str else date.today()
					expiry = datetime.strptime(expiry_str, format).date() if expiry_str else date.today()
					logger.debug(date,expiry)
					break  # Break the loop if parsing succeeds
				except ValueError:
					pass  # Continue to the next format if parsing fails

			# Convert integer fields to integers or set default to 0
			qty = int(fields[10]) if fields[10] else 0
			page_number = int(fields[11]) if fields[11] else 0

			# Truncate string fields to 255 characters
			symbol = fields[0][:255] if fields[0] else None
			action = fields[3][:255] if fields[3] else None
			transaction = fields[6][:255] if fields[6] else None
			account_type = fields[7][:255] if fields[7] else None

			

			created = Daily_Trades.objects.update_or_create(
				symbol=symbol,
				price=price,
				strike_price=strike_price,
				action=action,
				date=date,
				expiry=expiry,
				transaction=transaction,
				account_type=account_type,
				credit=credit,
				debit=debit,
				qty=qty,
				page_number=page_number,
				# description=fields[12],
			)

		url = reverse("main:layout")
		return HttpResponseRedirect(url)
	form = CsvImportForm()
	data = {"form": form}
	return render(request, "ai_services/uploaddata.html", data)


# from django.contrib import messages
from django.contrib.contenttypes.models import ContentType
def stocks_upload_csv(request):
    context = {
        "categories": App_Categories,
    }

    if request.method == "POST":
        csv_file = request.FILES.get("csv_upload")
        model_name = request.POST.get('model_name')
        app_label = request.POST.get('app_label')
       
        # Check if it's a CSV file
        if not csv_file.name.endswith(".csv"):
            messages.warning(request, "Not a CSV file")
            return render(request, "ai_services/uploaddata.html", context)

        try:
            model = ContentType.objects.get(app_label=app_label.lower(), model=model_name.lower()).model_class()

            # Read the CSV file
            file = csv_file.read().decode("ISO-8859-1")
            file_data = file.split("\n")
            csv_data = [line for line in file_data if line.strip() != ""]

            # Get the field names for the model, excluding auto fields like 'id'
            model_fields = [field.name for field in model._meta.fields if not field.auto_created]

            # Map the CSV header to model fields (assuming the CSV header matches model field names)
            csv_header = csv_data[0].split(",")
            csv_data = csv_data[1:]  # Remove the header row from data

            # Ensure that the CSV header matches the model fields, excluding auto fields
            matching_fields = [field for field in csv_header if field in model_fields]

            if not matching_fields:
                messages.warning(request, "CSV header does not match any model fields.")
                return render(request, "ai_services/uploaddata.html", context)

            # Identify the foreign key fields in the model
            foreign_key_fields = {field.name: field for field in model._meta.fields if field.is_relation and field.many_to_one}

            # Process CSV data and create or update records in the appropriate model
            for row in csv_data:
                fields = row.split(",")
                if len(fields) < len(matching_fields):  # Skip rows with insufficient data
                    continue

                data = {field_name: value for field_name, value in zip(matching_fields, fields)}

                # Handle foreign key relationships
                for fk_field, fk in foreign_key_fields.items():
                    if fk_field in data:
                        related_model = fk.related_model
                        try:
                            # Attempt to get the related object
                            related_obj = related_model.objects.get(pk=data[fk_field])
                            data[fk_field] = related_obj
                        except related_model.DoesNotExist:
                            messages.warning(request, f"Related object for field '{fk_field}' with ID '{data[fk_field]}' does not exist.")
                            data[fk_field] = None

                # Create the model instance with the resolved data
                model.objects.create(**data)

            messages.success(request, "Data populated successfully")
            return redirect('getdata:upload-data')

        except ContentType.DoesNotExist:
            messages.warning(request, f"No model found for '{model_name}' in app '{app_label}'")
            return render(request, "ai_services/uploaddata.html", context)
        except Exception as e:
            messages.warning(request, str(e))
            
    if request.method == 'GET':
        return render(request, "ai_services/uploaddata.html", context)
def download_daily_trades(request):
    # Query the first 10 records from the Task model
    tasks = Task.objects.all()[:10]

    # Create the HttpResponse object with the appropriate CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="tasks.csv"'

    # Create a CSV writer object
    writer = csv.writer(response)

    # Write the header row in lowercase
    writer.writerow([
        'group', 'groupname', 'category', 'employee', 'activity_name', 'description',
        'slug', 'duration', 'point', 'mxpoint', 'mxearning', 'submission',
        'is_active', 'featured'
    ])

    # Write data rows
    for task in tasks:
        writer.writerow([
            task.group, task.groupname, task.category, task.employee.username,
            task.activity_name, task.description, task.slug, task.duration,
            task.point, task.mxpoint, task.mxearning, task.submission,
            task.is_active, task.featured
        ])

    return response
    return response
def groups_upload_csv(request):
    context = {
        "categories": App_Categories,
    }
    if request.method == "POST":
        # Retrieve the uploaded CSV file
        csv_file = request.FILES.get("csv_upload")

        # Check if it's a CSV file
        if not csv_file.name.endswith(".csv"):
            messages.warning(request, "Not a CSV file")
            return render(request, "ai_services/uploaddata.html", context)
        try:
            # Read the CSV file
            file = csv_file.read().decode("ISO-8859-1")
            file_data = file.split("\n")
            csv_data = [line for line in file_data if line.strip() != " "]
            logger.debug(csv_data)
            
            # Create a set to store unique symbols
            unique_ids = set()
            for x in csv_data:
                logger.debug(x)
                fields = x.split(",")
                
                group_id = fields[0]

                # Check if the symbol is unique
                if group_id not in unique_ids:
                    unique_ids.add(group_id)
                    logger.debug(group_id)

                    # Create or update the record
                    created = Whatsapp_Groups.objects.update_or_create(
                            group_id=fields[0],
                            group_name=fields[1],
                            type=fields[2],
                    )

            messages.success(request, "Data populated successfully")
            return redirect('marketing:whatsapp_groups_list',id=None )
        
        except Exception as e:
            messages.warning(request, str(e))
            return render(request, "ai_services/uploaddata.html", context)

    if request.method == 'GET':
        return render(request, "ai_services/uploaddata.html", context)
	
def selinum_test(request):
	# to test on server - selenium not available in production
	if not SELENIUM_AVAILABLE:
		return HttpResponse("Selenium not available in production environment")
	
	chrome_options = webdriver.ChromeOptions()
	chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
	chrome_options.add_argument("--headless")
	chrome_options.add_argument("--disable-dev-shm-usage")
	chrome_options.add_argument("--no-sandbox")
	driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)

	# Navigate to Google's homepage
	driver.get("https://www.google.com/")

	# Get the page title
	title = driver.title
	return HttpResponse(title)

def LogsViewSet(request):
	logs = Logs.objects.all().order_by("-id")
	if request.user.is_superuser:
		return render(request, "ai_services/logs.html", {"logs": logs})
	else:
		return redirect("main:layout")
	

def refetch_data(request):
	fetch_and_insert_data()
	previous_path = request.META.get('HTTP_REFERER', '')
	return redirect(previous_path)


# =====================README VIEWS=======================================
# class UseCaseCreateView(LoginRequiredMixin, CreateView):
class CaseCategoryCreateView(CreateView):
    model = CaseCategory
    success_url = "/ai_services/display_usecases/all"
    fields =['title','description']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
	

@login_required
def UseCaseCreateView(request):
	if request.method == "POST":
		form = UseCaseForm(request.POST, request.FILES)
		if form.is_valid():
			try:
				form.instance.username = request.user
				usecase_description=form.instance.description
				if not usecase_description:
					openai_context = OpenaiPrompt.objects.filter(topic='usecase').first()
					# Gather requirements information
					requirements = form.instance.requirements_id
					what = requirements.what if requirements else ''
					why = requirements.why if requirements else ''
					requirement=f'{what},{why}'
					user_message=openai_user_message(openai_context,requirement)
					# Construct the user message
					# logger.debug(user_message)
					try:
						# openai_response = "For Testing"
						openai_response = generate_chatbot_response(user_message) if why else "No further context provided."
					except Exception as e:
						openai_response = f"Error generating response: {str(e)}"

					form.instance.description = openai_response

				form.save()
				return redirect('getdata:all_apps', app=form.instance.app)
			except DataError as e:
				logger.debug(f"DataError: {e}")
				# Check if the cleaned data has any values that are too long
				cleaned_data = form.cleaned_data
				for field_name, field_value in cleaned_data.items():
					if len(str(field_value)) > 50:  # Adjust the length as per your model
						logger.debug(f"Field causing the error: {field_name}")
						break  
		else:
			# Form is not valid, print errors
			logger.debug("Form is not valid. Errors:")
			for field, errors in form.errors.items():
				logger.debug(f"Field: {field}")
				for error in errors:
					logger.debug(f"- {error}")
	else:
		form = UseCaseForm()
		
	return render(request, "main/form.html", {"form": form})


def user_is_authorized(user):
    return user.is_authenticated

@login_required
@user_passes_test(user_is_authorized)
def use_case_update_view(request, pk):
    use_case = get_object_or_404(UseCase, pk=pk)
    openai_context = OpenaiPrompt.objects.filter(topic='usecase').first()

    if request.method == 'POST':
        form = UseCaseForm(request.POST, instance=use_case)
        if form.is_valid():
            form.instance.username = request.user
            usecase_description=form.instance.description
            if not usecase_description:
                # Gather requirements information
                requirements = form.instance.requirements_id
                what = requirements.what if requirements else ''
                why = requirements.why if requirements else ''

                # Construct the user message
                user_message = (
                    f"Question:{openai_context.expert_question}"
					f"based on this requirement: {what} and {why}, "
                    f"For more information consider topic: {openai_context.topic}," 
					f"The domain/role: {openai_context.role},"
                    f"description:{openai_context.context_description},"
                    f"clarification:{openai_context.clarification_description},"
                    f"Number of words:{openai_context.clarification_description},"
                )
                logger.debug(user_message)
                # Generate OpenAI response if 'why' is present
                try:
                    # openai_response = "testing"
                    openai_response = generate_chatbot_response(user_message) if why else "No further context provided."
                except Exception as e:
                    openai_response = f"Error generating response: {str(e)}"

                form.instance.description = openai_response

            form.save()
            return redirect('getdata:all_apps', app='all')
    else:
        form = UseCaseForm(instance=use_case)

    return render(request, 'main/form.html', {'form': form})

	
def all_apps(request, app="all"):
    apps=None
    app_usecase=None
    app_count=1
    try:
        if app == 'all':
            apps,*_ =all_applications()
            app_usecases = UseCase.objects.all()
            app_count=len(apps)

        elif app == 'AI':
            # case_categories = CaseCategory.objects.exclude(title='General')
            app_usecases = UseCase.objects.exclude(category__title='General')
            case_categories=[]
            for case in app_usecases:
                case_categories.append(case.category)

            case_categories = list(set(case_categories))
            logger.debug(case_categories)
			
            context={
				'case_categories':case_categories,
				'cases':app_usecases
			}
            return render(request, "ai_services/cases.html", context)
        else:
            apps=app.upper()
            app_usecases = UseCase.objects.filter(app=app)
            for app_usecase in app_usecases:
                app_usecase=app_usecase
 
    except UseCase.DoesNotExist:
        return redirect('main:layout')
    context = {
        "title": "USE CASE",
        "apps": apps,
        "app_usecases": app_usecases,
        "app_usecase": app_usecase,
        "app_count": app_count,
    }
    return render(request, "ai_services/all_apps.html", context)

def display_usecases(request, pk=None):
    coda_applications_list,coda_applications_tuple=all_applications()
    case=None
    usecase_count=None
    try:
        if not pk:
            usecases = UseCase.objects.all()
        else:
            usecases = UseCase.objects.filter(id=pk)
    except UseCase.DoesNotExist:
        return redirect('main:layout')
    
    usecase_count=usecases.count()
    context = {

        "title": "USE CASE",
        "coda_applications": coda_applications_list,
		"Hardware_Software_Req":Hardware_Software_Req,
        "table_contents": table_contents,
        "usecases": usecases,
        "usecase_count": usecase_count,
    }

    return render(request, "ai_services/readmeusecase.html", context)



# def migrate_transactions_to_testbudget():
	
# 	return

def migrate_transactions_to_codabudget(request):
    current_user=request.user
    From_Transaction='Transaction Table'
    To_CodaBudget='Budget Table'
    message=f'We are done transfering data from your {From_Transaction} to {To_CodaBudget}'
    logger.debug(message)
    cat='web'
    subcat='web'
    # populate_budget_categories(cat)
    populate_budget_subcategories(subcat)
    # transfer_transactions_to_codabudget(current_user)
    context={
        "message":message,
    }
    return render(request, "main/errors/generalerrors.html", context)

## Upwork connects and rate calculations

def calculate_connects(job):
    connects = 16  # Base connects

    # Add connects based on skills if skills is not None
    if job.skills:
        connects += len(job.skills) * 2  # 2 connects per skill
    
    # Add connects based on payment range
    if job.payment_range:
        if job.payment_range == '50-80':
            connects += 5
        elif job.payment_range == '80+':
            connects += 10
    
    # Add connects based on duration
    if job.duration_range:
        if job.duration_range == '1-3 months':
            connects += 2
        elif job.duration_range == '3-6 months':
            connects += 3
        elif job.duration_range == '6-12 months':
            connects += 5
        elif job.duration_range == '1 year+':
            connects += 7
    
    # Add connects based on project type
    if job.project_type:
        if job.project_type == 'ongoing':
            connects += 1
        else:
            connects += 2  
    
    # Add connects based on project category
    if job.project_category:
        if job.project_category == 'ERP SYSTEM':
            connects += 1
        elif job.project_category == 'SAAS':
            connects += 1
        elif job.project_category == 'TRAINING':
            connects += 1
        elif job.project_category == 'WEB DEVELOPMENT':
            connects += 1 
        elif job.project_category == 'BLOCKCHAIN':
            connects += 1            

    return connects
def connects_suggestion(request):
    suggestion = None
    proposal = None
    cocompany_details =company_details
    
    if request.method == 'POST':
        # Assuming a form submission here
        form = UpworkConnectsForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            connects = calculate_connects(job)
            # logger.debug(connects)
            suggestion = f"Based on your selections, you can apply for {connects} connects."
            main_context = (
				"Write a concise and engaging proposal that highlights CODA ANALYTICS' expertise in the relevant field, whether it's Business Intelligence, Web Development, AI, or Automation. "
				"Mention our client-centric approach and over a decade of experience in 7 to 8 lines. "
				"Focus on why we are the perfect fit for this specific project category, emphasizing how our skills align with the client's needs."
                "Note: it should be like humain written and remove unneeded things like name and etc. Add remember we are applying it as a company not a freelancer.Utilize professional diction,Maintain a formal,friendly and helpful tone and Keep the response concise to maintain the reader's engagement."
                "Focus on the job's demands and do not write greeting or repeat the title of the job.Also do not write any irrelivent skill that does not meet job description."
			)
            user_message = (
                f"Our company history:{company_details}"
				f"Job Title: {job.title}\n\n"
				f"Job Description:\n{job.description}\n\n"
				f"Main Context:\n{main_context}\n\n"
				
			)
            proposal = generate_chatbot_response(user_message)  
            logger.debug(proposal)

            

    else:
        form = UpworkConnectsForm()

    return render(request, 'ai_services/connect_suggestion.html', {'form': form, 'suggestion': suggestion, 'proposal': proposal})


#Excel data Fetching views

# Access GitHub API settings
        
BASE_GITHUB_API_URL = 'https://api.github.com/repos/coachofanalytics/Uat/contents/exceldata'
GITHUB_TOKEN = ''

def download_file_from_github(file_url, save_path):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3.raw'
    }
    response = requests.get(file_url, headers=headers)
    response.raise_for_status()
    
    with open(save_path, 'wb') as file:
        file.write(response.content)


def upload_excel(request, folder_name=None, file_name=None):
    form = ExcelUploadForm()  # Initialize the form
    if file_name:
        file_url = f"{BASE_GITHUB_API_URL}/{folder_name}/{file_name}"
        headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3.raw'
        }
        # local_save_path = os.path.join('/home/mehbfolder_nameoob/coda/task/cores/data', file_name)

        try:
            response = requests.get(file_url, headers=headers)
            response.raise_for_status()
            
            file_content = io.BytesIO(response.content)  
            logger.debug(f"File downloaded from GitHub: {file_name}")
            threading.Thread(target=process_excel_file, args=(file_content,)).start()
        
        except Exception as e:
            logger.debug(f"Error downloading or processing file: {e}")
            return render(request, 'excel_templates/upload.html', {
                'form': form,
                'error': f"Error downloading file: {str(e)}",
                'folder_name': folder_name,
            })
        # pass_file_name = f"data/{file_name}"
        # logger.debug('file', pass_file_name)
        # threading.Thread(target=process_excel_file, args=(local_save_path,)).start()
        
        return redirect('getdata:dashboard')  # Redirect after processing

    github_url = BASE_GITHUB_API_URL
    if folder_name:
        github_url = os.path.join(github_url, folder_name)

    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }

    # Make the request to GitHub API
    response = requests.get(github_url, headers=headers)
    
    # if response.status_code == 200:
    #     logger.debug(f"GitHub API error")
    #     return render(request, 'excel_templates/upload.html', {
    #         'form': form,
    #         'error': f"Failed to fetch data from GitHub. Status code: {response.status_code}",
    #         'folder_name': folder_name,
    #     })

    try:
        files_and_folders = response.json()
        logger.debug(files_and_folders)
      
    except json.JSONDecodeError as e:
        logger.debug(f"JSON decode error: {e}")
        return render(request, 'excel_templates/upload.html', {
            'form': form,
            'error': "Failed to parse GitHub API response as JSON.",
            'folder_name': folder_name,
        })

    logger.debug(f"==>> files_and_folders: {files_and_folders}")
    return render(request, 'excel_templates/upload.html', {'form': form, 'files': files_and_folders, 'folder_name': folder_name})

def dashboard(request):
    data = DynamicExcelData.objects.all().values_list('data', flat=True)
    data = [json.loads(item) for item in data] 
    logger.debug(data)# Convert JSON string to Python dict
    return render(request, 'excel_templates/dashboard.html', {'data': data})


def send_email(request):
    if request.method == 'POST':
        selected_indices = request.POST.getlist('selected_data')
        data = DynamicExcelData.objects.all().values_list('data', flat=True)
        data = [json.loads(item) for item in data]
        selected_data = [data[int(index)] for index in selected_indices]
        
        email_body = "Selected Data:\n\n"
        for item in selected_data:
            email_body += json.dumps(item, indent=4) + "\n\n"
        send_mail(
            'Selected Data from Dashboard',
            email_body, #Json
            settings.DEFAULT_FROM_EMAIL,
            [settings.RECIPIENT_EMAIL],  # Replace with the recipient's email
            fail_silently=False,
        )
        return redirect('dashboard')
    return redirect('dashboard')


# ==============================DIASPORA AI PLATFORM VIEWS=============================

import secrets
import json
from django.utils import timezone
from datetime import timedelta
from .ai_services import SimpleAIResponseManager
from .ai_integration_service import RealAIService, AIHealthChecker
from .forms import (
    RemittanceAnalysisForm, TradeFacilitationForm, InvestmentOpportunitiesForm,
    EducationPathwaysForm, HealthcareAccessForm
)
from .models import DiasporaAnalysisData, AnalysisSession, DiasporaAnalysisTypes, AIModelTypes
from .analytics_service import AnalyticsService
from .advanced_analytics_service import AdvancedAnalyticsService
from .ai_configuration_service import AIConfigurationService
from .presentation_service import PresentationService

def diaspora_dashboard(request):
    """Main diaspora platform dashboard with enhanced analytics tracking"""
    # Track dashboard view with enhanced data
    analytics_service = AnalyticsService()
    presentation_mode = request.GET.get('mode', 'standard')
    
    # Enhanced tracking data
    tracking_data = {
        'page': 'diaspora_dashboard',
        'presentation_mode': presentation_mode,
        'user_authenticated': request.user.is_authenticated,
        'user_type': 'staff' if request.user.is_staff else 'regular',
        'timestamp': timezone.now().isoformat(),
        'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        'ip_address': request.META.get('REMOTE_ADDR', ''),
    }
    
    analytics_service.track_event(request, 'page_view', event_data=tracking_data)
    
    # Check for presentation mode and type
    session_id = request.session.get('session_id')
    is_presentation_mode = False
    
    if session_id:
        try:
            session = AnalysisSession.objects.get(session_id=session_id)
            is_presentation_mode = session.presentation_mode
            # Track presentation session access
            analytics_service.track_event(request, 'presentation_access', event_data={
                'session_id': session_id,
                'presentation_mode': presentation_mode,
                'stakeholder_type': session.stakeholder_type,
                'is_authenticated_session': session.is_authenticated_session,
            })
        except AnalysisSession.DoesNotExist:
            pass
    
    # Use presentation service to get context
    presentation_service = PresentationService()
    context = presentation_service.get_presentation_context(presentation_mode)
    
    # Add analytics context for real-time tracking
    context['analytics_enabled'] = True
    context['presentation_mode'] = presentation_mode
    context['session_tracking'] = True
    
    # Render appropriate presentation mode template
    if is_presentation_mode or presentation_mode != 'standard':
        template_mapping = {
            'investor': 'ai_services/investor_presentation_dashboard.html',
            'banking': 'ai_services/banking_presentation_dashboard.html',
            'hybrid': 'ai_services/hybrid_presentation_dashboard.html',
        }
        
        template = template_mapping.get(presentation_mode, 'ai_services/presentation_dashboard.html')
        return render(request, template, context)
    
    return render(request, 'ai_services/diaspora_dashboard.html', context)

def create_session(request):
    """Create a new analysis session with user authentication support"""
    try:
        session_id = secrets.token_urlsafe(32)
        
        # Check if user is authenticated
        user = request.user if request.user.is_authenticated else None
        is_authenticated_session = user is not None
        
        # Handle presentation mode
        presentation_mode = request.GET.get('presentation_mode', 'false').lower() == 'true'
        
        # Create session record
        session = AnalysisSession.objects.create(
            session_id=session_id,
            user=user,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            stakeholder_type=request.GET.get('stakeholder_type', 'general'),
            is_authenticated_session=is_authenticated_session,
            presentation_mode=presentation_mode
        )
        
        # Store session ID in Django session
        request.session['session_id'] = session_id
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'presentation_mode': presentation_mode,
            'is_authenticated': is_authenticated_session,
            'user_name': user.get_full_name() if user else None,
            'message': 'Analysis session created successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating analysis session: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error creating analysis session. Please try again.',
            'details': str(e) if settings.DEBUG else None
        })

def analysis_form_view(request, analysis_type):
    """Display analysis form based on type"""
    if analysis_type not in [choice[0] for choice in DiasporaAnalysisTypes.choices]:
        return redirect('ai_services:diaspora_dashboard')
    
    # Get session ID
    session_id = getattr(request, 'session', {}).get('session_id')
    if not session_id:
        return redirect('ai_services:diaspora_dashboard')
    
    # Get appropriate form
    form_classes = {
        'remittance_analysis': RemittanceAnalysisForm,
        'trade_facilitation': TradeFacilitationForm,
        'investment_opportunities': InvestmentOpportunitiesForm,
        'education_pathways': EducationPathwaysForm,
        'healthcare_access': HealthcareAccessForm,
    }
    
    form_class = form_classes.get(analysis_type)
    if not form_class:
        return redirect('ai_services:diaspora_dashboard')
    
    form = form_class()
    
    context = {
        'title': f'{DiasporaAnalysisTypes(analysis_type).label} - Analysis',
        'analysis_type': analysis_type,
        'analysis_name': DiasporaAnalysisTypes(analysis_type).label,
        'form': form,
        'session_id': session_id,
    }
    
    return render(request, 'ai_services/analysis_form.html', context)

def process_analysis(request, analysis_type):
    """Process analysis form submission"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    # Get session ID
    session_id = getattr(request, 'session', {}).get('session_id')
    if not session_id:
        return JsonResponse({'success': False, 'error': 'No active session'})
    
    # Get appropriate form
    form_classes = {
        'remittance_analysis': RemittanceAnalysisForm,
        'trade_facilitation': TradeFacilitationForm,
        'investment_opportunities': InvestmentOpportunitiesForm,
        'education_pathways': EducationPathwaysForm,
        'healthcare_access': HealthcareAccessForm,
    }
    
    form_class = form_classes.get(analysis_type)
    if not form_class:
        return JsonResponse({'success': False, 'error': 'Invalid analysis type'})
    
    form = form_class(request.POST)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'error': 'Form validation failed',
            'errors': form.errors
        })
    
    try:
        # Get AI prediction using Real AI service with fallback
        ai_service = RealAIService()
        input_data = form.cleaned_data
        
        # Convert data types for JSON serialization
        for key, value in input_data.items():
            if isinstance(value, list):
                input_data[key] = value
            elif hasattr(value, '__float__'):  # Handle Decimal fields
                input_data[key] = float(value)
        
        prediction = ai_service.get_prediction(analysis_type, input_data, session_id)
        
        # Get user if authenticated
        user = request.user if request.user.is_authenticated else None
        
        # Store analysis data
        analysis_data = DiasporaAnalysisData.objects.create(
            session_id=session_id,
            user=user,
            analysis_type=analysis_type,
            user_input=input_data,
            ai_prediction=prediction,
            model_used=prediction.get('model_used', 'gpt4_primary'),
            confidence_score=prediction.get('confidence_score', 0.8),
            processing_time=prediction.get('processing_time', 0.0),
            fallback_used=prediction.get('fallback_used', False),
            is_real_ai=prediction.get('is_real_ai', False)
        )
        
        # Update session
        session = AnalysisSession.objects.get(session_id=session_id)
        session.total_analyses += 1
        session.save()
        
        return JsonResponse({
            'success': True,
            'analysis_id': analysis_data.id,
            'prediction': prediction,
            'message': 'Analysis completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Analysis processing failed: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Analysis processing failed',
            'details': str(e)
        })

def analysis_results(request, analysis_id):
    """Display analysis results"""
    try:
        analysis_data = DiasporaAnalysisData.objects.get(id=analysis_id, is_active=True)
        
        context = {
            'title': f'{analysis_data.analysis_type.replace("_", " ").title()} - Results',
            'analysis_data': analysis_data,
            'prediction': analysis_data.ai_prediction,
            'user_input': analysis_data.user_input,
            'analysis_type': analysis_data.analysis_type,
            'analysis_name': DiasporaAnalysisTypes(analysis_data.analysis_type).label,
        }
        
        return render(request, 'ai_services/analysis_results.html', context)
        
    except DiasporaAnalysisData.DoesNotExist:
        return redirect('ai_services:diaspora_dashboard')

def session_analytics(request, session_id):
    """Display session analytics"""
    try:
        session = AnalysisSession.objects.get(session_id=session_id)
        analyses = DiasporaAnalysisData.objects.filter(session_id=session_id, is_active=True).order_by('-created_at')
        
        context = {
            'title': 'Session Analytics',
            'session': session,
            'analyses': analyses,
            'total_analyses': analyses.count(),
        }
        
        return render(request, 'ai_services/session_analytics.html', context)
        
    except AnalysisSession.DoesNotExist:
        return redirect('ai_services:diaspora_dashboard')

def analytics_dashboard(request):
    """Enhanced analytics dashboard with comprehensive insights"""
    if not request.user.is_staff:
        return redirect('ai_services:diaspora_dashboard')
    
    # Track analytics dashboard view
    analytics_service = AnalyticsService()
    analytics_service.track_event(request, 'page_view', event_data={'page': 'analytics_dashboard'})
    
    # Get comprehensive analytics data
    analytics_data = analytics_service.get_analytics_dashboard_data()
    
    # Get recent sessions and analyses for display
    recent_sessions = AnalysisSession.objects.order_by('-start_time')[:10]
    recent_analyses = DiasporaAnalysisData.objects.filter(is_active=True).order_by('-created_at')[:10]
    
    # AI Health Status
    ai_health = AIHealthChecker.check_ai_health()
    
    context = {
        'title': 'Enhanced Analytics Dashboard',
        'recent_sessions': recent_sessions,
        'recent_analyses': recent_analyses,
        'ai_health': ai_health,
        **analytics_data  # Unpack all analytics data
    }
    
    return render(request, 'ai_services/analytics_dashboard.html', context)

def advanced_analytics_dashboard(request):
    """Advanced analytics dashboard with behavioral insights and predictive analytics"""
    if not request.user.is_staff:
        return redirect('ai_services:diaspora_dashboard')
    
    # Track advanced analytics dashboard view
    analytics_service = AnalyticsService()
    analytics_service.track_event(request, 'page_view', event_data={'page': 'advanced_analytics_dashboard'})
    
    # Get period from request
    days = int(request.GET.get('days', 30))
    
    # Get advanced analytics data
    advanced_analytics_service = AdvancedAnalyticsService()
    analytics_data = advanced_analytics_service.get_comprehensive_dashboard_data(days)
    
    context = {
        'title': 'Advanced Analytics Dashboard',
        'period_days': days,
        **analytics_data  # Unpack all advanced analytics data
    }
    
    return render(request, 'ai_services/advanced_analytics_dashboard.html', context)

def ai_health_check(request):
    """API endpoint to check AI service health"""
    health_status = AIHealthChecker.check_ai_health()
    return JsonResponse(health_status)

def ai_configuration_dashboard(request):
    """AI Configuration Dashboard for managing AI model integrations"""
    if not request.user.is_staff:
        return redirect('ai_services:diaspora_dashboard')
    
    # Track AI configuration dashboard view
    analytics_service = AnalyticsService()
    analytics_service.track_event(request, 'page_view', event_data={'page': 'ai_configuration_dashboard'})
    
    # Get AI configuration service
    ai_config_service = AIConfigurationService()
    
    # Get AI status and migration plan
    ai_status = ai_config_service.get_ai_service_status()
    migration_plan = ai_config_service.get_migration_plan()
    
    context = {
        'title': 'AI Configuration Dashboard',
        'ai_status': ai_status,
        'migration_plan': migration_plan
    }
    
    return render(request, 'ai_services/ai_configuration_dashboard.html', context)

def user_analytics(request):
    """User-specific analytics for authenticated users"""
    if not request.user.is_authenticated:
        return redirect('ai_services:diaspora_dashboard')
    
    # Get user's analysis data
    user_analyses = DiasporaAnalysisData.objects.filter(
        user=request.user, 
        is_active=True
    ).order_by('-created_at')
    
    user_sessions = AnalysisSession.objects.filter(
        user=request.user
    ).order_by('-start_time')
    
    # Analysis type breakdown for user
    user_analysis_breakdown = {}
    for analysis_type, _ in DiasporaAnalysisTypes.choices:
        count = user_analyses.filter(analysis_type=analysis_type).count()
        user_analysis_breakdown[analysis_type] = count
    
    context = {
        'title': 'My Analytics',
        'user_analyses': user_analyses,
        'user_sessions': user_sessions,
        'total_user_analyses': user_analyses.count(),
        'total_user_sessions': user_sessions.count(),
        'user_analysis_breakdown': user_analysis_breakdown,
    }
    
    return render(request, 'ai_services/user_analytics.html', context)

def presentation_guide(request):
    """Display comprehensive presentation guide for different stakeholder types"""
    context = {
        'title': 'Presentation Guide',
    }
    
    return render(request, 'ai_services/presentation_guide.html', context)