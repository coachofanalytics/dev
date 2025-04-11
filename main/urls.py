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
    path('Contact_Message_update/<int:pk>/', views.Contact_Message_update, name='Contact_Message_update'),
    path('ContactMessage_delete/<int:pk>/', views.ContactMessage_delete, name='ContactMessage_delete'),
    path('ContactMessage_detail/<int:pk>/', views.ContactMessage_detail, name='ContactMessage_detail'),
    path('Description_list/', views.Description_list, name='Description_list'),
    path('Description_create/', views.Description_create, name='Description_create'),
    path('Description_update/<int:pk>/', views.Description_update, name='Description_update'),
    path('Description_delete/<int:pk>/', views.Description_delete, name='Description_delete'),
    path('Description_detail/<int:pk>/', views.Description_detail, name='Description_detail'),
    path('Description2_list/', views.Description2_list, name='Description2_list'),
    path('Description2_create/', views.Description2_create, name='Description2_create'),
    path('Description2_update/<int:pk>/', views.Description2_update, name='Description2_update'),
    path('Description2_delete/<int:pk>/', views.Description2_delete, name='Description2_delete'),
    path('Description2_detail/<int:pk>/', views.Description2_detail, name='Description2_detail'),
    path('Testimonial_list/', views.Testimonial_list, name='Testimonial_list'),
    path('Testimonial_create/', views.Testimonial_create, name='Testimonial_create'),
    path('Testimonial_update/<int:pk>/', views.Testimonial_update, name='Testimonial_update'),
    path('Testimonial_delete/<int:pk>/', views.Testimonial_delete, name='Testimonial_delete'),
    path('Testimonial_detail/<int:pk>/', views.Testimonial_detail, name='Testimonial_detail'),
    path('Testimonial2_list/', views.Testimonial2_list, name='Testimonial2_list'),
    path('Testimonial2_create/', views.Testimonial2_create, name='Testimonial2_create'),


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
