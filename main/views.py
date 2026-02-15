from django.http import JsonResponse
from django.shortcuts import redirect, render
from .models import Assets,Readme,Location
from .utils import *
from .forms import LocationForm
from django.shortcuts import render, get_object_or_404, redirect

from coda_project import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
        CreateView,)

from .forms import *
from django.apps import apps
from django.contrib.auth import get_user_model
from django.shortcuts import render
from .models import Testimonials
from django.shortcuts import render, redirect
from .forms import TestimonialForm


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

#     services = Service.objects.filter(is_active=True).order_by('serial')
#     context = {
#         "services": services,
#         "posts": {},
#         "title": "layout",
#         "selected_class": None,
#     }
#     return render(request, "main/home_templates/newlayout.html", context)

# def fetch_model_table_names(request):
#     app_name = request.GET.get('category', None)  # Replace with the actual app name
#     app_models = apps.get_app_config(app_name).get_models()
#     # Get the actual model table names based on the application
#     # table_names = [model.__name__ for model in app_models]
#     table_names = [{'value': model.__name__, 'display_text': model._meta.verbose_name.replace('_', ' ').capitalize()} for model in app_models]
#     return JsonResponse({'model_table_names': table_names})


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






def testimonials_list(request):
    testimonials = Testimonials.objects.all().order_by("-date_posted")
    return render(request, "main/testmonial_list.html",)



def testimonial_create(request):
    if request.method == "POST":
        form = TestimonialForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("main:testimonials_list")
    else:
        form = TestimonialForm()

    return render(request, "main/testmonial_create.html", {
        "form": form
    })

