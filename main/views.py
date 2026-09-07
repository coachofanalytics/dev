# <<<<<<< HEAD
from django.shortcuts import render


def handler400(request, exception=None):
    return render(request, "errors/400.html", status=400)


def handler403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def handler500(request):
    return render(request, "errors/500.html", status=500)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# from .forms import ServiceCategoryForm


from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from .models import ServiceCategory


from django.db.models import Sum
from .models import Assets,Readme
# =======
from django.http import JsonResponse
from django.shortcuts import redirect, render
from .models import Assets,Readme,Location,ClientAvailability,Search


# >>>>>>> e79fe45578418c384fbb84ca7760d91bef020a33
from .utils import *
from .forms import LocationForm
from django.shortcuts import render, get_object_or_404, redirect
# from main.models import Testimonials
# Testimonials.objects.all()
# Testimonials.objects.count()
from django.shortcuts import render, redirect
from main.forms import PlanForm
from datetime import datetime

from coda_project import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
        CreateView,)

from django.shortcuts import render

def layout(request):
    return render(request, "layout.html")  # or any template you have

from .forms import *
from django.apps import apps
# <<<<<<< HEAD
from langchain_community.llms import OpenAI
from langchain_community.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from django.db.models import F, FloatField, Case, When, Value, Subquery, OuterRef
from django.contrib.auth import get_user_model
from django.db.models.functions import Coalesce
from django.views.generic.edit import DeleteView

from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from .models import ServiceCategory
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
# from .forms import ServiceCategoryForm
# =======
from django.contrib.auth import get_user_model
from django.shortcuts import render
# from .models import Testimonials
from django.shortcuts import render, redirect
# from .forms import TestimonialForm
from django.urls import reverse_lazy
from django.views.generic import UpdateView
# from .models import Testimonials
# >>>>>>> e79fe45578418c384fbb84ca7760d91bef020a33


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



# def layout(request):
#     # testimonials, selected_class = get_testimonials()

# <<<<<<< HEAD
    services = Service.objects.filter(is_active=True).order_by('serial')
    context = {
        "services": services,
        "posts": {},
        "title": "layout",
        "selected_class": None,
    }
    return render(request, "main/home_templates/layout.html", context)
# =======
#     services = Service.objects.filter(is_active=True).order_by('serial')
#     context = {
#         "services": services,
#         "posts": {},
#         "title": "layout",
#         "selected_class": None,
#     }
#     return render(request, "main/home_templates/newlayout.html", context)
# >>>>>>> e79fe45578418c384fbb84ca7760d91bef020a33

# def fetch_model_table_names(request):
#     app_name = request.GET.get('category', None)  # Replace with the actual app name
#     app_models = apps.get_app_config(app_name).get_models()
#     # Get the actual model table names based on the application
#     # table_names = [model.__name__ for model in app_models]
#     table_names = [{'value': model.__name__, 'display_text': model._meta.verbose_name.replace('_', ' ').capitalize()} for model in app_models]
#     return JsonResponse({'model_table_names': table_names})

# <<<<<<< HEAD
# =======

# # =====================SERVICES  VIEWS=======================================
# class ServiceCreateView(LoginRequiredMixin, CreateView):
#     model = Service
#     success_url = "/services/"
#     fields = "__all__"

#     def form_valid(self, form):
#         form.instance.user = self.request.user
#         return super().form_valid(form)

# def services(request):
#     services = Service.objects.filter(is_active=True).order_by('serial')
#     context = {
#         "SITEURL" :settings.SITEURL,
#         "services": services
#     }
#     return render(request, "main/services/show_service.html", context)

# def display_service(request, *args, **kwargs):
#     path_list, sub_title, pre_sub_title = path_values(request)
#     try:
#         service_shown = Service.objects.filter(is_active=True)
#     except Service.DoesNotExist:
#         return redirect('main:display_service')

