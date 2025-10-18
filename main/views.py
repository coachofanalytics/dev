import os
import datetime, json
import random
from django.db.models import Min,Max
from django.http import JsonResponse,Http404
from django.db.models import Q
from django.shortcuts import redirect, render,get_object_or_404
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
import openai
from django.db.models import Sum
from .models import Service,Assets,Readme,Location,Testimonials
from .utils import *
from coda_project import settings
from application.models import UserProfile
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
        CreateView,
        DeleteView,
        ListView,
        DetailView,
        UpdateView,)

from .forms import TestimonialForm,locationForm
from django.http import JsonResponse
from django.apps import apps
from langchain_community.llms import OpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from django.db.models import F, FloatField, Case, When, Value, Subquery, OuterRef, Q
from django.contrib.auth import get_user_model
from django.db.models.functions import Coalesce

import requests
from accounts.choices import CategoryChoices

User=get_user_model()

#  ===================================================================================   
def checkout(request):
    return render(request, "main/checkout.html", {"title": "checkout"})


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

def data_policy(request):
    return render(request, "main/datapolicy.html", {"title": "Data Policy"})

#===============Processing Images from Database==================

# def get_testimonials():
#     count_to_class = {
#         2: "col-md-6",
#         3: "col-md-4",
#         4: "col-md-3"
#     }
#     latest_posts = Testimonials.objects.values('writer').annotate(latest=Max('date_posted')).order_by('-latest')
#     testimonials = []
#     for post in latest_posts:
#         writer = post['writer']
#         user_profile = UserProfile.objects.filter(user=writer, user__is_client=True).first()
#         if user_profile:
#             latest_post = Testimonials.objects.filter(writer=writer, date_posted=post['latest']).first()
#             testimonials.append(latest_post)

#     number_of_testimonials = len(testimonials)
#     selected_class = count_to_class.get(number_of_testimonials, "default-class")

#     return testimonials, selected_class



def layout(request):
    # testimonials, selected_class = get_testimonials()

    services = Service.objects.filter(is_active=True).order_by('serial')
    context = {
        "services": services,
        "posts": {},
        "title": "layout",
        "selected_class": None,
    }
    return render(request, "main/home_templates/newlayout.html", context)

def fetch_model_table_names(request):
    app_name = request.GET.get('category', None)  # Replace with the actual app name
    app_models = apps.get_app_config(app_name).get_models()
    # Get the actual model table names based on the application
    # table_names = [model.__name__ for model in app_models]
    table_names = [{'value': model.__name__, 'display_text': model._meta.verbose_name.replace('_', ' ').capitalize()} for model in app_models]
    return JsonResponse({'model_table_names': table_names})


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

