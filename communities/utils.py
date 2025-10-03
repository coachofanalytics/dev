from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_email(subject, recipient_list, context, html_template, plain_template):
    """
    Sends an email with both HTML and plain text versions.

    :param subject: The subject of the email
    :param recipient_list: List of recipient email addresses
    :param context: The context data to render the template
    :param html_template: Path to the HTML template
    :param plain_template: Path to the plain text version of the email
    """
    # Render HTML message
    html_message = render_to_string(html_template, context)
    
    # Render plain text message
    plain_message = render_to_string(plain_template, context)
    
    # Strip tags for plain text version
    plain_message = strip_tags(html_message)
    
    try:
        # Send the email with both HTML and plain text parts
        send_mail(
            subject,
            plain_message,
            settings.EMAIL_HOST_USER,  # Sender email
            recipient_list,            # Recipients list
            html_message=html_message  # HTML message body
        )
    except Exception as e:
        # You can log the exception if necessary
        print(f"Error sending email: {e}")
