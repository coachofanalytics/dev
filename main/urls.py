from django.urls import path

from . import views
# from .utils import convert_html_to_pdf

app_name = 'main'
urlpatterns = [
    path('', views.home_view, name='home'),
    #=======================SERVICES=====================================
    path('newservice/', views.ServiceCreateView.as_view(template_name='main/form.html'), name='newservice'),
    path('services/', views.services, name='services'),
    path("display_service/<str:slug>/", views.display_service, name="display_service"),
    path("display_plans/<str:slug>/", views.service_plans, name="service_plans"),
    path("location_update/<str:pk>/", views.location_update, name="location_update"),

    #==============location==============================================
    path("location_list", views.location_list, name="account-location_list"),
    path("location_create", views.location_create, name="location_create"),
    path("location_update/<str:pk>/", views.location_update, name="location_update"),



    path("servicecategory_list", views.servicecategory_list, name="accounts-servicecategory_list"),
    path('servicecategory_create/', views.servicecategory_create, name='servicecategory_create'),
    path('services/<int:pk>/update/', views.servicecategory_update, name='servicecategory_update'),
    
    #==============DEPARTMENTS==============================================location_update
    #==============DEPARTMENTS==============================================
    #---------------HUMAN RESOURCE--------------------#

    #-----------------------------FINANCE--------------------#
       
        #--------------------------MANAGEMENT--------------------#
    #----------------------------IT-------------------------#
        path('it/', views.it, name='it'),
    #-----------------------README-------------------------#
    path('newusecase/', views.UseCaseCreateView.as_view(template_name='main/form.html'), name='newusecase'),
    path('display_usecases/', views.display_usecases, name='display_usecases'),

   #==============ERRORS==============================================
    path('400Error/', views.error400, name='400error'),
    path('403Error/', views.error403, name='403error'),
    path('404Error/', views.error404, name='404error'),
    path('500Error/', views.error500, name='500error'),

    path('400/', views.hendler400, name='400-error'),
    path('403/', views.hendler403, name='403-error'),
    path('404/', views.hendler404, name='404-error'),
    path('500/', views.hendler500, name='500-error'),

    #===========company records=======


]