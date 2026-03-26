from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import *
from .models import PaymentInformation

# Register your models here.
admin.site.register(PaymentInformation)