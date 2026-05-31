from django.shortcuts import redirect, render, get_object_or_404
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView,
    UpdateView,
)
#<<<<<<< 25.10_DC48_UAT_UO
from .models import Assets,Description, News, Page, Service, SubService,Team, SafetyAlertSubscription, EmergencyHotline, StaffContact, InsurancePlan, AIRecommendationRule, ExpertInquiry, ConsularAssistancePage


from django.db.models import Q


from .models import Scholarship, Donation_organisation, ContactMessage, Testimonial


from accounts.models import CustomerUser


from .models import Assets,Description, News, Page, Service, SubService,Team, Donation_organization, MedicalResourceInquiry,Governance
from accounts.models import CustomerUser
from .utils import image_view,path_values
from .forms import ContactForm, DonorForm, MessageForm,ScholarshipSearchForm


from django.views.decorators.csrf import csrf_exempt
from main.forms import ContactForm, GovernanceForm


from django.contrib.auth import get_user_model


from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse, HttpResponse
from django.core.mail import send_mail
from django.utils.html import strip_tags



from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
import csv

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



    page_instance, _ = Page.objects.get_or_create(page_name='Home')
    description = Description.objects.filter(page=page_instance)


    # Define page_instance for the home page or desired page
    page_instance = Page.objects.filter(page_name='Home').first()
    description = Description.objects.filter(page=page_instance)


    # Ensure a Page instance exists for the Home page; if it doesn't, create a minimal one
    page_instance, _ = Page.objects.get_or_create(page_name='Home')
    description = Description.objects.filter(page = page_instance)


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
    """Render a mock course registration page where users can view course types,
    see prices, and interact with a demo PayPal-style button. The page also
    includes a client-side form to add course types dynamically (no server save).
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
    # If requested as a partial (AJAX in-page load), return only the fragment
    if request.GET.get('partial') == '1':
        return render(request, 'main/education/course_register_fragment.html', {'courses': courses})
    return render(request, 'main/education/course_register.html', {'courses': courses})


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





# Scholarship views

def scholarship_search(request):
    scholarships = Scholarship.objects.all()
    form = ScholarshipSearchForm(request.GET or None)

    # Direct GET filters (used by integration tests)
    level = request.GET.get('level')
    field = request.GET.get('field')

    if level and level != 'All':
        scholarships = scholarships.filter(level=level)

    if field and field != 'All':
        scholarships = scholarships.filter(field=field)

    if form.is_valid():
        data = form.cleaned_data
        # apply filter
        if data['search_keyword']:
            scholarships = scholarships.filter(
                Q(title__icontains=data['search_keyword']) |
                Q(provider__icontains=data['search_keyword']) 
            )
        if data['filter_level'] and data['filter_level'] != 'All':
            scholarships = scholarships.filter(level=data['filter_level'])

        if data['filter_field'] and data['filter_field'] != 'All':
            scholarships = scholarships.filter(field=data['filter_field'])

        if data['filter_location'] and data['filter_location'] != 'All':
            scholarships = scholarships.filter(location=data['filter_location'])

        if data['filter_status']:
            scholarships = scholarships.filter(status='Closing soon')
    context = {
        'scholarships': scholarships,
        'form': form,
        'result_count': scholarships.count(),
    }
    return render(request, 'scholarship_app/scholarship_search.html',context)


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
    # Changed from 'list.html' to 'governance_list.html'
    return render(request, 'main/governance/governance_list.html', context)

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

    from django.shortcuts import render

# views.py
def legal_guidance_landing_page(request):
    context = {
        'hero_title': "Legal & Immigration Guidance",
        'hero_subtitle': "Expert guidance and trusted referrals to help you navigate the complexities of international law and immigration processes.",
        'cta_text': "Book a Legal Consultation",
        'hero_image': "/static/img/legal-hero.jpg",  # Replace with your actual image path
    }
    return render(request, 'main/legal_guidance_landing_page.html', context)