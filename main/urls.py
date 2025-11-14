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
    path('data/healthcare-info/', views.healthcare_info, name='healthcare_info'),
    # path('gallery/', views.gallery_list, name='gallery_list'),
    path('news/', views.news_list, name='news_list'),
    path('contract-us/', views.contact_us_list, name='contact_us_list'),
    path('about/', AboutView.as_view(), name='about'),
    path('donors/', views.donor_list, name='donor_list'),
    path('add-donor/', views.add_donor, name='add_donor'),
    path('donor/<int:pk>/', views.donor_details, name='donor_details'),
    path('edit-donor/<int:pk>/', views.edit_donor, name='edit_donor'),
    path('delete-donor/<int:pk>/', views.delete_donor, name='delete_donor'),
    path('messages/', views.message_list, name='message_list'),  # New URL pattern for contact messages
    path('message/<int:pk>/', views.message_details, name='message_details'),  # New URL pattern for message details
    path('edit-message/<int:pk>/', views.edit_message, name='edit_message'),  # New URL pattern for editing messages
    path('delete-message/<int:pk>/', views.delete_message, name='delete_message'),  # New URL pattern for deleting messages
    path('add-message/', views.add_message, name='add_message'),  # New URL pattern for adding messages

    path('donation/', views.donation_list, name='donation'),
    path('donation/<int:pk>/', views.DonationDetailView.as_view(), name='donation_detail'),
    path('donation/add/', views.DonationCreateView.as_view(), name='donation_add'),
    path('donation/<int:pk>/edit/', views.DonationEditView.as_view(), name='donation_edit'),
    path('donation/<int:pk>/delete/', views.DonationDeleteView.as_view(), name='donation_delete'),
    
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

    path('data/medical-resource-form/', views.medical_resource_form, name='medical_resource_form'),
    # Scholarship search (root-level /scholarship)
    path('scholarship', views.scholarship_search, name='scholarship_search'),

    # Education and training views

    path('education/', views.education_landing, name = 'education_landing'),
    path('education/scholarship/',views.education_landing, name = 'education_scholarship'),
    path('education/training/',views.education_landing, name = 'education_training'),
    path('education/courses/register/', views.course_register, name='course_register'),
    path('education/request-mentorship/', views.request_mentorship, name='request_mentorship'),

]    
