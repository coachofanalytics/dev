import os
import logging
from email import encoders
from django.shortcuts import render
import re
import html

logger = logging.getLogger(__name__)

# send_email imports
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from base64 import urlsafe_b64decode
from coda_project.settings import EMAIL_INFO, EMAIL_HR,EMAIL_FIN
from email.utils import COMMASPACE, formatdate

# Conditional import to prevent Django configuration issues
try:
    from ai_services.models import ReplyMail
    REPLY_MAIL_AVAILABLE = True
except (ImportError, Exception):
    REPLY_MAIL_AVAILABLE = False
    logger.warning("ReplyMail model not available - reply functionality will be limited")


def validate_email_address(email):
    """Enhanced email validation with edge case handling"""
    # Handle None and empty values
    if email is None or not isinstance(email, str):
        return False
    
    # Handle empty strings and whitespace-only strings
    if not email.strip():
        return False
    
    # Basic structure check - must have exactly one @ symbol
    if email.count('@') != 1:
        return False
    
    # Split into username and domain
    parts = email.split('@')
    if len(parts) != 2:
        return False
    
    username, domain = parts
    
    # Username validation
    if not username or len(username) > 64:
        return False
    
    # Domain validation
    if not domain or len(domain) > 253:
        return False
    
    # Check for double dots (consecutive dots) anywhere in the email
    if '..' in email:
        return False
    
    # Check domain parts
    domain_parts = domain.split('.')
    if len(domain_parts) < 2:  # Must have at least TLD and one level
        return False
    
    for part in domain_parts:
        # Domain part cannot be empty
        if not part:
            return False
        
        # Domain part cannot start or end with dash
        if part.startswith('-') or part.endswith('-'):
            return False
        
        # Domain part must be reasonable length
        if len(part) > 63:
            return False
    
    # TLD must be at least 2 characters
    if len(domain_parts[-1]) < 2:
        return False
    
    # Basic character validation for username and domain
    username_pattern = r'^[a-zA-Z0-9._%+-]+$'
    domain_pattern = r'^[a-zA-Z0-9.-]+$'
    
    if not re.match(username_pattern, username) or not re.match(domain_pattern, domain):
        return False
    
    return True


def sanitize_email_content(content):
    """Sanitize email content to prevent injection attacks"""
    if isinstance(content, str):
        return html.escape(content)
    return content


def send_email(category, to_email, subject, html_template, context):
    try:
        # Input validation
        if not all([category, to_email, subject, html_template]):
            logger.error("Missing required parameters for email sending")
            return False
        
        # Ensure to_email is a list
        if not isinstance(to_email, list):
            to_email = [to_email]
        
        # Validate all email addresses
        invalid_emails = [email for email in to_email if not validate_email_address(email)]
        if invalid_emails:
            logger.error(f"Invalid email addresses: {invalid_emails}")
            return False
        
        # Sanitize inputs to prevent injection attacks
        subject = sanitize_email_content(subject)
        to_email = [sanitize_email_content(email) for email in to_email]
        
        # Validate email configuration
        purpose = context.get('purpose', 'default')  
        if category == 1:
            __smtp_user = EMAIL_HR
        elif purpose == 'payment':
            __smtp_user = EMAIL_FIN
        else:
            __smtp_user = EMAIL_INFO

        if not __smtp_user or not __smtp_user.get("USER"):
            logger.error("Invalid email configuration")
            return False

        from_email = __smtp_user.get("USER")
        message = MIMEMultipart('alternative')
        message['From'] = from_email
        message['To'] = ', '.join(to_email)
        message['Subject'] = subject

        html_msg = render_to_string(html_template, context)
        html_part = MIMEText(html_msg, 'html')
        message.attach(html_part)

        text_msg = strip_tags(html_msg)
        text_part = MIMEText(text_msg, 'text')
        message.attach(text_part)

        msg_str = message.as_string()

        logger.debug(f'from_email: {from_email}')
        logger.debug(f'to_email: {to_email}')
        
        # Send email with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                with smtplib.SMTP(host=__smtp_user.get('HOST'), port=__smtp_user.get('PORT')) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(from_email, __smtp_user.get('PASS'))
                    server.sendmail(from_email, to_email, msg_str)
                    logger.info('Email sent successfully!')
                    return True
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f'Final attempt failed: {str(e)}')
                    return False
                logger.warning(f'Attempt {attempt + 1} failed: {str(e)}, retrying...')
                import time
                time.sleep(2)
                
    except Exception as e:
        logger.error(f"Unexpected error in send_email: {str(e)}")
        return False


