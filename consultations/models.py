

# Create your models here.
from django.db import models
from django.conf import settings
from django.db import models

from django.shortcuts import render, redirect




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