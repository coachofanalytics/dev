from django.shortcuts import redirect, render
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    CreateView,
    UpdateView,
)
from .models import Assets,Description,Page,MembershipPlan, JobListing, Faq
from accounts.models import CustomerUser
from .utils import image_view,path_values
from main.forms import ContactForm,registrationform, JoblistingForm
from django.contrib.auth import get_user_model


User=get_user_model()


def error400(request):
    return render(request, "main/errors/400.html", {"title": "400Error"})

def error403(request):
    return render(request, "main/errors/403.html", {"title": "403Error"})

def error404(request):
    return render(request, "main/errors/404.html", {"title": "404Error"})
    
def error500(request):
    return render(request, "main/errors/500.html", {"title": "500Error"})

#Other Error pages or no results error

def template_errors(request):
    url = request.path
    contact = 'Please contact admin at info@codanalytics.net'
    title = ['Bad Request', 'Permission Denied', 'Page Not Found', 'System Issue']

    # Map each error code to its corresponding context
    context_dict = {
        400: {'title': title[0], 'error_message': 'Kindly check your URL/link provided', 'contact_message': contact},
        403: {'title': title[1], 'error_message': 'You are not allowed to visit this page', 'contact_message': contact},
        404: {'title': title[2], 'error_message': 'Page not found', 'contact_message': contact},
        500: {'title': title[3], 'error_message': 'There is an issue on our end. Please try again later.', 'contact_message': contact},
    }

    # Get the context based on the error code, or use a default context
    error_code = getattr(url, 'response', None)
    context = context_dict.get(error_code, {'title': 'Error', 'error_message': 'An error has occurred', 'contact_message': contact})

    print(error_code)
    return render(request, 'main/errors/template_error.html', context)


def general_errors(request):
    # return render(request, "main/errors/noresult.html")
    context={'message':'message'}
    return render(request,'main/errors/generalerrors.html',context)

#  ===================================================================================   
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
    
def test(request):
    return render(request, "main/test.html", {"title": "test"})

def checkout(request):
    return render(request, "main/checkout.html", {"title": "checkout"})

from django.shortcuts import get_object_or_404

def layout(request):
    try:
        page_instance = Page.objects.first()  # Assuming you're fetching the first Page instance
    except Page.DoesNotExist:
        page_instance = None  # Fallback in case no page is found

    return render(request, 'main/home_templates/home.html', {'page_instance': page_instance})





# def layout(request):
#     try:
#         page_instance = Page.objects.first()  # Assuming you're fetching the first Page instance
#     except Page.DoesNotExist:
#         page_instance = None  # Fallback in case no page is found

#     return render(request, 'main/home_templates/home.html', {'page_instance': page_instance})







def History(request):
    page_instance = Page.objects.get(page_name='About')
    description = Description.objects.filter(page = page_instance)
    context={
            
            'description': description,
            
        }
    return render(request, "main/about_templates/history.html",context)

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
    # print(images)
    return render(request, "main/snippets_templates/static/images.html", {"title": "pay", "images": images})

class ImageUpdateView(LoginRequiredMixin,UpdateView):
    model=Assets
    fields = ['category','name','image_url','description']
     
    def form_valid(self,form):
        form.instance.username=self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('main:images') 
    

  


from django.shortcuts import render

def home(request):
    return render(request, 'main/home_templates/home.html')



from django.views.generic import TemplateView

class AboutView(TemplateView):
    template_name = 'main/snippets_templates/table/abour.html'



from django.shortcuts import render
from .models import membershirp_registration

def registration_list(request):
    # Fetch all membership registrations
    info = membershirp_registration.objects.all()
    print('info========================', info)  # Debugging statement (remove in production)
    
    return render(request, 'main/snippets_templates/table/regestration.html', {'info': info})







