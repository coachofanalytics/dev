from shared_core.users import CustomerUser
from datetime import datetime, timedelta
from mail.custom_email import send_email

def SendMsgApplicatUser():
    """Description: Aplicat user login after not upload section will send msg"""
    applicants = CustomerUser.objects.filter(category=1,is_active=True,profile__upload_a__exact='',profile__upload_b__exact='',profile__upload_c__exact='')  # Job_Applicant category
    for data in applicants:
        date_joined = data.date_joined
        after_10_date = timedelta(days = 10)
        pastdate = date_joined.date() + after_10_date
        presentdate = datetime.now().date()
        print('pastdate-->',pastdate)
        print("presentdate-->",presentdate)
        if pastdate == presentdate:
            subject = "No active mail"
            # to = data.email
            # content = f"""
            #         <span><h3>Hi {data.username},</h3>you applied for a position in CODA, kindly let us know of your progress, you can login at the following link to proceed with your interview </span>"""
            # email_template(subject,to,content)
            send_email(category=data.category, to_email=[data.email,], subject=subject, html_template='email/SendMsgApplicatUser.html', context={'username': data.username})
