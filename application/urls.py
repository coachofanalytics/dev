from django.urls import path, include
from . import views
from .views import codawcagslist_view,wcag_create_view
app_name = 'application'
urlpatterns = [
    # path('application/', include('application.urls')),
    #=============================USERS VIEWS=====================================
    #path('', views.home, name='home'),

    path('wcaglist/', views.codawcagslist_view, name='wcaglist'),
    path('openaicreate/', views.wcag_create_view, name='openaicreate'),
    #path('propertyupdate/<int:pk>/',views.company_properties_update,name='propertyupdate'),
    #path('propertydelete/<int:pk>/',views.company_properties_delete,name='propertydelete'),
    #path('propertydetail/<int:pk>/',views.company_properties_detail,name='propertydetail'),
]
