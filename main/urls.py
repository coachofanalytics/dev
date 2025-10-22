from django.urls import path
from main.views import AboutView

from . import views

# from .utils import convert_html_to_pdf

app_name = 'main'
urlpatterns = [
    path('', views.layout, name='layout'),
    path('team/', views.team_list, name='team_view'),
    path('history',views.History, name ='history'),
    path('services/', views.service_list, name='service_list'),
    # path('gallery/', views.gallery_list, name='gallery_list'),
    path('news/', views.news_list, name='news_list'),
    path('contract-us/', views.contact_us_list, name='contact_us_list'),
    path('about/', AboutView.as_view(), name='about'),
    path('donation/', views.donation_list, name='donation'),
    path('donation_create/', views.Donation_create, name='donation_create'),
    path("donation/<int:pk>/update/", views.Donation_update, name="donation_update"),
    path("donation/<int:pk>/delete/", views.Donation_delete, name="donation_delete"),
    path("donation/<int:pk>/details/", views.Donation_details, name="donation_details"),
    path("courses/", views.coursesListingAndReg, name="courses"),
    
  
    
    
   #==============ERRORS==============================================
    path('400Error/', views.error400, name='400error'),
    path('403Error/', views.error403, name='403error'),
    path('404Error/', views.error404, name='404error'),
    path('500Error/', views.error500, name='500error'),
    path('errors/', views.template_errors, name='template_errors'),

    path('400/', views.hendler400, name='400-error'),
    path('403/', views.hendler403, name='403-error'),
    path('404/', views.hendler404, name='404-error'),
    path('500/', views.hendler500, name='500-error'),

]
