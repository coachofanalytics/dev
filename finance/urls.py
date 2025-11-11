from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path("finance/", views.finance_dashboard, name="finance_dashboard"),
    path("overboughtsold/", views.OverBoughtSold_list, name="overboughtsold_list"),
]
