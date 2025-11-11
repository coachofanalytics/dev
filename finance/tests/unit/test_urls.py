from django.urls import path
from .test_views import (
    OverBoughtSoldListViewTest,
)  # Ensure you import the function-based view correctly

urlpatterns = [
    path(
        "test/overboughtsold/",
        OverBoughtSoldListViewTest,
        name="overboughtsold_list_test",
    ),  # URL name 'overboughtsold_list_test'
]
