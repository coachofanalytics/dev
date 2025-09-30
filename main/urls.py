from django.urls import path
from . import views
from .views import AboutView

app_name = "main"

urlpatterns = [
    # Main pages
    path('', views.layout, name='layout'),
    path('team/', views.team_list, name='team_view'),
    path('history/', views.History, name='history'),
    path('services/', views.service_list, name='service_list'),
    # path('gallery/', views.gallery_list, name='gallery_list'),
    path('news/', views.news_list, name='news_list'),
    path('contact-us/', views.contact_us_list, name='contact_us_list'),
    path('about/', AboutView.as_view(), name='about'),

    # Donation CRUD
    path('donation/', views.donation_list, name='donation_list'),
    path('donation/add/', views.donation_add, name='donation_add'),
    path('donation/<int:pk>/edit/', views.donation_edit, name='donation_edit'),
    path('donation/<int:pk>/delete/', views.donation_delete, name='donation_delete'),
    path('donation/<int:pk>/details/', views.donation_details, name='donation_details'),

    # Error pages
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
