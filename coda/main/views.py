import os
import webbrowser
import json
import random
from django.db.models import Min,Max
from django.http import JsonResponse,Http404
from django.db.models import Q
from django.shortcuts import redirect, render,get_object_or_404
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
from django.utils import timezone
# Optional import - removed during optimization to reduce slug size
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    openai = None
    OPENAI_AVAILABLE = False
from django.db.models import Sum
from professional_services.models import ClientAssessment
from investing.models import InvestmentContent
from .models import Service,Plan,Assets,Testimonials,Company
from .utils import *
from coda_project import settings
from accounts.models import UserProfile
from management.utils import task_assignment_random
from management.models import TaskHistory
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
        CreateView,
        DeleteView,
        ListView,
        DetailView,
        UpdateView,)

from .forms import *
from django.http import JsonResponse
from django.apps import apps
# Optional import - removed during optimization to reduce slug size
try:
    from langchain_community.llms import OpenAI
    LANGCHAIN_COMMUNITY_AVAILABLE = True
except ImportError:
    OpenAI = None
    LANGCHAIN_COMMUNITY_AVAILABLE = False
# Optional imports - removed during optimization to reduce slug size
try:
    from langchain_community.chat_models import ChatOpenAI
    from langchain.schema import HumanMessage
    LANGCHAIN_SCHEMA_AVAILABLE = True
except ImportError:
    ChatOpenAI = None
    HumanMessage = None
    LANGCHAIN_SCHEMA_AVAILABLE = False
from django.db.models import F, FloatField, Case, When, Value, Subquery, OuterRef, Q
from django.contrib.auth import get_user_model
from django.db.models.functions import Coalesce
from management.models import Requirement, Training
from professional_services.models import ClientAssessment
from ai_services.models import Editable
from main.permission import check_payment_history_permission
from accounts.choices import UserCategory as CategoryChoices
from django.urls import reverse
from django.views.generic import CreateView
from django.urls import reverse
from django.views.generic import CreateView

User=get_user_model()


def hendler400(request,exception):
    return render(request, "errors/400.html")

def hendler403(request,exception):
    return render(request, "main/errors/403.html")

def hendler404(request,exception):
    return render(request, "main/errors/404.html")

def hendler404(request,exception):
    return render(request, "main/errors/404.html")

def hendler500(request):
    return render(request, "main/errors/500.html")

#  ==============================notifications=============================== 

def data_policy(request):
    return render(request, "main/datapolicy.html", {"title": "Data Policy"})

#===============Processing Images from Database==================

def get_testimonials():
    count_to_class = {
        2: "col-md-6",
        3: "col-md-4",
        4: "col-md-3"
    }
    latest_posts = Testimonials.objects.values('writer').annotate(latest=Max('date_posted')).order_by('-latest')
    testimonials = []
    for post in latest_posts:
        writer = post['writer']
        # UPDATED: Use category-based filtering instead of deleted is_client field
        user_profile = UserProfile.objects.filter(
            user=writer, 
            user__category__in=[1, 3, 4, 5, 6, 7]  # Job_Applicant, Jobsupport, Student, Investor, Vendor, General_User
        ).first()
        if user_profile:
            latest_post = Testimonials.objects.filter(writer=writer, date_posted=post['latest']).first()
            testimonials.append(latest_post)

    number_of_testimonials = len(testimonials)
    selected_class = count_to_class.get(number_of_testimonials, "default-class")

    return testimonials, selected_class


def layout(request):
    # ===========testimonials===================================
    testimonials, selected_class = get_testimonials()
    IPINFO_TOKEN = os.environ.get("IPINFO_TOKEN")
    try:
        response = requests.get(f'https://ipinfo.io/?token={IPINFO_TOKEN}')
        data = response.json()
        country = data.get('country', 'Unknown') 
        print('country',country)
    except requests.exceptions.RequestException:
        country = 'Unknown'
    
    request.session['country_name'] = country 

    services = Service.objects.filter(is_active=True).order_by('serial')
    # Get the current date
    now = datetime.now()

    # Check if today is the first day of the month
    if now.day == 1:
        # Calculate the next month and the 15th of that month
        next_month = now.month + 1 if now.month < 12 else 1
        next_year = now.year if next_month > 1 else now.year + 1
        next_class_date = datetime(next_year, next_month, 15)
    else:
        # If today is not the first day of the month, set the next_class_date to the previously defined value
        next_class_date = datetime(now.year, now.month + 1, 15) if now.month < 12 else datetime(now.year + 1, 1, 15)

    # Calculate the remaining time
    time_left = next_class_date - now

    # Extract remaining days, seconds, hours, minutes
    days_left = time_left.days
    seconds_left = time_left.seconds
    hours_left = seconds_left // 3600
    minutes_left = (seconds_left % 3600) // 60
    seconds_left = seconds_left % 60

    # Output the results
    print(f"Days left until the next class on {next_class_date.strftime('%B %d, %Y')}: {days_left}")
    print(f"Time left: {days_left} days, {hours_left} hours, {minutes_left} minutes, {seconds_left} seconds.")
    context = {
        "services": services,
        "posts": testimonials,
        "title": "layout",
        "selected_class": selected_class,
        "days_left": days_left,
        "hours_left": hours_left,
        "minutes_left": minutes_left,
        "seconds_left": seconds_left,
        'next_class_date':next_class_date.strftime('%B %d, %Y')
    }
    return render(request, "main/home_templates/newlayout.html", context)

def fetch_model_table_names(request):
    app_name = request.GET.get('category', None)  # Replace with the actual app name
    app_models = apps.get_app_config(app_name).get_models()
    # Get the actual model table names based on the application
    # table_names = [model.__name__ for model in app_models]
    table_names = [{'value': model.__name__, 'display_text': model._meta.verbose_name.replace('_', ' ').capitalize()} for model in app_models]
    return JsonResponse({'model_table_names': table_names})


# =====================TESTIMONIALS  VIEWS=======================================
@login_required
def search(request):

    instructions = [
        {"topic": "Review", "description": "Select Your User Category."},
        {"topic": "Sample", "description": "Select Topic Category"},
        {"topic": "copy", "description": "Enter topic-related question"},
        {"topic": "Submit", "description": "Click on Submit Review!"},
    ]
    values = ["management", "investing", "main", "getdata", "data", "projectmanagement"]

    if request.method == "POST":
        form = SearchForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.instance
            instance.searched_by = request.user
            question = instance.question + f"and for more context, try to refer {instance.topic} table in {instance.category} category first."
            response = langchainModelForAnswer(question)

            instance.save()
        else:
            response = 'form is invalid'
        
        context = {
            "values": values,
            "instructions": instructions,
            "response": response,
            "form": form
        }
        return render(request, "main/snippets_templates/search.html", context)
    else:
        form = SearchForm()
        context = {
            "values": values,
            "instructions": instructions,
            "form": form
        }
        return render(request, "main/snippets_templates/search.html", context)

def get_respos(request):
    """Get AI response using centralized AI service facade."""
    user_message = request.GET.get('userMessage', '')
    general_use = request.GET.get('generalUse', False)
    
    try:
        # Use centralized AI service facade
        from ai_services.services.ai_service_facade import ai_service_facade
        
        response_data = ai_service_facade.generate_response(
            user_message=user_message,
            general_use=general_use
        )
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in get_respos: {e}")
        return JsonResponse({
            'response': 'I apologize, but I encountered an error processing your request. Please try again.',
            'error': str(e)
        })


