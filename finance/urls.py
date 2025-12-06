from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path("finance/", views.finance_dashboard, name="finance_dashboard"),
    path('OverBoughtSold/', views.OverBoughtSold_list, name='OverBoughtSold_list'),
    path("overboughtsold_add/", views.overboughtsold_create, name="overboughtsold_create"),
]
