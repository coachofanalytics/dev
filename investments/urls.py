from django.urls import path
from . import views

   
app_name = 'investments'

urlpatterns = [
    path('investments', views.investments_dashboard, name='investments'),
    path('investments_list', views.InvestmentStrategy_list, name='InvestmentStrategy_list'),
]