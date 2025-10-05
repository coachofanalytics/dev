from unicodedata import category
import django_filters 
from django_filters import DateFilter
from .forms import *
from .models import *
from django.contrib.auth import get_user_model,login,authenticate

#User=settings.AUTH_USER_MODEL
User = get_user_model()


class InterviewFilter(django_filters.FilterSet):
    #start_date=DateFilter(field_name="upload_date",lookup_expr='gte')
    #end_date=DateFilter(field_name="upload_date",lookup_expr='lte')
    class Meta:
        model=Interviews
        fields='__all__'
        exclude=['upload_date','doc','link','is_active','featured']
        
class QuestionFilter(django_filters.FilterSet):
    #start_date=DateFilter(field_name="upload_date",lookup_expr='gte')
    #end_date=DateFilter(field_name="upload_date",lookup_expr='lte')
    class Meta:
        model=Prep_Questions
        # fields='__all__'
        fields ={
        'company':['icontains'],
        'question':['icontains'],
        'response':['icontains'],
        }
        # exclude=['upload_date','doc','link','is_active','featured']
        


class ResponseFilter(django_filters.FilterSet):
    #start_date=DateFilter(field_name="upload_date",lookup_expr='gte')
    #end_date=DateFilter(field_name="upload_date",lookup_expr='lte')
    class Meta:
        model=Prep_Questions
        # model=UserAnswerStatus
        # fields='__all__'
        fields ={
        'company':['icontains'],
        'category':['icontains'],
        }
        # exclude=['upload_date','doc','link','is_active','featured']


class BitrainingFilter(django_filters.FilterSet):
    #start_date=DateFilter(field_name="upload_date",lookup_expr='gte')
    #end_date=DateFilter(field_name="upload_date",lookup_expr='lte')
    class Meta:
        model=FeaturedCategory
        fields='__all__'
        exclude=['updated_at','description','created_at','is_active','created_by']
