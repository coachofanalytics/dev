from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    #=============================USERS VIEWS=====================================
    path('accounts', views.home, name='home'),
    path('create_profile/', views.create_profile, name='account-create_profile'),
    path('login/', views.login_view, name='account-login'),
    path('profile/', views.profile, name='account-profile'),
]