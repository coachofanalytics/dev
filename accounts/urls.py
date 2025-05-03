from django.urls import path
from . import views
from .views import (
                    ClientDetailView,
                    ClientUpdateView,
                    ClientDeleteView
                    )

app_name = 'application'
urlpatterns = [
    #=============================USERS VIEWS=====================================
    path('', views.home, name='home'),
    path('join/', views.join, name='join'),
    path('login/', views.login_view, name='account-login'),
    path('profile/', views.profile, name='account-profile'),
    #=============================CREDENTIALS VIEWS=====================================
    path('credentials/', views.credential_view, name='account-crendentials'),
    path('newcredentialcategory/', views.newcredentialCategory, name='account-newcredentialcategory'),
    path('newcredential/', views.newcredential, name='account-newcredentials'),
    #=============================CLIENTS VIEWS=====================================
    path('clients/', views.clientlist, name='clients'),
    path('client/<int:pk>/update/', ClientUpdateView.as_view(), name='client-update'),
    path('client/<int:pk>/', ClientDetailView.as_view(), name='client-detail'),
    path('client/<int:pk>/delete/', ClientDeleteView.as_view(), name='client-delete'),
    #=============================EMPLOYEES VIEWS=====================================
    path('employees/', views.Employeelist, name='employees'),
 
]