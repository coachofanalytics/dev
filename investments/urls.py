from django.urls import path
from . import views

   
app_name = 'investments'

urlpatterns = [
    path('investments', views.investments_dashboard, name='investments'),
    path('investments_list', views.InvestmentStrategy_list, name='InvestmentStrategy_list'),
    path('investments_create', views.InvestmentStrategy_create, name='InvestmentStrategy_create'),
    path("investment/update/<int:pk>/",views.InvestmentStrategy_update,name="InvestmentStrategy_update"),
    path("investment/delete/<int:pk>/",views.InvestmentStrategy_delete,name="InvestmentStrategy_delete"),
]