#     (service_category_slug, service_category_title, service_description,service_sub_titles, service_id) = service_instances(service_shown, sub_title)
#     service_categories = ServiceCategory.objects.filter(is_active=True,service=service_id)
#     try:
#         asset = Assets.objects.get(name=service_category_title)
#         asset_image_url = asset.service_image.url
#     except Assets.DoesNotExist:
#         asset_image_url = None
    # investment_content = InvestmentContent.objects.first()

    # description = investment_content.description if investment_content else "No description available"

    # testimonials, selected_class = get_testimonials()

    # Calculate the number of students and other users
#     students_count = CustomerUser.objects.filter(category=CategoryChoices.Student).count()
#     teachers_count = 8  # Set the desired count
#     teachers = CustomerUser.objects.filter(category=CategoryChoices.Coda_Staff_Member)[:teachers_count].count()
#     # Calculate the total number of courses
#     title1 = "IT-Training"
#     title2 = "Interview"

#     total_courses_count =10
  
#     category_name = 'IT-Project Management'  
#     projects = None
#     #Description for IT Integrated Solutions & Consultancy 
#     # descriptions = InvestmentContent.objects.filter(title='IT Integrated Solutions & Consultancy')
#     context = {
#         'service_categories': service_categories,
#         "title": service_category_title,
#         "service_desc": service_description,
#         # 'content': description,
#         "General":General,
#         "projects": projects,
#         "Automation":Automation,
#         "sub_titles": service_sub_titles,
#         "posts": None,
#         "selected_class": None,
#         "slug": service_category_slug,
#         "asset_image_url": asset_image_url,
#         "students_count": students_count,
#         "teachers_count": teachers,
#         "total_courses_count": total_courses_count,
#     }
#     return render(request, "main/services/show_services.html", context)


# def service_plans(request, *args, **kwargs):
#     path_list, sub_title, pre_sub_title = path_values(request)
#     try:
#         if pre_sub_title == 'bigdata':
#             service_shown = ServiceCategory.objects.get(slug=sub_title).service

#         elif pre_sub_title:
#             try:
#                 service_shown = Service.objects.get(slug=pre_sub_title)
#                 # print("service_shown====>",service_shown)
#             except Service.DoesNotExist:
#     #             service_shown = ServiceCategory.objects.get(slug=sub_title).service

    #     elif sub_title.lower() in ["job-support","interview","full-course"]:
    #         # service_shown = Data Analysis
    #         service_shown = Service.objects.get(slug="data_analysis")
    #         # print("service_shown====>",service_shown)
    #     else:
    #         return redirect('main:layout')
        
    # except Service.DoesNotExist:
    #     return redirect('main:display_service', slug ='data_analysis')
    # except Exception:
    #     return redirect('main:layout')
    # service_categories = ServiceCategory.objects.filter(service=service_shown.id)
    # (category_slug,category_name,category_id)=service_plan_instances(service_categories,sub_title)
    # plans =None

    # context = {}
    # context = {
    #     "SITEURL": settings.SITEURL,
    #     "title": category_name,
    #     "packages": packages,
    #     "category_slug": category_slug,
    #     "courses": courses,
    #     "services_plans": plans
    # }
    # return render(request, "main/services/service_plan.html", context)


# >>>>>>> e79fe45578418c384fbb84ca7760d91bef020a33
# =====================README VIEWS=======================================
# class UseCaseCreateView(LoginRequiredMixin, CreateView):
#     model = Readme
#     success_url = "/usecases/"
#     fields = "__all__"

#     def form_valid(self, form):
#         form.instance.user = self.request.user
#         return super().form_valid(form)


# def display_usecases(request, *args, **kwargs):
#     try:
#         usecases = Readme.objects.all()
#     except Readme.DoesNotExist:
#         return redirect('main:layout')
    
#     context = {
#         "title": "USE CASE",
#         "table_contents": table_contents,
#         "usecases": usecases,
#     }
#     return render(request, "main/snippets_templates/readme_usecases.html", context)
    
# #========================Internal Team & Clients==============================

# def it(request):
#     return render(request, "main/departments/it.html", {"title": "IT"})

# def finance(request):
#     return render(request, "main/departments/finance_landing_page.html", {"title": "Finance"})

# def hr(request):
#     return render(request, "management/companyagenda.html", {"title": "HR"})

