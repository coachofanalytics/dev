from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
import json
import csv
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView,
    UpdateView,
)
from .models import * #Assets,Description, News, Page, Service, SubService,Team
from accounts.models import CustomerUser
from .utils import generate_chatbot_response
from main.forms import ContactForm, GetHelpForm, GovernanceForm
from django.contrib.auth import get_user_model

from mail.custom_email import send_email
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from coda_project import settings
from django.contrib import messages

#new code cece's assignment
from .models import History, ContactUs


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
    print("In layout")
    print("news table")
    page_instance = Page.objects.get(page_name='Home')
    description = Description.objects.filter(page = page_instance)
    service = Service.objects.all()
    subservice = SubService.objects.all()
    news = News.objects.all().order_by('-published_date')[:3] 
  
   
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




# def layout(request):
#     page_instance = Page.objects.get(page_name='Home')
#     description = Description.objects.filter(page = page_instance)
#     service = Service.objects.all()
#     subservice = SubService.objects.all()
#     news = News.objects.all().order_by('-published_date')[:3] 
#     print(news)
   
#     if request.method == "POST":
#         form = ContactForm(request.POST, request.FILES)
#         message=f'Thank You, we will get back to you within 48 hours.'
#         context={
#             "message":message,
#             # "link":SITEURL+'/management/companyagenda'
#         }
#         if form.is_valid():
#             # form.save()
#             instance=form.save(commit=False)
#             # instance.client_name='admin',
#             instance.task='NA',
#             instance.plan='NA',
#             instance.trained_by=request.user
#             instance.save()
#             # return redirect("management:assessment")
#             return render(request, "main/errors/generalerrors.html",context)
#     else:
#         form = ContactForm()
#     context={
#             # "posts":posts,
#             "form": form,
#             'description': description,
#             'service': service,
#             'news':news,
#             'subservice':subservice
#         }
#     return render(request, "main/home_templates/home.html",context)

def history(request):
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
    





def team_list(request):
    teams = Team.objects.all()
    print('info=============',teams)
    return render(request, 'main/snippets_templates/table/team.html', {'info': teams})






    

from .models import Service,Gallery,ContactUs

def service_list(request):
    services = Service.objects.all()  # Fetch all services and related subservices
    return render(request, 'main/services.html', {'services': services})


def gallery_list(request):
    images = Gallery.objects.all()
    return render(request, 'main/Gallery/gallery.html', {'images': images})



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
        # return render(request,url, context)
        # return render(request, 'main/messages/message.html', context)
    except Exception as e:
        error_message = (
            f'Hi {request.user.first_name}, Your message to '
            f'{request.user.email} was unsuccessful. '
            f'Please try again or contact info@diasporacounty48.org. Thank You. '
            f'Error: {e}'
        )
        return render(request, 'main/messages/message.html', {"message": error_message})

    # return render(request, url, context)




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



def governance_list(request):
    category = request.GET.get('category', 'Global Executive Committee')

    # Always get the Governor regardless of selected category
    governor = Governance.objects.filter(title__iexact="Governor").first()
    # deputy_governor = Governance.objects.filter(title__iexact="Deputy Governor").first()

    # Get all members for the selected category except the Governor
    govern = Governance.objects.filter(governance_category=category).exclude(title__iexact="Governor")

    govern_order = sorted(govern, key=lambda member:member.ui_order)

    categories = [
        'Global Executive Committee',
        'Regional Administration',
        'County Assembly Administration'
    ]


    return render(request, 'main/governance_list.html', {
        # 'govern': govern,
        "govern_order": govern_order,
        'governor': governor,
        # 'deputy_governor': deputy_governor,
        'selected_category': category,
        'categories': categories
    })

    


def governance_update(request, pk):

    govern = get_object_or_404(Governance, pk=pk)

   
    if request.method == 'POST':
        form = GovernanceForm(request.POST, instance=govern)
        if form.is_valid():
            form.save() 
            return redirect('main:governance_list')  

    else:
        form = GovernanceForm(instance=govern)

    return render(request, 'main/governance_update.html',{'form':form})



