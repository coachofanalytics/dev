import django_filters
from django_filters import DateFilter
from .forms import *
from .models import *


class ApplicationFilter(django_filters.FilterSet):
    # start_date=DateFilter(field_name="upload_date",lookup_expr='gte')
    # end_date=DateFilter(field_name="upload_date",lookup_expr='lte')
    class Meta:
        model = Application
        fields = "__all__"
        exclude = ["username", "phone", "email", "country", "resume"]
