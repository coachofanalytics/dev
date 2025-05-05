from django.urls import path
from . import views
from .views import (
                    CredentialUpdateView
                    )

app_name = 'accounts'
urlpatterns = [
    #=============================USERS VIEWS=====================================
    path('', views.home, name='home'),
    path('join/', views.join, name='join'),
    path('login/', views.login_view, name='account-login'),
    path('profile/', views.profile, name='account-profile'),

    path('credentials/', views.credential_view, name='account-crendentials'),
    path('newcredentialcategory/', views.newcredentialCategory, name='account-newcredentialcategory'),
    path('newcredential/', views.newcredential, name='account-newcredentials'),
    path('credential/update/<int:pk>/', CredentialUpdateView.as_view(template_name="accounts/admin/forms/credential_form.html"), name='credential-update'),
    
    #=============================EMPLOYEES VIEWS=====================================
    path('employees/', views.Employeelist, name='employees'),
]