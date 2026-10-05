from django import forms
from django.db.models import Q

from accounts.models import CustomerUser
from .models import Location, Plan, ServiceCategory


class ClientNameForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=CustomerUser.objects.filter(
            Q(is_client=True) | Q(is_staff=True)
        ),
        label="Select a client",
        empty_label="Select a client",
    )


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ["zipcode", "city", "state", "country"]


class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = [
            "service",
            "name",
            "slug",
            "description",
            "is_active",
            "is_featured",
        ]


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = "__all__"