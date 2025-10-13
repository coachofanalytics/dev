import django_filters 
from accounts.models import Credential,CustomerUser


class UserFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(label='Email', lookup_expr='icontains')
    first_name = django_filters.CharFilter(label='First name', lookup_expr='icontains')
    last_name = django_filters.CharFilter(label='Last name', lookup_expr='icontains')
    username = django_filters.CharFilter(label='Username', lookup_expr='icontains')
    date_joined = django_filters.DateFilter(label='Entry date', lookup_expr='exact')

    class Meta:
        model = CustomerUser
        fields = ['email', 'first_name', 'last_name', 'username','date_joined']


class CredentialFilter(django_filters.FilterSet):
    class Meta:
        model=Credential
        # fields= '__all__'
        fields ={
        'name':['icontains'],
        'link_name':['icontains'],
        }
        labels={
                'name':'credential',
                'link_name':'username/email',
        }


    
# ==================================INVESTING MODELS==================================================

class ReturnsFilter(django_filters.FilterSet):
    symbol = django_filters.CharFilter(label='Symbol', lookup_expr='icontains')
    action = django_filters.CharFilter(label='Type', lookup_expr='icontains')
    event = django_filters.CharFilter(label='Action', lookup_expr='icontains')
    date = django_filters.DateFilter(label='Date', field_name='date')

    class Meta:
        fields = ['symbol', 'action', 'event','date']


from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})
