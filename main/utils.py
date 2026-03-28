import os
import openai
import requests
from coda_project.settings import SITEURL
from .models import Assets
import datetime
#import pdfkit

# def convert_html_to_pdf():
#     html="main/doc_templates/appointment_letter.html"
#     html_str=str(html)
#     pdfkit.from_string(html_str, 'appointment_letter.pdf')
#     print("success")

# def convert_html_to_pdf():
#     html_path = "main/doc_templates/appointment_letter.html"
#     pdf_path = "appointment_letter.pdf"
#     pdfkit.from_file(html_path, pdf_path)
#     print("Success: HTML converted to PDF.")

# def convert_html_to_pdf(request):
#     html_path = "main/doc_templates/letter.html"
#     pdf_path = "appointment_letter.pdf"
#     pdfkit.from_file(html_path, pdf_path)
#     with open(pdf_path, 'rb') as pdf_file:
#         response = HttpResponse(pdf_file.read(), content_type='application/pdf')
#         response['Content-Disposition'] = 'attachment; filename="appointment_letter.pdf"'
#         return response


def countdown_in_month():
    now = datetime.datetime.now()
    next_month = now.replace(day=28) + datetime.timedelta(days=4)
    next_month = next_month.replace(day=1)

    remaining_time = next_month - now
    remaining_days = remaining_time.days
    remaining_seconds = remaining_time.total_seconds()
    remaining_minutes = remaining_seconds / 60
    remaining_hours = remaining_minutes / 60
    return (
                remaining_days,
                remaining_seconds ,
                remaining_minutes ,
                remaining_hours,
                now
            )
def generate_chatbot_response(user_message, user_message_dict=None):
    if user_message_dict is None:
        messages = [
        {"role": "system", "content": user_message},
        ]
    else:
        messages = user_message_dict
    client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

    response = client.chat.completions.create(
    # response = openai.completions.create(
            # model = os.environ.get('OPENAI_MODEL'),
            model="gpt-4-1106-preview",
            messages=messages,
            # response_format="json"
            # temperature=0.4,
            # max_tokens=4096,
            # top_p=1,
            # frequency_penalty=0,
            # presence_penalty=0
    )

    if response:
        result=response.choices[0].message.content     
        
    else:
        result = None
    return result


def path_values(request):
    try:
        previous_path = request.META.get('HTTP_REFERER', '')
    except Exception:
        previous_path = f"{SITEURL}/management/companyagenda/"

    pre_value = previous_path.split("/")
    previous_path_values = [i for i in pre_value if i.strip()]
    pre_sub_title = previous_path_values[-1] if previous_path_values else ""

    current_value = request.path.split("/")
    path_values = [i for i in current_value if i.strip()]
    sub_title = path_values[-1]

    return path_values, sub_title, pre_sub_title

#===============Downloading Image==================
def download_image(url):
    # Path definition
    image_path = "media/data/image.jpg"
    res = requests.get(url, stream=True)
    if res.status_code == 200:
        with open(image_path, "wb") as f:
            f.write(res.content)
        # print("Image sucessfully Downloaded: ", image_path)
    else:
        print("Image Couldn't be retrieved")
    return image_path


# ============= COMMUNITIES EMAIL UTILITIES =============
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_email(subject, recipient_list, context, html_template, plain_template):
    """
    Sends an email with both HTML and plain text versions.
    Used by communities app for welcome and contact emails.

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
    image_path = "media/data/image.jpg"
    res = requests.get(url, stream=True)
    if res.status_code == 200:
        with open(image_path, "wb") as f:
            f.write(res.content)
        # print("Image sucessfully Downloaded: ", image_path)
    else:
        print("Image Couldn't be retrieved")
    return image_path

#===============Processing Images from Database==================
def image_view(request):
    images= Assets.objects.all()
    image_names=Assets.objects.values_list('name',flat=True)
    return images,image_names


