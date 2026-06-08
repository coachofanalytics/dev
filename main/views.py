from django.shortcuts import redirect, render
from django.urls import reverse
from django.http import JsonResponse
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
# CONSULAR ASSISTANCE
# ============================================

def consular_assistance(request):
    page = ConsularAssistancePage.objects.first()
    context = { 'page': page, }
    return render(request, "main/consular_assistance.html", context)


def consular_information_updates(request):
    """
    Render the Consular Assistance - Information and Updates page.
    """
    page_instance, _ = Page.objects.get_or_create(page_name='Consular - Information and Updates')
    description = Description.objects.filter(page=page_instance)

    context = {
        'description': description,
        'title': 'Information and Updates',
    }

    return render(request, 'main/consular/information_updates.html', context)


def legal_immigration_guidance(request):
    from .models import LegalService

    services = LegalService.objects.filter(is_active=True).order_by('order')

    context = {
        'page_title': 'Legal & Immigration Guidance',
        'page_description': 'Expert guidance and trusted referrals to help you navigate the complexities of international law and immigration processes.',
        'services': services,
    }
    return render(request, 'main/legal_and_immigration_guidance.html', context)


def consular_press_releases(request):
    """
    Render Press Releases sub-page within Consular Assistance.
    """
    page_instance, _ = Page.objects.get_or_create(page_name='Consular - Press Releases')

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
                    html_template='main/email/consultation_confirmation.html',
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
                'message': 'Your consultation request has been submitted. We will contact you shortly. A confirmation email has been sent.'
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