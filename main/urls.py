from django.urls import path, include
from main.views import AboutView
from . import views
# from .utils import convert_html_to_pdf
from accounts import views as account_views

app_name = 'main'
urlpatterns = [
    path('', views.layout, name='layout'),
    path('team/', views.team_list, name='team_view'),
    path('support/', views.support_page, name='support_page'),
    path('history',views.History, name ='history'),
    path('services/', views.service_list, name='service_list'),
    path('data/healthcare-info/', views.healthcare_info, name='healthcare_info'),
    path('healthcare/insurance-support/', views.insurance_support, name='insurance_support'),
    path('healthcare/insurance-support/api/recommend/', views.ai_recommendation_api, name='ai_recommendation_api'),
    path('healthcare/insurance-support/api/inquiry/', views.submit_expert_inquiry, name='submit_expert_inquiry'),
    path('healthcare/insurance-support/download-csv/', views.download_comparison_csv, name='download_comparison_csv'),
    path('join_team/', views.join_team, name='join_team'),
    path('join_team/submit/', views.submit_join, name='submit_join'),
    path('volunteer_success/', views.volunteer_success, name='volunteer_success'),
    path('consular-assistance/', views.book_consular_consultation, name='book_consular_consultation'),

    path('data/consular/information-updates/', views.consular_information_updates, name='consular_information_updates'),
    
    # Communities App Integration - now handled at project level (coda_project/urls.py)
    # path('communities/', include('main.urls_communities')),
    # path('gallery/', views.gallery_list, name='gallery_list'),
    # path('news/add/', views.news_create, name='news_create'),
    # path('news/<int:id>/edit/', views.news_edit, name='news_edit'),
    # path('news/<int:id>/delete/', views.news_delete, name='news_delete'),
    path('news/<int:id>/', views.news_detail, name='news_detail'),
    path('news/', views.news_list, name='news_list'),
    # Document Services - frontend-only routes
    path('document-services/', views.document_services_dashboard, name='document_services_dashboard'),
    path('document-services/drafts/', views.document_services_drafts, name='document_services_drafts'),
    path('document-services/documents/', views.document_services_documents, name='document_services_documents'),
    path('document-services/history/', views.document_services_history, name='document_services_history'),
    path('document-services/application/', views.document_services_application_form, name='document_services_application_form'),
    path('document-services/summary/', views.document_services_summary, name='document_services_summary'),
    path('document-services/payment/', views.document_services_payment_summary, name='document_services_payment_summary'),
    path('document-services/notifications/', views.document_services_notifications, name='document_services_notifications'),
    path('document-services/notification-preferences/', views.document_services_notification_preferences, name='document_services_notification_preferences'),
    path('document-services/profile/', views.document_services_profile, name='document_services_profile'),
    path('document-services/settings/', views.document_services_settings, name='document_services_settings'),
    path('document-services/support-help/', views.document_services_support_help, name='document_services_support_help'),
    path('contract-us/', views.contact_us_list, name='contact_us_list'),
    path('about/', AboutView.as_view(), name='about'),
    # ===== Crisis/Emergency Features =====
    path('crisis_page/', views.crisis_page, name='crisis_page'),
    path('subscribe_alerts/', views.subscribe_alerts, name='subscribe_alerts'),
    path('activate_helpline/', views.activate_helpline, name='activate_helpline'),
    
    # ===== Donor Management =====
    path('donors/', views.donor_list, name='donor_list'),
    path('add-donor/', views.add_donor, name='add_donor'),
    path('donor/<int:pk>/', views.donor_details, name='donor_details'),
    path('edit-donor/<int:pk>/', views.edit_donor, name='edit_donor'),
    path('delete-donor/<int:pk>/', views.delete_donor, name='delete_donor'),
    
    # ===== Message Management =====
    path('messages/', views.message_list, name='message_list'),
    path('message/<int:pk>/', views.message_details, name='message_details'),
    path('edit-message/<int:pk>/', views.edit_message, name='edit_message'),
    path('delete-message/<int:pk>/', views.delete_message, name='delete_message'),
    path('add-message/', views.add_message, name='add_message'),

    # ===== Donation Management =====
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

    path('', views.home, name='home'),
    path('find-doctors/', views.find_doctors, name='find_doctors'),
    path('api/doctor/<int:pk>/', views.doctor_profile_api, name='doctor_profile_api'),
    path('api/doctor/<int:pk>/book/', views.book_appointment, name='book_appointment'),
    # Scholarship search (root-level /scholarship/)
    path('scholarship/', views.scholarship_search, name='scholarship_search'),

    path('education/', views.education_landing, name = 'education_landing'),
    path('education/scholarship/',views.education_landing, name = 'education_scholarship'),
    path('education/training/',views.education_training, name = 'education_training'),
    path('ai-courses/', views.ai_course_discovery, name='ai_course_discovery'),
    path('education/courses/register/', views.course_register, name='course_register'),
    path('education/request-mentorship/', views.request_mentorship, name='request_mentorship'),

    path('ai_refresh_scholarships/', views.ai_refresh_scholarships, name='ai_refresh_scholarships'),


    path('scholarship/add/', views.add_scholarship, name ='add_scholarship'),
    path('scholarship/edit/<int:pk>', views.scholarship_edit, name ='scholarship_edit'),
    path('scholarship/delete/<int:pk>', views.scholarship_delete, name ='scholarship_delete'),

    path('course/', views.course_crud, name ='course_crud'),
    path('course/add/', views.add_course, name='add_course'),
    path('course/edit/<int:pk>', views.edit_course, name='edit_course'),
    path('course/delete/<int:pk>',views.delete_course, name='delete_course'),
    
    # ============================================
    # MEMBERJOIN APP URLS (INTEGRATED)
    # ============================================
    # path('membership', views.member_home, name='member_home'),
    path('governance/', views.governance_list, name='governance_list'),
    path('governance/create/', views.governance_create, name='governance_create'),
    path('governance/<int:pk>/', views.governance_detail, name='governance_detail'),
    path('governance/<int:pk>/update/', views.governance_update, name='governance_update'),
    path('governance/<int:pk>/delete/', views.governance_delete, name='governance_delete'),

    # Quick add user endpoint
    path('quick-add-user/', views.quick_add_user, name='quick_add_user'),
    # In your app's urls.py
    path('test-user-endpoint/', views.test_user_endpoint, name='test_user_endpoint'),
    path('login/', account_views.custom_login_view, name='login'),
]

    
