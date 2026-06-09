from django.urls import path, include
from main.views import AboutView
from . import views
# from .utils import convert_html_to_pdf

app_name = 'main'
urlpatterns = [
    path('', views.layout, name='layout'),
    path('team/', views.team_list, name='team_view'),
    path('history',views.history, name ='history'),
    path('services/', views.service_list, name='service_list'),
    path('consular-assistance/', views.consular_assistance, name='consular_assistance'),
    path('consular-assistance/book-consultation/', views.book_consular_consultation, name='book_consular_consultation'),
    path('data/consular/information-updates/', views.consular_information_updates, name='consular_information_updates'),
    path('data/consular/press-releases/', views.consular_press_releases, name='consular_press_releases'),
    path('data/consular/embassy-news/', views.consular_embassy_news, name='consular_embassy_news'),
    path('data/consular/community-updates/', views.consular_community_updates, name='consular_community_updates'),
    path('data/consular/all-updates/', views.consular_all_updates, name='consular_all_updates'),
    path('legal-immigration-guidance/', views.legal_immigration_guidance, name='legal_immigration_guidance'),
    # Healthcare Information
    path('data/healthcare-info/', views.healthcare_info, name='healthcare_info'),
    path('data/medical-resource-form/', views.medical_resource_form, name='medical_resource_form'),
    path('healthcare/insurance-support/', views.insurance_support, name='insurance_support'),
    path('healthcare/insurance-support/api/recommend/', views.ai_recommendation_api, name='ai_recommendation_api'),
    path('healthcare/insurance-support/api/inquiry/', views.submit_expert_inquiry, name='submit_expert_inquiry'),
    path('healthcare/insurance-support/download-csv/', views.download_comparison_csv, name='download_comparison_csv'),
    path('find-doctors/', views.find_doctors, name='find_doctors'),
    path('api/doctor/<int:pk>/', views.doctor_profile_api, name='doctor_profile_api'),
    path('api/doctor/<int:pk>/book/', views.book_appointment, name='book_appointment'),

    path('gallery/', views.gallery_list, name='gallery_list'),
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
    path('send_email/', views.send_notification, name='send_email'),
    path('gethelp/', views.gethelp_list, name='gethelp'),
    path('gethelp/<int:pk>/update/', views.gethelp_update, name='gethelp_update'),
    path('create_gethelp/', views.gethelp_create, name='create_gethelp'),
    path('gethelp/<int:pk>/delete/', views.gethelp_delete, name='gethelp_delete'),
    path('governance_list/', views.governance_list, name='governance_list'),
    path('governance/<int:pk>/update/',views.governance_update , name='governance_update'),
    path('create_governance/', views.governance_create, name='create_governance'),
    path('governance/<int:pk>/delete/', views.governance_delete, name='governance_delete'),
    path('donation',views.organization_list_view, name ='donationorganisation_list'),
    path('ourhistory',views.ourhistory, name ='ourhistory'),
    path('contact_us',views.contact_us, name ='contact_us'),

    # ===== Crisis Management =====
    path('crisis_page/', views.crisis_page, name='crisis_page'),
    path('subscribe_alerts/', views.subscribe_alerts, name='subscribe_alerts'),
    path('activate_helpline/', views.activate_helpline, name='activate_helpline'),

    # ===== Education & Training =====
    path('education/', views.education_landing, name='education_landing'),
    path('education/scholarship/', views.education_landing, name='education_scholarship'),
    path('education/training/', views.education_training, name='education_training'),
    path('education/courses/manage/', views.course_crud, name='course_crud'),
    path('education/courses/<int:pk>/edit/', views.edit_course, name='edit_course'),
    path('education/courses/<int:pk>/delete/', views.delete_course, name='delete_course'),
    path('scholarship/', views.scholarship_search, name='scholarship_search'),
    path('ai-courses/', views.ai_course_discovery, name='ai_course_discovery'),
    path('education/courses/register/', views.course_register, name='course_register'),
    path('education/request-mentorship/', views.request_mentorship, name='request_mentorship'),
    path('ai_refresh_scholarships/', views.ai_refresh_scholarships, name='ai_refresh_scholarships'),
    path('scholarship/add/', views.add_scholarship, name='add_scholarship'),
    path('scholarship/edit/<int:pk>', views.scholarship_edit, name='scholarship_edit'),
    path('scholarship/delete/<int:pk>', views.scholarship_delete, name='scholarship_delete'),

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
    # MEMBERSHIP & GOVERNANCE URLS
    # ============================================
    # path('membership', views.member_home, name='member_home'),  # Currently disabled
    path('governance/', views.governance_list, name='governance_list'),
    path('governance/create/', views.governance_create, name='governance_create'),
    path('governance/<int:pk>/', views.governance_detail, name='governance_detail'),
    path('governance/<int:pk>/update/', views.governance_update, name='governance_update'),
    path('governance/<int:pk>/delete/', views.governance_delete, name='governance_delete'),

    # Quick add user endpoint
    path('quick-add-user/', views.quick_add_user, name='quick_add_user'),
    # In your app's urls.py
    path('test-user-endpoint/', views.test_user_endpoint, name='test_user_endpoint'),
    path('test/', views.test, name='legal_service_test'),
    path('test/<int:pk>/edit/', views.test_edit, name='legal_service_test_edit'),
    path('test/<int:pk>/delete/', views.test_delete, name='legal_service_test_delete'),
    path('legal-services/', views.legalServiceListView, name='legal_service_list'),
    path('legal-services/create/', views.legalServiceCreateView, name='legalservice_create'),
    path("legal-services/<int:pk>/delete/",views.legalServiceDeleteView,name="legal_service_delete"),
    path("legal-services/<int:pk>/update/", views.legalServiceUpdateView, name="legal_service_update"),

    # ===== COP Phase 1 =====
    path(
        "placements/<int:placement_id>/originate/",
        views.originate_placement,
        name="cop_originate_placement",
    ),
    path(
        "packages/<int:package_id>/send/",
        views.send_contract_package,
        name="cop_send_package",
    ),
    path(
        "contracts/sign/<str:token>/",
        views.contract_sign,
        name="cop_contract_sign",
    ),
    path(
        "packages/<int:package_id>/",
        views.contract_package_detail,
        name="cop_package_detail",
    ),

    # ===== COP Frontend =====
    path("cop/", views.cop_dashboard, name="cop_dashboard"),
    path("cop/placements/", views.cop_placements, name="cop_placements"),
    path("cop/templates/", views.cop_templates, name="cop_templates"),
    path("cop/contracts/", views.cop_contracts, name="cop_contracts"),
    path(
        "cop/placements/<int:placement_id>/generate/",
        views.generate_package_view,
        name="cop_generate_package",
    ),
    path(
        "cop/packages/<int:package_id>/send/",
        views.send_package_view,
        name="cop_send_package_view",
    ),
    path(
        "cop/sign/<str:token>/",
        views.sign_view,
        name="cop_sign",
    ),
    path(
        "cop/packages/<int:id>/",
        views.renderContract,
        name="contract_view",
    )
]

    
