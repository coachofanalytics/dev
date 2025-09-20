from django.contrib import messages
from django.http import JsonResponse
import os,requests
import json
from django.utils.text import slugify
import logging
# from django.core.management import call_command
from django.db.models import IntegerField, F,Sum, Q
from django.db.models.functions import Cast
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.utils import timezone
from accounts.choices import UserCategory as CategoryChoices
from marketing.models import Ads,Whatsapp_Groups
from coda_project import settings
from .forms import UpdateUserCategoryForm, WhatsappForm,AdsForm
from django.db.models import Count
from django.urls import reverse
from mail.custom_email import send_email

from accounts.models import CustomerUser, UserGroups
from main.utils import path_values,courses,get_15th_of_next_month,notification_days,today_date,switch_groups

from ai_services.utils import Run_Command
from ai_services.models import Editable
from main.context_processors import services
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
        CreateView,
        UpdateView,
    )
from main.context_processors import images
from django.contrib.auth import get_user_model
from .utils import update_ads_by_pricing
from main.permission import check_payment_history_permission

User=get_user_model()
logger = logging.getLogger(__name__)
#====================General===========================
def search_users(request):
    query = request.GET.get('q', '')
    users = CustomerUser.objects.filter(username__icontains=query) | CustomerUser.objects.filter(email__icontains=query)
    results = []
    for user in users:
        results.append({
            'id': user.id,
            'text': f"{user.username} ({user.email})"
        })
    return JsonResponse({'results': results, 'total_count': users.count()})