# def error400(request):
#     return render(request, "main/errors/400.html", {"title": "400Error"})

# def error403(request):
#     return render(request, "main/errors/403.html", {"title": "403Error"})

# def error404(request):
#     return render(request, "main/errors/404.html", {"title": "404Error"})
    
# def error500(request):
#     return render(request, "main/errors/500.html", {"title": "500Error"})

# def general_errors(request):
#     # return render(request, "main/errors/noresult.html")
#     context={'message':'message'}
#     return render(request,'main/errors/generalerrors.html',context)


def location_list(request):
    locations = Location.objects.all()
    return render(request, "main/locations_list.html", {"locations": locations})



def location_create(request):
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("main:location_list")
    else:
        form = LocationForm()

    return render(request, "main/location_create.html", {"form": form})



def location_update(request, pk):
    location = get_object_or_404(Location, pk=pk)

    if request.method == "POST":
        form = LocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            return redirect("main:location_list")
    else:
        form = LocationForm(instance=location)

    return render(request,"main/location_update.html",{"form": form, "location": location}
    )

def location_detail(request, pk):
    location = get_object_or_404(Location, pk=pk)
    return render(request, "main/location_detail.html", {
        "location": location
    })


def location_delete(request, pk):
    location = get_object_or_404(Location, pk=pk)

    if request.method == "POST":
        location.delete()
        return redirect("main:location_list")

    return render(request,"main/location_delete.html",{"location": location}
    )


# main/views.py
from django.shortcuts import render
from .models import Pricing


def pricing_list(request):
    pricings = Pricing.objects.filter(
        is_active=True
    ).order_by("serial")

    context = {
        "pricings": pricings
    }
    return render(request, "main/pricing_list.html", context)





# def testimonials_list(request):
#     testimonials = Testimonials.objects.all()
#     return render(request, 'main/testimonials_list.html', {
#         'testimonials': testimonials
#     })



# def testimonial_create(request):
#     if request.method == "POST":
#         form = TestimonialForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect("main:testimonials_list")
#     else:
#         form = TestimonialForm()

#     return render(request, "main/testmonial_create.html", {
#         "form": form
#     })




# from django.shortcuts import render, get_object_or_404, redirect
# from .models import Testimonials
# def testimonial_update(request, pk):
#     testimonial = get_object_or_404(Testimonials, pk=pk)

#     if request.method == "POST":
#         title = request.POST.get('title')
#         content = request.POST.get('content')
#         writer = request.POST.get('writer')

#         if not title:
#             return render(request, 'main/testmonial_updat.html', {
#                 'testimonial': testimonial,
#                 'error': 'Title is required'
#             })

#         testimonial.title = title
#         testimonial.content = content
#         testimonial.writer = writer
#         testimonial.save()

#         return redirect('main:testimonials_list')

#     return render(request, 'main/testmonial_updat.html', {'testimonial': testimonial})


# main/views/plan_views.py

from django.shortcuts import render
from main.models import Plan


def plan_list_view(request):
    plans = Plan.objects.all().order_by("-created_at")    
    search = request.GET.get("q")
    if search:
        plans = plans.filter(task__icontains=search)    
    active = request.GET.get("active")
    if active:
        plans = plans.filter(is_active=True)
    context = {
        "plans": plans
    }

    return render(request, "main/plan_list.html", context)

    # main/views/plan_views.py


def create_plan(request):
    if request.method == "POST":
        form = PlanForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("main:plan_list")  # redirect to list page
    else:
        form = PlanForm()

    return render(request, "main/plan_create.html", {"form": form})






def plan_update(request, pk):
    plan = get_object_or_404(Plan, pk=pk)

    if request.method == "POST":
        form = PlanForm(request.POST, request.FILES, instance=plan)
        if form.is_valid():
            form.save()
            return redirect('main:plan_list')  # ✅ FIXED
    else:
        form = PlanForm(instance=plan)

    return render(request, "main/plan_update.html", {"form": form})

    from django.shortcuts import redirect, get_object_or_404




def plan_delete(request, pk):
    plan = get_object_or_404(Plan, pk=pk)

    if request.method == "POST":
        plan.delete()
        return redirect("main:plan_list")

    return render(request, "main/plan_delete.html", {"plan": plan})



