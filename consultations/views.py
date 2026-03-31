from django.shortcuts import render
from django.contrib import messages

from django.contrib.auth.decorators import login_required

@login_required
def consultation_dashboard(request):
    return render(request, 'consultation/dashboard.html')


def book_consultations(request):
    return render(request, "consultations/book_consultations.html")

def login(request):
        return render(request, "consultations/login.html")


from django.shortcuts import render, redirect
from .models import Consultation, Signup
from django.contrib import messages

    

def signup(request):

    if request.method == "POST":

        firstname = request.POST.get("firstname")
        lastname = request.POST.get("lastname")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        create_password = request.POST.get("create_password")
        confirm_password = request.POST.get("confirm_password")

        # check password match
        if create_password != confirm_password:
            return render(request, "consultations/signup.html", {
                "error": "Passwords do not match"
            })

        # check if email already exists
        if Signup.objects.filter(email=email).exists():
            return render(request, "consultations/signup.html", {
                "error": "Email already registered"
            })

        # save user
        Signup.objects.create(
            firstname=firstname,
            lastname=lastname,
            email=email,
            phone=phone,
            create_password=create_password
        )
        messages.success(request, "Signup successful! Your account has been created. You can now continue with your visa application.")

        return redirect('/consultations/login/')

    return render(request, "consultations/signup.html")

import pycountry
from django.shortcuts import render

def visa_applicationform(request):

    countries = pycountry.countries

    return render(
        request,
        "consultations/visa_applicationform.html",
        {"countries": countries}
    )
from django.shortcuts import render, get_object_or_404
from .models import VisaApplication

def application_success(request, application_id):
    application = get_object_or_404(VisaApplication, id=application_id)
    return render(request, "consultations/application_success.html", {
        "application": application
    })
#///////////////////////////
from django.shortcuts import render, redirect
from django.core.mail import EmailMessage
from django.contrib import messages
from .models import VisaApplication
from .utils import generate_application_pdf
import pycountry

def submit_application(request):
    countries = pycountry.countries

    if request.method == "POST":
        # Save application
        application = VisaApplication.objects.create(
            first_name=request.POST.get("first_name"),
            last_name=request.POST.get("last_name"),
            dob=request.POST.get("dob"),
            gender=request.POST.get("gender"),
            nationality=request.POST.get("nationality"),
            marital_status=request.POST.get("marital_status"),
            email=request.POST.get("email"),
            phone=request.POST.get("phone"),
            address=request.POST.get("address"),
            passport_number=request.POST.get("passport_number"),
            passport_issue=request.POST.get("passport_issue"),
            passport_expiry=request.POST.get("passport_expiry"),
            passport_country=request.POST.get("passport_country"),
            destination_country=request.POST.get("destination_country"),
            visa_type=request.POST.get("visa_type"),
            arrival_date=request.POST.get("arrival_date"),
            departure_date=request.POST.get("departure_date"),
            purpose=request.POST.get("purpose"),
            occupation=request.POST.get("occupation"),
            employer=request.POST.get("employer"),
            employer_address=request.POST.get("employer_address"),

            # Save uploaded files
            passport_copy=request.FILES.get("passport_copy"),
            photo=request.FILES.get("photo"),
            travel_doc=request.FILES.get("travel_doc"),
        )

        # Generate PDF
        pdf_file = generate_application_pdf(application)

        # Send email
        email = EmailMessage(
            subject="Visa Application Submitted Successfully",
            body=f"""
Dear {application.first_name},

Your visa application has been submitted successfully.

Thank you for applying.

Visa Processing Team
""",
            to=[application.email],
        )
        email.attach_file(pdf_file)
        email.send()

        # Redirect to professional success page with reference id
        return redirect('consultations:application_success', application_id=application.id)

    # GET request: show form
    return render(request, "consultations/visa_applicationform.html", {"countries": countries})
