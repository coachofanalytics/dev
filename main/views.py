from django.shortcuts import redirect, render, get_object_or_404
from django.templatetags.static import static
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView,
    UpdateView,
    ListView,
    DetailView,
    DeleteView,
)
#<<<<<<< 25.10_DC48_UAT_UO
from .models import Assets,Description, News, Page, Service, SubService,Team, SafetyAlertSubscription, EmergencyHotline, StaffContact, InsurancePlan, AIRecommendationRule, ExpertInquiry, ConsularAssistancePage, NewsArticle, Category, Subscriber
#=======
from django.db.models import Q
#<<<<<<< HEAD
from .models import Scholarship, Donation_organisation, ContactMessage, Testimonial
#>>>>>>> origin/25.11_DC48K_UAT_FN
from accounts.models import CustomerUser
##=======
from .models import Assets,Description, News, Page, Service, SubService,Team, Donation_organization, MedicalResourceInquiry,Governance, NewsArticle, Category, Subscriber
from accounts.models import CustomerUser
from .utils import image_view,path_values
from .forms import ContactForm, DonorForm, MessageForm,ScholarshipSearchForm
##=======
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from main.forms import ContactForm, GovernanceForm, ArticleForm
#>>>>>>> origin/25.10_DC48K_UAT_FN
from django.contrib.auth import get_user_model
#<<<<<<< 25.10_DC48_UAT_UO
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.contrib.auth import get_user_model

# Models imports
from .models import (
    Assets, Description, News, Page, Service, SubService, Team,
    SafetyAlertSubscription, EmergencyHotline, StaffContact,
    InsurancePlan, AIRecommendationRule, ExpertInquiry,
    ConsularAssistancePage, NewsArticle, Category, Subscriber,
    Scholarship, ContactMessage, Testimonial, TrainingCourse,
    Donation_organization, MedicalResourceInquiry, Governance,
    Gallery, GetHelp, DonationOrganization, History, ContactUs,
    ServiceRequest, CommunityMessage
)
from accounts.models import CustomerUser
from .utils import image_view, path_values
from .forms import ContactForm, DonorForm, MessageForm, ScholarshipSearchForm, GovernanceForm, ArticleForm, ScholarshipForm,TrainingCourseForm, GetHelpForm, CommunityMessageForm
from mail.custom_email import send_email

import csv
import feedparser
import random


# Details Donation View
class DonationDetailView(DetailView):
    model = Donation_organization
    template_name = 'main/snippets_templates/table/donation_detail.html'
# Create Donation View
class DonationCreateView(CreateView):
    model = Donation_organization
    fields = ['donor_name', 'email', 'amount', 'message']
    template_name = 'main/snippets_templates/table/donation_create.html'
    success_url = reverse_lazy('main:donation')

User = get_user_model()


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



@csrf_exempt
def medical_resource_form(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        MedicalResourceInquiry.objects.create(name=name, email=email, message=message)
        # Redirect using the named URL so it works regardless of include path
        return redirect('main:healthcare_info')
    return render(request, 'main/data/medical_resource_form.html')


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
#<<<<<<< 25.10_DC48_UAT_UO
    page_instance, _ = Page.objects.get_or_create(page_name='Home')
    description = Description.objects.filter(page=page_instance)
#=======
#<<<<<<< HEAD
    # Define page_instance for the home page or desired page
    page_instance = Page.objects.filter(page_name='Home').first()
    description = Description.objects.filter(page=page_instance)
#=======
    # Ensure a Page instance exists for the Home page; if it doesn't, create a minimal one
    page_instance, _ = Page.objects.get_or_create(page_name='Home')
    description = Description.objects.filter(page = page_instance)
#>>>>>>> origin/25.10_DC48K_UAT_FN
#>>>>>>> 25.10_DC48_UAT_ND
    service = Service.objects.all()
    subservice = SubService.objects.all()
    news = News.objects.all().order_by('-published_date')[:3] 
    print(news)
   
    if request.method == "POST":
        form = ContactForm(request.POST, request.FILES)
        message='Thank You, we will get back to you within 48 hours.'
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
            'description': description,
            'service': service,
            'news':news,
            'subservice':subservice
        }
    return render(request, "main/home_templates/home.html",context)

def History(request):
    # Ensure About page exists to avoid crashes when the DB is empty
    page_instance, _ = Page.objects.get_or_create(page_name='About')
    description = Description.objects.filter(page = page_instance)
    context={

            'description': description,

        }
    return render(request, "main/about_templates/history.html",context)

# Lowercase alias for URL pattern compatibility
history = History

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
    
def crisis_page(request):
    hotlines = EmergencyHotline.objects.filter(is_active=True).order_by("sort_order", "id")
    return render(request, "main/crisis.html", {"hotlines": hotlines})




def team_list(request):
    teams = Team.objects.all()
    print('info=============',teams)
    return render(request, 'main/snippets_templates/table/team.html', {'info': teams})


@require_POST
@csrf_protect
def subscribe_alerts(request):
    email = request.POST.get('email', '').strip().lower()
    if not email:
        return JsonResponse({'success': False, 'message': 'Email is required.'}, status=400)

    subject = "DC48K Safety Alerts Subscription"
    html_message = """
      <p>Thank you for subscribing to DC48K Safety Alerts.</p>
      <p>You will receive updates about advisories and safety information.</p>
    """
    plain_message = strip_tags(html_message)
    # Check if already subscribed
    existing = SafetyAlertSubscription.objects.filter(email=email).first()
    if existing and existing.is_active:
        return JsonResponse({'success': True, 'message': 'You are already subscribed to Safety Alerts.'})

    if existing and not existing.is_active:
        existing.is_active = True
        existing.save()
    else:
        SafetyAlertSubscription.objects.create(
            email=email,
            user=request.user if request.user.is_authenticated else None,
            is_active=True,
        )

    # Attempt to send confirmation email
    try:
        send_mail(
            subject,
            plain_message,
            None,  # uses DEFAULT_FROM_EMAIL
            [email],
            html_message=html_message,
        )
        return JsonResponse({'success': True, 'message': 'Subscribed! A confirmation email has been sent.'})
    except Exception:
        # Gracefully succeed even if email backend is unavailable
        return JsonResponse({'success': True, 'message': 'Subscribed! (Email could not be sent right now.)'})




    

from .models import ContactUs

def service_list(request):
    services = Service.objects.all()  # Fetch all services and related subservices
    return render(request, 'main/services.html', {'services': services})

def consular_assistance(request):
    """
    Render the Consular Assistance landing page.
    """
    # Get or create a Page for consular assistance if you want to use the page/description pattern
    page_instance, _ = Page.objects.get_or_create(page_name='Consular Assistance')
    description = Description.objects.filter(page=page_instance)
    
    # Get active emergency hotlines for the emergency section
    hotlines = EmergencyHotline.objects.filter(is_active=True).order_by("sort_order", "id")
    
    context = {
        'description': description,
        'hotlines': hotlines,
        'title': 'Consular Assistance',
    }
    
    return render(request, 'main/consular_assistance.html', context)


def consular_information_updates(request):
    """
    Render the Consular Assistance → Information and Updates page.
    Follows the project's page/description pattern if available.
    """
    # Ensure a Page exists for this content (keeps behavior consistent with other pages)
    page_instance, _ = Page.objects.get_or_create(page_name='Consular - Information and Updates')
    description = Description.objects.filter(page=page_instance)

    context = {
        'description': description,
        'title': 'Information and Updates',
    }

    return render(request, 'main/consular/information_updates.html', context)


def consular_information_updates(request):
    """
    Render the Consular Assistance → Information and Updates page.
    Follows the project's page/description pattern if available.
    """
    # Ensure a Page exists for this content (keeps behavior consistent with other pages)
    page_instance, _ = Page.objects.get_or_create(page_name='Consular - Information and Updates')
    description = Description.objects.filter(page=page_instance)

    context = {
        'description': description,
        'title': 'Information and Updates',
    }

    return render(request, 'main/consular/information_updates.html', context)


def healthcare_info(request):
    """
    Render the Healthcare Information page (per spec this page presents financial services content).
    """
    hero = {
        'title': 'FINANCIAL SERVICES',
        'subtitle': 'Secure your wealth, invest smart, and manage your cross-border finances with confidence.',
        'cta_text': 'BOOK A FINANCIAL CONSULTATION',
        'hero_image': 'main/img/healthcare/doctor.svg',
    }

    mission = {
        'heading': 'Empowering Your Global Financial Future',
        'paragraph': 'International finance, investments, and repatriating funds can be complex. Our platform provides trusted tools and expert guidance to help you manage wealth across borders with confidence and compliance.'
    }

    sections = [
        {
            'number': '1',
            'title': 'Banking and Investment',
            'description': 'Access strategic advice on managing assets both locally and in Kenya. Connect with trusted partners for banking, real estate, and portfolio growth opportunities.',
            'bullets': [
                'Diaspora-focused mortgage and loan referrals',
                'Investment advisory for Kenyan stocks, bonds, and real estate',
                'Guidance on setting up international and Kenyan bank accounts',
                'Tax consultation and dual residency compliance',
            ],
            'cta_text': 'Explore Investment Portfolios',
            'image': 'main/img/healthcare/patient.svg',
            'align': 'left',
        },
        {
            'number': '2',
            'title': 'Remittances and Currency Exchange',
            'description': 'Ensure your money gets home quickly, safely, and cost-effectively. We compare and vet providers for the best rates and lowest fees.',
            'bullets': [
                'Real-time currency exchange comparisons',
                'Verified low-fee remittance partners',
                'Guidance on large fund transfers and declarations',
                'Alerts on economic and regulatory changes affecting transfers',
            ],
            'cta_text': 'View Remittance Calculator',
            'image': 'main/img/healthcare/doctor.svg',
            'align': 'right',
        }
    ]

    contact_cta = {
        'heading': 'URGENT MEDICAL ADVISORY',
        'description': "For life-threatening emergencies, always dial your host country's local emergency number first.",
        'cta_text': 'View Emergency Contacts by Country',
    }

    context = {
        'hero': hero,
        'mission': mission,
        'sections': sections,
        'contact_cta': contact_cta,
        # Static image URLs expected directly by the template
        'hero_image_url': static('main/img/healthcare/doctor.svg'),
        'services_image_url': static('main/img/healthcare/patient.svg'),
        'insurance_image_url': static('main/img/healthcare/doctor.svg'),
    }

    return render(request, 'main/data/healthcare_info.html', context)







