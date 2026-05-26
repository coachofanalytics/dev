from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from django.core.paginator import Paginator
import feedparser
import random
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView,
    UpdateView,
)
from .models import * #Assets,Description, News, Page, Service, SubService,Team
from accounts.models import CustomerUser
from .utils import generate_chatbot_response
from main.forms import ContactForm, GetHelpForm, GovernanceForm, ScholarshipSearchForm, ScholarshipForm, TrainingCourseForm
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
# EDUCATION & TRAINING
# ============================================

def education_landing(request):
    initial_view = request.GET.get('view', 'landing')
    context = {'initial_view': initial_view}
    return render(request, 'main/education/education.html', context)


def request_mentorship(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            if request.user.is_authenticated:
                instance.user = request.user
            if not instance.topic:
                instance.topic = 'Mentorship Request'
            instance.save()
            return redirect(reverse('main:education_landing') + '?view=landing&mentorship=success')
    else:
        initial = {'topic': 'Mentorship Request'}
        form = ContactForm(initial=initial)
    return render(request, 'main/education/mentorship_form.html', {'form': form})


def course_register(request):
    courses = [
        {'id': 101, 'title': 'Modern Web Development (React & Node)', 'category': 'Digital Skills', 'duration': '12 Weeks', 'format': 'Online Live', 'price': 150.00},
        {'id': 102, 'title': 'Financial Literacy for Diaspora Investors', 'category': 'Finance & Business', 'duration': '4 Weeks', 'format': 'Online Self-Paced', 'price': 40.00},
        {'id': 103, 'title': 'Entrepreneurship & Small Business Management', 'category': 'Business', 'duration': '8 Weeks', 'format': 'Blended', 'price': 95.00},
    ]

    selected_object = None
    selected_type = None

    course_id = request.GET.get('course_id', None)
    if course_id:
        try:
            selected_object = TrainingCourse.objects.get(id=int(course_id))
            selected_type = 'course'
        except (TrainingCourse.DoesNotExist, ValueError):
            selected_object = None

    scholarship_id = request.GET.get('scholarship_id', None)
    if scholarship_id and not selected_object:
        try:
            selected_object = Scholarship.objects.get(id=int(scholarship_id))
            selected_type = 'scholarship'
        except (Scholarship.DoesNotExist, ValueError):
            selected_object = None

    if request.GET.get('partial') == '1':
        return render(request, 'main/education/course_register_fragment.html', {
            'courses': courses, 'selected_object': selected_object, 'selected_type': selected_type,
        })

    return render(request, 'main/education/course_register.html', {
        'courses': courses, 'selected_object': selected_object, 'selected_type': selected_type,
    })


def scholarship_search(request):
    scholarships = Scholarship.objects.all()
    form = ScholarshipSearchForm(request.GET or None)

    if form.is_valid():
        data = form.cleaned_data
        keyword = data.get("search_keyword")
        if keyword:
            scholarships = scholarships.filter(Q(title__icontains=keyword) | Q(provider__icontains=keyword))

        currency = data.get("filter_currency")
        if currency:
            scholarships = scholarships.filter(amount_value__isnull=False, amount_currency=currency)

        level = data.get("filter_level")
        if level:
            scholarships = scholarships.filter(level=level)

        field = data.get("filter_field")
        if field:
            scholarships = scholarships.filter(field=field)

        location = data.get("filter_location")
        if location:
            scholarships = scholarships.filter(location=location)

        if data.get("filter_status"):
            scholarships = scholarships.filter(status=Scholarship.Status.CLOSING_SOON)

    context = {
        'scholarships': scholarships,
        'form': form,
        'result_count': scholarships.count(),
    }
    return render(request, 'scholarship_app/scholarship_search.html', context)


@login_required
def add_scholarship(request):
    if request.method == "POST":
        form = ScholarshipForm(request.POST)
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
        form = ScholarshipForm(instance=scholarship)
    return render(request, 'scholarship_app/scholarship_edit.html', {'form': form})


@login_required
def scholarship_delete(request, pk):
    scholarship = get_object_or_404(Scholarship, pk=pk, created_by=request.user)
    if request.method == "POST":
        scholarship.delete()
        return redirect('main:add_scholarship')
    return render(request, 'scholarship_app/scholarship_delete.html', {'scholarship': scholarship})


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
            "title": s.title, "provider": s.provider, "level": s.level,
            "field": s.field, "location": s.location, "amount": s.amount,
            "deadline": s.deadline.strftime("%Y-%m-%d") if s.deadline else None,
            "status": s.status
        })

    return JsonResponse({"scholarships": data, "count": len(data)})


def education_training(request):
    courses = TrainingCourse.objects.all()

    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) | Q(course_code__icontains=search_query) |
            Q(description__icontains=search_query) | Q(instructor__icontains=search_query)
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
        'page_obj': page_obj, 'paginator': paginator,
        'search_query': search_query, 'category_filter': category_filter,
        'format_filter': format_filter, 'status_filter': status_filter,
    }
    return render(request, 'main/education/training_skills.html', context)


def ai_course_discovery(request):
    courses = []
    seen = set()

    mit_feeds = [
        "https://ocw.mit.edu/courses/rss.xml",
        "https://ocw.mit.edu/courses/new-courses/feed",
    ]

    for url in mit_feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.title.strip()
            if title in seen:
                continue
            seen.add(title)
            courses.append({
                "title": title, "university": "MIT", "platform": "MIT OpenCourseWare",
                "duration": "Self-paced", "url": entry.link, "is_free": True
            })

    harvard_courses = [
        {"title": "CS50: Introduction to Computer Science", "university": "Harvard University", "platform": "edX", "duration": "12 Weeks", "url": "https://www.edx.org/cs50", "is_free": True},
        {"title": "Data Science: Machine Learning", "university": "Harvard University", "platform": "edX", "duration": "8 Weeks", "url": "https://www.edx.org/course/data-science-machine-learning", "is_free": True},
    ]

    youtube_courses = [
        {"title": "Python Full Course for Beginners", "university": "FreeCodeCamp", "platform": "Youtube", "duration": "Self-paced", "url": "https://www.youtube.com/watch?v=rfscVS0vtbw", "is_free": True},
        {"title": "JavaScript Full Course", "university": "FreeCodeCamp", "platform": "Youtube", "duration": "Self-paced", "url": "https://www.youtube.com/watch?v=jS4aFq5-91M", "is_free": True},
    ]

    stanford_courses = [
        {"title": "Machine Learning", "university": "Stanford University", "platform": "Coursera", "duration": "10 Weeks", "url": "https://www.coursera.org/learn/machine-learning"},
    ]

    futurelearn_courses = [
        {"title": "Digital Skills: Web Analytics", "university": "Accenture", "platform": "FutureLearn", "duration": "4 Weeks", "url": "https://www.futurelearn.com/courses/digital-skills-web-analytics", "is_free": True},
    ]

    courses.extend(harvard_courses)
    courses.extend(stanford_courses)
    courses.extend(youtube_courses)
    courses.extend(futurelearn_courses)

    if len(courses) < 6:
        return JsonResponse({"courses": courses, "count": len(courses)})

    random.shuffle(courses)
    pool = courses[:20]
    selected = random.sample(pool, min(6, len(pool)))

    return JsonResponse({"courses": selected, "count": len(selected)})