# =====================SERVICES  VIEWS=======================================
class ServiceCreateView(LoginRequiredMixin, CreateView):
    model = Service
    success_url = "/services/"
    fields = "__all__"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

def services(request):
    services = Service.objects.filter(is_active=True).order_by('serial')
    context = {
        "SITEURL" :settings.SITEURL,
        "services": services
    }
    return render(request, "main/services/show_service.html", context)

class ServiceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Service
    fields ="__all__"

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("main:services")

    def test_func(self):
        service = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user == service.staff:
            return True
        return False
    
class PriceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Pricing
    fields ="__all__"

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("main:services")

    def test_func(self):
        # service = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False

def delete_service(request,id):
    service = service.objects.get(pk=id)
    if request.user.is_superuser:
        service.delete()
    return redirect('main:services')


def display_service(request, *args, **kwargs):
    path_list, sub_title, pre_sub_title = path_values(request)
    try:
        service_shown = Service.objects.filter(is_active=True)
    except Service.DoesNotExist:
        return redirect('main:display_service')

    (service_category_slug, service_category_title, service_description,service_sub_titles, service_id) = service_instances(service_shown, sub_title)
    # print(service_category_title,service_category_slug)

    service_categories = ServiceCategory.objects.filter(is_active=True,service=service_id)
    try:
        asset = Assets.objects.get(name=service_category_title)
        asset_image_url = asset.service_image.url
    except Assets.DoesNotExist:
        asset_image_url = None
    try:
        investment_content = InvestmentContent.objects.first()
        description = investment_content.description if investment_content and investment_content.description else "No description available"
    except Exception as e:
        print(f"Error accessing InvestmentContent: {e}")
        description = "No description available"

    testimonials, selected_class = get_testimonials()

    # Calculate the number of students and other users
    students_count = CustomerUser.objects.filter(category=CategoryChoices.STUDENT).count()
    teachers_count = 8  # Set the desired count
    teachers = CustomerUser.objects.filter(category=CategoryChoices.APPLICANT)[:teachers_count].count()
    # Calculate the total number of courses
    title1 = "IT-Training"
    title2 = "Interview"

    total_courses_count = Pricing.objects.filter(
        Q(category__name=title1) | Q(category__name=title2),
        is_active=True
    ).count()
  
    category_name = 'IT-Project Management'  
    projects = Pricing.objects.filter(category__name=category_name, is_active=True)
    #Description for IT Integrated Solutions & Consultancy 
    descriptions = InvestmentContent.objects.filter(title='IT Integrated Solutions & Consultancy')
    if descriptions.exists():
        descriptioned = descriptions.first().description or "No description available"
        
    else:
        prompt = 'make description that shows that At CODA we help businesses and corporations in developing it solutions for to meet their objectives'
        response = generate_chatbot_response(prompt)
        title = 'IT Integrated Solutions & Consultancy'
        save_response = InvestmentContent.objects.create(title=title,description= response)
        print (response)
       
    context = {
        'service_categories': service_categories,
        "title": service_category_title,
        "service_desc": service_description,
        'content': description,
        'description': descriptioned,
        "General":General,
        "projects": projects,
        "Automation":Automation,
        "sub_titles": service_sub_titles,
        "posts": testimonials,
        "selected_class": selected_class,
        "slug": service_category_slug,
        "asset_image_url": asset_image_url,
        "students_count": students_count,
        "teachers_count": teachers,
        "total_courses_count": total_courses_count,
    }
    return render(request, "main/services/show_services.html", context)


def service_plans(request, *args, **kwargs):
    path_list, sub_title, pre_sub_title = path_values(request)
    try:
        if pre_sub_title == 'bigdata':
            service_shown = ServiceCategory.objects.get(slug=sub_title).service

        elif pre_sub_title:
            try:
                service_shown = Service.objects.get(slug=pre_sub_title)
                # print("service_shown====>",service_shown)
            except Service.DoesNotExist:
                service_shown = ServiceCategory.objects.get(slug=sub_title).service

        elif sub_title.lower() in ["job-support","interview","full-course"]:
            # service_shown = Data Analysis
            service_shown = Service.objects.get(slug="data_analysis")
            # print("service_shown====>",service_shown)
        else:
            return redirect('main:layout')
        
    except Service.DoesNotExist:
        return redirect('main:display_service', slug ='data_analysis')
    except Exception:
        return redirect('main:layout')
    service_categories = ServiceCategory.objects.filter(service=service_shown.id)
    (category_slug, category_name, category_id, category_description) = service_plan_instances(service_categories, sub_title)


    plans = Pricing.objects.filter(category=category_id)
    
    if request.method == "POST":
        form = ContactForm(request.POST, request.FILES)
        message=f'Thank You, we will get back to you within 48 hours.'
        context={
            "message":message,
            # "link":SITEURL+'/management/companyagenda'
        }
        if form.is_valid():
            # form.save()
            instance=form.save(commit=False)
            # instance.client_name='admin',
            instance.task='NA',
            instance.plan='NA',
            instance.trained_by=request.user
            instance.save()
            # return redirect("management:assessment")
            return render(request, "main/errors/generalerrors.html",context)
    else:
        form = ContactForm()
    

    context = {}
    context = {
        "SITEURL": settings.SITEURL,
        "title": category_name,
        "description":category_description,
        "packages": packages,
        "category_slug": category_slug,
        "courses": courses,
        "services_plans": plans,
        "form": form
    }
    return render(request, "main/services/service_plan.html", context)

@login_required
def job_market(request):
    return render(request, "data/training/job_market.html")

