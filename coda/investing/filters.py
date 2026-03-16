import django_filters
from .models import Portfolio


class PortfolioFilter(django_filters.FilterSet):
    is_active = django_filters.BooleanFilter(label="Is_active")

    class Meta:
        model = Portfolio
        fields = [
            "is_active",
        ]

