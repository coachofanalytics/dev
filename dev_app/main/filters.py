import django_filters 
from accounts.models import CustomerUser


class UserFilter(django_filters.FilterSet):
    email = django_filters.CharFilter(label='Email', lookup_expr='icontains')
    first_name = django_filters.CharFilter(label='First name', lookup_expr='icontains')
    last_name = django_filters.CharFilter(label='Last name', lookup_expr='icontains')
    username = django_filters.CharFilter(label='Username', lookup_expr='icontains')
    date_joined = django_filters.DateFilter(label='Entry date', lookup_expr='exact')

    class Meta:
        model = CustomerUser
        fields = ['email', 'first_name', 'last_name', 'username','date_joined']



class TaskHistoryFilter(django_filters.FilterSet):
    pass
#     class Meta:
#         model=TaskHistory
#         # fields= '__all__'
#         fields ={
#                 'group':['icontains'],
#                 'activity_name':['icontains']
#         }
#         labels={
#                 'employee'
#                 'activity_name':'Task',
#                 'group':'Group',
#         }

class TaskFilter(django_filters.FilterSet):
    pass
#     class Meta:
#         model=Task
#         # fields= '__all__'
#         fields ={
#                 'group':['icontains'],
#                 'activity_name':['icontains']
#         }
#         labels={
#                 'activity_name':'Task',
#                 'group':'Group',
#         }

class RequirementFilter(django_filters.FilterSet):
    pass
#     class Meta:
#         model=Requirement
#         # fields= '__all__'
#         fields ={
#         'category':['icontains'],
#         'status':['icontains'],
#         'is_active':['icontains'],
#         }
    
class FoodFilter(django_filters.FilterSet):
    pass
#     class Meta:
#         model=Food
#         # fields='__all__'
#         fields ={'supplier','item'}
    
# ==================================INVESTING MODELS==================================================

class ReturnsFilter(django_filters.FilterSet):
    symbol = django_filters.CharFilter(label='Symbol', lookup_expr='icontains')
    action = django_filters.CharFilter(label='Type', lookup_expr='icontains')
    event = django_filters.CharFilter(label='Action', lookup_expr='icontains')

    class Meta:
        model = CustomerUser
        fields = ['symbol', 'action', 'event']