from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView,
    UpdateView,
)
from .models import * #Assets,Description, News, Page, Service, SubService,Team
from accounts.models import CustomerUser
from .utils import generate_chatbot_response
from main.forms import ContactForm, GetHelpForm, GovernanceForm, CommunityPostForm, CommunityCommentForm, CommunityEventForm, CommunityContactForm
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
# COMMUNITIES VIEWS
# ============================================

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
            region="Global"
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

    context = {
        'members': members,
        'search_query': search_query,
        'region_filter': region_filter,
        'profession_filter': profession_filter,
        'unique_regions': unique_regions,
        'unique_professions': unique_professions,
        'total_members': members.count()
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
    member_id = request.session.get('joined_member_id')
    member = None
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
                name=name, profession=profession, region=region, is_public_directory=True
            )
            request.session['joined_member_id'] = member.id
        else:
            member.name = name
            member.profession = profession
            member.region = region
            member.is_public_directory = True
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

    context = {
        'name': member.name if member else '',
        'profession': member.profession if member else '',
        'region': member.region if member else '',
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