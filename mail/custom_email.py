import os
import logging
from email import encoders

logger = logging.getLogger(__name__)

# send_email imports
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from base64 import urlsafe_b64decode
from email.utils import COMMASPACE, formatdate
from coda_project import settings
# from getdata.models import ReplyMail


# def send_email(category, to_email, subject, html_template, context):
#     purpose=context['purpose']
#     if category == 1:
#         __smtp_user = EMAIL_HR

#     if purpose in ['payment']:
#         __smtp_user = EMAIL_FIN
        
#     else:
#         __smtp_user = EMAIL_INFO
        
#     from_email = __smtp_user.get("USER")
#     message = MIMEMultipart('alternative')
#     message['From'] = from_email
#     message['To'] = ', '.join(to_email)
#     message['Subject'] = subject

#     html_msg = render_to_string(html_template, context)
#     html_part = MIMEText(html_msg, 'html')
#     message.attach(html_part)

#     text_msg = strip_tags(html_msg)
#     text_part = MIMEText(text_msg, 'text')
#     message.attach(text_part)

#     msg_str = message.as_string()

#     logger.debug(f'from_email: {from_email}')
#     logger.debug(f'to_email: {to_email}')
#     # logger.debug(f'msg_str: {msg_str}')

#     with smtplib.SMTP(host=__smtp_user.get('HOST'), port=__smtp_user.get('PORT')) as server:
#         server.ehlo()
#         server.starttls()
#         server.login(from_email, __smtp_user.get('PASS'))
#         server.sendmail(from_email, to_email, msg_str)
#         logger.info('the mail is sent!)')

# def send_email(category, to_email, subject, html_template, context):
#     purpose = context.get('purpose', 'default')  
#     if category == 1:
#         __smtp_user = EMAIL_HR

#     if purpose == 'payment':
#         __smtp_user = EMAIL_FIN
#     else:
#         __smtp_user = EMAIL_INFO

#     from_email = __smtp_user.get("USER")
#     message = MIMEMultipart('alternative')
#     message['From'] = from_email
#     message['To'] = ', '.join(to_email)
#     message['Subject'] = subject

#     html_msg = render_to_string(html_template, context)
#     html_part = MIMEText(html_msg, 'html')
#     message.attach(html_part)

#     text_msg = strip_tags(html_msg)
#     text_part = MIMEText(text_msg, 'text')
#     message.attach(text_part)

#     msg_str = message.as_string()

#     logger.debug(f'from_email: {from_email}')
#     logger.debug(f'to_email: {to_email}')
    
#     try:
#         with smtplib.SMTP(host=__smtp_user.get('HOST'), port=__smtp_user.get('PORT')) as server:
#             server.ehlo()
#             server.starttls()
#             server.login(from_email, __smtp_user.get('PASS'))
#             server.sendmail(from_email, to_email, msg_str)
#             logger.info('Email sent successfully!')
#     except Exception as e:
#         logger.error(f'Error sending email: {str(e)}')


def send_email(category, to_email, subject, html_template, context, from_name="Diaspora County 048"):
    purpose = context.get('purpose', 'default')  
    # if category == 1:
    #     __smtp_user = EMAIL_HR

    # if purpose == 'payment':
    #     __smtp_user = EMAIL_FIN
    # else:
    #     __smtp_user = EMAIL_INFO

    # from_email = __smtp_user.get("USER")
    hr_user = settings.EMAIL_INFO_USER 
    hr_port = settings.EMAIL_INFO_PORT
    hr_host = settings.EMAIL_INFO_HOST
    hr_password = settings.EMAIL_INFO_PASS


    from_email_header = formataddr((from_name, hr_user)) 

    message = MIMEMultipart('alternative')
    message['From'] = from_email_header
    message['To'] = ', '.join(to_email)
    message['Subject'] = subject

    html_msg = render_to_string(html_template, context)
    html_part = MIMEText(html_msg, 'html')
    message.attach(html_part)

    text_msg = strip_tags(html_msg)
    text_part = MIMEText(text_msg, 'text')
    message.attach(text_part)

    msg_str = message.as_string()

    logger.debug(f'from_email(header): {from_email_header}')
    logger.debug(f'to_email: {to_email}')
    
    try:
        with smtplib.SMTP(host= hr_host, port=hr_port) as server:
            server.ehlo()
            server.starttls()
            server.login(hr_user, hr_password)
            server.sendmail(hr_user, to_email, msg_str)
            logger.info('Email sent successfully!')
    except Exception as e:
        logger.error(f'Error sending email: {str(e)}')



def send_reply(service, msg_id):
    if msg_id:
        check = ReplyMail.objects.filter(id=msg_id)
        if check.exists():
            return None
    msg = service.users().messages().modify(
        userId='me',
        id=msg_id,
        body={
            'addLabelIds': [],
            'removeLabelIds': ['UNREAD'],
        },
        x__xgafv='1').execute()

    # get all the data about msg.
    msg = service.users().messages().get(userId='me', id=msg_id).execute()
    if not msg:
        logger.error('message not found!')
        return

    msg_payload = msg.get('payload')
    headers = msg_payload.get('headers')
    received_date=''
    from_mail=[]
    to_mail=''
    subject=''
    for header in headers:
        if header.get('name') == 'Date':
            received_date = header.get('value')
        if header.get('name') == 'From':
            # from_mail = header.get('value').split('<')[1].split('>')[0]
            from_mail = header.get('value')
            from_mail = [from_mail,]
        if header.get('name') == 'To':
            to_mail = header.get('value')
        if header.get('name') == 'Subject':
            subject = header.get('value')

    mssg = "Hi there, Call me for this role(4174137966)"

    msg = MIMEMultipart()
    msg['From'] = to_mail
    msg['To'] = COMMASPACE.join(from_mail)
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    try:
        cwd=os.getcwd()
        doc = 'BIResume_10022021_v1_CM'  #make sure the document is in .docx format
        resumes = 'resumes'
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open('''{}/media/{}/doc/{}.docx'''.format(cwd, resumes, doc), "rb").read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        'attachment; filename="{0}"'.format(doc))
        msg.attach(part)
    except Exception as e:
        print(e)
        pass
    msg.attach(MIMEText(mssg))
    import ssl
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(host='smtp.gmail.com', port=587) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login('chris.c.maghas@gmail.com', 'umrjdmxetfmdonqf')
            server.sendmail(to_mail, from_mail, msg.as_string())
            logger.info('the mail is sent!)')
    except Exception as e:
        logger.error('error msg is ' + str(e))
    try:
        text_part = msg.get('payload').get('parts')[0]
        encoded_data = text_part.get('body').get('data')
        decoded_str = str(urlsafe_b64decode(encoded_data), 'UTF-8')
    except:
        decoded_str = 'None'

    return {
        'id': msg_id,
        'from_mail': from_mail,
        'to_mail': to_mail,
        'subject': subject,
        'text_mail': decoded_str,
        'received_date': received_date,
    }

