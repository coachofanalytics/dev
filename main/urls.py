from django.urls import path
from django.urls import path
# from django.shortcuts import render
from django.views.generic import ListView
# from .models import ClientAvailability
from django.urls import path, include
# from .utils import convert_html_to_pdf
from django.urls import path
from .views import VolunteerListView
app_name = 'main'
urlpatterns = [
    
    # # path('', views.layout, name='layout'),
    # #=======================SERVICES=====================================
    # path('newservice/',ServiceCreateView.as_view(template_name='main/form.html'), name='newservice'),
    # path('services/',services, name='services'),
    # path("display_service/<str:slug>/",display_service, name="display_service"),
    # path("display_plans/<str:slug>/", service_plans, name="service_plans"),
    # path('client_availability/', views.client_availability_view, name='client_availability'),
    # path('admin/', admin.site.urls),
    # path('', include('main.urls')),
    #==============DEPARTMENTS==============================================
    #==============DEPARTMENTS==============================================
    #---------------HUMAN RESOURCE--------------------#

    #-----------------------------FINANCE--------------------#
       
        #--------------------------MANAGEMENT--------------------#
#     #----------------------------IT-------------------------#
#     path('it/', views.it, name='it'),
#     #-----------------------README-------------------------#
#     path('newusecase/', views.UseCaseCreateView.as_view(template_name='main/form.html'), name='newusecase'),
#     path('display_usecases/', views.display_usecases, name='display_usecases'),
#     # path('', include('project.urls')),

#    #==============ERRORS==============================================
#     path('400Error/', views.error400, name='400error'),
#     path('403Error/', views.error403, name='403error'),
#     path('404Error/', views.error404, name='404error'),
#     path('500Error/', views.error500, name='500error'),

#     path('400/', views.hendler400, name='400-error'),
#     path('403/', views.hendler403, name='403-error'),
#     path('404/', views.hendler404, name='404-error'),
#     path('500/', views.hendler500, name='500-error'),


    # path('', VolunteerListView.as_view(), name='list'),      # ✅ CORRECT
    # path('create/', VolunteerCreateView.as_view(), name='create'),  # ✅ CORRECT


    #===========company records=======
]# main/views.py
# from rest_framework import generics
# from .models import ServiceCategory


# class ServiceCategoryCreateView(generics.CreateAPIView):
#     queryset = ServiceCategory.objects.all()
#     serializer_class = ServiceCategorySerializer
# main/urls.py
from django.urls import path
from . import views
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),  # This enables the admin panel at /admin/
]

urlpatterns = [
    path('', views.home, name='main_home'),
]

from django.urls import path
from .views import WCAGStandardWebsiteListView

urlpatterns = [
   path('websites/', WCAGStandardWebsiteListView.as_view(), name='website-list')
]

from django.urls import path
from django.views.generic import RedirectView
from .views import WCAGStandardWebsiteListView

urlpatterns = [
    path('', RedirectView.as_view(url='/websites/')),  # 👈 redirect root to websites/
    path('websites/', WCAGStandardWebsiteListView.as_view(), name='website-list'),
]
from django.urls import path
from .views import home, WCAGStandardWebsiteListView

urlpatterns = [
    path('', home, name='home'),  # 👈 homepage
    path('websites/', WCAGStandardWebsiteListView.as_view(), name='website-list'),
]

from django.urls import path
from .views import home, WCAGStandardWebsiteListView, WCAGStandardWebsiteCreateView
from django.urls import path
from .views import (
    WCAGStandardWebsiteListView,
    WCAGStandardWebsiteDetailView,
    WCAGStandardWebsiteCreateView,
    WCAGStandardWebsiteUpdateView,
    WCAGStandardWebsiteDeleteView,
)

urlpatterns = [
    path('websites/', WCAGStandardWebsiteListView.as_view(), name='website-list'),
    path('websites/add/', WCAGStandardWebsiteCreateView.as_view(), name='website-add'),
    path('websites/<int:pk>/', WCAGStandardWebsiteDetailView.as_view(), name='website-detail'),
    path('websites/<int:pk>/edit/', WCAGStandardWebsiteUpdateView.as_view(), name='website-edit'),
    path('websites/<int:pk>/delete/', WCAGStandardWebsiteDeleteView.as_view(), name='website-delete'),
]