@login_required
@user_passes_test(lambda user: check_payment_history_permission(user, pricing_serial=19), login_url='/display_plans/it_solutions/')
def marketing(request):
    # Filtering groups based on their category names
    job_applicant_groups = UserGroups.objects.filter(name__startswith='job-applicant')
    coda_staff_member_groups = UserGroups.objects.filter(name__startswith='coda-staff-member')
    jobsupport_groups = UserGroups.objects.filter(name__startswith='jobsupport')
    student_groups = UserGroups.objects.filter(name__startswith='student')
    investor_groups = UserGroups.objects.filter(name__startswith='investor')
    general_user_groups = UserGroups.objects.filter(name__startswith='general-user')
    vendor_groups = UserGroups.objects.filter(name__startswith='vendor')
    user = CustomerUser.objects.first() 
    # Process the form if it's submitted
    if request.method == 'POST':
        form = UpdateUserCategoryForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            new_category = form.cleaned_data['category']

            # Check if the user is already in the desired category
            if user.category == int(new_category):
                messages.error(request, f'User is already in the {dict(CategoryChoices.choices)[int(new_category)]} category.')
            else:
                # Update the user's category
                old_category = user.category
                user.category = int(new_category)
                user.save()

                # Remove user from the old group
                old_group_name_prefix = slugify(dict(CategoryChoices.choices).get(old_category, 'unknown-category'))
                old_group = UserGroups.objects.filter(name__startswith=old_group_name_prefix).first()
                if old_group:
                    old_group.users.remove(user)

                # Assign user to the new group
                new_group_name_prefix = slugify(dict(CategoryChoices.choices).get(int(new_category), 'unknown-category'))
                new_group = UserGroups.objects.filter(name__startswith=new_group_name_prefix).order_by('id').first()

                if not new_group or new_group.users.count() >= 30:
                    group_count = UserGroups.objects.filter(name__startswith=new_group_name_prefix).count() + 1
                    new_group_name = f"{new_group_name_prefix} Group {group_count}"
                    new_group = UserGroups.objects.create(
                        name=new_group_name,
                        is_active=True,
                        is_featured=False
                    )
                new_group.users.add(user)
                new_group.save()

                messages.success(request, f"{user.username} has been successfully moved to the new {new_group.name} group from old {old_group } group ")

            return redirect('marketing:marketing')
    else:
        form = UpdateUserCategoryForm()

    # Analytics data: count the number of users in each group
    group_counts = {
        'Job Applicants': job_applicant_groups.annotate(user_count=Count('users')),
        'Coda Staff Members': coda_staff_member_groups.annotate(user_count=Count('users')),
        'Job Support': jobsupport_groups.annotate(user_count=Count('users')),
        'Students': student_groups.annotate(user_count=Count('users')),
        'Investors': investor_groups.annotate(user_count=Count('users')),
        'General Users': general_user_groups.annotate(user_count=Count('users')),
        'Vendors': vendor_groups.annotate(user_count=Count('users')),
    }

    # Pie chart data preparation
    pie_chart_data = {
        'Job Applicants': sum(group.user_count for group in group_counts['Job Applicants']),
        'Coda Staff Members': sum(group.user_count for group in group_counts['Coda Staff Members']),
        'Job Support': sum(group.user_count for group in group_counts['Job Support']),
        'Students': sum(group.user_count for group in group_counts['Students']),
        'Investors': sum(group.user_count for group in group_counts['Investors']),
        'General Users': sum(group.user_count for group in group_counts['General Users']),
        'Vendors': sum(group.user_count for group in group_counts['Vendors']),
    }

    # Existing social media cards
    social_media_cards = [  
        {
            'title': 'Whatsapp',
            'description': 'Managing WhatsApp groups.',
            'menu_items': [
                {'text': 'Run to Publish', 'url': reverse('marketing:whatsapp')},
                {'text': 'Add New Group', 'url': reverse('marketing:whatsapp_new')},
                {'text': 'See Groups', 'url': reverse('marketing:whatsapp_list', kwargs={'title': 'all'})},
                {'text': 'Populate Groups', 'url': reverse('getdata:whatsappgroups') if request.user.is_superuser else reverse('finance:pay')},
                {'text': 'PPT-Automation', 'url': 'https://docs.google.com/presentation/d/1JBWX_QI6BBJrJhtZdahYRzFpFRXpe-lK/edit#slide=id.p2'}
            ]
        },
        {
            'title': 'Facebook',
            'description': 'Managing Facebook',
            'menu_items': [
                {'text': 'Run to Publish', 'url': 'https://www.facebook.com/chris.maghas/'},
                {'text': 'Our Page', 'url': 'https://www.facebook.com/coachchrismaghas/'},
                {'text': 'PPT-Automation', 'url': '#'}
            ]
        },
        {
            'title': 'Twitter',
            'description': 'Managing Twitter',
            'menu_items': [
                {'text': 'Run to Publish', 'url': '#'},
                {'text': 'twitter Page', 'url': 'https://twitter.com/CrownData'},
                {'text': 'PPT-Automation', 'url': '#'}
            ]
        },
    ]

    context = {
        "title": "Marketing",
        'social_media_cards': social_media_cards,
        'job_applicant_groups': job_applicant_groups,
        'coda_staff_member_groups': coda_staff_member_groups,
        'jobsupport_groups': jobsupport_groups,
        'student_groups': student_groups,
        'investor_groups': investor_groups,
        'general_user_groups': general_user_groups,
        'vendor_groups': vendor_groups,
        'pie_chart_data': pie_chart_data,
        'form': form,
    }
    return render(request, "marketing/socialmedia.html", context)




#====================AD MANAGEMENT===========================
class AdsCreateView(LoginRequiredMixin, CreateView):
    model = Ads
    success_url = "marketing/adslist/"  
    form_class=AdsForm
    # fields = "__all__"

    def get_success_url(self):
        return reverse("marketing:ads_list")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user.is_superuser
        return kwargs

    def form_valid(self, form):
        form.instance.my_user = self.request.user
        if not self.request.user.is_superuser:
            
            if not self.request.user.is_superuser:
                is_featured, is_active = update_ads_by_pricing(form.instance.my_user)
                form.instance.is_featured = is_featured
                form.instance.is_active = is_active

        return super().form_valid(form)


class AdsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Ads # Whatsapp 
    form_class=AdsForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user.is_superuser
        return kwargs
    
    def form_valid(self, form):
        form.instance.username = self.request.user
        
        if not self.request.user.is_superuser:
            is_featured, is_active = update_ads_by_pricing(form.instance.my_user)
            form.instance.is_featured = is_featured
            form.instance.is_active = is_active
            
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("marketing:ads_list")

    def test_func(self):
        # plan = self.get_object()
        if self.request.user.is_superuser:
            return True
        elif self.request.user:
            return True
        return False

