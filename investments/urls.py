from django.urls import path
from . import views

app_name = "investments"

urlpatterns = [
    path("investments/", views.investments_dashboard, name="investments_dashboard"),
    path("invest_list/", views.investment_list, name="investment_list"),
    path("investments_creat/", views.investment_create, name="investment_create"),
]
