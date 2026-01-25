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

from .forms import ServiceCategoryForm


from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from .models import ServiceCategory


from django.db.models import Sum
from .models import Service,Assets,Readme
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

from .forms import *
from django.http import JsonResponse
from django.apps import apps
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
from .forms import ServiceCategoryForm


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
    return render(request, "main/home_templates/layout.html", context)

def fetch_model_table_names(request):
    app_name = request.GET.get('category', None)  # Replace with the actual app name
    app_models = apps.get_app_config(app_name).get_models()
    # Get the actual model table names based on the application
    # table_names = [model.__name__ for model in app_models]
    table_names = [{'value': model.__name__, 'display_text': model._meta.verbose_name.replace('_', ' ').capitalize()} for model in app_models]
    return JsonResponse({'model_table_names': table_names})

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

from .models import Service, ServiceCategory
from .forms import ServiceCategoryForm


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