@login_required
def delete_ads(request,id):
    ad = Ads.objects.get(pk=id)
    if request.user.is_superuser:
        ad.delete()
    return redirect('marketing:ads_list')

@login_required
def ads(request):
    if request.user.is_superuser:
        
        ad_items=Ads.objects.all()
    else:
        ad_items=Ads.objects.filter(my_user=request.user)
    context={
            "ad_items":ad_items
    }
    return render(request, 'marketing/adlist.html',context)

#====================WHATSAPP MANAGEMENT===========================
class whatsappCreateView(LoginRequiredMixin, CreateView):
    model = Whatsapp_Groups
    success_url = "/marketing/whatsapplist/"  
    form_class=WhatsappForm
    # fields = "__all__"

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    

class whatsappUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Whatsapp_Groups
    form_class = WhatsappForm

    def form_valid(self, form):
        form.instance.username = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        # Replace 'all' with the appropriate title value you need to pass
        return reverse("marketing:whatsapp_list", kwargs={'title': 'all'})

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        elif self.request.user:
            return True
        return False


@login_required
def delete_whatsapp(request,slug):
    whatsapp_record = Whatsapp_Groups.objects.get(pk=slug)
    if request.user.is_superuser:
        whatsapp_record.delete()
    return redirect('marketing:whatsapp_list')

@login_required
def whatsapp_groups(request, title):
    CATEGORY_CHOICES = [
        "all",
        "Finance",
        "IT",
        "Internal",
        "Political",
        "Business",
        "other",
    ] 
    TYPE_CHOICES = [
        "all",
        "investments",
        "data_analysis",
        "coda",
        "Job_Support",
        "interview",
        "mentorship",
        "automation",
        "other",
    ]

    # Annotate groups with participant count
    annotated_whatsapp_groups = Whatsapp_Groups.objects.annotate(
        participant_count=Cast('participants', IntegerField())
    )

    if request.method == 'POST':
        if request.headers.get('Content-Type') == 'application/json':
            try:
                data = json.loads(request.body)
                # For individual updates
                if 'group_id' in data and 'field' in data and 'status' in data:
                    group_id = data.get('group_id')
                    field = data.get('field')
                    status = data.get('status')

                    group = Whatsapp_Groups.objects.get(id=group_id)
                    if field == 'is_active':
                        group.is_active = status
                    elif field == 'is_featured':
                        group.is_featured = status

                    group.save()

                    return JsonResponse({'success': True})

                elif 'field' in data and 'status' in data:
                    field = data.get('field')
                    status = data.get('status')

                    # Get filters from data
                    category = data.get('category', 'all')
                    ads_type = data.get('ads_type', 'all')
                    participants_range = data.get('participants_range', 'all')

                    # Filter groups based on provided filters
                    groups_to_update = annotated_whatsapp_groups

                    if category != 'all':
                        groups_to_update = groups_to_update.filter(category=category)
                    if ads_type != 'all':
                        groups_to_update = groups_to_update.filter(type=ads_type)
                    if participants_range == 'less_than_20':
                        groups_to_update = groups_to_update.filter(participant_count__lt=20)
                    elif participants_range == 'greater_than_20':
                        groups_to_update = groups_to_update.filter(participant_count__gte=20)

                    if field == 'is_active':
                        groups_to_update.update(is_active=status)
                        groups_to_update.update(is_featured=status)

                    elif field == 'is_featured':
                        groups_to_update.update(is_featured=status)

                    return JsonResponse({'success': True})

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        # Handle form submission
        selected_option = request.POST.get('dropdown_option')
        category = request.POST.get('category', 'all')
        ads_type = request.POST.get('ads_type', 'all')
        participants_range = request.POST.get('participants_range', 'all')
        action = request.POST.get('action', 'search')

        # Filter based on form selections
        if category != "all":
            annotated_whatsapp_groups = annotated_whatsapp_groups.filter(category=category)

        if ads_type != "all":
            annotated_whatsapp_groups = annotated_whatsapp_groups.filter(type=ads_type)

        if participants_range == 'less_than_20':
            annotated_whatsapp_groups = annotated_whatsapp_groups.filter(participant_count__lt=20)
        elif participants_range == 'greater_than_20':
            annotated_whatsapp_groups = annotated_whatsapp_groups.filter(participant_count__gte=20)

        if action != "search":
            # Update action for search or status change
            status = action == 'true'
            if selected_option == 'is_active':
                annotated_whatsapp_groups.update(is_active=status)
            elif selected_option == 'is_featured':
                annotated_whatsapp_groups.update(is_featured=status)

    # Fetch groups based on title
    if title == 'active_groups':
        whatsapp_groups = annotated_whatsapp_groups.filter(is_active=True)
    elif title == 'featured_groups':
        whatsapp_groups = annotated_whatsapp_groups.filter(is_featured=True)
    else:
        # Default case: Fetch all groups and order by participant count
        whatsapp_groups = annotated_whatsapp_groups

    # Calculate the total participants across all fetched groups
    total_participants = whatsapp_groups.aggregate(total=Sum('participant_count'))['total'] if whatsapp_groups else 0

    # Prepare the context data for rendering
    context = {
        "whatsapp_items": whatsapp_groups.order_by('-participant_count'),
        "total_participants": total_participants,
        "category_choices": CATEGORY_CHOICES,
        "ads_type_choices": TYPE_CHOICES
    }
    return render(request, 'marketing/groups.html', context)

