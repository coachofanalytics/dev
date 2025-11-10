from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_email(subject, recipient_list, context, html_template, plain_template):
    """
    Sends an email with both HTML and plain text versions.

    :param subject: The subject of the email
    :param recipient_list: List of recipient email addresses
    :param context: Context data for rendering the template
    :param html_template: Path to the HTML template
    :param plain_template: Path to the plain text version
    """
    try:
        # Render templates
        html_message = render_to_string(html_template, context)
        plain_message = render_to_string(plain_template, context)
        
        # Fallback: if plain template is empty, strip HTML
        if not plain_message.strip():
            plain_message = strip_tags(html_message)

        # Create the multi-part email
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.EMAIL_HOST_USER,
            to=recipient_list
        )

        # Attach the HTML version
        email.attach_alternative(html_message, "text/html")

        # Send it
        email.send(fail_silently=False)
        print(f"✅ Email sent to {recipient_list}")

    except Exception as e:
        print(f"❌ Error sending email: {e}")