def governance_create(request):
    if request.method == 'POST':
        form = GovernanceForm(request.POST)
        if form.is_valid():
            #impliment API call to populate description field automantically
            # API_description = generate_chatbot_response()
            # form.description = API_description
            form.save()
            return redirect('main:governance_list')

    else:
        form = GovernanceForm() 

    return render(request, 'main/governance_create.html',{'form':form})



def governance_create(request):
    print("Entered governance_create view")

    if request.method == 'POST':
        print("Request method is POST")
        form = GovernanceForm(request.POST)
        print("Form data received:")
        for field_name, field_value in request.POST.items():
            print(f"{field_name}: {field_value}")

        if form.is_valid():
            print("Form is valid")
            try:
                title = form.cleaned_data.get('title')
                if not title:
                    print("Title is missing in cleaned_data")
                    raise ValueError("Title is missing for generating the description.")
                
                message = f"Provide a brief description of around 50 words for the DC48K {title}"
                print(f"Generated message for AI: {message}")

                try:
                    api_description = generate_chatbot_response(message)
                    print(f"API description generated: {api_description}")
                except Exception as api_exception:
                    print(f"Error while calling generate_chatbot_response: {api_exception}")
                    # api_description = "Please provide a manual description."
                    api_description = f"This is the {form.instance.title} under the {form.instance.governance_category}"
                    

                # Set description and save form instance
                instance = form.save(commit=False)
                instance.description = api_description
                instance.save()
                print("Form instance saved successfully")

                return redirect('main:governance_list')

            except Exception as e:
                print(f"Error while processing form submission: {e}")
        else:
            print("Form is invalid")
            print(f"Form errors: {form.errors}")

    else:
        print("Request method is not POST, initializing empty form")
        form = GovernanceForm()

    # Optional: for debugging GET requests or invalid POSTs
    return render(request, 'main/governance_create.html',{'form':form})

########################################################################################################################
# def governance_create(request):
#     if request.method == 'POST':
#         form = GovernanceForm(request.POST)
#         message = f"Provide a brief description of around 50 words for the DC48K {form.title}"
#         if form.is_valid():
#             # message = f"Provide a brief description of around 50 words for the DC48K{form.title}"
#             try:
#                 api_description = generate_chatbot_response(message)
#             except Exception as e:
#                 api_description = "Please provide a manual description."
#             form.description = api_description
#             form.save()
#             return redirect('main:governance_list')

#     else:
#         form = GovernanceForm() 

#     return render(request, 'main/governance_create.html',{'form':form})



def governance_delete(request, pk):
   
    govern = get_object_or_404(Governance, pk=pk)

    if request.method == 'POST':

        govern.delete()
        return redirect('main:governance_list')

    return render(request, 'main/governance_confirm_delete.html', {'govern':govern})


def organization_list_view(request):
    organizations = DonationOrganization.objects.all()
    return render(request, 'main/snippets_templates/table/donation_list.html', {'organizations':organizations})


def ourhistory(request):
    history_years = History.objects.all()
    context = {
        "history_years": history_years
    }
    return render(request, "main/ourhistory.html", context)


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

    return render(reqest, "main/home_templates/home.html")


# ============================================
# HEALTHCARE INFORMATION
# ============================================

def healthcare_info(request):
    """Render the Healthcare Information page."""
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