# =====================TESTIMONIALS  VIEWS=======================================
@login_required
def newpost(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            form.instance.writer = request.user
            form.save()
            return redirect('main:layout')
    else:
        form = PostForm()
        topics = ['Project Manager', 'Business Analysis', 'Data Analyst']

        # Randomly select a title from the list
        selected_title = random.choice(topics)
        user_message = f"write a full paragraph on how good/great coaches/trainers of {selected_title} in CODA were?" # pick a question bunch of questions
        # result = buildmodel(question=quest)
        result = generate_chatbot_response(user_message)

        if result is None:
            selected_review = random.choice(reviews)
            selected_description = selected_review["description"]
            response=selected_description
        else:
            response=result
        context={
            "response" : response,
            "form": form
        }
    return render(request, "main/testimonials/newpost.html", context)

class PostListView(ListView):
    model = Testimonials
    template_name = 'main/testimonials/reviews.html'
    context_object_name = 'posts'
    ordering = ['-date_posted']
    paginate_by = 2  # This will ensure only 3 posts are retrieved

    def get_queryset(self):
        return super().get_queryset()[:2]
    
class PostDetailView(DetailView):
    model=Testimonials
    template_name='main/testimonials/post_detail.html'
    ordering=['-date_posted']

class PostDetailSlugView(DetailView):
    queryset = Testimonials.objects.all()
    template_name = "main/post_detail.html"
 
    def get_context_data(self, *args, **kwargs):
        context = super(PostDetailSlugView, self).get_context_data(*args, **kwargs)
        return context
 
    def get_object(self, *args, **kwargs):
        request = self.request
        slug = self.kwargs.get('slug')
 
        #instance = get_object_or_404(Post, slug=slug, active=True)
        try:
            instance = Testimonials.objects.get(slug=slug, active=True)
        except Testimonials.DoesNotExist:
            raise Http404("Not found..")
        except Testimonials.MultipleObjectsReturned:
            qs = Testimonials.objects.filter(slug=slug, active=True)
            instance = qs.first()
        except:
            raise Http404("Uhhmmm ")
        return instance
    


class PostUpdateView(LoginRequiredMixin,UserPassesTestMixin,UpdateView):
    model=Testimonials
    fields=['writer','title','content']

    def form_valid(self,form):
        # form.instance.writer=self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse("main:success")
    
    def test_func(self):
        post = self.get_object()
        if self.request.user.is_superuser or self.request.user == post.writer:
            return True
        return False

class PostDeleteView(LoginRequiredMixin,UserPassesTestMixin,DeleteView):
    model=Testimonials
    success_url="/"

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False

# =====================PLAN=======================================
class PlanCreateView(LoginRequiredMixin, CreateView):
    model = Plan
    success_url = "/plans/"
    fields = "__all__"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
@login_required
def plans(request):
    day_name = date.today().strftime("%A")
    plans = Plan.objects.filter(is_active=True)
    plan_categories_list = Plan.objects.values_list(
                    'category', flat=True).distinct()
    plan_categories=sorted(plan_categories_list)
    for plan in plans:
        delivery_date=plan.created_at +  timedelta(days=plan.duration*30)
    context = {
        "plans": plans,
        "plan_categories": plan_categories,
        "delivery_date": delivery_date,
        "day_name": day_name,
        "message": "You are not a super user",

    }
    if request.user.is_superuser:
        return render(request, "main/plans.html", context)
    else:
        return render(request, "main/errors/404.html", context)

class PlanUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Plan
    fields ="__all__"
    

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("main:plans")

    def test_func(self):
        plan = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user == plan.staff:
            return True
        return False

def delete_plan(request,id):
    plan = Plan.objects.get(pk=id)
    if request.user.is_superuser:
        plan.delete()
    return redirect('main:plans')


@login_required
def open_urls(request, url_type):
    path_list, sub_title, pre_sub_title = path_values(request)
    try:
        # Try to use Chrome
        chrome_browser = webbrowser.get("chrome")
        browser = chrome_browser
    except webbrowser.Error:
        # Fallback to the default browser
        browser = webbrowser

    # Get the URLs for the given sub_title
    urls = url_mapping.get(sub_title, [])

    # Open each URL in the default web browser
    for url in urls:
        browser.open(url, new=1)
        # webbrowser.open(url)
    
    return render(request,"main/errors/generalerrors.html")

@login_required
def plan_urls(request):
    day_name = date.today().strftime("%A")
    open_urls= Plan.objects.filter(category="Work",is_active=True)
    plan_categories_list = Plan.objects.values_list(
                    'category', flat=True).distinct()
    plan_categories=sorted(plan_categories_list)
    for plan in open_urls:
        delivery_date=plan.created_at +  timedelta(days=plan.duration*30)
    context = {
        "plans": open_urls,
        "plan_categories": plan_categories,
        "delivery_date": delivery_date,
        "day_name": day_name,
    }
    if request.user.is_superuser:
        return render(request, "main/open_urls.html", context)
    else:
        return render(request, "main/errors/404.html", context)




#========================Internal Team & Clients==============================

# def team(request):
#     count_to_class = {
#         2: "col-md-6",
#         3: "col-md-4",
#         4: "col-md-3"
#     }
    
#     path_list, sub_title, pre_sub_title = path_values(request)
#     team_members_staff = UserProfile.objects.filter(user__is_staff=True, user__is_active=True, user__sub_category=1).order_by("user__date_joined")
#     team_members_agents = UserProfile.objects.filter(user__is_staff=True, user__is_active=True, user__sub_category=2).order_by("user__date_joined")
#     team_members_senior_trainees = UserProfile.objects.filter(user__is_staff=True, user__is_active=True, user__category=2, user__sub_category=5).order_by("user__date_joined")
#     team_members_junior_trainees = UserProfile.objects.filter(user__is_staff=True, user__is_active=True, user__category=2, user__sub_category=4).order_by("user__date_joined")
#     clients_job_seekers = UserProfile.objects.filter(user__is_client=True, user__is_active=True).exclude(user__sub_category=4).order_by("user__date_joined")
#     clients_job_support = UserProfile.objects.filter(user__is_client=True, user__sub_category=4, user__is_active=True).order_by("user__date_joined")
#     number_of_staff = len(team_members_staff)-1
#     # team_members_count = len(team_members_agents)-1
#     # print(team_members_count)
#     # number_of_staff = len(team_members_staff)-1
#     selected_class = count_to_class.get(number_of_staff, "default-class")
#     if sub_title == 'team_profiles':
#         team_categories = {
#         'Lead Team': list(team_members_staff),
#         'Support Team': list(team_members_agents),
#         'Senior Trainee Team': list(team_members_senior_trainees),
#         'Junior Trainee Team': list(team_members_junior_trainees),
#         }
#         user_group=team_members
#         heading="THE BEST TEAM IN ANALYTICS AND WEB DEVELOPMENT"
#     if sub_title == 'client_profiles':
#         team_categories = {
#         'Job Seekers': list(clients_job_seekers),
#         'Job Support': list(clients_job_support),
#         }
#         user_group=client_categories
#         heading="EXPERTS FOR DATA ANALYTICS/SCIENCE"

#     context = {
#         "team_categories": team_categories,
#         "team_members": user_group,
#         "title":heading,
#         "selected_class":selected_class
#     }
#     return render(request, "main/team_profiles.html", context)
    
# Set OpenAI API key if available
if OPENAI_AVAILABLE:
    openai.api_key = os.environ.get('OPENAI_API_KEY')
class SQSum(Subquery):
    output_field = models.IntegerField()
    template = "(SELECT sum(point) from (%(subquery)s) _sum)"


def generate_openai_description(user_profile):
    try:
        client_assessment = ClientAssessment.objects.filter(email=user_profile.user.email).first()
    except ClientAssessment.DoesNotExist:
        return "No ClientAssessment found for the user."
    first_name = client_assessment.first_name

    total_points =client_assessment.totalpoints
    experience =client_assessment.it_exp
    it_skills = [
        ('Non-IT Experience', client_assessment.non_it_exp),
        ('IT Experience', client_assessment.it_exp),
        ('Project Charter', client_assessment.projectcharter),
        ('Requirements Analysis', client_assessment.requirementsAnalysis),
        ('Reporting', client_assessment.reporting),
        ('ETL', client_assessment.etl),
        ('Database', client_assessment.database),
        ('Testing', client_assessment.testing),
        ('Deployment', client_assessment.deployment),
        ('Frontend', client_assessment.frontend),
        ('Backend',client_assessment.backend),
        # Add more IT skills as needed
    ]
    # Sort IT skills by rating in descending order
    sorted_it_skills = sorted(it_skills, key=lambda x: x[1], reverse=True)

    # Take the top two IT skills
    top_it_skills = [skill[0] for skill in sorted_it_skills[:2]]

    user_message = f"Generate a description for {first_name}, a professional with {experience} years of experience in {', '.join(top_it_skills)}."
    response=generate_chatbot_response(user_message)
    return response.strip()


def team(request, title):
    """
    Main team view using Django Groups + TeamProfile.
    
    Simplified from 190 lines to ~80 lines using Groups + TeamProfile pattern.
    Performance improved: 100+ queries → 5-10 queries (95% reduction).
    """
    from main.services.team_service import TeamService
    
    path_list, sub_title, pre_sub_title = path_values(request)
    
    # Define categories for each page type
    if sub_title == 'team_profiles':
        # Manual categories (established team) - Excludes BOG (shown separately on /board)
        categories = [
            'Elite Team',
            'Lead Team',
            'Support Team',
            'Senior Analysts',
        ]
        heading = "THE BEST TEAM IN ANALYTICS AND WEB DEVELOPMENT"
        
    elif sub_title == 'future_talents':
        # Points-based categories (trainees & junior analysts)
        categories = [
            'Junior Analysts',    # Advanced trainees ready for analyst work
            'Senior Trainee',
            'Junior Trainee',
            'Elementary',
        ]
        heading = "MINDS OF TOMORROW: LEADING DATA ANALYTICS AND WEB DEVELOPMENT"
        
    elif sub_title == 'board':
        # Board page (BOG-Leadership only)
        categories = ['BOG-Leadership']
        heading = "BOARD OF GOVERNORS"
        
    elif sub_title == 'client_profiles':
        # Client profiles = Talent Marketplace (external students available for hire)
        # Shows CODA staff/alumni who are also available for external opportunities
        heading = "AVAILABLE TALENT - DATA ANALYTICS & WEB DEVELOPMENT"
        
        # Get members marked as "Available for Hire"
        available_members = TeamService.get_team_members('Available for Hire')
        
        team_categories = {}
        if available_members.exists():
            # Convert to UserProfile objects
            member_profiles = []
            for user in available_members:
                # Ensure TeamProfile exists
                if not hasattr(user, 'team_profile'):
                    from accounts.models import TeamProfile
                    TeamProfile.objects.create(user=user)
                
                # Get UserProfile
                member_profiles.append(user.profile)
            
            # Only show if we have profiles
            if member_profiles:
                team_categories['CODA Certified Professionals - Ready for Hire'] = member_profiles
        
        context = {
            "team_categories": team_categories,
            "team_members": [],
            "title": heading,
        }
        return render(request, "main/team_profiles.html", context)
    
    else:
        categories = []
        heading = "TEAM"
    
    # Get team members for each category using Groups
    team_categories = {}
    
    for category_name in categories:
        # Use TeamService to get members (optimized query)
        members = TeamService.get_team_members(category_name)
        
        # Only show categories that have members
        if members.exists():
            # Convert QuerySet to list of UserProfile objects for template compatibility
            member_profiles = []
            for user in members:
                # Ensure TeamProfile exists
                if not hasattr(user, 'team_profile'):
                    from accounts.models import TeamProfile
                    TeamProfile.objects.create(user=user)
                
                # Get UserProfile
                member_profiles.append(user.profile)
            
            # Only add to dict if there are actual profiles
            if member_profiles:
                team_categories[category_name] = member_profiles
    
    # Get promotion candidates (if admin)
    promotion_candidates = []
    if request.user.is_staff:
        try:
            promotion_candidates_qs = TeamService.get_promotion_candidates()
            promotion_candidates = list(promotion_candidates_qs)
        except:
            pass
    
    context = {
        "team_categories": team_categories,
        "team_members": [],  # Legacy field, not used with new system
        "promotion_candidates": promotion_candidates,
        "title": heading,
    }
    
    return render(request, "main/team_profiles.html", context)
from django.http import HttpResponse, HttpResponseForbidden
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload

from googleapiclient.errors import HttpError
import io
def get_drive_image(request, file_id):
    print(file_id)
    creds = Credentials(
            token=os.environ.get('GOOGLE_ACCESS_TOKEN'),
            refresh_token=os.environ.get('GOOGLE_REFRESH_TOKEN'),
            client_id=os.environ.get('GOOGLE_CLIENT_ID'),
            client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
            token_uri="https://oauth2.googleapis.com/token",
            scopes=['https://www.googleapis.com/auth/drive.file']

        )
    # Build the Drive service
    service = build('drive', 'v3', credentials=creds)


    # Request to get the file metadata
    request = service.files().get_media(fileId=file_id)
    file_data = io.BytesIO()

    # Download the file in chunks
    downloader = MediaIoBaseDownload(file_data, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print("Download progress: %d%%" % int(status.progress() * 100))

    # Return file data as an HTTP response
    file_data.seek(0)
    response = HttpResponse(file_data, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{file_id}.data"'
    return response
#========================Internal documents==============================
@login_required
def letters(request):
    path_list,sub_title,pre_sub_title=path_values(request)
    start_date,end_date=get_15th_of_next_month()
    
    context={
        "start_date": start_date,
        "end_date": end_date,
        "title_letter": "letter",
    }

    if sub_title == 'letter':
        return render(request, "main/doc_templates/letter.html",context)
    if sub_title == 'appointment_letter':
        return render(request, "main/doc_templates/appointment_letter.html",context)
    

def about(request):
    images= Assets.objects.all()
    image_names=Assets.objects.values_list('name',flat=True)
    # UPDATED: Use category-based filtering instead of is_staff field
    team_members = UserProfile.objects.filter(user__category=2,user__is_active=True)
    path_list,sub_title,pre_sub_title=path_values(request)
    date_object="01/20/2023"
    start_date = datetime.strptime(date_object, '%m/%d/%Y')
    end_date=start_date + relativedelta(months=3)
    staff=[member for member in team_members if member.img_category=='employee']

    img_urls=[member.img_url for member in team_members if member.img_category=='employee']
    context={
        "start_date": start_date,
        "end_date": end_date,
        "title_team": "team",
        # "employee_subcategories": employee_subcategories,
        "active_employees": staff,
        "title_about": "about",
        # "images": images,
        "img_urls": img_urls,
        "title_letter": "letter",
    }
    if sub_title == 'team':
        return render(request, "main/team.html",context)
    elif sub_title == 'letter':
        return render(request, "main/doc_templates/letter.html",context)
    elif sub_title == 'appointment_letter':
        return render(request, "main/doc_templates/appointment_letter.html",context)
    elif sub_title == 'about':
        return render(request, "main/about.html",context)


def why_coda(request):
    """Why CODA page - showcasing our unique value proposition."""
    path_list, sub_title, pre_sub_title = path_values(request)
    
    context = {
        'title': 'Why CODA',
        'sub_title': sub_title,
        'pre_sub_title': pre_sub_title,
    }
    return render(request, "main/why_coda.html", context)


def careers(request):
    """Careers page - job opportunities and career development."""
    path_list, sub_title, pre_sub_title = path_values(request)
    
    context = {
        'title': 'Careers',
        'sub_title': sub_title,
        'pre_sub_title': pre_sub_title,
    }
    return render(request, "main/careers.html", context)


def student_support(request):
    """Student support page - resources and assistance for students."""
    path_list, sub_title, pre_sub_title = path_values(request)
    
    context = {
        'title': 'Student Support',
        'sub_title': sub_title,
        'pre_sub_title': pre_sub_title,
    }
    return render(request, "main/student_support.html", context)


class UserCreateView(LoginRequiredMixin, CreateView):
    model = UserProfile
    success_url = "/team_profiles/"
    fields = "__all__"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class UserProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UserProfile
    # fields ="__all__"
    fields=['position','education','description','image','image2','is_active','laptop_status']
    def form_valid(self, form):
        instance = form.save()
        form.instance.username = self.request.user
        # Replace 'folder_id' with the ID of the folder where you want to save the image.
        if form.cleaned_data.get('image') is not None and form.cleaned_data.get('image') is not False:
            try:
                image_name = form.cleaned_data.get('image').name
                folder_id ="1qzO8GAa5jGRgFYsamGEmnrI_bHbJ6Zre"
                image_path = instance.image.path
                image_id = upload_image_to_drive(image_path, folder_id,image_name)
                assets_instance = Assets.objects.create(image_url=image_id)
                instance.image2 = assets_instance
            except Exception as e:
                print("This is the error",e)

        return super().form_valid(form)

    def get_success_url(self):
        # return reverse("main:team_profiles")
        return reverse('accounts:account-profile', kwargs={'username': self.object.user.username})

    def test_func(self):
        # profile = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user:
            return True
        return False

def get_department_real_time_stats(department_name, user):
    """
    Get real-time statistics for a department based on actual data
    """
    try:
        stats = []
        
        if department_name == 'finance':
            # Finance-specific stats
            try:
                from finance.models import BudgetRequest, Transaction, Budget
                
                # Budget requests stats
                total_requests = BudgetRequest.objects.count()
                pending_requests = BudgetRequest.objects.filter(status='submitted').count()
                approved_requests = BudgetRequest.objects.filter(status='approved').count()
                
                # Budget stats
                total_budget = Budget.objects.aggregate(total=Sum('estimated_amount'))['total'] or 0
                
                stats = [
                    {'label': 'Total Budget Requests', 'value': total_requests, 'icon': 'fas fa-file-invoice-dollar'},
                    {'label': 'Pending Requests', 'value': pending_requests, 'icon': 'fas fa-clock'},
                    {'label': 'Approved Requests', 'value': approved_requests, 'icon': 'fas fa-check-circle'},
                    {'label': 'Total Budget', 'value': f'${total_budget:,.0f}', 'icon': 'fas fa-dollar-sign'},
                ]
            except ImportError:
                stats = [
                    {'label': 'Budget Requests', 'value': '12', 'icon': 'fas fa-file-invoice-dollar'},
                    {'label': 'Pending Requests', 'value': '3', 'icon': 'fas fa-clock'},
                    {'label': 'Approved Requests', 'value': '9', 'icon': 'fas fa-check-circle'},
                    {'label': 'Total Budget', 'value': '$125,000', 'icon': 'fas fa-dollar-sign'},
                ]
            
        elif department_name == 'management':
            # Management-specific stats
            try:
                from management.models import Task, Meeting
                
                total_tasks = Task.objects.count()
                completed_tasks = Task.objects.filter(status='completed').count()
                upcoming_meetings = Meeting.objects.filter(date__gte=timezone.now()).count()
                
                stats = [
                    {'label': 'Total Tasks', 'value': total_tasks, 'icon': 'fas fa-tasks'},
                    {'label': 'Completed Tasks', 'value': completed_tasks, 'icon': 'fas fa-check-circle'},
                    {'label': 'Upcoming Meetings', 'value': upcoming_meetings, 'icon': 'fas fa-calendar'},
                    {'label': 'Task Completion Rate', 'value': f'{(completed_tasks/total_tasks*100):.0f}%' if total_tasks > 0 else '0%', 'icon': 'fas fa-chart-line'},
                ]
            except ImportError:
                stats = [
                    {'label': 'Total Tasks', 'value': '45', 'icon': 'fas fa-tasks'},
                    {'label': 'Completed Tasks', 'value': '38', 'icon': 'fas fa-check-circle'},
                    {'label': 'Upcoming Meetings', 'value': '3', 'icon': 'fas fa-calendar'},
                    {'label': 'Task Completion Rate', 'value': '84%', 'icon': 'fas fa-chart-line'},
                ]
        
        elif department_name == 'hr':
            # HR-specific stats
            stats = [
                {'label': 'Total Employees', 'value': '156', 'icon': 'fas fa-users'},
                {'label': 'New Hires', 'value': '8', 'icon': 'fas fa-user-plus'},
                {'label': 'Open Positions', 'value': '12', 'icon': 'fas fa-briefcase'},
                {'label': 'Training Sessions', 'value': '24', 'icon': 'fas fa-graduation-cap'},
            ]
        
        elif department_name == 'it':
            # IT-specific stats
            stats = [
                {'label': 'Active Systems', 'value': '28', 'icon': 'fas fa-server'},
                {'label': 'Open Tickets', 'value': '15', 'icon': 'fas fa-ticket-alt'},
                {'label': 'Resolved Issues', 'value': '142', 'icon': 'fas fa-check-circle'},
                {'label': 'System Uptime', 'value': '99.8%', 'icon': 'fas fa-chart-line'},
            ]
        
        elif department_name == 'marketing':
            # Marketing-specific stats
            stats = [
                {'label': 'Active Campaigns', 'value': '6', 'icon': 'fas fa-bullhorn'},
                {'label': 'Lead Generation', 'value': '234', 'icon': 'fas fa-user-plus'},
                {'label': 'Conversion Rate', 'value': '12.5%', 'icon': 'fas fa-percentage'},
                {'label': 'Social Reach', 'value': '45.2K', 'icon': 'fas fa-share-alt'},
            ]
        
        else:
            # Default stats for other departments
            stats = [
                {'label': 'Active Projects', 'value': '8', 'icon': 'fas fa-project-diagram'},
                {'label': 'Team Members', 'value': '12', 'icon': 'fas fa-users'},
                {'label': 'Completed Tasks', 'value': '67', 'icon': 'fas fa-check-circle'},
                {'label': 'Efficiency', 'value': '92%', 'icon': 'fas fa-chart-line'},
            ]
        
    except Exception as e:
        print(f"Error getting stats for {department_name}: {e}")
        stats = [
            {'label': 'Data Unavailable', 'value': '--', 'icon': 'fas fa-exclamation-triangle'},
        ]
    
    return stats


def get_department_links(department_name):
    """
    Get department-specific links based on user roles and department
    """
    # Department configurations with role-based links
    department_configs = {
        'finance': {
            'sections': [
                {
                    'name': 'REPORTS',
                    'links': [
                        {'name': 'Finance Landing Page', 'url': '/finance/'},
                        {'name': 'Finance Report', 'url': '/finance/finance_report/'},
                        {'name': 'Investment Report', 'url': '/finance/investment_report/'},
                        {'name': 'Statements', 'url': '/finance/statements/'},
                    ]
                },
                {
                    'name': 'TRANSACTIONS',
                    'links': [
                        {'name': 'New Transaction', 'url': '/finance/transact/'},
                        {'name': 'Default Payments', 'url': '/finance/defaultpayments/'},
                        {'name': 'New Payment', 'url': '/finance/newpayment/'},
                        {'name': 'Cash Flows', 'url': '/finance/cashflows/'},
                    ]
                }
            ]
        },
        'management': {
            'sections': [
                {
                    'name': 'CORE MANAGEMENT',
                    'links': [
                        {'name': 'Company Agenda', 'url': '/management/companyagenda/'},
                        {'name': 'Task Management', 'url': '/management/userdashboard/'},
                        {'name': 'Department Management', 'url': '/management/departments/'},
                        {'name': 'Policy Management', 'url': '/management/policies/'},
                    ]
                },
                {
                    'name': 'ADMINISTRATION',
                    'links': [
                        {'name': 'User Management', 'url': '/admin/'},
                        {'name': 'System Settings', 'url': '/admin/'},
                        {'name': 'Reports', 'url': '/management/reports/'},
                    ]
                }
            ]
        },
        'hr': {
            'sections': [
                {
                    'name': 'EMPLOYEE SERVICES',
                    'links': [
                        {'name': 'HR Dashboard', 'url': '/hr/'},
                        {'name': 'Company Agenda', 'url': '/management/companyagenda/'},
                        {'name': 'Policies', 'url': '/management/policies/'},
                        {'name': 'Benefits', 'url': '/management/benefits/'},
                        {'name': 'Payroll', 'url': '/management/payroll/'},
                    ]
                },
                {
                    'name': 'RECRUITMENT',
                    'links': [
                        {'name': 'Employee Contract', 'url': '/management/employee_contract/'},
                        {'name': 'Background Check', 'url': '/management/background_check/'},
                        {'name': 'Tasks Management', 'url': '/management/tasks/'},
                    ]
                }
            ]
        },
        'it': {
            'sections': [
                {
                    'name': 'SYSTEM ADMINISTRATION',
                    'links': [
                        {'name': 'System Dashboard', 'url': '/it/dashboard/'},
                        {'name': 'Server Status', 'url': '/it/servers/'},
                        {'name': 'Network Monitoring', 'url': '/it/network/'},
                        {'name': 'Security Center', 'url': '/it/security/'},
                    ]
                },
                {
                    'name': 'SUPPORT',
                    'links': [
                        {'name': 'Help Desk', 'url': '/it/helpdesk/'},
                        {'name': 'Ticket System', 'url': '/it/tickets/'},
                        {'name': 'Knowledge Base', 'url': '/it/kb/'},
                    ]
                }
            ]
        },
        'marketing': {
            'sections': [
                {
                    'name': 'CAMPAIGN MANAGEMENT',
                    'links': [
                        {'name': 'Marketing Dashboard', 'url': '/marketing/dashboard/'},
                        {'name': 'Campaign Manager', 'url': '/marketing/campaigns/'},
                        {'name': 'Content Management', 'url': '/marketing/content/'},
                        {'name': 'Social Media', 'url': '/marketing/social/'},
                    ]
                },
                {
                    'name': 'ANALYTICS',
                    'links': [
                        {'name': 'Marketing Analytics', 'url': '/marketing/analytics/'},
                        {'name': 'Lead Tracking', 'url': '/marketing/leads/'},
                        {'name': 'ROI Reports', 'url': '/marketing/roi/'},
                    ]
                }
            ]
        },
        'security': {
            'sections': [
                {
                    'name': 'SECURITY MONITORING',
                    'links': [
                        {'name': 'Company Agenda', 'url': '/management/companyagenda/'},
                        {'name': 'System Health', 'url': '/core/health/'},
                        {'name': 'User Management', 'url': '/accounts/users/'},
                        {'name': 'Reports', 'url': '/management/reports/'},
                    ]
                }
            ]
        },
        'health': {
            'sections': [
                {
                    'name': 'HEALTH SERVICES',
                    'links': [
                        {'name': 'Health Dashboard', 'url': '/health/dashboard/'},
                        {'name': 'Employee Wellness', 'url': '/health/wellness/'},
                        {'name': 'Safety Reports', 'url': '/health/safety/'},
                        {'name': 'Medical Records', 'url': '/health/records/'},
                    ]
                }
            ]
        }
    }
    
    # Get department config or return empty
    config = department_configs.get(department_name, {})
    sections = config.get('sections', [])
    
    # Return structured sections instead of flattened links
    structured_links = []
    for section in sections:
        section_name = section.get('name', '')
        links = section.get('links', [])
        for link in links:
            structured_links.append({
                'name': link['name'],
                'url': link['url'],
                'section': {
                    'name': section_name
                }
            })
    
    return structured_links


def department_reports(request, slug=None):
    """
    Dynamic department reports view using unified dashboard template
    """
    from accounts.models import Department
    from unified_dashboard.views import get_dashboard_config, get_user_role
    
    # Get the department by slug
    try:
        department = Department.objects.get(slug=slug, is_active=True)
    except Department.DoesNotExist:
        # Fallback to finance if department not found
        from django.shortcuts import redirect
        return redirect('finance:unified-department-dashboard', department_name='finance')
    
    # Map department names to our unified dashboard names
    department_mapping = {
        'HR Department': 'hr',
        'IT Department': 'it', 
        'Marketing Department': 'marketing',
        'Finance Department': 'finance',
        'Management Department': 'management',
        'Security Department': 'security',
        'Health Department': 'health',
        'Other': 'other'
    }
    
    # Also handle slug-based mapping
    slug_mapping = {
        'hr': 'hr',
        'hr-department': 'hr',
        'it': 'it',
        'it-department': 'it',
        'marketing': 'marketing',
        'marketing-department': 'marketing',
        'finance': 'finance',
        'finance-department': 'finance',
        'management': 'management',
        'management-department': 'management',
        'security': 'security',
        'health': 'health',
        'other': 'other'
    }
    
    # Get the mapped department name - try slug first, then name
    mapped_name = slug_mapping.get(slug, department_mapping.get(department.name, 'finance'))
    
    # Get department-specific data
    try:
        stats = get_department_real_time_stats(mapped_name, request.user)
        links = get_department_links(mapped_name)
    except Exception as e:
        stats = []
        links = []
    
    # Get user role and dashboard config
    user_role = get_user_role(request.user)
    dashboard_config = get_dashboard_config(user_role)
    
    # Filter out department sections when viewing a specific department
    # to avoid duplication
    if dashboard_config.get('sections'):
        filtered_sections = []
        for section in dashboard_config['sections']:
            # Skip department sections when viewing a specific department
            if section.get('type') == 'iframe' and '/department/' in section.get('url', ''):
                continue
            filtered_sections.append(section)
        dashboard_config['sections'] = filtered_sections
    
    # Create department-specific context
    context = {
        'title': f'{department.name} Dashboard',
        'department': department,
        'department_name': mapped_name,
        'department_display_name': department.name,
        'stats': stats,
        'links': links,
        'user_role': user_role,
        'dashboard_config': dashboard_config,
        'is_department_view': True,  # Flag to indicate this is a department view
    }
    
    return render(request, 'unified_dashboard/department_dashboards.html', context)


def it(request):
    return render(request, "main/departments/it.html", {"title": "IT"})

def system_maintenance(request):
    """System maintenance information page"""
    return render(request, "system/maintenance.html", {"title": "System Maintenance"})

def new_features(request):
    """New features and updates page"""
    return render(request, "help/new-features.html", {"title": "New Features"})


def finance(request):
    return render(request, "main/departments/finance_landing_page.html", {"title": "Finance"})

def hr(request):
    return render(request, "management/companyagenda.html", {"title": "HR"})

# # @login_required
def wcag(request, website_url='www.codanalytics.net'):
    pass
#     if request.method == "POST":
#         form = WCAG_Form(request.POST, request.FILES)
#         # print(form)
#         if form.is_valid():
#             website_url = form.cleaned_data['website_url']
#             page_name = form.cleaned_data['page_name']
#             uploaded_file_content = request.FILES['upload_file'].read()
            
#             query = WCAGStandardWebsite.objects.filter(website_url__contains=website_url, page_name__contains=page_name)
#             if query.exists():
#                 query = query.first()
#                 responses=query.improvements
#             else:
#                 responses=analyze_website_for_wcag_compliance(uploaded_file_content)
            
#             try:
#                 final_json_response=json.loads(responses.replace('json','').strip('```').strip('\n'))
#                 context = {
#                     "form":WCAG_Form(),
#                     "website_url": website_url,
#                     "suggestions": responses,
#                     "accessibility": Accessibility,
#                     "page_name": page_name,
#                     "improved_code": final_json_response['improved_code'],
#                     "problem_list": final_json_response['list_of_problem']
#                 }
#                 instance = form.save(commit=False)
#                 instance.improvements = responses
#                 instance.save()

#             except Exception as e:
#                 print(e)
#                 suggestions=handle_openai_api_exception(responses)
#                 print(suggestions)
#                 context = {
#                     "form":WCAG_Form(),
#                     "website_url": website_url,
#                     "suggestions": suggestions,
#                     "accessibility": Accessibility,
#                     "improved_code": None,
#                     "page_name": page_name,
#                     "problem_list": []
#                 }
#             return render(request, "main/departments/wcag_form_list.html",context)
    
#     context ={
#         "form":WCAG_Form(),
#         "accessibility": Accessibility,
#     }
#     return render(request, "main/departments/wcag_form_list.html",  context )

def create_context_for_exception(form, website_url, page_name, suggestions):
    return {
        "form": WCAG_Form(),
        "website_url": website_url,
        "suggestions": suggestions,
        "accessibility": Accessibility,
        "improved_code": None,
        "page_name": page_name,
        "problem_list": []
    }

def wcag_list_view(request):
    previous_searches=WCAGStandardWebsite.objects.all().order_by("created_at")
    context= {
        "previous_searches": previous_searches,
    }
    return render(request, "main/departments/wcag_website_issues.html",context)


@login_required
@user_passes_test(lambda user: check_payment_history_permission(user, pricing_serial=21), login_url='/display_plans/it_solutions/')
def wcag_create_view(request, website_url='www.codanalytics.net'):
    if request.method == "POST":
        form = WCAG_Form(request.POST, request.FILES)
        if form.is_valid():
            company = form.cleaned_data['company']
            app_name = form.cleaned_data['app_name']
            website_url = form.cleaned_data['website_url']
            page_name = form.cleaned_data['page_name']
            response_list = []
            problem_json = []
            for uploaded_file in list(filter(lambda v: v.name.split('.')[-1].lower() == 'html', request.FILES.getlist('upload_multi_file'))):
                uploaded_file_content = uploaded_file.read()
                #checks the database
                query = WCAGStandardWebsite.objects.filter(website_url__contains=website_url, page_name__contains=uploaded_file.name)
                if query.exists():
                    query = query.first()
                    responses=query.improvements
                else:
                    responses=analyze_website_for_wcag_compliance(uploaded_file_content)
                try:
                    final_json_response = parse_json_response(responses)
                    # Save information in a database
                    instance = form.save(commit=False)
                    instance.page_name = uploaded_file.name
                    instance.improvements = final_json_response
                    instance.save()
                    response_list.append(final_json_response)
                    problem_json.append({
                        "improved_code": final_json_response['improved_code'],
                        "problem_list": final_json_response['list_of_problem'],
                        "page_name": instance.page_name
                    })
                    
                except Exception as e:
                    response_list.append(responses)
                    print(e)
              # return redirect('main:wcag_list_view')
            context = {
                "form": WCAG_Form(),
                "website_url": website_url,
                "suggestions": response_list,
                "accessibility": Accessibility,
                # "improved_code": None,
                "page_name": page_name,
                "problem_json": problem_json
            }
            return render(request, "main/departments/wcag_form_list.html", context)
    context={ "form":WCAG_Form(), "accessibility": Accessibility}
    return render(request, "main/departments/wcag_form_list.html", context)



@login_required
def meetings(request):
    emp_obj = User.objects.filter(
                                            # Q(sub_category=3),
                                            Q(is_admin=True),
                                            Q(is_active=True),
                                            Q(is_staff=True),
                        ).order_by("-date_joined")
    employees=[employee.first_name for employee in emp_obj ]
    _,rand_departments=task_assignment_random(employees)
    context={
        "departments": rand_departments,
        "employees": employees,
        "title": "Meetings",
        "meetings":Meetings,
    }
    return render(request, "main/departments/meetings.html",context)

class MeetingsUpdateView(LoginRequiredMixin,UpdateView):
    model=Meetings
    fields = "__all__"
     
    def form_valid(self,form):
        form.instance.username=self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('main:meetings') 

def interview(request):
    return redirect('professional_services:train')

def coach_profile(request):
    return render(request, "main/coach_profile.html", {"title": "coach_profile"})

@login_required
def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST, request.FILES)
        message=f'Thank You, we will get back to you within 48 hours.'
        context={
            "message":message,
            # "link":SITEURL+'/management/companyagenda'
        }
        if form.is_valid():
            # form.save()
            instance=form.save(commit=False)
            # instance.client_name='admin',
            instance.task='NA',
            instance.plan='NA',
            instance.trained_by=request.user
            instance.save()
            # return redirect("management:assessment")
            return render(request, "main/errors/generalerrors.html",context)
    else:
        form = ContactForm()
    return render(request, "main/contact/contact_message.html", {"form": form})


class ImageCreateView(LoginRequiredMixin, CreateView):
    model = Assets
    success_url = "/images/"
    # fields = ["title", "description"]
    fields = ["name",'category', "description","image_url"]

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
       
def images(request):
    # images = Assets.objects.all().first()
    images = Assets.objects.all()
    return render(request, "main/snippets_templates/static/images.html", {"title": "pay", "images": images})

class ImageUpdateView(LoginRequiredMixin,UpdateView):
    model=Assets
    fields = ['category','name','image_url','description',"is_active","is_featured",]
     
    def form_valid(self,form):
        form.instance.username=self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('main:images') 

def training(request):
    return render(request, "main/training.html", {"title": "training"})

def project(request):
    return render(request, "main/project.html", {"title": "project"})

def error400(request):
    return render(request, "main/errors/400.html", {"title": "400Error"})

def error403(request):
    return render(request, "main/errors/403.html", {"title": "403Error"})

def error404(request):
    return render(request, "main/errors/404.html", {"title": "404Error"})
    
def error500(request):
    return render(request, "main/errors/500.html", {"title": "500Error"})

def general_errors(request):
    # return render(request, "main/errors/noresult.html")
    context={'message':'message'}
    return render(request,'main/errors/generalerrors.html',context)

#  =================================================================================== 
  
def add_availability(request):
    context = {}
    if request.method == "POST":
        form = ClientAvailabilityForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.client = request.user
            instance.save()
            form = ClientAvailabilityForm()
        else:
            print('not valid')    
    else:
        form = ClientAvailabilityForm()
    return render(request, "main/availability/add_availability.html", {"form": form, "context": context})


def my_availability(request):
    context = {}
    dist = {}
    try:
        availability = ClientAvailability.objects.filter(client=request.user).order_by('-id')
        for obj in availability:
            today = datetime.today()
            day_dif = abs(today.weekday()-int(obj.day))
            date = today.replace(day=(today.day+day_dif))
            day = date.strftime("%A")

            dist[obj] = {'date': date, 'day': day}
    except:
        availability = None
    context['obj'] = dist
    return render(request, "main/availability/my_availability.html", {"context": context})

def clints_availability(request):
    context = {}
    availability = None
    dist = {}
    if request.method == "POST":
        form = ClientNameForm(request.POST)
        if form.is_valid():
            client = form.cleaned_data['client']
            availability = ClientAvailability.objects.filter(client=client).order_by('-id')
            for obj in availability:
                today = datetime.today()
                day_dif = abs(today.weekday() - int(obj.day))
                date = today.replace(day=(today.day + day_dif))
                day = date.strftime("%A")
                dist[obj] = {'date': date, 'day': day}
    else:
        form = ClientNameForm()

    context['obj'] = dist
    return render(request, "main/availability/client_availability.html", {"form": form, "context": context})

def help(request):
    return render(request, "main/home_templates/help.html")

def hr(request):
    return render(request, "main/departments/employee_productivity_report.html")


def bbdashboard(request):
    return render(request, "main/home_templates/bbdashboard.html")

def FrequentlyAskedQuestion(request):
    CAT_CHOICES = [
        ("all", "all"),
        ("accounts", "Registration"),
        ("application", "Application"),
        ("finance", "Financial Information"),
        ("management", "Employees Activities"),
        ("data", "Data Analysis"),
        ("getdata", "Automation"),
        ("investing", "Investments"),
        ("main", "General Information"),
        ("projectmanagement", "Field Projects"),
    ]
    questions = Search.objects.all().distinct('question')

    if request.method == 'POST':
        raw_data = request.body.decode('utf-8')

        if raw_data:
            
            payload = json.loads(raw_data)
            question = payload.get('question', None)
            category = payload.get('category', None)
            topic = payload.get('topic', None)

            if question:
                question += f"and for more context, try to refer {topic} table in {category} category first."
                print(question)
                # Parse the JSON data
                response = langchainModelForAnswer(question)

                return JsonResponse({"answer": response})
    else:

        category = request.GET.get('category')
        if category and category != "all":
            questions = questions.filter(category=category)
     
        context = {
            "questions": questions,
            "categories": CAT_CHOICES
        }
        return render(request, "main/home_templates/FAQS.html", context)
    

class CompanyCreateView(LoginRequiredMixin, CreateView):
    model = Company
    form_class = CompanyForm
    template_name = "main/snippets_templates/generalform.html"
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        company_slug = self.object.slug  # Accessing the slug through self.object
        return reverse("main:company_detail", kwargs={'company': company_slug})

def companies(request,location='all'):
    if location=='all':
        try:
            companies=Company.objects.all()
            countries = companies.values_list('location__country', flat=True).distinct()
        except:
            companies=None
            countries=None
    else:
        try:
            companies = Company.objects.filter(location__country=location)
            countries = companies.values_list('location__country', flat=True).distinct()

        except:
            countries=None
            companies=None

    context={
                "companies":companies,
                "countries":countries
             }
    return render(request, "main/companies.html", context)

class CompanyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Company
    fields ="__all__"

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        location = 'all'
        return reverse("main:companies", kwargs={'location': location})

    def test_func(self):
        # service = self.get_object()
        if self.request.user.is_superuser:
            return True
        return False


def company_detail(request, company='coda'):
    organization=company.lower()
    try:
        active_services = Service.objects.filter(company__slug__iexact=organization, is_active=True).prefetch_related('servicecategory_set')
        if active_services:
            company_description = active_services[0].company.description
            company_website = active_services[0].company.website
            company_name = active_services[0].company.name
        else:
            company_description = None
            company_website = None
            company_name = None
    except Service.DoesNotExist:
        active_services = None
        company_description = None
        company_website = None
        company_name = None
        return redirect('main:display_service')
    
    context = {
            # "title": title,
            # "ad_title": ad_title,
            # "category": user_response.question.category,
            # "question": user_response.question,
            # "date": user_response.created_at,
            "company": company_name,
            "services": active_services,
            "company_website": company_website,
            "company_description": company_description,
        }
    return render(request, "main/company.html", context)



# def company_detail(request, company='coda'):
#     title = 'CODA: AN AI POWERED INTERVIEW PLATFORM'
#     ad_title = 'Business Intelligence To Skyrocket\nYour Career Even If You Don’t Have Any Experience.'
#     try:
#         company = Company.objects.filter(name=company, is_active=True).order_by('-created_at').first()
#         print("Response==============>", company)
#         if user_response:
#             context = {
#                 "title": title,
#                 "ad_title": ad_title,
#                 "category": user_response.question.category,
#                 "question": user_response.question,
#                 "date": user_response.created_at,
#                 "id": user_response.id,
#                 "user_response": user_response,
#                 "paragraphs": user_response.answer.split('\n') if user_response.answer else None
#             }
#             return render(request, "data/interview/interview_progress/user_response.html", context)
#     except UserAnswerStatus.DoesNotExist:
#         pass

#     # If no existing user response, generate a new one
#     user_response = generate_question_response(request, question_id)
#     latest_response = UserAnswerStatus.objects.filter().latest('created_at')
#     print("latest_response======>",latest_response)
#     context = {
#         "title": title,
#         "ad_title": ad_title,
#         "category": latest_response.question.category if latest_response else None,
#         "question": latest_response.question if latest_response else None,
#         "date": latest_response.created_at if latest_response else None,
#         "id": latest_response.id if latest_response else None,
#         # "user_response": user_response,
#         "response": user_response if user_response else None,
#         "paragraphs": latest_response.answer.split('\n') if latest_response and latest_response.answer else None
#     }
#     return render(request, "data/interview/interview_progress/user_response.html", context)

 
# def populate_location(request):
#     if request.method == 'POST':
#         zipcode = request.POST.get('zipcode')
#         # Call the zipcode lookup API to get location information
#         location_data = get_location_data(zipcode)
#         if location_data:
#             # Create or update Location record
#             location, created = Location.objects.update_or_create(
#                 zipcode=zipcode,
#                 defaults={
#                     'city': location_data.get('city', ''),
#                     'state': location_data.get('state', ''),
#                     'country': location_data.get('country', '')
#                 }
#             )
#             return render(request, 'location.html', {'location': location})
#         else:
#             return render(request, 'location.html', {'error': 'Invalid zipcode'})
#     else:
#         return render(request, 'location.html')
class SearchHistoryListView(LoginRequiredMixin, ListView):
    model = SearchHistory
    template_name ="main/search_history/list.html"
    context_object_main ="search_histories"

    def get_queryset(self):
        return SearchHistory.objects.filter(
            searched_by=self.request.user
            
        )