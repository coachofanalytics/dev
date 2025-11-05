from django.urls import path

from . import views
from . import views_team_management
# from .utils import convert_html_to_pdf

app_name = 'main'
urlpatterns = [
    path('', views.layout, name='layout'),
    
    #=======================TEAM MANAGEMENT (ADMIN)=====================================
    # IMPORTANT: Specific action URLs MUST come BEFORE the category_name catch-all!
    path('team-management/', views_team_management.team_management_dashboard, name='team_management_dashboard'),
    path('team-management/recalculate-points/', views_team_management.recalculate_all_points, name='recalculate_all_points'),
    path('team-management/assign/<int:user_id>/<str:category_name>/', views_team_management.assign_member_to_category, name='assign_member_to_category'),
    path('team-management/remove/<int:user_id>/<str:category_name>/', views_team_management.remove_member_from_category, name='remove_member_from_category'),
    path('team-management/update-priority/<int:user_id>/', views_team_management.update_member_priority, name='update_member_priority'),
    # This catch-all MUST be last - matches category names (including URL-encoded ones like BOG%2FLeadership)
    path('team-management/<str:category_name>/', views_team_management.team_category_detail, name='team_category_detail'),
    #====================================================================================
    
    path('get_respos', views.get_respos, name='get_respos'),
    path('fetch_model_table_names/', views.fetch_model_table_names, name='fetch_model_table_names'),
    # path('get_respos/<str:table>', views.get_respos, name='get_respos'),
    path('data_policy/', views.data_policy, name='data_policy'),
    path('about/', views.about, name='about'),
    path('why-coda/', views.why_coda, name='why_coda'),
    path('careers/', views.careers, name='careers'),
    path('student-support-Page/', views.student_support, name='student_support'),
    path('search/', views.search, name='search'),
    path('wcag/', views.wcag, name='wcag'),
    path('check_wcag_compliance/', views.wcag_create_view, name='check_wcag_compliance'),
    path('wcag_list_view/', views.wcag_list_view, name='wcag_list_view'),
    path('contact/', views.contact, name='contact'),
    path('help/', views.help, name='help'),
    path('help/new-features/', views.new_features, name='new_features'),
    path('hr/', views.hr, name='hr'),
    path('bbdashboard/', views.bbdashboard, name='bbdashboard'),
    path('FAQS/', views.FrequentlyAskedQuestion, name='FAQS'),
    
    path('members/<str:title>', views.team, name='members'),
    path('newcompany/', views.CompanyCreateView.as_view(), name='newcompany'),
    path('companies/<str:location>', views.companies, name='companies'),
    path('company/<str:company>', views.company_detail, name='company_detail'),
    path('update/<int:pk>/', views.CompanyUpdateView.as_view(template_name='main/form.html'), name='update_company'),
    path('letter/', views.letters, name='letter'),
    path('appointment_letter/', views.letters, name='appointment_letter'),
    # path('download/', convert_html_to_pdf, name='appointment_letter_download'),
    path('drive-image/<str:file_id>/', views.get_drive_image, name='drive_image'),

    #=======================SERVICES=====================================
    path('newservice/', views.ServiceCreateView.as_view(template_name='main/form.html'), name='newservice'),
    path('services/', views.services, name='services'),
    path("display_service/<str:slug>/", views.display_service, name="display_service"),
    path("display_plans/<str:slug>/", views.service_plans, name="service_plans"),
    path('update/<int:pk>/', views.ServiceUpdateView.as_view(template_name='main/form.html'), name='update_service'),
    path('price_update/<int:pk>/', views.PriceUpdateView.as_view(template_name='main/form.html'), name='update_price'),
    path('delete/<int:id>/', views.delete_service, name='delete_service'),

    #=======================SERVICES=====================================
    path('posts/', views.PostListView.as_view(), name='success'),
    path('post/new/', views.newpost, name='post-create'),
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post-detail'),
    path('post/<int:pk>/update/', views.PostUpdateView.as_view(template_name='main/snippets_templates/generalform.html'), name='post-update'),
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post-delete'),
    #==============DEPARTMENTS==============================================
    #==============Clint Available Time==============================================
    path('add_availability/', views.add_availability, name='add_availability'),
    path('my_availability/', views.my_availability, name='my_availability'),
    path('clints_availability/', views.clints_availability, name='clints_availability'),

    #==============DEPARTMENTS==============================================
        #--------------------------MANAGEMENT--------------------#
    path('newprofile/', views.UserCreateView.as_view(template_name='main/form.html'), name='newprofile'),
    path('updateprofile/<int:pk>/', views.UserProfileUpdateView.as_view(template_name='main/form.html'), name='update_profile'),
    path('newplan/', views.PlanCreateView.as_view(template_name='main/form.html'), name='newplan'),
    path('plans/', views.plans, name='plans'),
    path('plan_urls/', views.plan_urls, name='plans'),
    path('plan/update/<int:pk>/', views.PlanUpdateView.as_view(template_name='main/form.html'), name='update_plan'),
    path('plan/delete/<int:id>/', views.delete_plan, name='delete_plan'),
    path('meetings/', views.meetings, name='meetings'),
    path('meetings/<str:title>/', views.MeetingsUpdateView.as_view(template_name='main/form.html'), name='update_meetings'),
        
    #----------------------------IT-------------------------#
        path('it/', views.it, name='it'),
    #-----------------------finance-------------------------#
    # path('finance/', views.finance, name='finance'),
    path('department/<str:slug>/', views.department_reports, name='department_reports'),
    path('system/maintenance/', views.system_maintenance, name='system_maintenance'),

    path('coach_profile/', views.coach_profile, name='coach_profile'),
    path('contact/', views.contact, name='contact'),
    path('project/', views.project, name='project'),
    path('training/', views.training, name='training'),
    
    path('image/', views.ImageCreateView.as_view(template_name='main/form.html'), name='image'),
    path('image/<int:pk>/', views.ImageUpdateView.as_view(template_name='main/form.html'), name='updateimage'),
    path('images/', views.images, name='images'),
    path('interview/', views.interview, name='interview'),

   #==============URLS==============================================
    path('open_urls/<str:url_type>', views.open_urls, name='open_urls'),

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