@login_required(login_url="accounts:account-login")
def refresh_whatsapp_groups(request):
    # Trigger the management command
    if request.user.is_superuser:
        Run_Command('fetch_whatsapp_groups')
        return redirect('marketing:whatsapp_list')
    else:
        return redirect('marketing:whatsapp_list')

# @login_required(login_url="accounts:account-login")
# def refresh_whatsapp_groups(request):
#     Run_Command('fetch_whatsapp_groups')
#     return redirect('marketing:whatsapp_list')

@user_passes_test(lambda u: u.is_superuser, login_url="accounts:account-login")
@login_required(login_url="accounts:account-login")
def runwhatsapp(request):
    product_id = os.environ.get('MAYTAPI_PRODUCT_ID')
    screen_id = os.environ.get('MAYTAPI_SCREEN_ID')
    token = os.environ.get('MAYTAPI_TOKEN')
    title = 'WHATSAPP'
    # ads_items = Ads.objects.filter(is_active=True, image_name__is_active=True)
    ads_items = Ads.objects.filter(is_active=True).filter(Q(is_active=True) | Q(is_featured=True))
    print("ads_items==========>",ads_items)
    
    notification_obj = Editable.objects.filter(name='whatsapp_notification').first()

    Number_notification_days, notification_date = notification_days(notification_obj) if notification_obj else None
    thresh_hold = int(notification_obj.threshhold) if notification_obj.threshhold else 0
    print(Number_notification_days,thresh_hold)

    
    if Number_notification_days is not None and Number_notification_days == thresh_hold:
        for ad in ads_items:
            print('image',ad.image_name.name)
            # whatsapp_groups = Whatsapp_Groups.objects.filter(type=ad.image_name.category,is_active=True)
            # whatsapp_groups = Whatsapp_Groups.objects.filter(type=ad.image_name.name,is_active=True)
        
            if ad.is_featured:
                whatsapp_groups = Whatsapp_Groups.objects.filter(is_active=True,is_featured=True)
            elif ad.is_active:
                whatsapp_groups = Whatsapp_Groups.objects.filter(is_active=True)
            else:
                whatsapp_groups = Whatsapp_Groups.objects.filter(type=ad.image_name.name).annotate(
                    participant_count=Cast('participants', IntegerField())
                ).filter(participant_count__lt=150)
            # print("whatsapp_groups==========>",whatsapp_groups)
            group_ids = list(whatsapp_groups.values_list('group_id', flat=True))
            group_names = list(whatsapp_groups.values_list('group_name', flat=True))
            print("whatsapp_NAMES==========>",group_names)
            
            image_url = ad.image_name.image_url
            full_image__url=f'http://drive.google.com/uc?export=view&id={image_url}'
            message = ad.message
            company_description = ad.description if ad.description else ''
            link = ad.link
            # topic=ad.ad_title if ad.ad_title else 'General'
            topic=ad.bulletin if ad.bulletin else 'General'
            company=ad.company if ad.company else 'CROWN DATA ANALYSIS & CONSULTING LLC'
            short_name=ad.short_name if ad.short_name else 'CODA'
            signature=ad.signature if ad.signature else 'Chris Maghas-AI|Automation Expert'
            company_site=ad.company_site if ad.signature else 'www.codanalytics.net/accounts/join'
            video_link= f"Here is the recorded video:{ad.video_link}" if ad.video_link else ''
            join_link= f"Join Zoom Meeting \n:{ad.meeting_link}" if ad.meeting_link else ''
            post= f'{company}-{short_name}\n\n{company_description}\n\n{topic}\n\n{message}\n\n{video_link}\n{join_link}\n\nFor questions, please reach us at: {company_site}\n{signature}'

            for group_id in group_ids:
                # Validate data
                if not group_id:
                    logger.error("Group ID is missing.")
                    continue

                if not full_image__url:
                    logger.error(f"image__url content is missing for group {group_id}.")
                    continue

                if not post:
                    logger.error(f" post is missing for group {group_id}.")
                    continue

                if image_url:
                    message_type = "media"
                    message_content = full_image__url
                    filename = "image.jpg"

                    payload = {
                        "to_number": group_id,
                        "type": message_type,
                        "message": message_content,
                        "text":post #f'{message}\nvisit us at {link}'
                    }
                else:
                    message_type = "text"
                    message_content = post # f'{message}\nvisit us at {link}'
                    filename = None

                    payload = {
                        "to_number": group_id,
                        "type": message_type,
                        "message": message_content,
                        "filename": filename,
                    }
                headers = {
                    "accept": "application/json",
                    "Content-Type": "application/json",
                    "x-maytapi-key": token,
                }
                url = f"https://api.maytapi.com/api/{product_id}/{screen_id}/sendMessage"
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                if response.status_code != 200:
                    error_message=f"Error sending message to group {group_id}. Details: {response.content}"
                    logger.error(error_message)
                    print(error_message)

                new_thresh_hold = thresh_hold + 3
                notification_obj.threshhold = str(new_thresh_hold)
                notification_obj.save()

                if timezone.now().date().day == 1:
                    try:
                        value_json = json.loads(notification_obj.value)
                    except json.JSONDecodeError:
                        value_json = {}

                    value_json['notification_date'] = today_date
                    notification_obj.value = json.dumps(value_json)
                    notification_obj.threshhold = 1
                    notification_obj.save()
        message = f"Hi, {request.user}, your ads have been sent to your selected groups"
        context = {"title": title, "message": message}
    else:
        message = f"Hi, {request.user}, days do not meet.Please check Notification days: {Number_notification_days} vis a vi threshhold: {thresh_hold}"
        context = {"title": title, "message": message}

    return render(request, "main/errors/generalerrors.html", context)