from .models import Signup
def login_view(request):

    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']

        user = Signup.objects.filter(email=email, create_password=password).first()

        if user:
            request.session['user_id'] = user.id
            return redirect('consultations:visa_applicationform')

        else:
            return render(request, "consultations/login.html", {
                "error": "Invalid credentials"
            })

    return render(request, "consultations/login.html")


    #new code

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Consultation

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from io import BytesIO
from weasyprint import HTML

from .models import Consultation

@login_required
def book_consultation(request):
    if request.method == 'POST':
        application_number = request.POST.get('application_number')
        service = request.POST.get('service')
        mode = request.POST.get('mode')
        date = request.POST.get('date')
        time = request.POST.get('time')

        # === Save Consultation Booking ===
        consultation = Consultation.objects.create(
            user=request.user,
            application_number=application_number,
            service_type=service,
            consultation_mode=mode,
            date=date,
            time=time,
            status='pending'
        )

        # === Generate PDF Confirmation ===
        html_string = render_to_string('emails/consultation_pdf.html', {
            'consultation': consultation,
            'user': request.user
        })
        pdf_file = BytesIO()
        HTML(string=html_string).write_pdf(pdf_file)
        pdf_file.seek(0)

        # === Send Email with PDF Attachment ===
        subject = 'Consultation Booking Confirmation'
        email = EmailMessage(
            subject,
            f"Hello {request.user.first_name},\n\nYour consultation booking details are attached as a PDF.\n\nThank you!",
            None,  # uses DEFAULT_FROM_EMAIL
            [request.user.email]
        )
        email.attach(f'Consultation_{consultation.application_number}.pdf', pdf_file.read(), 'application/pdf')
        email.send()

        # === Show success message ===
        messages.success(request, "Your consultation has been booked successfully! A confirmation email with PDF has been sent.")
        return redirect('consultations:booking_success')

    return render(request, 'consultations/book_consultation.html')
def booking_success(request):
    return render(request, 'consultations/booking_success.html')
from django.shortcuts import render, redirect
from .forms import PreAssessmentForm

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import PreAssessmentForm

def pre_assessment(request):
    if request.method == 'POST':
        form = PreAssessmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Pre-assessment submitted successfully!")
            return redirect('consultations:book_consultation')  # FIXED
    else:
        form = PreAssessmentForm()

    return render(request, 'consultations/pre_assessment.html', {'form': form})

#new code
from django.shortcuts import render
from .forms import EligibilityForm

def eligibility_check(request):
    if request.method == 'POST':
        form = EligibilityForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            suggestions = []

            # LOGIC RULES
            if data['years_of_residence'] >= 5:
                suggestions.append("Naturalization")

            if data['married_to_citizen'] == 'yes':
                suggestions.append("Citizenship by Marriage")

            if data['has_ancestry'] == 'yes':
                suggestions.append("Citizenship by Descent")

            if data.get('investment_budget') and data['investment_budget'] >= 100000:
                suggestions.append("Citizenship by Investment")

            return render(request, 'consultations/results.html', {
                'suggestions': suggestions,
                'data': data
            })

    else:
        form = EligibilityForm()

    return render(request, 'consultations/eligibility_form.html', {'form': form})


def path_detail(request, path_name):
    return render(request, 'consultations/path_detail.html', {
        'path_name': path_name
    })
def eligibility_form(request):
    form = EligibilityForm()
    return render(request, 'consultations/eligibility_form.html', {'form': form})

#newcode
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import AttorneyRequest

def find_attorney(request):
    if request.method == 'POST':
        AttorneyRequest.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=request.POST.get('full_name'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            country=request.POST.get('country'),
            issue_type=request.POST.get('issue_type'),
            description=request.POST.get('description'),
        )

        messages.success(request, "Your request has been submitted successfully!")
        return redirect('consultations:attorney_success')

    return render(request, 'consultations/find_attorney.html')

def attorney_success(request):

    return render(request, 'consultations/attorney_success.html')

def contacts(request):
    return render(request, 'consultations/contacts.html')
def pre_social_login(self, request, sociallogin):
        # Optional custom logic
        pass