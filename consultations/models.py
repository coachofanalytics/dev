

# Create your models here.
from django.db import models
from django.conf import settings
from django.db import models

from django.shortcuts import render, redirect


from django_countries.fields import CountryField



class consultations(models.Model):

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('pending', 'Pending'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    CONSULTATION_TYPES = [
        ('immigration', 'Immigration Visa'),
        ('asylum', 'Asylum'),
        ('family', 'Family Immigration'),
        ('work', 'Work Permit'),
        ('student', 'Student Visa'),
        ('legal', 'General Legal Advice'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    consultation_type = models.CharField(
        max_length=100,
        choices=CONSULTATION_TYPES
    )
    description = models.TextField()
    document = models.FileField(
        upload_to='consultation_documents/',
        blank=True,
        null=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.consultation_type}"
    
    

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

        return redirect('/consultations/visa_applicationform/')

    return render(request, "consultations/signup.html")


from django.db import models


class Signup(models.Model):
    firstname = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    create_password = models.CharField(max_length=128)

    def __str__(self):
        return self.email
    #///////////////////////////////
    from django.db import models

class VisaApplication(models.Model):

    # PERSONAL
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20)
    nationality = models.CharField(max_length=100)
    marital_status = models.CharField(max_length=20)

    # CONTACT
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    address = models.TextField()

    # PASSPORT
    passport_number = models.CharField(max_length=50)
    passport_issue = models.DateField(null=True, blank=True)
    passport_expiry = models.DateField(null=True, blank=True)
    passport_country = models.CharField(max_length=100)

    # TRAVEL
    destination_country = models.CharField(max_length=100)
    visa_type = models.CharField(max_length=50)
    arrival_date = models.DateField(null=True, blank=True)
    departure_date = models.DateField(null=True, blank=True)
    purpose = models.TextField()

    # EMPLOYMENT
    occupation = models.CharField(max_length=100)
    employer = models.CharField(max_length=100)
    employer_address = models.TextField()
    passport_copy = models.FileField(upload_to='documents/passports/', null=True, blank=True)
    photo = models.ImageField(upload_to='documents/photos/', null=True, blank=True)
    travel_doc = models.FileField(upload_to='documents/travel/', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)


    #////bookings
from django.db import models
from django.conf import settings


from django.db import models
from django.conf import settings


from django.db import models
from django.conf import settings

class Consultation(models.Model):
    SERVICE_CHOICES = [
        ('visa', 'Visa Application'),
        ('work', 'Work Permit'),
        ('residency', 'Residency'),
        ('legal', 'Legal Advice'),
    ]

    MODE_CHOICES = [
        ('online', 'Online'),
        ('physical', 'In-person'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_consultations'
    )

    application_number = models.CharField(max_length=50, unique=True)

    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    consultation_mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f"{self.application_number} - {self.service_type}"

from django.db import models

class PreAssessment(models.Model):
    
    COUNTRY_CHOICES = [
        ('canada', 'Canada'),
        ('usa', 'USA'),
        ('uk', 'UK'),
    ]

    PURPOSE_CHOICES = [
        ('study', 'Study'),
        ('work', 'Work'),
        ('tourism', 'Tourism'),
    ]

    country = models.CharField(max_length=50, choices=COUNTRY_CHOICES)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    rejected_before = models.BooleanField()
    details = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.country} - {self.purpose}"



        #ahaa
from django.db import models

# Eligibility rules
class EligibilityRule(models.Model):
    country = models.CharField(max_length=100)
    min_age = models.IntegerField(default=18)
    min_years_residence = models.IntegerField(default=5)
    requires_clean_record = models.BooleanField(default=True)

    def __str__(self):
        return self.country

# Applicants
class Applicant(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    years_in_country = models.IntegerField()
    has_criminal_record = models.BooleanField(default=False)
    country = models.CharField(max_length=100)

    def __str__(self):
        return self.name

# Citizenship paths
class CitizenshipPath(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    min_years = models.IntegerField(default=0)
    requires_investment = models.BooleanField(default=False)
    country = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} - {self.country}"

        #newcode
from django.db import models
from django.conf import settings

class AttorneyRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    issue_type = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.issue_type}"