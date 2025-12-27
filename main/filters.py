import django_filters 
from accounts.models import User
from finance.models import Food


class UserFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(label='Email', lookup_expr='icontains')
    first_name = django_filters.CharFilter(label='First name', lookup_expr='icontains')
    last_name = django_filters.CharFilter(label='Last name', lookup_expr='icontains')
    username = django_filters.CharFilter(label='Username', lookup_expr='icontains')
    date_joined = django_filters.DateFilter(label='Entry date', lookup_expr='exact')

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'username','date_joined']