def send_reply(service, msg_id):
    try:
        # Check if ReplyMail model is available
        if not REPLY_MAIL_AVAILABLE:
            logger.error("ReplyMail model not available - cannot check existing replies")
            return None
            
        if msg_id:
            check = ReplyMail.objects.filter(id=msg_id)
            if check.exists():
                return None
        
        # Mark message as read
        msg = service.users().messages().modify(
            userId='me',
            id=msg_id,
            body={
                'addLabelIds': [],
                'removeLabelIds': ['UNREAD'],
            },
            x__xgafv='1').execute()

        # Get message data
        msg = service.users().messages().get(userId='me', id=msg_id).execute()
        if not msg:
            logger.error('Message not found!')
            return None

        msg_payload = msg.get('payload')
        headers = msg_payload.get('headers')
        received_date = ''
        from_mail = []
        to_mail = ''
        subject = ''
        
        for header in headers:
            if header.get('name') == 'Date':
                received_date = header.get('value')
            elif header.get('name') == 'From':
                from_mail = [header.get('value')]
            elif header.get('name') == 'To':
                to_mail = header.get('value')
            elif header.get('name') == 'Subject':
                subject = header.get('value')

        # Sanitize message content
        mssg = "Hi there, Call me for this role(4174137966)"
        mssg = sanitize_email_content(mssg)

        # Create email message
        msg = MIMEMultipart()
        msg['From'] = to_mail
        msg['To'] = COMMASPACE.join(from_mail)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = sanitize_email_content(subject)
        
        # Handle resume attachment
        try:
            cwd = os.getcwd()
            doc = 'BIResume_10022021_v1_CM'  # make sure the document is in .docx format
            resumes = 'resumes'
            file_path = f'{cwd}/media/{resumes}/doc/{doc}.docx'
            
            if os.path.exists(file_path):
                part = MIMEBase('application', "octet-stream")
                with open(file_path, "rb") as f:
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{doc}.docx"')
                msg.attach(part)
            else:
                logger.warning(f"Resume file not found: {file_path}")
        except Exception as e:
            logger.error(f"Error attaching resume: {str(e)}")
        
        msg.attach(MIMEText(mssg))
        
        # Send email using environment variables
        reply_email_user = os.environ.get('REPLY_EMAIL_USER', 'noreply@example.com')
        reply_email_pass = os.environ.get('REPLY_EMAIL_PASS', '')
        
        if not reply_email_pass:
            logger.error("Reply email password not configured")
            return None
        
        # Use environment variable for SMTP host
        smtp_host = os.environ.get('REPLY_SMTP_HOST', 'smtp.gmail.com')
        smtp_port = int(os.environ.get('REPLY_SMTP_PORT', '587'))
        
        import ssl
        context = ssl.create_default_context()
        
        try:
            with smtplib.SMTP(host=smtp_host, port=smtp_port) as server:
                server.ehlo()
                server.starttls(context=context)
                server.login(reply_email_user, reply_email_pass)
                server.sendmail(to_mail, from_mail, msg.as_string())
                logger.info('Reply email sent successfully!')
        except Exception as e:
            logger.error(f'Error sending reply email: {str(e)}')
            return None
        
        # Extract text content
        try:
            text_part = msg.get('payload', {}).get('parts', [{}])[0]
            encoded_data = text_part.get('body', {}).get('data')
            if encoded_data:
                decoded_str = str(urlsafe_b64decode(encoded_data), 'UTF-8')
            else:
                decoded_str = 'None'
        except Exception as e:
            logger.error(f'Error decoding message content: {str(e)}')
            decoded_str = 'None'

        return {
            'id': msg_id,
            'from_mail': from_mail,
            'to_mail': to_mail,
            'subject': subject,
            'text_mail': decoded_str,
            'received_date': received_date,
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in send_reply: {str(e)}")
        return None

