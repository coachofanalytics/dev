import os
import json
import random
import datetime
from datetime import datetime as date_obj
from django.conf import settings
from django.utils.text import slugify
from django import template
# from django.apps import appss
from django.db.models import Q
import string

# Use this function to get the current SITEURL dynamically
def get_site_url():
    return getattr(settings, 'SITEURL', 'http://127.0.0.1:8000')

register = template.Library()

@register.filter
def convert_date(date_string):
    return datetime.datetime.strptime(date_string, "%m/%d/%Y").date()

def random_string_generator(size=25, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def dates_functionality():
    current_year = date_obj.now().year
    current_date = date_obj.now()
    first_date = current_date.replace(day=1)
    start_of_year = date_obj(current_date.year, 1, 1)
    ytd_duration = (current_date - start_of_year).days
    return ytd_duration, current_year, first_date

# --- Data Structures using dynamic URL resolution ---

data_interview = [
    {"Inteview": "1. Transcripts", "Description": "Write Your Responses to 8 Topics", "Duration": "5 Days/3 Runs", "Lead": "Self/Coach", "Link": get_site_url() + "/data/interviewuploads/"},
    {"Inteview": "2. Practice Sessions", "Description": "Self recorded practice sessions for all 8 questions", "Duration": "5 Days/24 sessions", "Lead": "Self/Coach", "Link": get_site_url() + "/management/sessions/interview"},
    {"Inteview": "3. Role-Concentration", "Description": "Interact with a database of 80 Technical Interview Questions", "Duration": "5 Days ", "Lead": "Self/Coach", "Link": get_site_url() + "/data/prepquestions/"},
    {"Inteview": "4. Mock Interviews", "Description": "Real Life simulation of mock interview with coach of analytics", "Duration": "2 Mock/4 Past Interviews", "Lead": "Coach", "Link": get_site_url() + "/management/sessions/mock"},
    {"Inteview": "5. Job Application & Salary Negotiation", "Description": "Guide you on how to apply and respond to recruiters", "Duration": "14 Days", "Lead": "self/Coach", "Link": get_site_url() + "/data/job_market/"},
]

job_support = [
    {"Inteview": "1. onboarding", "Description": "Organization,Working PPT,Tools Access", "Duration": "4 hours", "Lead": "Self/Coach", "Link": get_site_url() + "data/Course%20Overview/"},
    {"Inteview": "2. Requirements Review", "Description": "Elicitation Questions", "Duration": "Ongoing", "Lead": "Self/Coach", "Link": "https://app.box.com/s/oee1wn85sk2slbc0fkzs2sahe8ob8qhi"},
    {"Inteview": "2. Project Scope & Definition", "Description": "SDLC Process in Box", "Duration": "Ongoing", "Lead": "Self/Coach", "Link": "https://app.box.com/s/fqdxfywn8c0uixarpuvoo2o7gx18lwdw"},
    {"Inteview": "3. Technical Support", "Description": "Training & Troubleshooting", "Duration": " >25 hours", "Lead": "Self/Coach", "Link": get_site_url() + "/data/Development/"},
]

Automation = [
    {"title": "OPENAI", "link": "https://chat.openai.com/chat", "description": "CHATGPT/Gemini: The super power of modern day analytics", "service_category_slug": None, "service_url": "https://chat.openai.com/chat", "serial": None},
    {"title": "Testimonials", "link": get_site_url() + "/post/new/", "description": "Using AI to aid Clients to leave feedback", "service_category_slug": None, "service_url": get_site_url() + "/post/new/", "serial": None},
    {"title": "Search Data", "link": get_site_url() + "/search/", "description": "Giving You the power to search your own data", "service_category_slug": None, "service_url": get_site_url() + "/search/", "serial": None},
    {"title": "Stocks & Options", "link": get_site_url() + "/investing/options/shortputdata", "description": "Fetching information from options play", "service_category_slug": 'options', "service_url": get_site_url() + '/display_plans/options', "serial": None},
    {"title": "Social Media", "link": get_site_url() + "/marketing/", "description": "Posting ads to social media", "service_category_slug": 'social_media', "service_url": get_site_url() + '/display_plans/it_solution/', "serial": 19},
    {"title": "Accessibility Checks", "link": get_site_url() + "/check_wcag_compliance/", "description": "Expanding accessibility to all", "service_category_slug": 'accessibility', "service_url": get_site_url() + '/display_plans/it_solution/', "serial": 21},
]

Meetings = [
    {"title": "1-1 Session", "link": "...", "linkname": "1-1 Session", "video": "..."},
    {"title": "General Meeting", "link": get_site_url() + "/management/companyagenda/", "linkname": "General Meeting", "video": "..."},
    {"title": "BI Session", "link": get_site_url() + "/management/companyagenda/", "linkname": "BI Session", "video": "..."},
    # ... Add remaining links using get_site_url() ...
]

# --- Helper functions remain the same as your snippet ---

def path_values(request):
    try:
        previous_path = request.META.get('HTTP_REFERER', '')
    except Exception:
        previous_path = f"{get_site_url()}/management/companyagenda/"
    # ... Rest of function logic ...
    return path_values, sub_title, pre_sub_title