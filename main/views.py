from django.shortcuts import redirect, render
from datetime import datetime,date,timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
    CreateView,
    UpdateView,
)
from .models import * #Assets,Description, News, Page, Service, SubService,Team
from accounts.models import CustomerUser
from .utils import image_view,path_values,generate_chatbot_response
from main.forms import ContactForm, GetHelpForm, GovernanceForm,PaymentForm
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site

from mail.custom_email import send_email
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from coda_project import settings

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

from django.shortcuts import render, get_object_or_404
from .models import Page, Description, Service, SubService, News

# def layout(request):
#     page_instance = get_object_or_404(Page, page_name='Home')
#     return render(request, 'main/home_templates/home.html', {'page': page_instance})








from django.shortcuts import get_object_or_404, render
from .models import Page, Description, Service, SubService, News
from .forms import ContactForm

def layout(request):
    print("In layout")
    page_instance = Page.objects.filter(page_name='Home').first()
    description = Description.objects.filter(page=page_instance)
    service = Service.objects.all()
    subservice = SubService.objects.all()
    news = News.objects.all().order_by('-published_date')[:3]

    if request.method == "POST":
        form = ContactForm(request.POST, request.FILES)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.task = 'NA'
            instance.plan = 'NA'
            instance.trained_by = request.user
            instance.save()
            return render(
                request,
                "main/errors/generalerrors.html",
                {"message": "Thank you, we will get back to you within 48 hours."}
            )
    else:
        form = ContactForm()

    context = {
        "form": form,
        "description": description,
        "service": service,
        "news": news,
        "subservice": subservice
    }

    return render(
        request,
        "main/home_templates/home.html",
        context
    )






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
    





def team_list(request):
    teams = Team.objects.all()
    print('info=============',teams)
    return render(request, 'main/snippets_templates/table/team.html', {'info': teams})






    

from django.shortcuts import render
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
    deputy_governor = Governance.objects.filter(title__iexact="Deputy Governor").first()

    # Get all members for the selected category except the Governor
    govern = Governance.objects.filter(governance_category=category).exclude(title__in=["Governor", "Deputy Governor"])

    categories = [
        'Global Executive Committee',
        'Regional Administration',
        'County Assembly Administration'
    ]

    return render(request, 'main/governance_list.html', {
        'govern': govern,
        'governor': governor,
        'deputy_governor': deputy_governor,
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



def governance_delete(request, pk):
   
    govern = get_object_or_404(Governance, pk=pk)

    if request.method == 'POST':

        govern.delete()
        return redirect('main:governance_list')

    return render(request, 'main/governance_confirm_delete.html', {'govern':govern})


from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Payment


def payment_history(request):
    payments = Payment.objects.filter(user=request.user)
    print('info ============', payments)
    return render(request, "main/snippets_templates/table/peyments.html", {"info": payments} )
         
        
      
    

@login_required
def payment_create(request):
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.save()
            messages.success(request, "Payment successfully created!")
            return redirect("main:payment_history")
    else:
        form = PaymentForm()
    return render(request, "main/snippets_templates/table/payment_create.html", {"form": form})




def payment_update(request, pk):
    payment = get_object_or_404(Payment, pk=pk, user=request.user)
    if request.method == "POST":
        form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, "Payment updated successfully!")
            return redirect("main:payment_history")
    else:
        form = PaymentForm(instance=payment)
    return render(request, "main/snippets_templates/table/payments_update.html", {"form": form, "payment": payment})