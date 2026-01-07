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
#<<<<<<< 25.10_DC48_UAT_UO
from .models import Assets,Description, News, Page, Service, SubService,Team, SafetyAlertSubscription, EmergencyHotlines, StaffContact, EmergencyHelpActivations
#=======
from django.db.models import Q
#<<<<<<< HEAD
#<<<<<<< HEAD
from .models import Assets,Description, News, Page, Service,Scholarship, SubService,Team,Donation_organisation, ContactMessage
#>>>>>>> 25.10_DC48_UAT_ND
#=======
from .models import (
    Assets, Description, News, Page, Service, Scholarship, SubService, Team,
    Donation_organisation, Donation_organization, ContactMessage, MedicalResourceInquiry
)
#>>>>>>> origin/25.11_DC48K_UAT_FN
from accounts.models import CustomerUser
from .utils import image_view, path_values
from django.views.decorators.csrf import csrf_exempt
from .forms import ContactForm, DonorForm, MessageForm, ScholarshipSearchForm
from django.contrib.auth import get_user_model
#<<<<<<< 25.10_DC48_UAT_UO
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.utils.html import strip_tags
#=======

from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
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

#>>>>>>> 25.10_DC48_UAT_ND
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
    hotlines = EmergencyHotlines.objects.filter(is_active=True).order_by("sort_order", "id")
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




    

from django.shortcuts import render
from .models import Service,ContactUs
from django.db.models import Q
from .models import Scholarship
from .forms import ScholarshipSearchForm,DocumentRequestForm

def service_list(request):
    services = Service.objects.all()  # Fetch all services and related subservices
    return render(request, 'main/services.html', {'services': services})


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
    EmergencyHelpActivations.objects.create(
        event_type="callback_requested",
        name=name,
        phone=phone,
        location=location,
        notes=notes,
        ip_address=ip,
    )

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
        message=f'Thank You for your donation, we will get back to you within 48 hours.'
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
        message=f'Thank You, we will get back to you within 48 hours.'
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
    # Flag to indicate a successful mentorship request submission
    mentorship_success = request.GET.get('mentorship') == 'success'
    context = {
        'initial_view': initial_view,
        'mentorship_success': mentorship_success,
    }
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


# Scholarship search view — renders the scholarship search template and handles basic filters
def scholarship_search(request):
    scholarships = Scholarship.objects.all()
    form = ScholarshipSearchForm(request.GET or None)
    if form.is_valid():
        data = form.cleaned_data
        # keyword search
        kw = data.get('search_keyword')
        if kw:
            scholarships = scholarships.filter(
                Q(title__icontains=kw) | Q(provider__icontains=kw)
            )
        # level filter
        level = data.get('filter_level')
        if level:
            scholarships = scholarships.filter(level=level)
        # field filter
        field = data.get('filter_field')
        if field:
            scholarships = scholarships.filter(field=field)
        # location filter
        location = data.get('filter_location')
        if location:
            scholarships = scholarships.filter(location=location)
        # status
        if data.get('filter_status'):
            scholarships = scholarships.filter(status__icontains='Closing')
    context = {
        'scholarships': scholarships,
        'form': form,
        'result_count': scholarships.count(),
    }
#<<<<<<< HEAD
    return render(request, 'scholarship_app/scholarship_search.html',context)
#>>>>>>> 25.10_DC48_UAT_ND
#=======
    return render(request, 'scholarship_app/scholarship_search.html', context)

# document request view
def services_spa(request):
     form = DocumentRequestForm()
     return render(request, 'main/index.html', {'form': form})

@require_POST
def submit_reques(request):
    form = DocumentRequestForm(request.POST)
    if form.is_valid():
        try:
            document_request = form.save(commit=False)
            document_request.status = 'Pending'
            document_request.save()
            success_message = (
                f"Thank you, {document_request.full_name}."
                f"your request for {document_request.get_document_type_display()} has been submitted successfully."
                f"We will get back to you at {document_request.email} as soon as possible."
            )
            return JsonResponse({
                'success': True,
                'message': success_message,
                'redirect_id': document_request.id,
            })
           
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error':'An error occurred while processing your request. Please try again later.',
            },status=400)
    else:
        error = {}
        for field, error_list in form.errors.items():
            error[field] = [str(error) for error in error_list]
        return JsonResponse({
            'success': False,
            'error': error,
        },status=400)

