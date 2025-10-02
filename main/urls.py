from django.urls import path
from django.urls import path
from . import views
from django.urls import path
from . import views

app_name = "main"  # ✅ Required for namespacing
from django.urls import path
from . import views  # ✅ This is okay

app_name = "main"

urlpatterns = [
    path('', views.home, name='home'),  # ✅ At least one valid path
]
 

from django.http import HttpResponse

def test_view(request):
    return HttpResponse("It works!")

urlpatterns = [
    path('', test_view, name='home'),
]
from django.http import HttpResponse

def temp_view(request):
    return HttpResponse("Temporary view works!")

urlpatterns = [
    path('', temp_view, name='home'),  # replace views.home with temp_view
]


def layout(request):
    return (request, 'main/layout.html')  # Adjust template path as needed

    #=======================SERVICES=====================================
    path('newservice/', views.ServiceCreateView.as_view(template_name='main/form.html'), name='newservice'),
    path('services/', views.services, name='services'),
    path("display_service/<str:slug>/", views.display_service, name="display_service"),
    path("display_plans/<str:slug>/", views.service_plans, name="service_plans"),
    #==============DEPARTMENTS==============================================
    #==============DEPARTMENTS==============================================
    # ---------------HUMAN RESOURCE--------------------#

    #-----------------------------FINANCE--------------------#
       
        #--------------------------MANAGEMENT--------------------#
    #----------------------------IT-------------------------#
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


