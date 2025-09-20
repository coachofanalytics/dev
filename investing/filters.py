import django_filters
from .models import Portifolio


class PortfolioFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter(label="Is_active")

    class Meta:
        model = Portifolio
        fields = [
            "is_active",
        ]
