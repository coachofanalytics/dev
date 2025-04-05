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
from .models import Assets,Description, Page,ContactMessage
from accounts.models import User,UserProfile
from .utils import Meetings,image_view,path_values
from main.forms import ContactForm,FeedbackForm,GalleryImageForm, ContactMessage_form
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
    error_code = request.META.get('HTTP_X_ERROR', 500)  # This can be a custom header
    contact = 'Please contact admin at info@codanalytics.net'
    title = ['Bad Request', 'Permission Denied', 'Page Not Found', 'System Issue']

    context_dict = {
        400: {'title': title[0], 'error_message': 'Kindly check your URL/link provided', 'contact_message': contact},
        403: {'title': title[1], 'error_message': 'You are not allowed to visit this page', 'contact_message': contact},
        404: {'title': title[2], 'error_message': 'Page not found', 'contact_message': contact},
        500: {'title': title[3], 'error_message': 'There is an issue on our end. Please try again later.', 'contact_message': contact},
    }

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


def hendler500(request):
    return render(request, "main/errors/500.html")
    
def test(request):
    return render(request, "main/test.html", {"title": "test"})

def checkout(request):
    return render(request, "main/checkout.html", {"title": "checkout"})

from django.shortcuts import get_object_or_404


def layout(request):
    page_instance = Page.objects.get(page_name='Home')
    description = Description.objects.filter(page = page_instance)
    
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
    context={
            # "posts":posts,
            "form": form,
            'description': description
        }
    return render(request, "main/home_templates/home.html",context)

    
def about(request):
    # Get active employee team members
    team_members = UserProfile.objects.filter(user__is_employee=True, user__is_active=True, user__is_staff=True)
    
    # Set start and end dates
    start_date_str = "01/20/2023"
    start_date = datetime.strptime(start_date_str, '%m/%d/%Y')
    end_date = start_date + relativedelta(months=3)
    
    # Filter active employees and get their image URLs
    active_employees = [member for member in team_members if member.img_category == 'employee']
    img_urls = [member.img_url for member in active_employees]
    
    # Set context variables
    context = {
        "start_date": start_date,
        "end_date": end_date,
        "title_team": "team",
        "active_employees": active_employees,
        "title_about": "about",
        "img_urls": img_urls,
        "title_letter": "letter",
    }
    
    # Map page names to templates
    templates = {
        'team': 'main/team.html',
        'letter': 'main/doc_templates/letter.html',
        'appointment_letter': 'main/doc_templates/appointment_letter.html',
        'about': 'main/about.html',
    }
    
    # Render the appropriate template based on the page name
    page_name = path_values(request)[-1]
    template = templates.get(page_name, 'main/about.html')
    return render(request, template, context)


class UserCreateView(LoginRequiredMixin, CreateView):
    model = UserProfile
    success_url = "/team/"
    fields = "__all__"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class UserProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = UserProfile
    # fields ="__all__"
    fields=['position','description','image','image2','is_active','laptop_status']
    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    # def get_success_url(self):
    #     return reverse("management:companyagenda")

    def test_func(self):
        # profile = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user:
            return True
        return False
    
@login_required
def contact(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST, request.FILES)
        message=f'Thank You, we will get back to you within 48 hours.'
        context={
            "message":message,
            # "link":SITEURL+'/management/companyagenda'
        }
        if form.is_valid():
            # form.save()
            instance=form.save(commit=False)
            print("USER========>",request.user)
            instance.user=request.user
            instance.save()
            return render(request, "main/messages/message.html",context)
    else:
        form = FeedbackForm()
        print("USER========>",request.user)
    return render(request, "main/contact/contact_form.html", {"form": form})


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

from django.shortcuts import get_object_or_404
from .models import Page

def home_view(request):
    page = get_object_or_404(Page, slug='home')
    return render(request, 'home.html', {'page': page})


def Gallery_list(request):
    info=GalleryImage.objects.all()
    print("info===============================",info)
    return render(request,"main/snippets_templates/list.html",{"GalleryImage":info})



from django.http import HttpResponseRedirect
from django.urls import reverse

def gallery_create(request):
    if request.method == "POST":
        form = GalleryImageForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to a new URL after POST
            return HttpResponseRedirect(reverse('gallery_list'))  # Assuming you have a URL named 'gallery_list'
    else:
        form = GalleryImageForm()  # Provide an empty form for GET requests

    return render(request, 'main/snippets_templates/table/create.html', {'form': form})





def Gallery_update(request, pk):
    gallery_instance = get_object_or_404(GalleryImage, pk=pk)
    if request.method == 'POST':
        form = GalleryImageForm(request.POST, request.FILES, instance=gallery_instance)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('Gallery_list'))
    else:
        form = GalleryImageForm(instance=gallery_instance)
    
    return render(request, 'main/snippets_templates/table/Gallery.html', {'form': form})


def gallery_delete(request, pk):
    gallery_instance = get_object_or_404(GalleryImage, pk=pk)
    if request.method == 'POST':
        gallery_instance.delete()
        return redirect('main:gallery_list')
    
    return render(request, 'main/snippets_templates/table/delete.html', {'object': gallery_instance})



def gallery_detail(request, pk):
    gallery_instance = get_object_or_404(GalleryImage, pk=pk)
    return render(request, 'main/snippets_templates/table/detail.html', {'gallery_instance': gallery_instance})










def contact_message_list(request):
    info=ContactMessage.objects.all()
    print("info===============================",info)
    return render(request,"main/snippets_templates/table/Contactmessage_list.html",{"info":info})


def contact_message_create(request):
    if request.method == "POST":
        form = ContactMessage_form(request.POST)
        if form.is_valid():
            form.save()
            # Redirect to a new URL after POST
            return HttpResponseRedirect(reverse('main:contact_message_list')) 
    else:
        form = ContactMessage_form()

    return render(request, 'main/snippets_templates/table/Contact_message_create.html', {'form': form})



def Contact_Message_update(request, pk):
    ContactMessage_instance = get_object_or_404(ContactMessage, pk=pk)
    if request.method == 'POST':
        form = ContactMessage_form(request.POST, request.FILES, instance=ContactMessage_instance)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('main:contact_message_list'))
    else:
        form = ContactMessage_form(instance=ContactMessage_instance)
    
    return render(request, 'main/snippets_templates/table/Contact_Message_update.html', {'form': form})



def ContactMessage_delete(request, pk):
    ContactMessage_instance = get_object_or_404(ContactMessage, pk=pk)
    if request.method == 'POST':
        ContactMessage_instance.delete()
        return redirect('main:contact_message_list')
    
    return render(request, 'main/snippets_templates/table/ContactMessage_delete.html', {'object': ContactMessage_instance})


from django.shortcuts import render, get_object_or_404



def ContactMessage_detail(request, pk):
    contact_message = get_object_or_404(ContactMessage, pk=pk)
    return render(request, 'main/snippets_templates/table/ContactMessage_detail.html', {'contact_message': contact_message})
