from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Main dashboard
    path('', views.unified_dashboard, name='unified_dashboard'),
    path('overview/', views.dashboard_overview, name='dashboard_overview'),
    path('departments/', views.unified_department_view, name='unified_department'),
    path('departments/<str:department_slug>/', views.unified_department_view, name='unified_department'),
    
    # Dashboard sections
    path('services/', views.service_catalog, name='service_catalog'),
    path('profile/', views.user_profile, name='user_profile'),
    path('notifications/', views.notifications, name='notifications'),
    path('analytics/', views.role_analytics, name='role_analytics'),
    path('settings/', views.user_settings, name='user_settings'),
    
    # Widget management
    path('widgets/add/', views.add_widget, name='add_widget'),
    path('widgets/<int:widget_id>/remove/', views.remove_widget, name='remove_widget'),
    path('widgets/reorder/', views.reorder_widgets, name='reorder_widgets'),
    
    # Service tracking
    path('services/<int:service_id>/access/', views.track_service_access, name='track_service_access'),
]

