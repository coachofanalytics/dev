from django.urls import path
from . import views

app_name = 'main'
urlpatterns = [
    
    #==============ERRORS==============================================
    path('', views.home_view, name='home'),
    path('Gallery_list/', views.Gallery_list, name='Gallery_list'),
    path('gallery_create/', views.gallery_create, name='gallery_create'),
    path('Gallery_update/<int:pk>/', views.Gallery_update, name='Gallery_update'),
    path('gallery_delete/<int:pk>/', views.gallery_delete, name='gallery_delete'),
    path('gallery_detail/<int:pk>/', views.gallery_detail, name='gallery_detail'), 
    path('contact_message_list/', views.contact_message_list, name='contact_message_list'),
    path('team/', views.about, name='team'),
    path('contact_message_create/', views.contact_message_create, name='contact_message_create'),

    #=======================SERVICES=====================================
    # path('newservice/', views.ServiceCreateView.as_view(template_name='main/form.html'), name='newservice'),
    # path('services/', views.services, name='services'),
    # path('update/<int:pk>/', views.ServiceUpdateView.as_view(template_name='main/form.html'), name='update_service'),
    # path('delete/<int:id>/', views.delete_service, name='delete_service'),
    #==============DEPARTMENTS==============================================
    path('newprofile/', views.UserCreateView.as_view(template_name='main/form.html'), name='newprofile'),
    path('updateprofile/<int:pk>/', views.UserProfileUpdateView.as_view(template_name='main/form.html'), name='update_profile'),

    #==============ERRORS==============================================
    path('400Error/', views.error400, name='400error'),
    path('403Error/', views.error403, name='403error'),
    path('404Error/', views.error404, name='404error'),
    path('500Error/', views.error500, name='500error'),
    path('errors/', views.template_errors, name='template_errors'),

    # path('400/', views.hendler400, name='400-error'),
    # path('403/', views.handler403, name='403-error'),
    # path('404/', views.handler404, name='404-error'),
    # path('500/', views.handler500, name='500-error'),
]