def display_service(request, *args, **kwargs):
    path_list, sub_title, pre_sub_title = path_values(request)
    try:
        service_shown = Service.objects.filter(is_active=True)
    except Service.DoesNotExist:
        return redirect('main:display_service')

    (service_category_slug, service_category_title, service_description,service_sub_titles, service_id) = service_instances(service_shown, sub_title)
    service_categories = ServiceCategory.objects.filter(is_active=True,service=service_id)
    try:
        asset = Assets.objects.get(name=service_category_title)
        asset_image_url = asset.service_image.url
    except Assets.DoesNotExist:
        asset_image_url = None
    # investment_content = InvestmentContent.objects.first()

    # description = investment_content.description if investment_content else "No description available"

    # testimonials, selected_class = get_testimonials()

    # Calculate the number of students and other users
    students_count = CustomerUser.objects.filter(category=CategoryChoices.Student).count()
    teachers_count = 8  # Set the desired count
    teachers = CustomerUser.objects.filter(category=CategoryChoices.Coda_Staff_Member)[:teachers_count].count()
    # Calculate the total number of courses
    title1 = "IT-Training"
    title2 = "Interview"

    total_courses_count =10
  
    category_name = 'IT-Project Management'  
    projects = None
    #Description for IT Integrated Solutions & Consultancy 
    # descriptions = InvestmentContent.objects.filter(title='IT Integrated Solutions & Consultancy')
    context = {
        'service_categories': service_categories,
        "title": service_category_title,
        "service_desc": service_description,
        # 'content': description,
        "General":General,
        "projects": projects,
        "Automation":Automation,
        "sub_titles": service_sub_titles,
        "posts": None,
        "selected_class": None,
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
    (category_slug,category_name,category_id)=service_plan_instances(service_categories,sub_title)
    plans =None

    context = {}
    context = {
        "SITEURL": settings.SITEURL,
        "title": category_name,
        "packages": packages,
        "category_slug": category_slug,
        "courses": courses,
        "services_plans": plans
    }
    return render(request, "main/services/service_plan.html", context)


# =====================README VIEWS=======================================
class UseCaseCreateView(LoginRequiredMixin, CreateView):
    model = Readme
    success_url = "/usecases/"
    fields = "__all__"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


def display_usecases(request, *args, **kwargs):
    try:
        usecases = Readme.objects.all()
    except Readme.DoesNotExist:
        return redirect('main:layout')
    
    context = {
        "title": "USE CASE",
        "table_contents": table_contents,
        "usecases": usecases,
    }
    return render(request, "main/snippets_templates/readme_usecases.html", context)
    
#========================Internal Team & Clients==============================

def it(request):
    return render(request, "main/departments/it.html", {"title": "IT"})

def finance(request):
    return render(request, "main/departments/finance_landing_page.html", {"title": "Finance"})

def hr(request):
    return render(request, "management/companyagenda.html", {"title": "HR"})

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

def home_view(request):
    return render(request, 'main/home_templates/home.html')    




def location_list(request):
    locations = Location.objects.all()
    return render(request, 'main/snippets_templates/table/location_list.html', {'locations': locations})


def location_create(request):
    if request.method == 'POST':
        form = locationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("accounts:account-location_list")
    else:
        form = locationForm()
    return render(request, "main/snippets_templates/table/location_create.html", {'form': form})


def location_update(request, pk):
    locations = get_object_or_404(Location, pk=pk)  
    if request.method == 'POST':
        form = locationForm(request.POST, instance=locations)
        if form.is_valid():
            form.save()
            return redirect("accounts:account-location_list")
    else:
        form = locationForm()  
    return render(request, "main/snippets_templates/table/location_edit.html", {'form': form})


def servicecategory_list(request):
    categories = ServiceCategory.objects.all()
    return render(request, 'main/snippets_templates/table/sevices.html', {'categories': categories})




def servicecategory_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = bool(request.POST.get('is_active'))
        is_featured = bool(request.POST.get('is_featured'))

        ServiceCategory.objects.create(
            name=name,
            description=description,
            is_active=is_active,
            is_featured=is_featured,
        )
        return redirect('main:servicecategory_list')
    return render(request, 'main/snippets_templates/table/services_create.html')



def servicecategory_update(request, pk):
    category = get_object_or_404(ServiceCategory, pk=pk)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        category.is_active = bool(request.POST.get('is_active'))
        category.is_featured = bool(request.POST.get('is_featured'))
        category.save()
        return redirect(':mainservicecategory_list')
    return render(request, 'main/snippets_templates/table/services_update.html', {'category': category}) 



def servicecategory_delete(request, pk):
    category = get_object_or_404(ServiceCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        return redirect('main:servicecategory_list')
    return render(request, 'main/snippets_templates/table/services_delete.html', {'category': category})


def servicecategory_detail(request, pk):
    category = get_object_or_404(ServiceCategory, pk=pk)
    return render(request, 'main/snippets_templates/table/services_detail.html', {'category': category})
   



def testimonials_list(request):
    testimonials = Testimonials.objects.order_by('-date_posted')
    return render(request, 'main/snippets_templates/table/testmonial.html', {'testimonials': testimonials})


def testimonial_create(request):
    if request.method == 'POST':
        form = TestimonialForm(request.POST)
        if form.is_valid():
            testimonial = form.save(commit=False)
            testimonial.writer = request.user.id  # save user ID
            testimonial.save()
            return redirect('testimonials_list')
    else:
        form = TestimonialForm()
    return render(request, 'main/snippets_templates/table/testmonial_create.html', {'form': form, 'title': 'Add Testimonial'})


def testimonial_update(request, pk):
    testimonial = get_object_or_404(Testimonials, pk=pk)
    if request.method == 'POST':
        form = TestimonialForm(request.POST, instance=testimonial)
        if form.is_valid():
            form.save()
            return redirect('testimonials_list')
    else:
        form = TestimonialForm(instance=testimonial)
    return render(request, 'main/snippets_templates/table/testmonial_update.html', {'form': form, 'title': 'Edit Testimonial'})