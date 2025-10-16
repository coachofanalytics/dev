from django.contrib import admin
from .models import MembershipRegistration, ContactMessage

# Register your models here.
admin.site.register(MembershipRegistration)
admin.site.register(ContactMessage)