def clientavailability_list(request):
    availabilities = ClientAvailability.objects.all()

    today = datetime.today().strftime("%A")
    today_slots = ClientAvailability.objects.filter(day=today).count()
    active_days = ClientAvailability.objects.values("day").distinct().count()

    context = {
        "availabilities": availabilities,
        "today_slots": today_slots,
        "active_days": active_days,
    }
    return render(request, "main/clientavailability_list.html", context)


def clientavailability_create(request):
    if request.method == "POST":
        form = ClientAvailabilityForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("main:clientavailability_list")
    else:
        form = ClientAvailabilityForm()
    return render(request, "main/clientvailability_create.html", {"form": form})


def clientavailability_update(request, pk):
    availability = get_object_or_404(ClientAvailability, pk=pk)
    if request.method == "POST":
        form = ClientAvailabilityForm(request.POST, instance=availability)
        if form.is_valid():
            form.save()
            return redirect("main:clientavailability_list")
    else:
        form = ClientAvailabilityForm(instance=availability)
    return render(request, "main/clientavailability_update.html", {"form": form})


def clientavailability_detail(request, pk):
    availability = get_object_or_404(ClientAvailability, pk=pk)
    return render(request, "main/clientavailability_detail.html", {"availability": availability})
  


def clientavailability_delete(request, pk):
    availability = get_object_or_404(ClientAvailability, pk=pk)
    if request.method == "POST":
        availability.delete()
        return redirect("main:clientavailability_list")
    return render(request, "main/clientavailability_delete.html", {"availability": availability})





def search_list(request):
    searches = Search.objects.all().order_by('-created_at')
    return render(request, 'main/search_list.html', {'searches': searches})