def news_list(request):
    news_list = News.objects.all()
    print('info=============',news_list)
    return render(request, 'main/snippets_templates/table/news.html', {'news_list': news_list})


def news_detail(request, id):
    news = get_object_or_404(News, id=id)
    return render(request, 'main/snippets_templates/table/news_detail.html', {'news': news})


def contact_us_list(request):
    # Fetch the list of ContactUs objects
    contact_us_list = ContactUs.objects.all()

    # Debugging print statement (if necessary)
    print('info=============', contact_us_list)

    # Render the template with the context
    return render(request, 'main/snippets_templates/table/contact_us_list.html', {'contact_us_list': contact_us_list})


def contact_us(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        print (name,email,message)
        contact_message = ContactUs.objects.create(
            name = name,
            email = email,
            message = message
        )
        contact_message.save

        messages.success(request, "Thank You For Contacting Us We Will Get To You As Soon As Possible.")
        return redirect('main:layout')

    return render(request, "main/home_templates/home.html")


def gallery_list(request):
    images = Gallery.objects.all()
    return render(request, 'main/Gallery/gallery.html', {'images': images})


# Send a welcome email to a new user

def send_notification(request):
    url = 'email/welcome.html'
    new_user = CustomerUser.objects.all().order_by('-id').first()
    print(new_user)

    print(new_user)
    print(new_user.id, new_user.first_name, new_user.category, new_user.member_number, new_user.email)


    user_category = "Ordinary"
    first_name = new_user.first_name
    last_name = new_user.last_name
    user_id = new_user.member_number
    user_email = new_user.email
    subject = "Welcome To DC48K"

    print(new_user.id)

    context = {
        'user_category': user_category,
        'first_name': first_name,
        'last_name': last_name,
        'user_id': user_id,
        'subject': subject
    }
    try:
        send_email(
            category=user_category,
            to_email=[user_email],
            subject=subject,
            html_template=url,
            context=context
        )

        print("EMAIL SENT")
    except Exception as e:
        error_message = (
            f'Hi {request.user.first_name}, Your message to '
            f'{request.user.email} was unsuccessful. '
            f'Please try again or contact info@diasporacounty48.org. Thank You. '
            f'Error: {e}'
        )
        return render(request, 'main/messages/message.html', {"message": error_message})


def send_welcome_email(user_id=None):
    url = 'email/welcome.html'
    user_information = CustomerUser.objects.get(id=user_id)
    user_category = user_information.category
    first_name = user_information.first_name
    last_name = user_information.last_name
    user_id = user_information.id
    user_email = user_information.email
    subject = "Welcome To DC48K"


    context = {
        'user_category': user_category,
        'first_name': first_name,
        'last_name': last_name,
        'user_id': user_id
    }
    html_message = render_to_string(url, context)

    email = EmailMessage(
        subject=subject,
        body = html_message,
        from_email = settings.EMAIL_HOST_USER,
        to = [user_email]
    )
    email.content_subtype = 'html'
    email.send()
    print('Email Sent Successfully')



def gethelp_list(request):
    helps = GetHelp.objects.all()
    context = {
        'helps': helps
    }

    return render(request, 'main/gethelp_list.html', context)



def gethelp_update(request, pk):

    gethelp = get_object_or_404(GetHelp, pk=pk)


    if request.method == 'POST':
        form = GetHelpForm(request.POST, instance=gethelp)
        if form.is_valid():
            form.save()
            return redirect('main:gethelp')

    else:
        form = GetHelpForm(instance=gethelp)

    return render(request, 'main/gethelp_update.html', {'form':form})




def gethelp_create(request):
    if request.method == 'POST':
        form = GetHelpForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main:gethelp')

    else:
        form = GetHelpForm()

    return render(request, 'main/gethelp_create.html',{'form':form})



def gethelp_delete(request, pk):

    gethelp = get_object_or_404(GetHelp, pk=pk)

    if request.method == 'POST':

        gethelp.delete()
        return redirect('main:gethelp')

    return render(request, 'main/gethelp_confirm_delete.html', {'gethelp':gethelp})


def organization_list_view(request):
    organizations = DonationOrganization.objects.all()
    return render(request, 'main/snippets_templates/table/donation_list.html', {'organizations':organizations})


def ourhistory(request):
    history_years = History.objects.all()
    context = {
        "history_years": history_years
    }
    return render(request, "main/ourhistory.html", context)


from django.views.generic import TemplateView

class AboutView(TemplateView):
    template_name = 'main/snippets_templates/table/abour.html'


#<<<<<<< 25.10_DC48_UAT_UO
@require_POST
@csrf_protect
def activate_helpline(request):
    name = request.POST.get('name', '').strip() or None
    phone = request.POST.get('phone', '').strip() or None
    location = request.POST.get('location', '').strip() or None
    notes = request.POST.get('notes', '').strip() or None

    # Basic validation
    if not phone:
        return JsonResponse({'success': False, 'message': 'Phone number is required.'}, status=400)

    # Client IP
    ip = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip:
        ip = ip.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')

    # Log activation
    # EmergencyHelpActivation.objects.create(
    #     event_type="callback_requested",
    #     name=name,
    #     phone=phone,
    #     location=location,
    #     notes=notes,
    #     ip_address=ip,
    # )

    # Notify active staff via email
    recipients = list(
        StaffContact.objects.filter(is_active=True, notify_via_email=True)
        .exclude(email__isnull=True)
        .exclude(email__exact='')
        .values_list('email', flat=True)
    )

    subject = "Emergency Callback Requested"
    lines = [
        "An emergency callback has been requested.",
        f"Name: {name or '-'}",
        f"Phone: {phone or '-'}",
        f"Location: {location or '-'}",
        f"Notes: {notes or '-'}",
        f"IP: {ip or '-'}",
    ]
    message = "\n".join(lines)

    try:
        if recipients:
            send_mail(subject, message, None, recipients)
    except Exception:
        # Fail silently for the user; we still return success
        pass

    return JsonResponse({'success': True, 'message': 'Request received. Our team will call you shortly.'})


#=======
#<<<<<<< HEAD
def donor_list(request):
    donations = Donation_organisation.objects.all()  # Remove is_donor filter
    return render(request, 'main/donor.html', {'donations': donations})
def donor_details(request, pk):
    donation = get_object_or_404(Donation_organisation, pk=pk)
    return render(request, 'main/donor_details.html', {'donation': donation})
def add_donor(request):
    if request.method == "POST":
        form = DonorForm(request.POST, request.FILES)
        message='Thank You for your donation, we will get back to you within 48 hours.'
        context={
            "message":message,
            # "link":SITEURL+'/management/companyagenda'
        }
        if form.is_valid():
            instance=form.save(commit=False)
            instance.save()
            return render(request, "main/errors/generalerrors.html",context)
    else:
        form = DonorForm()
    context={
            "form": form,
        }
    return render(request, "main/add_donor.html",context)
def edit_donor(request, pk):
    donation = get_object_or_404(Donation_organisation, pk=pk)
    if request.method == "POST":
        form = DonorForm(request.POST, instance=donation)
        if form.is_valid():
            form.save()
            return redirect('main:donor_list')
    else:
        form = DonorForm(instance=donation)
    return render(request, 'main/edit_donor.html', {'form': form, 'donation': donation})
def delete_donor(request, pk):
    donation = get_object_or_404(Donation_organisation, pk=pk)
    if request.method == "POST":
        donation.delete()
        return redirect('main:donor_list')
    return render(request, 'main/delete_donor.html', {'donation': donation})

# contact message list view
def message_list(request):
    messages = ContactMessage.objects.all()  # Fetch all contact messages
    return render(request, 'main/snippets_templates/table/contact_message_list.html', {'messages': messages})
# contact message detail view
def message_details(request, pk):
    message = get_object_or_404(ContactMessage, pk=pk)
    return render(request, 'main/message_details.html', {'message': message})
# contact message edit view
def edit_message(request, pk):
    message = get_object_or_404(ContactMessage, pk=pk)
    if request.method == "POST":
        form = MessageForm(request.POST, instance=message)
        if form.is_valid():
            form.save()
            return redirect('main:message_list')
    else:
        form = MessageForm(instance=message)
    return render(request, 'main/edit_message.html', {'form': form, 'message': message})
# contact message delete view
def delete_message(request, pk):
    message = get_object_or_404(ContactMessage, pk=pk)
    if request.method == "POST":
        message.delete()
        return redirect('main:message_list')
    return render(request, 'main/delete_message.html', {'message': message})

# add contact message view (if needed)
def add_message(request):
    if request.method == "POST":
        form = MessageForm(request.POST, request.FILES)
        message='Thank You, we will get back to you within 48 hours.'
        context={
            "message":message,
            # "link":SITEURL+'/management/companyagenda'
        }
        if form.is_valid():
            instance=form.save(commit=False)
            instance.save()
            return render(request, "main/errors/generalerrors.html",context)
    else:
        form = MessageForm()
    context={
            "form": form,
        }
    return render(request, "main/add_message.html",context)
#=======
def education_landing(request):

    initial_view = request.GET.get('view','landing')
    context = {'initial_view': initial_view}
    return render(request, 'main/education/education.html', context)


def request_mentorship(request):
    """Render and handle the mentorship request form. Uses the same ContactForm/Feedback
    model used elsewhere so styling and behavior are consistent across the site.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            # If user is authenticated, attach them; otherwise leave blank
            if request.user.is_authenticated:
                instance.user = request.user
            # Ensure topic denotes mentorship request if left blank
            if not instance.topic:
                instance.topic = 'Mentorship Request'
            instance.save()
            # redirect back to education landing with a success flag
            return redirect(reverse('main:education_landing') + '?view=landing&mentorship=success')
    else:
        # Prefill the form topic to guide the user
        initial = {'topic': 'Mentorship Request'}
        form = ContactForm(initial=initial)

    return render(request, 'main/education/mentorship_form.html', {'form': form})


def course_register(request):
    """
    Render course/scholarship registration page.
    Supports:
    - Browse available courses
    - Pre-select a course via course_id parameter
    - Pre-select a scholarship via scholarship_id parameter
    """
    courses = [
        {
            'id': 101,
            'title': 'Modern Web Development (React & Node)',
            'category': 'Digital Skills',
            'duration': '12 Weeks',
            'format': 'Online Live',
            'price': 150.00,
        },
        {
            'id': 102,
            'title': 'Financial Literacy for Diaspora Investors',
            'category': 'Finance & Business',
            'duration': '4 Weeks',
            'format': 'Online Self-Paced',
            'price': 40.00,
        },
        {
            'id': 103,
            'title': 'Entrepreneurship & Small Business Management',
            'category': 'Business',
            'duration': '8 Weeks',
            'format': 'Blended',
            'price': 95.00,
        },
    ]
    
    # Get selected object if provided
    selected_object = None
    selected_type = None
    
    # Check for course_id (TrainingCourse)
    course_id = request.GET.get('course_id', None)
    if course_id:
        try:
            selected_object = TrainingCourse.objects.get(id=int(course_id))
            selected_type = 'course'
        except (TrainingCourse.DoesNotExist, ValueError):
            selected_object = None
    
    # Check for scholarship_id (Scholarship)
    scholarship_id = request.GET.get('scholarship_id', None)
    if scholarship_id and not selected_object:
        try:
            selected_object = Scholarship.objects.get(id=int(scholarship_id))
            selected_type = 'scholarship'
        except (Scholarship.DoesNotExist, ValueError):
            selected_object = None
    
    # If requested as a partial (AJAX in-page load), return only the fragment
    if request.GET.get('partial') == '1':
        return render(request, 'main/education/course_register_fragment.html', {
            'courses': courses,
            'selected_object': selected_object,
            'selected_type': selected_type,
        })
    
    return render(request, 'main/education/course_register.html', {
        'courses': courses,
        'selected_object': selected_object,
        'selected_type': selected_type,
    })


def donation_list(request):
    donations = Donation_organization.objects.all().order_by('-created_at')
    return render(request,'main/snippets_templates/table/donation_list.html',{'donations': donations})


# Edit Donation View
class DonationEditView(UpdateView):
    model = Donation_organization
    fields = ['donor_name', 'email', 'amount', 'message']
    template_name = 'main/snippets_templates/table/donation_edit.html'
    success_url = reverse_lazy('main:donation')

# Delete Donation View
class DonationDeleteView(DeleteView):
    model = Donation_organization
    template_name = 'main/snippets_templates/table/donation_confirm_delete.html'
    success_url = reverse_lazy('main:donation')


#>>>>>>> origin/25.10_DC48K_UAT_FN

# Scholarship views

def scholarship_search(request):
    scholarships = Scholarship.objects.all()
    form = ScholarshipSearchForm(request.GET or None)


    if form.is_valid():
        data = form.cleaned_data
        # apply filter
        keyword = data.get("search_keyword")
        if keyword:
            scholarships = scholarships.filter(
                Q(title__icontains=keyword) |
                Q(provider__icontains=keyword) 
            )

        currency = data.get("filter_currency")
        if currency:
            scholarships = scholarships.filter(
                amount_value__isnull=False, 
                amount_currency = currency
            )
        else:
            pass

        level = data.get("filter_level")
        if level:
            scholarships = scholarships.filter(level=level)

        field = data.get("filter_field")
        if field:
            scholarships = scholarships.filter(field=field)

        location = data.get("filter_location")
        if location:
            scholarships = scholarships.filter(location=location)

        if  data.get("filter_status"):
            scholarships = scholarships.filter(status=Scholarship.Status.CLOSING_SOON)
        
    context = {
        'scholarships': scholarships,
        'form': form,
        'result_count': scholarships.count(),
    }
    return render(request, 'scholarship_app/scholarship_search.html',context)

@login_required
def add_scholarship(request):
    if request.method == "POST":
        form  = ScholarshipForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = request.user
            obj.save()
            return redirect('main:scholarship_search')
    
    else:
        form = ScholarshipForm()

    return render(request, "scholarship_app/add_scholarship.html", {"form": form})

@login_required
def scholarship_edit(request, pk):
    scholarship = get_object_or_404(Scholarship, pk=pk, created_by=request.user)
    if request.method == "POST":
        form = ScholarshipForm(request.POST, instance=scholarship)
        if form.is_valid():
            form.save()
            return redirect('main:add_scholarship')
    
    else:
        form  = ScholarshipForm(instance=scholarship)

    return render(request,'scholarship_app/scholarship_edit.html', {'form': form})


@login_required
def scholarship_delete(request, pk):
    scholarship = get_object_or_404(Scholarship, pk=pk, created_by=request.user)
    if request.method == "POST":
        scholarship.delete()
        return redirect('main:add_scholarship')

    return render(request,'scholarship_app/scholarship_delete.html', {'form': form})


def ai_refresh_scholarships(request):
    today = timezone.now().date()
    scholarships = Scholarship.objects.all()
    scored = []

    for s in scholarships:
        score = 0

        if not s.deadline:
            continue

        days_left = (s.deadline - today).days

        if days_left < 0:
            continue

        if days_left <= 7:
            score += 5
        elif days_left <= 30:
            score += 3

        if s.status and s.status.lower() == "open":
            score += 3

        if isinstance(s.amount, str) and "full" in s.amount.lower():
            score += 4

        scored.append((score, s))

    scored.sort(reverse=True, key=lambda x: x[0])
    top_pool = scored[:25]
    selected = random.sample(top_pool, min(6, len(top_pool)))
    best = [s for score, s in selected]

    data = []
    for s in best:
        data.append({
            "title": s.title,
            "provider": s.provider,
            "level": s.level,
            "field": s.field,
            "location": s.location,
            "amount": s.amount,
            "deadline": s.deadline.strftime("%Y-%m-%d") if s.deadline else None,
            "status": s.status
        })

    return JsonResponse({
        "scholarships": data,
        "count": len(data)
    })

def education_training(request):
    courses = TrainingCourse.objects.all()  # Changed from filter(created_by=request.user)
    
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) |
            Q(course_code__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(instructor__icontains=search_query)
        )
    
    category_filter = request.GET.get('category', '')
    if category_filter:
        courses = courses.filter(category=category_filter)
    
    format_filter = request.GET.get('format', '')
    if format_filter:
        courses = courses.filter(format=format_filter)
    
    status_filter = request.GET.get('status', '')
    if status_filter:
        courses = courses.filter(status=status_filter)

    paginator = Paginator(courses, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'paginator': paginator,
        'search_query': search_query,
        'category_filter': category_filter,
        'format_filter': format_filter,
        'status_filter': status_filter,
    }
    
    return render(request, 'main/education/training_skills.html', context)


@login_required
def course_crud(request):
    from django.contrib import messages
    
    courses = TrainingCourse.objects.filter(created_by=request.user)
    editing_course = False
    course_id = request.GET.get('edit', None)
    course_to_edit = None
    
    # Check if editing an existing course
    if course_id:
        try:
            course_to_edit = get_object_or_404(TrainingCourse, id=int(course_id), created_by=request.user)
            editing_course = True
        except (ValueError, TrainingCourse.DoesNotExist):
            pass
    
    if request.method == 'POST':
        if course_to_edit:
            # Updating existing course
            form = TrainingCourseForm(request.POST, request.FILES, instance=course_to_edit)
        else:
            # Creating new course
            form = TrainingCourseForm(request.POST, request.FILES)
        
        if form.is_valid():
            course = form.save(commit=False)
            if not course_to_edit:
                course.created_by = request.user
            course.save()
            if course_to_edit:
                messages.success(request, f'Course "{course.title}" updated successfully!')
            else:
                messages.success(request, f'Course "{course.title}" created successfully!')
            return redirect('main:course_crud')
    else:
        if course_to_edit:
            form = TrainingCourseForm(instance=course_to_edit)
        else:
            form = TrainingCourseForm()
    
    return render(request, 'main/education/course_crud.html', {
        'courses': courses,
        'form': form,
        'editing_course': editing_course,
        'course_to_edit': course_to_edit,
    })



@login_required
def add_course(request):
    form = TrainingCourseForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        course = form.save(commit=False)
        course.created_by = request.user
        course.save()
        return redirect('main:education_training')

    return render(request, 'main/education/add_course.html', {'form': form})


@login_required
def edit_course(request, pk):
    course = get_object_or_404(TrainingCourse, id=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = TrainingCourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            return redirect('main:course_crud') 
    else:
        form = TrainingCourseForm(instance=course)
    
    courses = TrainingCourse.objects.filter(created_by=request.user)
    return render(request, 'main/education/course_crud.html', {
        'courses': courses,
        'form': form,
        'editing_course': True,
    })

@login_required
def delete_course(request, pk):
    from django.contrib import messages
    
    course = get_object_or_404(TrainingCourse, id=pk, created_by=request.user)
    
    if request.method == "POST":
        course_title = course.title
        course.delete()
        messages.success(request, f'Course "{course_title}" deleted successfully!')
        return redirect('main:course_crud')  
    
    return redirect('main:course_crud')



def ai_course_discovery(request):

    courses = []
    seen = set()

    mit_feeds = [
        "https://ocw.mit.edu/courses/rss.xml",
        "https://ocw.mit.edu/courses/new-courses/feed",
    ]

    courses = []

    for url in mit_feeds:
        feed = feedparser.parse(url)

        for entry in feed.entries:
            title = entry.title.strip()

            if title in seen:
                continue
            seen.add(title)

            courses.append({
                "title": title,
                "university": "MIT",
                "platform": "MIT OpenCourseWare",
                "duration": "Self-paced",
                "url": entry.link,
                "is_free": True
            })

    # Harvard / edX courses
    harvard_courses = [
        {
            "title": "CS50: Introduction to Computer Science",
            "university": "Harvard University",
            "platform": "edX",
            "duration": "12 Weeks",
            "url": "https://www.edx.org/cs50",
            "is_free": True
        },
        {
            "title": "Data Science: Machine Learning",
            "university": "Harvard University",
            "platform": "edX",
            "duration": "8 Weeks",
            "url": "https://www.edx.org/course/data-science-machine-learning",
            "is_free": True
        },
        {
            "title": "CS50's AI with Python",
            "university": "Harvard University",
            "platform": "edX",
            "duration": "7 Weeks",
            "url": "https://www.edx.org/course/cs50s-introducation-to-artificial-intelligence-with-python",
            "is_free": True
        }
    ]

    # Youtube Courses

    youtube_courses = [
        {
            "title": "Python Full Course for Beginners",
            "university": "FreeCodeCamp",
            "platform": "Youtube",
            "duration": "Self-paced",
            "url": "https://www.youtube.com/watch?v=rfscVS0vtbw",
            "is_free": True
        },
        {
            "title": "JavaScript Full Course",
            "university": "FreeCodeCamp",
            "platform": "Youtube",
            "duration": "Self-paced",
            "url": "https://www.youtube.com/watch?v=jS4aFq5-91M",
            "is_free": True
        },
        {
            "title": "Machine Learning Full Course",
            "university": "Stanford (Andrew Ng)",
            "platform": "Youtube",
            "duration": "Self-paced",
            "url": "https://www.youtube.com/watch?v=jGwoUgTS7I",
            "is_free": True
        },
    ]
  
    stanford_courses = [
        {
            "title": "Machine Learning",
            "university": "Stanford University",
            "platform": "Coursera",
            "duration": "10 Weeks",
            "url": "https://www.coursera.org/learn/machine-learning"
        }
    ]

    futurelearn_courses = [
        {
            "title": "Digital Skills: Web Analytics",
            "university": "Accenture",
            "platform": "FutureLearn",
            "duration": "4 Weeks",
            "url": "https://www.futurelearn.com/courses/digital-skills-web-analytics",
            "is_free": True
        },
    ]

    courses.extend(harvard_courses)
    courses.extend(stanford_courses)
    courses.extend(youtube_courses)
    courses.extend(futurelearn_courses)

    if len(courses) < 6:
        return JsonResponse({
            "courses": courses,
            "count": len(courses)
        })
    
    random.shuffle(courses)
    pool = courses[:20]
    selected = random.sample(pool, min(6,len(pool)))

    return JsonResponse({
        "courses": selected,
        "count": len(selected)
    })
    


def testimonial_list(request):
    testimonial = Testimonial.objects.all() 
    return render(request, "main/snippets_templates/table/testimonial_list.html",{"testimonial":testimonial})
# views.py - ADD THESE VIEWS (place them together)

# ============================================
# SIMPLE GOVERNANCE CRUD VIEWS
# ============================================

# views.py - CORRECTED TEMPLATE NAMES

# List all governance records
def governance_list(request):
    from .models import Governance
    records = Governance.objects.all().select_related('members')
    
    context = {
        'records': records,
        'title': 'Governance Records'
    }
    return render(request, 'main/governance_list.html', context)

# Create new governance record
# REPLACE your entire governance_create function with this:

def governance_create(request):
    """Create governance record - handles both existing and new users"""
    from .forms import GovernanceForm
    from django.contrib.auth.models import User
    from django.contrib import messages
    
    print("=== CREATE VIEW STARTED ===")
    
    if request.method == 'POST':
        print("POST data:", request.POST)
        
        form = GovernanceForm(request.POST)
        
        if form.is_valid():
            print("Form is valid!")
            
            # Get cleaned data
            cleaned_data = form.cleaned_data
            members = cleaned_data.get('members')
            new_username = cleaned_data.get('new_username', '').strip()
            new_password = cleaned_data.get('new_password', '').strip()
            new_email = cleaned_data.get('new_email', '').strip()
            
            # If creating a new user
            if new_username and new_password:
                print(f"Creating new user: {new_username}")
                try:
                    # Create the user
                    new_user = User.objects.create_user(
                        username=new_username,
                        password=new_password,
                        email=new_email if new_email else ''
                    )
                    print(f"User created: {new_user.id}")
                    
                    # Update the form instance to use new user
                    form.instance.members = new_user
                    messages.success(request, f'User "{new_username}" created successfully!')
                    
                except Exception as e:
                    print(f"Error creating user: {e}")
                    messages.error(request, f'Error creating user: {str(e)}')
                    return render(request, 'main/governance/governance_form.html', {
                        'form': form,
                        'title': 'Create Governance Record'
                    })
            
            # Save the governance record
            governance = form.save()
            print(f"Governance saved: {governance.id}")
            messages.success(request, f'Governance record "{governance.governance_category}" created!')
            
            return redirect('main:governance_detail', pk=governance.pk)
        else:
            print("Form errors:", form.errors)
            # Show form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    
    else:
        # GET request - show empty form
        form = GovernanceForm()
    
    return render(request, 'main/governance/governance_form.html', {
        'form': form,
        'title': 'Create Governance Record'
    })

# View single governance record
def governance_detail(request, pk):
    from .models import Governance
    from django.shortcuts import get_object_or_404
    
    record = get_object_or_404(Governance, pk=pk)
    
    context = {
        'record': record,
        'title': f'Details - {record.governance_category}'
    }
    # Changed from 'detail.html' to 'governance_detail.html'
    return render(request, 'main/governance/governance_detail.html', context)

# Update governance record
def governance_update(request, pk):
    from .models import Governance
    from .forms import GovernanceForm
    from django.shortcuts import get_object_or_404
    
    record = get_object_or_404(Governance, pk=pk)
    
    if request.method == 'POST':
        form = GovernanceForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            return redirect('main:governance_detail', pk=record.pk)
    else:
        form = GovernanceForm(instance=record)
    
    context = {
        'form': form,
        'title': f'Update {record.governance_category}',
        'record': record
    }
    # Changed from 'form.html' to 'governance_form.html'
    return render(request, 'main/governance/governance_form.html', context)

# Delete governance record

def governance_delete(request, pk):
    """Delete a governance record"""
    from django.shortcuts import get_object_or_404, redirect
    from django.contrib import messages
    from .models import Governance
    
    record = get_object_or_404(Governance, pk=pk)
    
    if request.method == 'POST':
        record.delete()
        messages.success(request, f'Record "{record.governance_category}" deleted successfully!')
        return redirect('main:governance_list')
    
    # Use the correct template name
    return render(request, 'main/governance/governance_confirm_delete.html', {
        'record': record,
        'title': f'Delete {record.governance_category}'
    })



@csrf_exempt
def quick_add_user(request):
    """
    Quick user creation endpoint
    Returns JSON response
    """
    print("DEBUG: quick_add_user called")
    
    # Only accept POST requests
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Only POST requests are allowed'
        })
    
    try:
        # Parse JSON data if sent as JSON, otherwise use form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            username = data.get('username', '').strip()
            password = data.get('password', '').strip()
            email = data.get('email', '').strip()
        else:
            # Form data
            username = request.POST.get('username', '').strip()
            password = request.POST.get('password', '').strip()
            email = request.POST.get('email', '').strip()
        
        print(f"DEBUG: Received - username='{username}', password length={len(password)}, email='{email}'")
        
        # Validate
        if not username:
            return JsonResponse({
                'success': False,
                'error': 'Username is required'
            })
        
        if not password:
            return JsonResponse({
                'success': False,
                'error': 'Password is required'
            })
        
        # Check if user exists
        if User.objects.filter(username=username).exists():
            return JsonResponse({
                'success': False,
                'error': f'Username "{username}" already exists'
            })
        
        # Create user
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email if email else ''
        )
        
        print(f"DEBUG: User created successfully - ID: {user.id}, Username: {user.username}")
        
        # Return success
        return JsonResponse({
            'success': True,
            'user_id': user.id,
            'username': user.username,
            'email': user.email if user.email else ''
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data'
        })
    except Exception as e:
        print(f"DEBUG: Exception: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })
           

    # Add to views.py
def test_user_endpoint(request):
    """Test page for quick_add_user endpoint"""
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test User Endpoint</title>
        <script>
        async function testEndpoint() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const email = document.getElementById('email').value;
            
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);
            formData.append('email', email);
            
            try {
                const response = await fetch('/quick-add-user/', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.text();
                document.getElementById('result').innerHTML = 
                    '<h3>Raw Response:</h3><pre>' + result + '</pre>';
                
                try {
                    const jsonResult = JSON.parse(result);
                    document.getElementById('result').innerHTML += 
                        '<h3>Parsed JSON:</h3><pre>' + JSON.stringify(jsonResult, null, 2) + '</pre>';
                } catch(e) {
                    document.getElementById('result').innerHTML += 
                        '<h3>Not valid JSON</h3>';
                }
            } catch(error) {
                document.getElementById('result').innerHTML = 'Error: ' + error;
            }
        }
        </script>
    </head>
    <body>
        <h1>Test Quick Add User Endpoint</h1>
        <div>
            <input type="text" id="username" placeholder="Username" value="testuser"><br>
            <input type="password" id="password" placeholder="Password" value="testpass123"><br>
            <input type="email" id="email" placeholder="Email" value="test@example.com"><br>
            <button onclick="testEndpoint()">Test Endpoint</button>
        </div>
        <div id="result"></div>
    </body>
    </html>
    '''
    from django.http import HttpResponse
    return HttpResponse(html)


    # Changed from 'delete.html' to 'governance_confirm_delete.html'
    return render(request, 'main/governance/governance_confirm_delete.html', context)


def testimonial_delete(request, pk):
    testimonial = get_object_or_404(Testimonial, pk=pk)
    testimonials = Testimonial.objects.all()

    if request.method == "POST":
        testimonial.delete()
        return redirect('main:testimonial_list')

    return render(request, "main/testimonial/testimonial_confirm_delete.html", {
        'testimonial': testimonial,
        'testimonials': testimonials,
    })


def consular_assistance(request):
    page = ConsularAssistancePage.objects.first()
    context = { 'page': page, }
    return render(request, "main/consular_assistance.html", context)


from .models import Doctor, AppointmentRequest
from .forms import SearchForm, AppointmentRequestForm
from django.core.paginator import Paginator
DOCTORS_PER_PAGE = getattr(settings, 'DOCTORS_PER_PAGE', 6)


def find_doctors(request):
    """Main find doctors page."""
    form = SearchForm(request.GET)
    doctors = Doctor.objects.all()

    specialty_q = request.GET.get('specialty', '').strip()
    location_q = request.GET.get('location', '').strip()
    categories = request.GET.getlist('categories')
    languages = request.GET.getlist('languages')
    sort_by = request.GET.get('sort', 'recommended')

    # Filter by specialty
    if specialty_q:
        doctors = doctors.filter(specialty__icontains=specialty_q) | \
                  doctors.filter(title__icontains=specialty_q) | \
                  doctors.filter(name__icontains=specialty_q)

    # Filter by location
    if location_q:
        doctors = doctors.filter(location_city__icontains=location_q) | \
                  doctors.filter(location_country__icontains=location_q)

    # Filter by categories (any match)
    if categories:
        filtered_ids = []
        for doc in doctors:
            if any(cat in doc.categories for cat in categories):
                filtered_ids.append(doc.pk)
        doctors = doctors.filter(pk__in=filtered_ids)

    # Filter by languages (any match)
    if languages:
        filtered_ids = []
        for doc in doctors:
            if any(lang in doc.languages for lang in languages):
                filtered_ids.append(doc.pk)
        doctors = doctors.filter(pk__in=filtered_ids)

    # Sorting
    if sort_by == 'rating':
        doctors = doctors.order_by('-rating', '-review_count')
    elif sort_by == 'reviews':
        doctors = doctors.order_by('-review_count', '-rating')
    elif sort_by == 'name':
        doctors = doctors.order_by('name')
    else:  # recommended
        doctors = doctors.order_by('-rating', '-review_count')

    total_count = doctors.count()

    # Pagination
    paginator = Paginator(doctors, DOCTORS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'form': form,
        'page_obj': page_obj,
        'total_count': total_count,
        'specialty_q': specialty_q,
        'location_q': location_q,
        'selected_categories': categories,
        'selected_languages': languages,
        'sort_by': sort_by,
        'category_choices': Doctor.CATEGORY_CHOICES,
        'language_choices': Doctor.LANGUAGE_CHOICES,
        'sort_options': [
            ('recommended', 'Recommended'),
            ('rating', 'Highest Rated'),
            ('reviews', 'Most Reviews'),
            ('name', 'Name (A–Z)'),
        ],
        'page_range': paginator.get_elided_page_range(page_obj.number, on_each_side=2, on_ends=1),
    }
    return render(request, 'main/find_doctors.html', context)


def doctor_profile_api(request, pk):
    """AJAX endpoint: return doctor profile as JSON for the modal."""
    doctor = get_object_or_404(Doctor, pk=pk)
    data = {
        'id': doctor.pk,
        'name': doctor.name,
        'title': doctor.title,
        'specialty': doctor.specialty,
        'location': doctor.full_location,
        'clinic': doctor.clinic_name,
        'languages': doctor.get_language_display_list(),
        'telehealth': doctor.telehealth,
        'available': doctor.available,
        'rating': str(doctor.rating),
        'review_count': doctor.review_count,
        'bio': doctor.bio,
        'education': doctor.education,
        'avatar_color': doctor.avatar_color,
        'avatar_initials': doctor.avatar_initials or doctor.name[:2].upper(),
    }
    return JsonResponse(data)


@require_POST
def book_appointment(request, pk):
    """Handle appointment booking form submission."""
    doctor = get_object_or_404(Doctor, pk=pk)

    # Rate limiting via session
    session_key = f'booking_attempts_{pk}'
    attempts = request.session.get(session_key, 0)
    if attempts >= 5:
        return JsonResponse({'success': False, 'error': 'Too many requests. Please try again later.'}, status=429)

    form = AppointmentRequestForm(request.POST)

    if form.is_valid():
        appointment = form.save(commit=False)
        appointment.doctor = doctor
        appointment.save()

        # Track attempts
        request.session[session_key] = attempts + 1

        # Send email notification (prints to console in dev)
        try:
            send_mail(
                subject=f'New Appointment Request – {doctor.name}',
                message=f"""
New appointment request received:

Doctor: {doctor.name}
Patient: {appointment.full_name}
Email: {appointment.email}
Date: {appointment.preferred_date}
Time: {appointment.get_preferred_time_display()}
Reason: {appointment.reason}

Log in to the admin to respond.
                """.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
            send_mail(
                subject=f'Appointment Request Received – {doctor.name}',
                message=f"""
Dear {appointment.full_name},

Thank you for submitting an appointment request with {doctor.name}.

Your request details:
  Date: {appointment.preferred_date}
  Time: {appointment.get_preferred_time_display()}
  Reason: {appointment.reason}

The provider will review your request and contact you at {appointment.email} to confirm availability.

– Diaspora County 48
                """.strip(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[appointment.email],
                fail_silently=True,
            )
        except Exception:
            pass

        return JsonResponse({
            'success': True,
            'message': f'Your appointment request with {doctor.name} has been submitted successfully! '
                       f'The clinic will contact you at {appointment.email} to confirm your appointment.'
        })
    else:
        errors = {field: list(errs) for field, errs in form.errors.items()}
        return JsonResponse({'success': False, 'errors': errors}, status=400)


def home(request):
    """Simple home redirect."""
    from django.shortcuts import redirect
    return redirect('find_doctors')



def insurance_support(request):
    """Main insurance support page view"""
    # Get all active insurance plans ordered by display_order and score
    insurance_plans = InsurancePlan.objects.filter(
        is_active=True
    ).order_by('display_order', '-score')
    
    # Get featured plans (top 3 by score)
    featured_plans = insurance_plans[:3]
    
    # Get stats for the template
    total_plans = insurance_plans.count()
    highest_score = insurance_plans.first().score if total_plans > 0 else 0
    
    context = {
        'insurance_plans': insurance_plans,
        'featured_plans': featured_plans,
        'total_plans': total_plans,
        'highest_score': highest_score,
        'page_title': 'Insurance Support',
    }
    
    return render(request, 'main/healthcare/insurance_support.html', context)



@require_POST
def ai_recommendation_api(request):
    """API endpoint for AI recommendations - FULLY AUTOMATED"""
    try:
        # Parse JSON data from request
        data = json.loads(request.body)
        age = data.get('age')
        residence = data.get('residence')
        priority = data.get('priority')
        
        print(f" AI Request - Age: {age}, Residence: {residence}, Priority: {priority}")
        
        # Try to find a matching rule in the database
        rule = AIRecommendationRule.objects.filter(
            age_bracket=age,
            residence=residence,
            priority=priority,
            is_active=True
        ).select_related('recommended_plan').first()
        
        if rule:
            # Found a matching rule
            plan = rule.recommended_plan
            response_data = {
                'success': True,
                'plan_name': f"{plan.provider_name} {plan.plan_name}",
                'recommendation_text': rule.recommendation_text,
                'plan_id': plan.id,
                'score': float(plan.score),
                'network': plan.network,
                'evacuation': plan.evacuation
            }
            print(f" Found rule: {rule}")
            
        else:
            # No exact match - find the best alternative
            print(" No exact match found, finding best alternative...")
            
            # Try to find a plan with matching priority
            alternative_plan = InsurancePlan.objects.filter(
                is_active=True
            ).order_by('-score').first()
            
            if alternative_plan:
                # Generate dynamic recommendation text
                rec_text = generate_recommendation_text(age, residence, priority, alternative_plan)
                
                response_data = {
                    'success': True,
                    'plan_name': f"{alternative_plan.provider_name} {alternative_plan.plan_name}",
                    'recommendation_text': rec_text,
                    'plan_id': alternative_plan.id,
                    'score': float(alternative_plan.score),
                    'network': alternative_plan.network,
                    'evacuation': alternative_plan.evacuation
                }
                print(f" Using alternative plan: {alternative_plan}")
            else:
                response_data = {
                    'success': False,
                    'error': 'No insurance plans available'
                }
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        print(f" Error in ai_recommendation_api: {str(e)}")
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

def generate_recommendation_text(age, residence, priority, plan):
    """Generate dynamic recommendation text based on inputs and plan"""
    
    age_text = {
        'young': 'young professionals',
        'mid': 'established professionals',
        'senior': 'seniors'
    }.get(age, 'individuals')
    
    residence_text = {
        'usa': 'in the USA',
        'europe': 'in Europe',
        'other': 'internationally'
    }.get(residence, '')
    
    priority_text = {
        'budget': 'budget-conscious',
        'comprehensive': 'comprehensive',
        'emergency': 'emergency-focused'
    }.get(priority, '')
    
    base_text = f"Based on your inputs, we recommend the {plan.provider_name} {plan.plan_name} plan for {age_text} {residence_text} seeking {priority_text} coverage. "
    
    if plan.score >= 9.5:
        base_text += f"This top-rated plan offers {plan.network.lower()} coverage with {plan.evacuation.lower()} evacuation benefits. "
    elif plan.score >= 9.0:
        base_text += f"This excellent plan provides {plan.network.lower()} coverage and {plan.evacuation.lower()} evacuation. "
    else:
        base_text += f"This plan offers solid {plan.network.lower()} coverage with {plan.evacuation.lower()} evacuation options. "
    
    if 'Included' in plan.evacuation:
        base_text += "Emergency evacuation is included for peace of mind."
    else:
        base_text += "Evacuation coverage is available as an optional add-on."
    
    return base_text

@require_POST
def submit_expert_inquiry(request):
    """Handle expert consultation form submissions"""
    try:
        data = json.loads(request.body)
        
        # Create new inquiry
        inquiry = ExpertInquiry.objects.create(
            full_name=data.get('full_name'),
            email=data.get('email'),
            phone=data.get('phone', ''),
            question=data.get('question'),
            interested_plan_id=data.get('plan_id') if data.get('plan_id') else None
        )
        
        # TODO: Send email notification to admin
        # send_inquiry_notification(inquiry)
        
        return JsonResponse({
            'success': True,
            'message': 'Your request has been submitted successfully. An expert will contact you within 24 hours.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def download_comparison_csv(request):
    """Generate and download CSV of insurance plans"""
    # Create HttpResponse with CSV header
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="insurance_comparison.csv"'
    
    # Get all active plans
    plans = InsurancePlan.objects.filter(is_active=True).order_by('display_order', '-score')
    
    # Create CSV writer
    writer = csv.writer(response)
    
    # Write headers
    writer.writerow([
        'Provider',
        'Plan Name',
        'Global Network',
        'Max Benefit',
        'Evacuation Coverage',
        'Rating (out of 10)'
    ])
    
    # Write data rows
    for plan in plans:
        writer.writerow([
            plan.provider_name,
            plan.plan_name,
            plan.network,
            plan.max_benefit,
            plan.evacuation,
            f"{plan.score}/10"
        ])
    
    return response


# -----------------------------
# Document Services (frontend-only views)
# -----------------------------
def document_services_dashboard(request):
    """Render the Document Services dashboard (frontend-only)."""
    return render(request, 'main/document_services/dashboard.html')


def document_services_drafts(request):
    """Render the Drafts list (frontend-only)."""
    return render(request, 'main/document_services/drafts.html')


def document_services_documents(request):
    """Render the Documents listing (frontend-only)."""
    return render(request, 'main/document_services/documents.html')


def document_services_history(request):
    """Render the Document history (frontend-only)."""
    return render(request, 'main/document_services/history.html')


def document_services_application_form(request):
    """Render the application form (frontend-only)."""
    return render(request, 'main/document_services/application.html')


def document_services_summary(request):
    """Render the summary page (frontend-only)."""
    return render(request, 'main/document_services/summary.html')


def document_services_payment_summary(request):
    """Render the payment summary placeholder (frontend-only)."""
    return render(request, 'main/document_services/payment_summary.html')


def document_services_notifications(request):
    """Render the notifications page (frontend-only)."""
    return render(request, 'main/document_services/notifications.html')


def document_services_notification_preferences(request):
    """Render the notification preferences page (frontend-only)."""
    return render(request, 'main/document_services/notification_preferences.html')


def document_services_profile(request):
    """Render the profile page (frontend-only)."""
    return render(request, 'main/document_services/profile.html')


def document_services_settings(request):
    """Render the settings page (frontend-only)."""
    return render(request, 'main/document_services/settings.html')


def document_services_support_help(request):
    """Render the support and help page (frontend-only)."""
    return render(request, 'main/document_services/support_help.html')



class LandingPageView(TemplateView):
    template_name = 'main/news/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['latest_news'] = NewsArticle.objects.filter(status = 'PUBLISHED').order_by('created_at')[:3]
        context['categories'] = Category.objects.all()
        return context


class ArticleHomeView(ListView):
    model = NewsArticle
    template_name = 'main/news/news_listing.html'
    context_object_name = 'articles'
    paginate_by = 7

    def get_queryset(self):
        queryset = NewsArticle.objects.filter(status = 'PUBLISHED').order_by('created_at')

        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
    
        all_articles = context['articles']
        if all_articles:
            context['hero_article'] = all_articles[0]
            context['grid_articles'] = all_articles[1:]
        return context

class ArticleDetailView(DetailView):
    model = NewsArticle 
    template_name = 'main/news/article_detail.html'
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_articles'] = NewsArticle.objects.filter(
            category=self.object.category
        ).exclude(
            id=self.object.id
        )[:3]
        return context

class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = NewsArticle
    form_class = ArticleForm
    template_name = 'main/news/article_form.html'
    success_url =reverse_lazy('news:dashboard')

    def form_valid(self, form):
        if not form.instance.author:
            form.instance.author = self.request.user
        return super().form_valid(form)
    
class ArticleEditView(LoginRequiredMixin, UpdateView):
    model = NewsArticle
    form_class = ArticleForm
    template_name = 'main/news/article_form.html'
    success_url = reverse_lazy('news:dashboard')

    
class ArticleDeleteView(LoginRequiredMixin, DeleteView):
    model = NewsArticle
    template_name = 'main/news/article_confirm_delete.html'
    success_url = reverse_lazy('news:dashboard')



# Category Views
class CategoryArticleListView(ListView):
    model = NewsArticle
    template_name = 'main/news/category_articles.html'
    context_object_name = 'articles'
    paginate_by = 6 

    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return NewsArticle.objects.filter(category=self.category, status = 'PUBLISHED').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context
        

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    fields = ['name', 'description']
    template_name = 'main/news/category_form.html'
    success_url = reverse_lazy('news:dashboard')

    
class CategoryEditView(LoginRequiredMixin, UpdateView):
    model = Category
    fields = ['name', 'description']
    template_name = 'main/news/category_form.html'
    success_url = reverse_lazy('news:dashboard')

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'main/news/category_confirm_delete.html'
    success_url = reverse_lazy('news:dashboard')


class AdminDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'main/news/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) 
        query = self.request.GET.get('q')
        articles = NewsArticle.objects.all()
        
        if query:
           
            recent_articles = articles.filter(
                Q(title__icontains=query) | 
                Q(category__name__icontains=query)
            ).order_by('-created_at')
        else:
           
            recent_articles = articles.order_by('-created_at')[:10]

        context['total_count'] = articles.count()
        context['published_count'] = articles.filter(status='PUBLISHED').count()
        context['draft_count'] = articles.filter(status='DRAFT').count()
        context['subscriber_count'] = Subscriber.objects.filter(confirmed=True).count()
        context['categories'] = Category.objects.all()
        context['recent_articles'] = recent_articles
        context['query'] = query 
        
        return context

def subscribe(request):
    if request.method == "POST":
        email = request.POST.get('email')
        if email:
            sub, created = Subscriber.objects.get_or_create(email=email)
            if created:
                verify_url = request.build_absolute_uri(
                    reverse('news:confirm_email', args=[sub.conf_token])
                )

                send_mail(
                    "Action Required: Confirm your subscription",
                    f"Thanks for signing up! please Verify your email here: {verify_url}",
                    "noreply@dc48kcoda.dev",
                    [email]
                )

                return JsonResponse({"status": "success", "msg": "Check your email to confirm!"})
            return JsonResponse({"status": "exists", "msg": "you're already on the list."})
        return JsonResponse({"status": "error", "msg": "Invalid Request"})

    return JsonResponse({"status": "error", "msg": "Only POST allowed"}, status=405)

def member_home(request):
    """Handle member registration and contact message submission"""
    if request.method == 'POST':
        if 'register_submit' in request.POST:
            from .forms import MembershipRegistrationForm
            member_form = MembershipRegistrationForm(request.POST)
            if member_form.is_valid():
                member_form.save()
                messages.success(request, 'Membership registration successful! Welcome to DC48.')
                return redirect('main:member_home')

        elif 'contact_submit' in request.POST:
            from .forms import ContactMessageForm
            contact_form = ContactMessageForm(request.POST)
            if contact_form.is_valid():
                contact_form.save()
                messages.success(request, 'Your message has been sent successfully!')
                return redirect('main:member_home')

    else:
        from .forms import MembershipRegistrationForm, ContactMessageForm
        member_form = MembershipRegistrationForm()
        contact_form = ContactMessageForm()

    context = {
        'form': member_form,
        'contact_form': contact_form
    }
    return render(request, 'main/memberjoin/member_home.html', context)


# ============================================
# LEGAL & IMMIGRATION SERVICES VIEWS
# ============================================

def legal_immigration_guidance(request):
    from .models import LegalService
    
    services = LegalService.objects.filter(is_active=True).order_by('order')
    
    context = {
        'page_title': 'Legal & Immigration Guidance',
        'page_description': 'Expert guidance and trusted referrals to help you navigate the complexities of international law and immigration processes.',
        'services': services,
    }
    return render(request, 'main/legal_and_immigration_guidance.html', context)


# ============================================
# CONSULAR ASSISTANCE - SUB-PAGES
# ============================================

def consular_press_releases(request):
    """
    Render Press Releases sub-page within Consular Assistance.
    Built-in static content for now - can be extended with database later.
    """
    page_instance, _ = Page.objects.get_or_create(page_name='Consular - Press Releases')
    
    # Sample press releases data structure (can be enhanced with database later)
    press_releases = [
        {
            'date': 'September 25, 2025',
            'title': 'DC48K Launches New Financial Literacy Program in Partnership with Diaspora Bank',
            'summary': 'A comprehensive financial literacy initiative designed to improve financial management skills among diaspora members.',
        },
        {
            'date': 'August 15, 2025',
            'title': 'Key Updates to Consular Assistance Services',
            'summary': 'Streamlined appointment booking and expanded legal consultation services now available.',
        },
    ]
    
    context = {
        'title': 'Press Releases',
        'page': page_instance,
        'press_releases': press_releases,
    }
    return render(request, 'main/consular/press_releases.html', context)


def consular_embassy_news(request):
    """
    Render Embassy & Government News sub-page within Consular Assistance.
    """
    page_instance, _ = Page.objects.get_or_create(page_name='Consular - Embassy News')
    
    # Sample embassy news data
    embassy_news = [
        {
            'date': 'October 1, 2025',
            'title': 'Temporary Suspension of e-Passport Services in London Effective October 15',
            'type': 'EMBASSY ALERT',
            'summary': 'The Kenyan Embassy in London will suspend e-Passport services for system upgrade.',
        },
        {
            'date': 'September 20, 2025',
            'title': 'New Visa Processing Requirements',
            'type': 'GOVERNMENT UPDATE',
            'summary': 'Updated documentation requirements for visa applications effective immediately.',
        },
    ]
    
    context = {
        'title': 'Embassy & Government News',
        'page': page_instance,
        'embassy_news': embassy_news,
    }
    return render(request, 'main/consular/embassy_news.html', context)


def consular_community_updates(request):
    """
    Render Community & General Updates sub-page within Consular Assistance.
    """
    page_instance, _ = Page.objects.get_or_create(page_name='Consular - Community Updates')
    
    # Sample community updates data
    community_updates = [
        {
            'date': 'September 18, 2025',
            'title': 'Call for Volunteers: Annual Diaspora Mentorship Drive Now Accepting Applications',
            'type': 'COMMUNITY UPDATE',
            'summary': 'Join us as a mentor or mentee in our flagship diaspora support program.',
        },
        {
            'date': 'September 10, 2025',
            'title': 'Community Resources: New Legal Aid Partner Join Network',
            'type': 'RESOURCE UPDATE',
            'summary': 'Expanded access to affordable legal services through our partner organizations.',
        },
    ]
    
    context = {
        'title': 'Community & General Updates',
        'page': page_instance,
        'community_updates': community_updates,
    }
    return render(request, 'main/consular/community_updates.html', context)


def consular_all_updates(request):
    """
    Render consolidated all updates page combining all consular news categories.
    """
    page_instance, _ = Page.objects.get_or_create(page_name='Consular - All Updates')
    
    context = {
        'title': 'All Updates',
        'page': page_instance,
    }
    return render(request, 'main/consular/all_updates.html', context)


def book_consular_consultation(request):
    """
    Render the Book Consultation form page and handle AJAX POST submissions.
    Saves consultation requests to database and sends confirmation email.
    """
    if request.method == 'POST':
        import json
        import logging
        logger = logging.getLogger(__name__)
        try:
            data = json.loads(request.body)

            # Save the consultation request to database
            service_request = ServiceRequest.objects.create(
                service_type='consular',
                full_name=data.get('full_name', '').strip(),
                email=data.get('email', '').strip(),
                phone=data.get('phone', '').strip(),
                consultation_type=data.get('consultation_type', ''),
                preferred_language=data.get('preferred_language', 'English'),
                location=data.get('location', '').strip(),
                question=data.get('question', '').strip(),
                urgency=data.get('urgency', 'Not Urgent'),
                additional_notes=data.get('additional_notes', '').strip(),
            )

            # Send confirmation email (non-blocking: SMTP failure won't crash the request)
            try:
                send_email(
                    category=0,
                    to_email=[service_request.email],
                    subject='Your Consultation Request Has Been Received - DC48K',
                    html_template='email/consultation_confirmation.html',
                    context={
                        'purpose': 'consultation_confirmation',
                        'full_name': service_request.full_name,
                        'consultation_type': service_request.consultation_type,
                        'urgency': service_request.urgency,
                        'reference_number': f'CR-{service_request.id:05d}',
                        'created_at': service_request.created_at,
                    },
                    from_name="Diaspora County 048 - Consular Services"
                )
            except Exception as e:
                logger.error(f'Failed to send consultation confirmation email to {service_request.email}: {e}')

            return JsonResponse({
                'success': True,
                'message': 'Your consultation request has been submitted. We will contact you shortly.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    context = {
        'title': 'Book a Consultation',
    }
    return render(request, 'main/consular/book_consultation.html', context)


# ============================================
# NEWS SUBSCRIPTION
# ============================================

def confirm_email(request, token):
    subscriber = get_object_or_404(Subscriber, conf_token=token)
    subscriber.confirmed = True
    subscriber.save()

    return render(request, 'main/news/subscription_confirmed.html', {
        'email': subscriber.email
    })


# ============================================
# COMMUNITIES APP VIEWS (MERGED FROM communities app)
# ============================================
from .models import CommunityMember, DirectoryProfile, ForumCategory, CommunityPost, CommentP, EventCalendar
from .forms import CommunityCommentForm, CommunityPostForm, CommunityEventForm, CommunityContactForm
from .utils import send_email


def communities_home(request):
    return render(request, 'main/communities/home.html')


def communities_join(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        agree_to_directory = request.POST.get('agree_to_directory') == 'true'

        if not name or not email:
            messages.error(request, 'Please fill in all required fields')
            return redirect('communities:join')

        if CommunityMember.objects.filter(email=email).exists():
            messages.error(request, 'This email is already registered')
            return redirect('communities:join')

        member = CommunityMember.objects.create(
            name=name,
            email=email,
            is_public_directory=agree_to_directory,
            profession="To be updated",
            region="Global",
            user=request.user if request.user.is_authenticated else None,
        )

        subject = 'Welcome to Our Community!'
        recipient_list = [email]
        context = {'name': name}

        try:
            send_email(
                subject,
                recipient_list,
                context,
                'main/communities/email.html',
                'main/communities/email.txt'
            )
        except Exception:
            pass  # Don't fail if email can't be sent

        messages.success(request, f'Welcome {name}! You have joined the community.')
        return redirect('communities:member_directory')

    return render(request, 'main/communities/join.html')


def _get_community_member_for_user(user):
    """Get the CommunityMember linked to the authenticated user, or None."""
    if not user or not user.is_authenticated:
        return None
    return CommunityMember.objects.filter(user=user).first()


def communities_member_directory(request):
    members = CommunityMember.objects.filter(is_public_directory=True).order_by('-date_joined')

    search_query = request.GET.get('search', '')
    region_filter = request.GET.get('region', '')
    profession_filter = request.GET.get('profession', '')

    if search_query:
        members = members.filter(
            Q(name__icontains=search_query) |
            Q(profession__icontains=search_query) |
            Q(specialization__icontains=search_query) |
            Q(bio__icontains=search_query)
        )
    if region_filter:
        members = members.filter(region__icontains=region_filter)
    if profession_filter:
        members = members.filter(profession__icontains=profession_filter)

    unique_regions = CommunityMember.objects.filter(is_public_directory=True).values_list('region', flat=True).distinct().order_by('region')
    unique_professions = CommunityMember.objects.filter(is_public_directory=True).values_list('profession', flat=True).distinct().order_by('profession')

    for member in members:
        member.is_premium = member.id % 3 == 0

    # Unread message count for inbox badge
    unread_count = 0
    current_member = _get_community_member_for_user(request.user)
    if current_member:
        unread_count = CommunityMessage.objects.filter(recipient=current_member, is_read=False).count()

    context = {
        'members': members,
        'search_query': search_query,
        'region_filter': region_filter,
        'profession_filter': profession_filter,
        'unique_regions': unique_regions,
        'unique_professions': unique_professions,
        'total_members': members.count(),
        'unread_count': unread_count,
        'current_member': current_member,
    }
    return render(request, 'main/communities/member_directory.html', context)


def communities_join_directory(request, member_id):
    if request.method == 'POST':
        member = get_object_or_404(CommunityMember, id=member_id)
        member.is_public_directory = True
        member.save()
        messages.success(request, 'Your profile is now visible in the directory!')
        return redirect('communities:member_directory')
    return redirect('communities:member_directory')


def communities_join_directory_form(request):
    member = None

    # Priority 1: If user is authenticated, find their linked CommunityMember
    if request.user.is_authenticated:
        member = CommunityMember.objects.filter(user=request.user).first()

    # Priority 2: Fall back to session-based member
    if not member:
        member_id = request.session.get('joined_member_id')
        if member_id:
            try:
                member = CommunityMember.objects.get(id=member_id)
            except CommunityMember.DoesNotExist:
                pass

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        profession = request.POST.get('profession', '').strip()
        region = request.POST.get('region', '').strip()
        category = request.POST.get('category', '').strip()
        expertise = request.POST.get('expertise', '').strip()

        errors = []
        if not name: errors.append('Name is required.')
        if not profession: errors.append('Profession is required.')
        if not region: errors.append('Region is required.')

        if errors:
            for e in errors:
                messages.error(request, e)
            context = {
                'name': name, 'profession': profession, 'region': region,
                'categories': ['Tech & IT', 'Legal', 'Finance', 'Healthcare', 'Education', 'Business', 'Creative & Media', 'Engineering', 'Other'],
            }
            return render(request, 'main/communities/join_directory_form.html', context)

        if not member:
            member = CommunityMember.objects.create(
                name=name, profession=profession, region=region,
                is_public_directory=True,
                user=request.user if request.user.is_authenticated else None,
            )
            request.session['joined_member_id'] = member.id
        else:
            member.name = name
            member.profession = profession
            member.region = region
            member.is_public_directory = True
            # Link to user if not already linked
            if request.user.is_authenticated and member.user is None:
                member.user = request.user
            member.save()

        DirectoryProfile.objects.update_or_create(
            community_member=member,
            defaults={
                'full_name': name, 'profession': profession, 'region_city': region,
                'category': category, 'expertise_summary': expertise, 'is_approved': True
            },
        )

        messages.success(request, f'Profile updated for {name}!')
        return redirect('communities:member_directory')

    # Pre-fill from existing member or from user account
    if member:
        default_name = member.name
        default_profession = member.profession
        default_region = member.region
    elif request.user.is_authenticated:
        default_name = f"{request.user.first_name} {request.user.last_name}".strip() or request.user.username
        default_profession = ''
        default_region = ''
    else:
        default_name = ''
        default_profession = ''
        default_region = ''

    context = {
        'name': default_name,
        'profession': default_profession,
        'region': default_region,
        'categories': ['Tech & IT', 'Legal', 'Finance', 'Healthcare', 'Education', 'Business', 'Creative & Media', 'Engineering', 'Other']
    }
    return render(request, 'main/communities/join_directory_form.html', context)


def communities_forum_home(request):
    forum_categories = ForumCategory.objects.all()
    return render(request, 'main/communities/forum_home.html', {'forum_categories': forum_categories})


def communities_category_detail(request, slug):
    from django.core.paginator import Paginator
    category = get_object_or_404(ForumCategory, slug=slug)
    posts = CommunityPost.objects.filter(category=category).order_by('-created_at')
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'main/communities/category_detail.html', {'category': category, 'posts': page_obj})


def communities_view_post(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)
    comments = CommentP.objects.filter(post=post).order_by('-created_at')
    if request.method == 'POST':
        form = CommunityCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('communities:view_post', post_id=post.id)
    else:
        form = CommunityCommentForm()
    return render(request, 'main/communities/view_post.html', {'post': post, 'comments': comments, 'form': form})


@login_required
def communities_create_post(request, slug):
    category = get_object_or_404(ForumCategory, slug=slug)
    if request.method == 'POST':
        form = CommunityPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.category = category
            post.author = request.user
            post.save()
            return redirect('communities:category_detail', slug=category.slug)
    else:
        form = CommunityPostForm()
    return render(request, 'main/communities/create_post.html', {'form': form, 'category': category})


@login_required
def communities_add_comment(request, post_id):
    post = get_object_or_404(CommunityPost, id=post_id)
    if request.method == 'POST':
        form = CommunityCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('communities:view_post', post_id=post.id)
    return redirect('communities:view_post', post_id=post.id)


@login_required
def communities_edit_post(request, post_id):
    """Edit a forum post. Only superuser/staff can edit."""
    post = get_object_or_404(CommunityPost, id=post_id)

    # Permission check: only superuser/staff can edit
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, 'Only administrators can edit posts.')
        return redirect('communities:view_post', post_id=post.id)

    if request.method == 'POST':
        form = CommunityPostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save()
            messages.success(request, f'Post "{post.title}" updated successfully!')
            return redirect('communities:view_post', post_id=post.id)
    else:
        form = CommunityPostForm(instance=post)

    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    return render(request, 'main/communities/edit_post.html', context)


@login_required
def communities_delete_post(request, post_id):
    """Delete a forum post. Only superuser/staff can delete."""
    post = get_object_or_404(CommunityPost, id=post_id)
    category_slug = post.category.slug

    # Permission check: only superuser/staff can delete
    if not request.user.is_superuser and not request.user.is_staff:
        messages.error(request, 'Only administrators can delete posts.')
        return redirect('communities:view_post', post_id=post.id)

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('communities:category_detail', slug=category_slug)

    context = {
        'post': post,
    }
    return render(request, 'main/communities/delete_post.html', context)


def communities_event_calendar(request):
    events = EventCalendar.objects.all().order_by('start_date')
    return render(request, 'main/communities/event_calendar.html', {'events': events})


def communities_create_event(request):
    if request.method == 'POST':
        form = CommunityEventForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event created successfully')
            return redirect('communities:event_calendar')
        else:
            messages.error(request, 'There was an error in your form.')
    else:
        form = CommunityEventForm()
    return render(request, 'main/communities/create_event.html', {'form': form})


def communities_event_detail(request, id):
    event = get_object_or_404(EventCalendar, id=id)
    return render(request, 'main/communities/event_detail.html', {'event': event})


def communities_edit_event(request, id):
    event = get_object_or_404(EventCalendar, id=id)
    if request.method == 'POST':
        form = CommunityEventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Event updated successfully!")
            return redirect('communities:event_detail', id=event.id)
        else:
            messages.error(request, "There was an error with your form. Please try again.")
    else:
        form = CommunityEventForm(instance=event)
    return render(request, 'main/communities/edit_event.html', {'form': form, 'event': event})


def communities_delete_event(request, id):
    try:
        event = EventCalendar.objects.get(id=id)
    except EventCalendar.DoesNotExist:
        messages.error(request, "This event has already been deleted or does not exist.")
        return redirect('communities:event_calendar')

    if request.method == 'POST':
        event.delete()
        messages.success(request, "Event deleted successfully!")
        return redirect('communities:event_calendar')
    return render(request, 'main/communities/delete_event.html', {'event': event})


def communities_contact_view(request):
    if request.method == 'POST':
        form = CommunityContactForm(request.POST)
        if form.is_valid():
            contact = form.save()
            context = {'name': contact.name, 'email': contact.email, 'message': contact.message}
            subject = f'Hello {contact.name}, thank you for contacting us!'
            recipient_list = [contact.email]
            try:
                send_email(
                    subject=subject,
                    recipient_list=recipient_list,
                    context=context,
                    html_template='main/communities/contact_response.html',
                    plain_template='main/communities/contact_response.txt'
                )
            except Exception:
                pass  # Don't fail if email can't be sent
            return redirect('communities:home')
    else:
        form = CommunityContactForm()
    return render(request, 'main/communities/contact_form.html', {'form': form})


# ============================================
# COMMUNITY MESSAGING VIEWS
# ============================================

@login_required
def communities_message_compose(request, recipient_id):
    """Send a message to a community member."""
    sender = _get_community_member_for_user(request.user)
    if not sender:
        messages.warning(request, 'You need a community profile to send messages. Please join the directory first.')
        return redirect('communities:join_directory_form')

    recipient = get_object_or_404(CommunityMember, id=recipient_id)

    if sender == recipient:
        messages.error(request, 'You cannot send a message to yourself.')
        return redirect('communities:member_directory')

    if request.method == 'POST':
        form = CommunityMessageForm(request.POST)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = sender
            msg.recipient = recipient
            msg.save()
            messages.success(request, f'Message sent to {recipient.name}!')
            return redirect('communities:message_inbox')
    else:
        form = CommunityMessageForm()

    context = {
        'form': form,
        'recipient': recipient,
    }
    return render(request, 'main/communities/message_compose.html', context)


@login_required
def communities_message_inbox(request):
    """View received messages."""
    member = _get_community_member_for_user(request.user)
    if not member:
        messages.warning(request, 'You need a community profile to view messages. Please join the directory first.')
        return redirect('communities:join_directory_form')

    inbox_messages = CommunityMessage.objects.filter(recipient=member).order_by('-created_at')
    unread_count = inbox_messages.filter(is_read=False).count()

    context = {
        'inbox_messages': inbox_messages,
        'unread_count': unread_count,
        'active_tab': 'inbox',
    }
    return render(request, 'main/communities/message_inbox.html', context)


@login_required
def communities_message_sent(request):
    """View sent messages."""
    member = _get_community_member_for_user(request.user)
    if not member:
        messages.warning(request, 'You need a community profile to view messages. Please join the directory first.')
        return redirect('communities:join_directory_form')

    sent_messages = CommunityMessage.objects.filter(sender=member).order_by('-created_at')

    context = {
        'sent_messages': sent_messages,
        'active_tab': 'sent',
    }
    return render(request, 'main/communities/message_sent.html', context)


@login_required
def communities_message_detail(request, message_id):
    """Read a single message."""
    member = _get_community_member_for_user(request.user)
    if not member:
        messages.warning(request, 'You need a community profile to view messages.')
        return redirect('communities:join_directory_form')

    msg = get_object_or_404(CommunityMessage, id=message_id)

    # Authorization: only sender or recipient can view
    if msg.sender != member and msg.recipient != member:
        messages.error(request, 'You do not have permission to view this message.')
        return redirect('communities:message_inbox')

    # Mark as read if recipient is viewing
    if msg.recipient == member and not msg.is_read:
        msg.is_read = True
        msg.save(update_fields=['is_read'])

    # Get thread: replies to this message
    replies = CommunityMessage.objects.filter(parent_message=msg).order_by('created_at')

    context = {
        'msg': msg,
        'replies': replies,
        'is_recipient': msg.recipient == member,
    }
    return render(request, 'main/communities/message_detail.html', context)


@login_required
def communities_message_reply(request, message_id):
    """Reply to a received message."""
    member = _get_community_member_for_user(request.user)
    if not member:
        messages.warning(request, 'You need a community profile to reply to messages.')
        return redirect('communities:join_directory_form')

    original = get_object_or_404(CommunityMessage, id=message_id)

    # Authorization: only sender or recipient can reply
    if original.sender != member and original.recipient != member:
        messages.error(request, 'You do not have permission to reply to this message.')
        return redirect('communities:message_inbox')

    # Reply goes to the other party
    reply_to = original.sender if original.recipient == member else original.recipient

    if request.method == 'POST':
        form = CommunityMessageForm(request.POST)
        if form.is_valid():
            reply_msg = form.save(commit=False)
            reply_msg.sender = member
            reply_msg.recipient = reply_to
            reply_msg.parent_message = original
            if not reply_msg.subject and original.subject:
                reply_msg.subject = f"Re: {original.subject}"
            reply_msg.save()
            messages.success(request, f'Reply sent to {reply_to.name}!')
            return redirect('communities:message_detail', message_id=original.id)
    else:
        initial_subject = f"Re: {original.subject}" if original.subject else ''
        form = CommunityMessageForm(initial={'subject': initial_subject})

    context = {
        'form': form,
        'recipient': reply_to,
        'original': original,
        'is_reply': True,
    }
    return render(request, 'main/communities/message_compose.html', context)