def medical_resource_form(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        MedicalResourceInquiry.objects.create(name=name, email=email, message=message)
        return redirect('main:healthcare_info')
    return render(request, 'main/data/medical_resource_form.html')


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

    if specialty_q:
        doctors = doctors.filter(specialty__icontains=specialty_q) | \
                  doctors.filter(title__icontains=specialty_q) | \
                  doctors.filter(name__icontains=specialty_q)

    if location_q:
        doctors = doctors.filter(location_city__icontains=location_q) | \
                  doctors.filter(location_country__icontains=location_q)

    if categories:
        filtered_ids = []
        for doc in doctors:
            if any(cat in doc.categories for cat in categories):
                filtered_ids.append(doc.pk)
        doctors = doctors.filter(pk__in=filtered_ids)

    if languages:
        filtered_ids = []
        for doc in doctors:
            if any(lang in doc.languages for lang in languages):
                filtered_ids.append(doc.pk)
        doctors = doctors.filter(pk__in=filtered_ids)

    if sort_by == 'rating':
        doctors = doctors.order_by('-rating', '-review_count')
    elif sort_by == 'reviews':
        doctors = doctors.order_by('-review_count', '-rating')
    elif sort_by == 'name':
        doctors = doctors.order_by('name')
    else:
        doctors = doctors.order_by('-rating', '-review_count')

    total_count = doctors.count()

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
            ('name', 'Name (A-Z)'),
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
    from django.core.mail import send_mail
    doctor = get_object_or_404(Doctor, pk=pk)

    session_key = f'booking_attempts_{pk}'
    attempts = request.session.get(session_key, 0)
    if attempts >= 5:
        return JsonResponse({'success': False, 'error': 'Too many requests. Please try again later.'}, status=429)

    form = AppointmentRequestForm(request.POST)

    if form.is_valid():
        appointment = form.save(commit=False)
        appointment.doctor = doctor
        appointment.save()

        request.session[session_key] = attempts + 1

        try:
            send_mail(
                subject=f'New Appointment Request - {doctor.name}',
                message=f'New appointment request received:\n\nDoctor: {doctor.name}\nPatient: {appointment.full_name}\nEmail: {appointment.email}\nDate: {appointment.preferred_date}\nTime: {appointment.get_preferred_time_display()}\nReason: {appointment.reason}\n\nLog in to the admin to respond.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=True,
            )
            send_mail(
                subject=f'Appointment Request Received - {doctor.name}',
                message=f'Dear {appointment.full_name},\n\nThank you for submitting an appointment request with {doctor.name}.\n\nYour request details:\n  Date: {appointment.preferred_date}\n  Time: {appointment.get_preferred_time_display()}\n  Reason: {appointment.reason}\n\nThe provider will review your request and contact you at {appointment.email} to confirm availability.\n\n- Diaspora County 48',
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


def insurance_support(request):
    """Main insurance support page view"""
    insurance_plans = InsurancePlan.objects.filter(
        is_active=True
    ).order_by('display_order', '-score')

    featured_plans = insurance_plans[:3]

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
    """API endpoint for AI recommendations"""
    try:
        data = json.loads(request.body)
        age = data.get('age')
        residence = data.get('residence')
        priority = data.get('priority')

        rule = AIRecommendationRule.objects.filter(
            age_bracket=age,
            residence=residence,
            priority=priority,
            is_active=True
        ).select_related('recommended_plan').first()

        if rule:
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
        else:
            alternative_plan = InsurancePlan.objects.filter(
                is_active=True
            ).order_by('-score').first()

            if alternative_plan:
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
            else:
                response_data = {
                    'success': False,
                    'error': 'No insurance plans available'
                }

        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    except Exception as e:
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

        inquiry = ExpertInquiry.objects.create(
            full_name=data.get('full_name'),
            email=data.get('email'),
            phone=data.get('phone', ''),
            question=data.get('question'),
            interested_plan_id=data.get('plan_id') if data.get('plan_id') else None
        )

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
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="insurance_comparison.csv"'

    plans = InsurancePlan.objects.filter(is_active=True).order_by('display_order', '-score')

    writer = csv.writer(response)

    writer.writerow([
        'Provider',
        'Plan Name',
        'Global Network',
        'Max Benefit',
        'Evacuation Coverage',
        'Rating (out of 10)'
    ])

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