from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    #=============================USERS VIEWS=====================================
    path('', views.home, name='home'),
    path('join/', views.join, name='join'),
    path('login/', views.login_view, name='account-login'),
    path('profile/', views.profile, name='account-profile'),
    path('trackers/', views.trackers_list_view, name='trackers'),
    path('trackers_create/', views.TrackersCreateView, name='TrackersCreateView'),
    path('trackers/<int:pk>/update/', views.TrackersUpdateView, name='trackers_update'),
    path('trackers/<int:pk>/detail/', views.TrackersDetailView, name='trackers_detail'),
    path('trackers/<int:pk>/delete/', views.TrackersDeleteView, name='trackers_delete'),
 
    
]