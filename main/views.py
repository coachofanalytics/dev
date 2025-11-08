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
from .models import Assets,Description, News, Page, Service, SubService,Team, SafetyAlertSubscription, EmergencyHotline, StaffContact, EmergencyHelpActivation
from accounts.models import CustomerUser
from .utils import image_view,path_values
from main.forms import ContactForm
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.utils.html import strip_tags
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
    page_instance, _ = Page.objects.get_or_create(page_name='Home')
    description = Description.objects.filter(page=page_instance)
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




    

from django.shortcuts import render
from .models import Service,ContactUs

def service_list(request):
    services = Service.objects.all()  # Fetch all services and related subservices
    return render(request, 'main/services.html', {'services': services})







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
    EmergencyHelpActivation.objects.create(
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


