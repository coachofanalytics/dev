import django_filters 
from accounts.models import Credential,CustomerUser
from management.models import Requirement,TaskHistory,Task
from finance.models import Food
from accounts.models import Department


class UserFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(label='Email', lookup_expr='icontains')
    first_name = django_filters.CharFilter(label='First name', lookup_expr='icontains')
    last_name = django_filters.CharFilter(label='Last name', lookup_expr='icontains')
    username = django_filters.CharFilter(label='Username', lookup_expr='icontains')
    date_joined = django_filters.DateFilter(label='Entry date', lookup_expr='exact')

    class Meta:
        model = CustomerUser
        fields = ['email', 'first_name', 'last_name', 'username','date_joined']

class DepartmentFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(label='name', lookup_expr='icontains')
#     email = django_filters.CharFilter(label='Email', lookup_expr='icontains')
#     last_name = django_filters.CharFilter(label='Last name', lookup_expr='icontains')
#     username = django_filters.CharFilter(label='Username', lookup_expr='icontains')
#     date_joined = django_filters.DateFilter(label='Entry date', lookup_expr='exact')

    class Meta:
        model = Department
        fields = ['name']


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

class TaskHistoryFilter(django_filters.FilterSet):
    class Meta:
        model=TaskHistory
        # fields= '__all__'
        fields ={
                'group':['icontains'],
                'activity_name':['icontains']
        }
        labels={
                'employee'
                'activity_name':'Task',
                'group':'Group',
        }

class TaskFilter(django_filters.FilterSet):
    class Meta:
        model=Task
        # fields= '__all__'
        fields ={
                'group':['icontains'],
                'activity_name':['icontains']
        }
        labels={
                'activity_name':'Task',
                'group':'Group',
        }

class RequirementFilter(django_filters.FilterSet):
    class Meta:
        model=Requirement
        # fields= '__all__'
        fields ={
        'category':['icontains'],
        'status':['icontains'],
        'is_active':['icontains'],
        'app':['icontains']
        }
    
class FoodFilter(django_filters.FilterSet):
    office_location = django_filters.CharFilter(label='Location', lookup_expr='icontains')
    supplier = django_filters.CharFilter(label='Supplier', lookup_expr='icontains')
    item = django_filters.CharFilter(label='Item', lookup_expr='icontains')

    class Meta:
        model=Food
        # fields='__all__'
        fields ={'office_location','supplier','item','created_at'}
    
# ==================================INVESTING MODELS==================================================

class ReturnsFilter(django_filters.FilterSet):
    symbol = django_filters.CharFilter(label='Symbol', lookup_expr='icontains')
    action = django_filters.CharFilter(label='Type', lookup_expr='icontains')
    event = django_filters.CharFilter(label='Action', lookup_expr='icontains')
    date = django_filters.DateFilter(label='Date', field_name='date')

    class Meta:
        fields = ['symbol', 'action', 'event','date']
