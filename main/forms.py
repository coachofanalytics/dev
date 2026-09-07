from django import forms
from django.db.models import Q
from accounts.models import CustomerUser
from django import forms
from main.models import Plan
# from .models import Expenses
from .models import *
# <<<<<<< HEAD
# from django.db import transaction
from multiupload.fields import MultiFileField
from django import forms
from .models import ServiceCategory
# =======
# from django.db import transactionfrom django import forms
from main.models import Location
# >>>>>>> e79fe45578418c384fbb84ca7760d91bef020a33

class ClientNameForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=CustomerUser.objects.filter(Q(is_client=True) | Q(is_staff=True)),
        label='Select a client'

    )
# <<<<<<< HEAD
from django import forms
from .models import Location
# =======
# >>>>>>> e79fe45578418c384fbb84ca7760d91bef020a33

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
# <<<<<<< HEAD
        fields = ['zipcode', 'city', 'state', 'country']



# # class ServiceCategoryForm(forms.ModelForm):
#     class Meta:
#         model = ServiceCategory
#         fields = ['name', 'description', 'is_active', 'is_featured']
# # =======
#         fields = ["country", "state", "city", "zipcode"]

#         from django import forms
from .models import Testimonials

class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonials
        fields = ['title', 'content', 'writer']


        # main/forms.py




class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = "__all__"
# >>>>>>> e79fe45578418c384fbb84ca7760d91bef020a33