# @login_required(login_url="accounts:account-login")
# def runwhatsapp(request):
#     product_id = os.environ.get('MAYTAPI_PRODUCT_ID')
#     screen_id = os.environ.get('MAYTAPI_SCREEN_ID')
#     token = os.environ.get('MAYTAPI_TOKEN')
#     title = 'WHATSAPP'

#     ads_items = Ads.objects.filter(is_active=True).prefetch_related('image_name')
#     for ad in ads_items:
#         whatsapp_groups = Whatsapp_Groups.objects.filter(type=ad.image_name.category)
#         group_ids = list(whatsapp_groups.values_list('group_id', flat=True))

#         message_payload = build_message_payload(ad)

#         for group_id in group_ids:
#             send_message(product_id, screen_id, token, group_id, message_payload)

#     messages.success(request, "Your messages have been sent to your groups.")
#     return render(request, "main/errors/generalerrors.html", {"title": title})

def send_email_ads(request):
    path_list,sub_title,pre_sub_title=path_values(request)
    subject='NEXT CLASSES!SIGN UP!'
    url='marketing/marketing_ads.html'
    message=''
    error_message=f'Hi,{request.user.first_name}, there seems to be an issue on our end.kindly contact us directly for payment details.'
    context_data = services(request)
    # user_category = request.user.category
    # Retrieve the list of users based on their category
    # users_to_email = User.objects.filter(category=user_category)
    users_to_email = User.objects.filter(is_staff=True,is_active=True)
    # print(users_to_email)
    plans = context_data.get('plans')
    pricing_info = context_data.get('pricing_info')
    context={
                "SITEURL": settings.SITEURL,
                'subtitle': sub_title,
                # "services": plans,
                'services': pricing_info,
                'courses':courses,
                'message':message,
                'error_message':error_message,
                'contact_message':'info@codanalytics.net',
            }
    try:
        # Send email to each user in the selected category
        # for user in users_to_email:
        #     context['user'] = user.first_name
        #     send_email(
        #         category=user.category,  
        #         to_email=[user.email],
        #         subject=subject,
        #         html_template=url,
        #         context=context
        #     )

        # return render(request, "marketing/marketing_ads.html", context)
        return render(request, "marketing/newad.html", context)
    except Exception as e:
        print(f"An error occurred: {e}")
        # return render(request, "marketing/marketing_ads.html", context)
        return render(request, "marketing/trainingad.html", context)
    