def search_create(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main:search_list')
    else:
        form = SearchForm()

    return render(request, 'main/search_create.html', {'form': form})

def search_update(request, pk):
    search = get_object_or_404(Search, pk=pk)

    if request.method == 'POST':
        form = SearchForm(request.POST, instance=search)
        if form.is_valid():
            form.save()
            return redirect('main:search_list')
    else:
        form = SearchForm(instance=search)

    return render(request, 'main/search_update.html', {'form': form})

def search_delete(request, pk):
    search = get_object_or_404(Search, pk=pk)

    if request.method == 'POST':
        search.delete()
        return redirect('main:search_list')

    return render(request, 'main/search_delete.html', {'search': search})

def search_detail(request, pk):
    search = get_object_or_404(Search, pk=pk)
    return render(request, 'main/search_detail.html', {'search': search})


def company_list(request):
    companies = Company.objects.all()
    return render(request, "main/company_list.html", {"companies": companies})

    
# <<<<<<< HEAD
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




from django.views.generic import ListView
from django.urls import reverse_lazy
from .models import Volunteer

# List View
class VolunteerListView(ListView):
    model = Volunteer
    template_name = 'volunteer/volunteer_list.html'
    context_object_name = 'volunteers'




from django.views.generic import DetailView
from django.urls import reverse_lazy
from .models import Volunteer

# Detail View
class VolunteerDetailView(DetailView):
    model = Volunteer
    template_name = 'volunteer/volunteer_detail.html'
    context_object_name = 'volunteer'



from django.views.generic import CreateView
from django.urls import reverse_lazy
from .models import Volunteer

# Create View
class VolunteerCreateView(CreateView):
    model = Volunteer
    fields = ['name', 'email', 'motivation']
    template_name = 'volunteer/volunteer_form.html'
    success_url = reverse_lazy('volunteer_list')

# from django.http import JsonResponse
# from django.views import View

# class ClientAvailability(View):
#     def get(self, request):
#         # logic here
#         return JsonResponse({'status': 'available'})
from django.shortcuts import render



from django.views.generic import ListView
from .models import WCAGStandardWebsite

class WCAGStandardWebsiteListView(ListView):
    model = WCAGStandardWebsite
    template_name = 'main/website_list.html'  # Custom template
    context_object_name = 'websites'  # Optional: changes the default 'object_list'
from django.shortcuts import render

def home(request):
    return render(request, 'main/home.html')
class WCAGStandardWebsiteListView(ListView):
    model = WCAGStandardWebsite
    template_name = 'main/website_list.html'  # Explicit path
    context_object_name = 'websites'

from django.views.generic.edit import CreateView
from .models import WCAGStandardWebsite
from django.urls import reverse_lazy

class WCAGStandardWebsiteCreateView(CreateView):
    model = WCAGStandardWebsite
    fields = ['company', 'app_name', 'page_name', 'website_url']  # exclude auto fields like created_at
    template_name = 'main/website_form.html'
    success_url = reverse_lazy('website-list')  # redirect after successful form submission
from django.views.generic.detail import DetailView

class WCAGStandardWebsiteDetailView(DetailView):
    model = WCAGStandardWebsite
    template_name = 'main/website_detail.html'
from django.views.generic.edit import DeleteView
from .models import WCAGStandardWebsite
from django.urls import reverse_lazy

class WCAGStandardWebsiteDeleteView(DeleteView):
    model = WCAGStandardWebsite  # ✅ Required line
    template_name = 'main/website_confirm_delete.html'
    success_url = reverse_lazy('website-list')

from django.views.generic.edit import CreateView
from .models import WCAGStandardWebsite
from django.urls import reverse_lazy

class WCAGStandardWebsiteCreateView(CreateView):
    model = WCAGStandardWebsite
    fields = ['company', 'app_name', 'page_name', 'website_url']
    template_name = 'main/website_form.html'
    success_url = reverse_lazy('website-list')
from django.views.generic.edit import UpdateView

class WCAGStandardWebsiteUpdateView(UpdateView):
    model = WCAGStandardWebsite
    fields = ['company', 'app_name', 'page_name', 'website_url']
    template_name = 'main/website_form.html'
    success_url = reverse_lazy('website-list')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# from .models import  ServiceCategory
# from .forms import ServiceCategoryForm


# ✅ 1) LIST ALL CATEGORIES
@login_required
def all_service_categories(request):
    categories = ServiceCategory.objects.all().order_by("-id")
    return render(request, "main/servicecategory_list.html", {"categories": categories})


# ✅ 2) LIST CATEGORIES UNDER ONE SERVICE
@login_required
def service_category_list(request, service_id):
    service = get_object_or_404(Service, id=service_id)

    categories = ServiceCategory.objects.filter(service=service).order_by("-id")

    context = {
        "service": service,
        "categories": categories,
    }
    return render(request, "main/servicecategory_list.html", context)


# ✅ 3) CREATE CATEGORY
@login_required
def servicecategory_create(request):
    if request.method == "POST":
        form = ServiceCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Service Category created successfully ✅")
            return redirect("main:servicecategory_create")  # ✅ back to create page
    else:
        form = ServiceCategoryForm() 
    return render(request, "main/servicecategory_createviews.html", {"form": form})


# ✅ 4) DETAIL CATEGORY
@login_required
def service_category_detail(request, pk):
    category = get_object_or_404(ServiceCategory, pk=pk)
    return render(request, "main/servicecategory_detail.html", {"category": category})


# ✅ 5) UPDATE CATEGORY
@login_required
def servicecategory_update(request, pk):
    category = get_object_or_404(ServiceCategory, pk=pk)

    if request.method == "POST":
        form = ServiceCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Service Category updated successfully ✅")
            return redirect("main:service_category_detail", pk=category.pk)
    else:
        form = ServiceCategoryForm(instance=category)

    return render(request, "main/templates\servicecategory_update.html", {"form": form, "category": category})


# ✅ 6) DELETE CATEGORY
@login_required
def servicecategory_delete(request, pk):
    category = get_object_or_404(ServiceCategory, pk=pk)

    if request.method == "POST":
        category.delete()
        messages.success(request, "Service Category deleted successfully ✅")
        return redirect("main:servicecategory_list")

    return render(request, "main/servicecategory_delete.html", {"category": category})
# =======
# >>>>>>> e79fe45578418c384fbb84ca7760d91bef020a33
