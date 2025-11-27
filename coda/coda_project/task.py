# Optional import - removed during optimization to reduce slug size
try:
    import tweepy
    TWEEPY_AVAILABLE = True
except ImportError:
    tweepy = None
    TWEEPY_AVAILABLE = False
import logging

from celery import shared_task
from mail.custom_email import send_email
from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
# importing modules
from management.models import Task, TaskHistory,Advertisement,TaskLinks
from shared_core.users import CustomerUser
# Infrastructure migrated to use shared_core - 25.11_INFRASTRUCTURE_DEV_CM test change
from accounts.models import TaskGroups
from finance.models import LoanApplication,PayslipConfig
from ai_services.models import ReplyMail, GotoMeetings
from management.utils import employee_group_level, increment_in_graduation_of_employee

# importing utils & Views
from management.utils import loan_computation, paymentconfigurations
from main.utils import download_image
# from main.context_processors import image_view

from gapi.gservices import get_service, search_messages
from mail.custom_email import send_reply

logger = logging.getLogger(__name__)
User = get_user_model()

JOB_SUPPORTS = ["job support", "job_support", "jobsupport"]
ACTIVITY_LIST = ['BOG', 'BI Sessions', 'DAF Sessions', 'Project', 'web sessions']


@shared_task(name="task_history")
def dump_data(request):
    """
    Monthly task reset: Move tasks from Task to TaskHistory.
    
    Uses TaskResetService for proper error handling and recovery.
    
    This function is scheduled to run automatically on the 1st of each month at midnight.
    For manual override, use TaskResetService.manual_reset() directly.
    """
    try:
        from management.services.task_reset_service import TaskResetService
        
        reset_service = TaskResetService()
        result = reset_service.reset_tasks(is_manual=False, dry_run=False)
        
        if not result['success']:
            # Log error but don't raise - Celery will handle retry
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Task reset failed: {result.get('errors', [])}")
        
        return result['success']
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Task reset error: {str(e)}", exc_info=True)
        # Re-raise for Celery retry mechanism
        raise
        import calendar
        bulk_object = []
        
        # Calculate daf_date based on when reset is run
        from dateutil.relativedelta import relativedelta
        from datetime import date
        from django.utils import timezone
        
        current_date = date.today()
        
        # OPTION 1: If running on 1st of month, set daf_date to last day of previous month
        if current_date.day == 1:
            # Automated reset on 1st - use last day of previous month
            last_month = current_date - relativedelta(months=1)
            last_day = calendar.monthrange(last_month.year, last_month.month)[1]
            default_daf_date = date(last_month.year, last_month.month, last_day)
        else:
            # Manual reset (not on 1st) - use same day of last month
            default_daf_date = current_date - relativedelta(months=1)
        
        ai_services_data = Task.objects.exclude(employee__email=None)
        for data in ai_services_data:
            
            # Default: use calculated daf_date
            daf_date_value = default_daf_date
            
            # If task has a submission date, use that to calculate daf_date more accurately
            if data.submission:
                submission_date = timezone.localtime(data.submission).date()
                
                # If submission is this month, task was performed last month
                if submission_date.month == current_date.month and submission_date.year == current_date.year:
                    # Submitted this month, so task was performed last month
                    if current_date.day == 1:
                        # Running on 1st: use last day of previous month
                        last_month = current_date - relativedelta(months=1)
                        last_day = calendar.monthrange(last_month.year, last_month.month)[1]
                        daf_date_value = date(last_month.year, last_month.month, last_day)
                    else:
                        # Manual reset: use same day of last month
                        daf_date_value = submission_date - relativedelta(months=1)
                else:
                    # Submission is from a previous month, use submission - 1 month
                    daf_date_value = submission_date - relativedelta(months=1)
            
            bulk_object.append(
                TaskHistory(
                    group=data.group,
                    category=data.category,
                    employee=data.employee,
                    activity_name=data.activity_name,
                    description=data.description,
                    slug=data.slug,
                    duration=data.duration,
                    point=data.point,
                    mxpoint=data.mxpoint,
                    mxearning=data.mxearning,
                    submission=data.submission,
                    is_active=data.is_active,
                    featured=data.featured,
                    daf_date=daf_date_value,  # Set daf_date when creating TaskHistory
                )
            )

        TaskHistory.objects.bulk_create(bulk_object)
        employees = User.objects.filter(is_staff=True, is_active=True)
        
        updated_task = []
        for employee in employees: 

            # Get current tasks for this employee
            employee_task = ai_services_data.filter(employee__is_staff=True, employee__is_active=True,employee=employee)
            if employee_task.count() > 0:
                
                # Get TaskHistory for this employee (including just-created records)
                employee_taskhistory = TaskHistory.objects.filter(employee__is_staff=True, employee__is_active=True,
                                                      employee_id=employee)
                
                for task in employee_task:
                    
                    group, group_title, total_point = employee_group_level(employee_taskhistory.filter(activity_name=task.activity_name), TaskGroups)
                    new_max_earning = task.mxearning
                    
                    #incrementing contractual people max_earnig by one whenever hr/she will complete 30 hour on project
                    #here point is incresed by duration(hour) when newevidence uploaded for particular requirement.
                    if group_title == 'Group H' and total_point > 30: 
                        
                        new_max_earning += (total_point // 3)

                        task.groupname_id = group
                        task.group = group_title
                        task.point = 0
                        task.mxearning = new_max_earning

                        updated_task.append(task)

                    #for intern no earning 
                    elif group_title == 'Group I':
                        
                        new_max_earning = 0

                        task.groupname_id = group
                        task.group = group_title
                        task.point = 0
                        task.mxearning = new_max_earning
                        updated_task.append(task)

                    elif task.groupname.id != group:

                        new_max_earning = increment_in_graduation_of_employee(employee, task.mxearning, group, PayslipConfig)

                        task.groupname_id = group
                        task.group = group_title
                        task.point = 0
                        task.mxearning = new_max_earning
                        
                        updated_task.append(task)
                    
                    else:
                        task.point = 0
                        updated_task.append(task)
                    

        if len(updated_task) > 0:
            Task.objects.bulk_update(updated_task, ['groupname', 'group', 'point', 'mxearning'])

        return True
        # ai_services_data.update(point=0)
        # for task in ai_services_data:
        #     task.point = 0
        #     task.save()
        # return True
    except Exception as e:
        print("error",str(e))
        # return False

@shared_task(name="SendMsgApplicatUser")
def SendMsgApplicatUser():
  applicants = CustomerUser.objects.filter(category=1,is_active=True,profile__upload_a__exact='',profile__upload_b__exact='',profile__upload_c__exact='')  # Job_Applicant category
  for data in applicants:
    date_joined = data.date_joined
    after_10_date = timedelta(days = 10)
    pastdate = date_joined.date() + after_10_date
    presentdate = datetime.now().date()
    if pastdate == presentdate:
        subject = "No active mail"
        send_email(
            category=data.category,
            to_email=(data.email,),
            subject=subject,
            html_template='email/SendMsgApplicatUser.html',
            context={'username': data.first_name}
        )

@shared_task(name="replies_job_mail")
def search_job_mail():
    search_results=[]
    search_query = ['jobs role', 'hiring', 'recruitment']
    # search_query = 'ranjeetgup19@gmail.com is:unread'
    service = get_service()  # default service with default scope, gmail-v1
    if not service:
        logger.error('No Service!')
    for search in search_query:
        se=search+" is:unread"
        search_results += search_messages(service, se)

    if not search_results:
        logger.error('NO SEARCH RESULTS FOUND !')
        # return render(request,'main/snippets_templates/interview_snippets/result.html',{"message":message})
    else:
        for result in search_results:
            print(result.get('id'))
            try:
                msg_dict = send_reply(service=service, msg_id=result.get('id'))
                if msg_dict:
                    try:
                        ReplyMail.objects.create(
                            id=msg_dict.get('id'),
                            from_mail=msg_dict.get('from_mail'),
                            to_mail=msg_dict.get('to_mail'),
                            subject=msg_dict.get('subject'),
                            text_mail=msg_dict.get('text_mail'),
                            received_date=msg_dict.get('received_date')
                        )
                    except Exception as e:
                        logger.error('error on adding new record!')
                        logger.error('error msg is ' + str(e))
                        logger.error(f'msg id is: msg_dict.get("id")')
            except Exception as e:
                logger.error('error msg is ' + str(e))

                # from django.core.management import call_command
# Optional import - removed during optimization to reduce slug size
try:
    import tweepy
    TWEEPY_AVAILABLE_2 = True
except ImportError:
    tweepy = None
    TWEEPY_AVAILABLE_2 = False
import requests
from management.models import Advertisement

"""

Twitter and Facebook AD management Scripts below

"""

@shared_task(name="advertisement")
def advertisement():
    #This function will post the latest tweet
    if not TWEEPY_AVAILABLE:
        logging.warning("Tweepy not available - Twitter posting disabled during optimization")
        return
        
    context = Advertisement.objects.all().first()
    apiKey = context.twitter_api_key 
    apiSecret = context.twitter_api_key_secret
    accessToken = context.twitter_access_token
    accessTokenSecret = context.twitter_access_token_secret
    # 3. Create Oauth client and set authentication and create API object
    oauth = tweepy.OAuthHandler(apiKey, apiSecret)
    oauth.set_access_token(accessToken, accessTokenSecret)

    api = tweepy.API(oauth)

    # 4. upload media
    value=None
    url = "https://www.codanalytics.net/static/main/img/service-3.jpg"
    image_path=download_image(url)
    print(image_path)

    # upload media
    media = api.media_upload(image_path)

    # post tweet with media_id
    description = context.post_description #'This is my tweet with an image'
    api.update_status(status=description, media_ids=[media.media_id])

# This function will auto upload the eviedence

@shared_task(name="auto_uplaod_evidence")
def auto_uplaod_evidence():
    try:
        links = TaskLinks.objects.last()
        goto_data = GotoMeetings.objects.filter(created_at__gte=links.created_at)
        user_data = CustomerUser.objects.filter(is_active=True)
        for goto_meet in goto_data and goto_meet.attendee_duration > 5:
            if goto_meet.recording:
                for user in user_data:
                    if user.username.casefold() == goto_meet.attendee_name.casefold():
                        task_obj = Task.objects.filter(employee= user,activity_name= goto_meet.meeting_topic).first()
                        if not task_obj:
                            task_obj = Task.objects.filter(activity_name= 'General Meeting').first()
                        # task_activity = Task.objects.filter(activity_name= goto_meet.meeting_topic).first()
                        points, maxpoints = Task.objects.values_list("point", "mxpoint").get(id=task_obj.id)
                        # if task_obj.activity_name in ACTIVITY_LIST:
                        if points != maxpoints and task_obj.activity_name.lower() not in JOB_SUPPORTS:
                            Task.objects.filter(id=task_obj.id).update(point=points + 1)
                        task_links = TaskLinks.objects.create(task=task_obj,added_by=user,link_name=goto_meet.meeting_topic,
                                            description=goto_meet.meeting_topic,link=goto_meet.recording)
    except Exception as e:
        print("error",str(e))


# This function will post the latest Facebook Ad
@shared_task(name="advertisement_facebook")
def advertisement_facebook():
    pass
    # facebook_page_id = context.facebook_page_id
    # access_token = context.facebook_access_token
    # url = "https://graph.facebook.com/{}/photos".format(facebook_page_id)
    # msg = context.post_description
    # image_location = context.image
    # payload = {
    #     "url": image_location,
    #     "access_token": access_token,
    #     "message": msg,
    # }

    # # Send the POST request
    # requests.post(url, data=payload)


# @shared_task(name="advertisement_whatsapp")
# def advertisement_whatsapp(request):
#     runwhatsapp(request)

# def advertisement_whatsapp(request):
#     whatsapp_items = Whatsapp.objects.all()
#     image_url = None
#     # Get a list of all group IDs from the Whatsapp model
#     # group_ids = list(whatsapp_items.values_list('group_id', flat=True))
#     group_ids = list(whatsapp_items.values_list('group_id', flat=True))
#     # group_ids = ["120363047226624982@g.us"]

#     # Get the image URL and message from the first item in the Whatsapp model
#     if whatsapp_items:
#         image_url = whatsapp_items[0].image_url
#         message = whatsapp_items[0].message
#     else:
#         message = "local testing"
#     product_id = whatsapp_items[0].product_id
#     screen_id = whatsapp_items[0].screen_id
#     token = whatsapp_items[0].token
#     # product_id = os.environ.get('MYAPI_PRODUCT_ID')
#     # screen_id = os.environ.get('MYAPI_SCREEN_ID')
#     # token = os.environ.get('MYAPI_TOKEN_ID')
#     # Loop through all group IDs and send the message to each group
#     for group_id in group_ids:
#         print("Sending message to group", group_id)

#         # Set the message type to "text" or "media" depending on whether an image URL is provided
#         conn = http.client.HTTPSConnection("api.maytapi.com")
#         if image_url:
#             # Set the length of the random string
#             length = 10
#             # Generate a random string of lowercase letters and digits
#             random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
#             payload = json.dumps({
#                 "to_number": group_id,
#                 "type": "media",
#                 "message": image_url,
#                 "filename": random_string
#             })
#         else:
#             payload = json.dumps({
#                 "to_number": group_id,
#                 "type": "text",
#                 "message": message
#             })

#         headers = {
#             'accept': 'application/json',
#             'x-maytapi-key': token,
#             'Content-Type': 'application/json'
#         }
#         conn.request("POST", f"/api/{product_id}/{screen_id}/sendMessage", payload, headers)
#         res = conn.getresponse()
#         data = res.read()
#         print(data.decode("utf-8"))
#         # if response.status_code == 200:
#         if json.loads(data).get('success') is True:
#             print("Message sent successfully!")
#             message = f"Hi, {request.user}, your messages have been sent to your groups."
#         else:
#             # print("Error sending message:", response.text)
#             message = data
#     # Display a success message on the page
#     context = {"title": "WHATSAPP", "message": message}
#     return render(request, "main/errors/generalerrors.html", context)
