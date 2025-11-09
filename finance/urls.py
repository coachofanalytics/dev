from django.urls import path
from . import views

urlpatterns = [
    path('pay', views.home_view, name='home'),


    path("overboughtsold/", views.OverBoughtSold, name="OverBoughtSold_list"),
    path("payments_information/", views.PaymentInformation_list, name="PaymentInformation_list"),

]
