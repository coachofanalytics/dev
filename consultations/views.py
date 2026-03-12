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
from .models import Signup
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