def registration_create(request):
    if request.method == 'POST':
        form = registrationform(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main:registration_list')
    else:
        form = registrationform()
    return render(request, 'main/snippets_templates/table/regestration_create.html', {'form': form})






from .models import membershirp_registration
from .forms import registrationform,MembershipPlanform

def registration_update(request, pk):
    membershirps_registration = get_object_or_404(membershirp_registration, pk=pk)
    if request.method == 'POST':
        form = registrationform(request.POST, instance=membershirps_registration)
        if form.is_valid():
            form.save()
            return redirect('main:registration_list')  
    else:
        form = registrationform(instance=membershirps_registration)
    return render(request, 'main/snippets_templates/table/registrations_update.html', {'form': form})













from .models import membershirp_registration

def membershirp_registration_delete(request, pk):
    volunteer = get_object_or_404(membershirp_registration, pk=pk)
    if request.method == 'POST':
        volunteer.delete()
        return redirect('main:registration_list')  # Redirect to the volunteers list page
    return render(request, 'main/snippets_templates/table/regritration_delete.html', {'membershirp_registrations': membershirp_registration})






def MembershipPlan_list(request):
    # Fetch all membershipplan
    info = MembershipPlan.objects.all()
    print('info========================', info)  # Debugging statement (remove in production)
    
    return render(request, 'main/snippets_templates/table/plan.html', {'info': info})






def membershipplan_create(request):
    if request.method == 'POST':
        form = MembershipPlanform(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main:MembershipPlan_list')
    else:
        form = MembershipPlanform()
    return render(request, 'main/snippets_templates/table/plan_creat.html', {'form': form})    





from .forms import MembershipPlanform  # Ensure the correct import

def membershipplan_update(request, pk):
    info = get_object_or_404(MembershipPlan, pk=pk)
    if request.method == 'POST':
        form = MembershipPlanform(request.POST, instance=info)  # Correct form name
        if form.is_valid():
            form.save()
            return redirect('main:MembershipPlan_list')  # Ensure this URL name exists
    else:
        form = MembershipPlanform(instance=info)
    return render(request, 'main/snippets_templates/table/plan_update.html', {'form': form})



def delete_membershipplan(request, pk):
    info = get_object_or_404(MembershipPlan, pk=pk)
    if request.method == 'POST':
        info.delete()
        return redirect('main:MembershipPlan_list')  # Ensure this URL exists
    return render(request, 'mainsnippets_templates/table/plan_delet.html', {'info': info})





from django.shortcuts import get_object_or_404, render

from django.shortcuts import get_object_or_404, render
from .models import MembershipPlan

def membershipplan_detail(request, pk):
    info = get_object_or_404(MembershipPlan, pk=pk)
    return render(request, 'main/snippets_templates/table/plan_detal .html', {'info': info})



def joblist_list(request):
    # Fetch all membershipplan
    jobs = JobListing.objects.all()
    
    return render(request, 'main/snippets_templates/table/joblist_list.html', {'jobs': jobs})



def joblisting_create(request):
    if request.method == 'POST':
        form = JoblistingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main:jobs_list')
    else:
        form = JoblistingForm()
    return render(request, 'main/snippets_templates/table/joblist_create.html', {'form': form})   



def joblisting_update(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    if request.method == 'POST':
        form = JoblistingForm(request.POST, instance=job)  # Correct form name
        if form.is_valid():
            form.save()
            return redirect('main:jobs_list')  # Ensure this URL name exists
    else:
        form = JoblistingForm(instance=job)
    return render(request, 'main/snippets_templates/table/joblist_update.html', {'form': form})



def joblist_detail(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    return render(request, 'main/snippets_templates/table/joblist_detail .html', {'job': job})



def joblist_delete(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    if request.method == 'POST':
        job.delete()
        return redirect('main:jobs_list')  # Redirect to the jobs list page
    return render(request, 'main/snippets_templates/table/joblist_delete.html', {'job': job})


def faq_list(request):
    faqs = Faq.objects.all()
    print (faqs)
    template_name = 'main/faq.html'
    context = {
        'faqs': faqs 
    }

    return render(request, template_name, context)