def send_training_ad(request):
    subject = 'DATA ANALYSIS|SCIENCE|AI COURSE'
    title2 = 'TIMELINE,LOCATION & OUTCOMES'
    url = 'email/marketing/trainad.html'
    image_url = 'https://www.codanalytics.net/static/main/image/ittraining.jpg'
    image_url2 = 'https://www.codanalytics.net/static/main/image/interviews.png'
    image_url3 = 'https://www.codanalytics.net/static/main/image/jobsupport.jpg'
    
    message = (
        f'Hi ,Your message was successfully sent. To confirm, please check '
        f'sent mails of finance@codanalytics.net. Thank You.'
    )
    error_message = f'Hi, there seems to be an issue on our end. Kindly contact us directly for payment details.'

    notification_obj = Editable.objects.filter(name='notification_date').first()

    Number_notification_days, notification_date = notification_days(notification_obj) if notification_obj else None
    thresh_hold = int(notification_obj.threshhold) if notification_obj.threshhold else 0
    print(Number_notification_days,thresh_hold)

    users = []
    email_statuses = []
    if Number_notification_days is not None and Number_notification_days == thresh_hold:
        group = UserGroups.objects.filter(is_featured=True).first()
        user = group.users.all()
        switch_groups()
        print(Number_notification_days,thresh_hold)
        new_thresh_hold = thresh_hold + 3
        notification_obj.threshhold = str(new_thresh_hold)
        notification_obj.save()

        if timezone.now().date().day == 1:
            try:
                value_json = json.loads(notification_obj.value)
            except json.JSONDecodeError:
                value_json = {}

            value_json['notification_date'] = today_date
            notification_obj.value = json.dumps(value_json)
            notification_obj.threshhold = 1
            notification_obj.save()

        users_to_email = user
        for users in users_to_email:
            
            print(users.email)

        start_date, end_date = get_15th_of_next_month()

        context = {
            "SITEURL": settings.SITEURL,
            "purpose": "marketing",
            "title": subject,
            'title2': title2,
            'courses': courses,
            'message': message,
            'error_message': error_message,
            'image_url': image_url,
            'image_url2': image_url2,
            'image_url3': image_url3,
            'start_date': start_date,
            'end_date': end_date,
        }

        try:
            for user in users_to_email:
                context['user'] = user.first_name
                # Uncomment the send_email function to actually send the email
                try:
                    send_email(
                        category=user.category,  
                        to_email=[user.email],
                        subject=subject,
                        html_template=url,
                        context=context
                    )
                    email_statuses.append({'email': user.email, 'status': 'Success'})
                except Exception as e:
                    email_statuses.append({'email': user.email, 'status': f'Failed: {str(e)}'})

            return render(request, 'marketing/email_sent_list.html', {'email_statuses': email_statuses})
        
        
        except Exception as e:
            error_message = (
                f'Hi {request.user.first_name}, Your message was unsuccessful. '
                f'Please try again or contact info@codanalytics.net. Thank You. '
                f'Error: {e}'
            )
            return render(request, 'main/messages/message.html', {"message": error_message})
    else:
        message = (
                f'Hi {request.user.first_name}, No email sent check Notification days: {Number_notification_days} vis a vi threshhold: {thresh_hold}. '
            )
        return render(request, 'main/messages/message.html', {"message": message})
