from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    #=============================USERS VIEWS=====================================
    path('', views.home, name='home'),
    path('join/', views.join, name='join'),
    path('login/', views.login_view, name='account-login'),
    path('profile/', views.profile, name='account-profile'),
    path('Tracker/', views.Tracker_list, name='account-Tracker_list'),
    path('add/', views.Tracker_create, name='account-Tracker_create'),
    path('tracker/update/<int:pk>/', views.Tracker_update,name='account-Tracker_update'),
]