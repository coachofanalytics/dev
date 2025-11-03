from django.urls import path
from django.shortcuts import render
from management import views
from management.views import (
                        TaskDetailView,
                        TaskUpdateView,TaskDeleteView,UsertaskUpdateView,
                        TaskCategoryCreateView,TaskGroupCreateView,
                        DepartmentUpdateView, BackgroundCheckListView,
                        RequirementUpdateView,RequirementDetailView,RequirementDeleteView,
                        TaskListView, DSUListView
                     )
from management.views_enhanced_dashboard import (
                        enhanced_task_dashboard, refresh_dashboard, export_my_data,
                        request_help, report_issue, load_more_tasks, submit_evidence,
                        task_leaderboard, task_history_view, tier_analytics
                     )
# Import task reset selective views
from management.views_task_reset_selective import reset_tasks_select, reset_all_tasks

# Import insights views from views directory (temporarily commented for testing)
# from management.views import insights_views

# Import AI dashboard views for Phase 2 (temporarily commented for deployment)
# Note: ai_dashboard_views will be added in Phase 3
# from management.views import ai_dashboard_views

# Import user testing views for Phase 2 (temporarily commented - file not in repo)
# from management.views import user_testing_views

app_name = 'management'
urlpatterns = [
    path('', views.home, name='management-home'),
    #-----------COMPANY REPORTS---------------------------------------
    path('companyagenda/', views.companyagenda, name='companyagenda'),
    path('companyagenda-improved/', views.companyagenda_improved, name='companyagenda_improved'),
    # userdashboard URL removed - functionality moved to unified dashboard
    path('update-agenda/<str:title>/<int:pk>/', views.updatelinks_companyagenda, name='update_agenda'),
    #-----------COMPANY POLICIES---------------------------------------
    path('policy/', views.policy, name='policy'),
    path('policies/', views.policies, name='policies'),
    path("policy/<int:pk>/update/", views.PolicyUpdateView.as_view(template_name="management/departments/hr/policy_form.html"), name="policy-update"),
    path('benefits/', views.benefits, name='benefits'),
    #========================Employee Assessment=====================================================
    path("employee_contract/", views.employee_contract, name="employee_contract"),
    path("read_employee_contract/", views.read_employee_contract, name="read_employee_contract"),
    path("confirm_employee_contract/", views.confirm_employee_contract, name="confirm_employee_contract"),
    path('tasks/', TaskListView.as_view(), name='tasks'),
    path('payroll/',views.payslip, name='user_pay'),
    # Updated task reset - selective interface
    path("reset_tasks/select/", reset_tasks_select, name="reset_tasks_select"),
    # Old reset_tasks redirects to new interface
    path("reset_tasks/", reset_all_tasks, name="reset_tasks"),
    path('score_report/', views.score_report, name='score_report'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='taskdetail'),
    path('newevidence/<int:taskid>', views.newevidence, name='new_evidence'),
    path('userevidence/',views.userevidence, name='user_evidence'),
    # path('userevidence/<str:username>/',views.userevidence, name='user_evidence'),
    path('<id>/update', views.evidence_update_view ,name='evidence_update'),
    path('getaveragetargets/', views.getaveragetargets, name='getaveragetargets'),
    path('newtask/', views.newtaskcreation, name='newtask'),
    path('gettasksuggestions/', views.gettasksuggestions, name='gettasksuggestions'),
    path('verifytaskgroupexists/', views.verifytaskgroupexists, name='verifytaskgroupexists'),

    path('task/<int:pk>/update/', TaskUpdateView.as_view(), name='updatetask'),
    path('usertask/<int:pk>/update/', UsertaskUpdateView.as_view(), name='userupdatetask'),
    # path('gettotalduration/', views.gettotalduration, name='gettotalduration'),
    path('task/<int:pk>/delete/', TaskDeleteView.as_view(), name='deletetask'),
    path('newcategory/', TaskCategoryCreateView.as_view(), name='newcategory'),
    path('newtaskgroup/', TaskGroupCreateView.as_view(template_name="main/snippets_templates/generalform.html"), name='newtaskgroup'),
    path('contract/',views.contract, name='contract'),

    path('newclient/', views.clientassessment, name='newclient'),
    path('clientassessment/', views.ClientAssessmentListView.as_view(), name='clientassessment'),
     # =============================BACKGROUND CHECK VIEWS=====================================
    path("backgroundcheckadd/",views.add_background_info,name="background-create"),
    path("backgroundchecklist/",BackgroundCheckListView.as_view(template_name="management/background/backgroundchecklist.html"),name="background-list"),
    path('new_grievance/', views.grievance_form, name='new_grievance'),
    path('grievance_file/<str:slug>', views.grievance_file, name='grievance_file'),
    path('update_grievance/<int:pk>/', views.GrievanceUpdateView.as_view(template_name="main/snippets_templates/generalform.html"), name='update_grievance'),
    path('update_resolution/<int:pk>/', views.ResolutionUpdateView.as_view(template_name="main/snippets_templates/generalform.html"), name='update_resolution'),
    path('update_assessment/<int:pk>/', views.AssessmentUpdateView.as_view(template_name="main/snippets_templates/generalform.html"), name='update_assessment'),
    path('assess/', views.assess, name='assess'),
    path('assessment/<str:user_type>', DSUListView.as_view(), name='assessment'),
    path('update_dsu/<int:pk>/', views.AssessUpdateView.as_view(template_name="main/snippets_templates/generalform.html"), name='update_dsu'),
    path('session/', views.SessionCreateView.as_view(template_name="main/snippets_templates/generalform.html"), name='session'),
    path('session/<int:pk>/', views.SessionUpdateView.as_view(template_name="main/snippets_templates/generalform.html"), name='updatesession'),
    path('sessions/<str:slug>', views.sessions, name='sessions'),
    path('usersession/<str:username>/',views.usersession, name='user_session'),

    path('newdepartment/', views.newdepartment, name='newdepartment'),
    path('departments/', views.department, name='departments'),
    path('department/<int:pk>/', DepartmentUpdateView.as_view(template_name='management/tag_form.html'), name='department-update'),
    path('newmeeting/', views.newmeeting, name='newmeeting'),
    path('meetings/<str:status>', views.meetings, name='meetings'),
    path('meeting/<int:pk>/', views.MeetingUpdateView.as_view(template_name='main/snippets_templates/generalform.html'), name='meeting-update'),

    #========================REQUIREMENTS SECTION=====================================================
    path('requirement/new', views.newrequirement, name='new_requirement'),
    path('form_submission_view/', views.form_submission_view, name='form_submission_view'),
    path('requirements/', views.requirements, name='requirements'),
    path('activerequirements/', views.active_requirements, name='requirements-active'),
    path('client_requirements/', views.requirements, name='client_requirements'),
    path('coda_requirements/', views.requirements, name='coda_requirements'),
    path('dyc_requirements/', views.requirements, name='dyc_requirements'),
    path('reviewed/', views.requirements, name='reviewed'),
    path('tested/', views.requirements, name='tested'),
    path('requirement/<int:pk>/update/', RequirementUpdateView.as_view(template_name='management/doc_templates/requirement_form.html'), name='requirement-update'),
    path('requirement/<int:pk>/delete/', RequirementDeleteView.as_view(), name='requirement-delete'),
    path('requirement/<int:pk>/', RequirementDetailView.as_view(), name='RequirementDetail'),
    path('requirementvideo/<int:detail_id>/', views.videolink, name='video_req_code'),
    path('justification/<int:pk>/', views.justification, name='justification'),
    path('add_justification/', views.add_requirement_justification, name='addjustification'),
    path("attendee-duration/", views.get_attendee_duration, name="attendee_duration"),

    path("create_advertisement/", views.AdsCreateView.as_view(), name="create_advertisement"),
    path("advertisement/", views.AdsContent.as_view(), name="advertisement"),
    path("update_advertisement/<int:pk>/", views.AdsUpdateView.as_view(), name="update_advertisement"),
    # path('FilterUsersByLoan/', views.FilterUsersByLoan, name='FilterUsersByLoan'),
    path('upload/', views.assignment_upload, name='assignment_upload'),
    path('assignments/', views.assignment_list, name='assignment_list'),
    path('assignments/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/<int:assignment_id>/delete/', views.delete_assignment, name='delete_assignment'),
    path('oauth/login/', views.oauth_login, name='oauth_login'),
    path('oauth/callback/', views.oauth_callback, name='oauth_callback'),
    path('attendee_duration/', views.get_attendee_duration, name='attendee_duration'),
    
# ========== Phase 1: Performance Insights ==========
# Temporarily commented out for testing
# path('insights/performance-dashboard/', insights_views.PerformanceInsightsDashboard.as_view(), name='performance_insights_dashboard'),
# path('insights/export-report/', insights_views.export_insights_report, name='export_insights_report'),
# path('insights/api/', insights_views.get_insights_api, name='insights_api'),

# ========== Phase 2: AI-Enhanced Features ==========
# User Testing Dashboard (TEMPORARILY DISABLED - file not in repo)
# Uncomment when user_testing_views.py is added to the repository

# User Testing Dashboard
# path('ai-test-dashboard/', user_testing_views.UserTestingDashboardView.as_view(), name='ai_test_dashboard'),
# path('ai-features-overview/', user_testing_views.AIFeaturesOverviewView.as_view(), name='ai_features_overview'),

# User Testing API Endpoints
# path('test-ai-predictions/', user_testing_views.test_ai_predictions_user, name='test_ai_predictions_user'),
# path('test-task-assignment/', user_testing_views.test_task_assignment_user, name='test_task_assignment_user'),
# path('test-department-optimization/', user_testing_views.test_department_optimization_user, name='test_department_optimization_user'),
# path('test-monitoring/', user_testing_views.test_monitoring_user, name='test_monitoring_user'),
# path('test-data-quality/', user_testing_views.test_data_quality_user, name='test_data_quality_user'),
# path('ai-system-status/', user_testing_views.get_ai_system_status, name='ai_system_status'),

# AI Dashboard Views (temporarily commented for deployment - services are working)
# path('ai-dashboard/', ai_dashboard_views.AIEnhancedDashboardView.as_view(), name='ai_dashboard'),
# path('ai-dashboard/employee-performance/', ai_dashboard_views.EmployeePerformanceDashboardView.as_view(), name='ai_employee_performance'),
# path('ai-dashboard/task-assignment/', ai_dashboard_views.TaskAssignmentDashboardView.as_view(), name='ai_task_assignment'),
# path('ai-dashboard/department-optimization/', ai_dashboard_views.DepartmentOptimizationDashboardView.as_view(), name='ai_department_optimization'),

# AI API Endpoints (temporarily commented for deployment - services are working)
# path('ai-api/realtime-dashboard/', ai_dashboard_views.get_realtime_dashboard_data, name='ai_realtime_dashboard'),
# path('ai-api/performance-alerts/', ai_dashboard_views.get_performance_alerts, name='ai_performance_alerts'),
# path('ai-api/employee-performance/<int:employee_id>/', ai_dashboard_views.get_employee_performance, name='ai_employee_performance_api'),
# path('ai-api/department-status/<str:department_name>/', ai_dashboard_views.get_department_status, name='ai_department_status'),
# path('ai-api/task-assignment/', ai_dashboard_views.get_task_assignment_recommendation, name='ai_task_assignment_api'),
# path('ai-api/department-optimization/<str:department_name>/', ai_dashboard_views.get_department_optimization, name='ai_department_optimization_api'),
# path('ai-api/data-quality/', ai_dashboard_views.get_data_quality_report, name='ai_data_quality'),
# path('ai-api/export-report/', ai_dashboard_views.export_performance_report, name='ai_export_report'),

    # Enhanced Dashboard URLs
    path('enhanced-dashboard/', enhanced_task_dashboard, name='enhanced-dashboard'),
    path('api/refresh-dashboard/', refresh_dashboard, name='refresh-dashboard'),
    path('api/export-my-data/', export_my_data, name='export-my-data'),
    path('api/request-help/', request_help, name='request-help'),
    path('api/report-issue/', report_issue, name='report-issue'),
    path('api/load-more-tasks/', load_more_tasks, name='load-more-tasks'),
    path('api/submit-evidence/', submit_evidence, name='submit-evidence'),
    path('leaderboard/', task_leaderboard, name='leaderboard'),
    path('task-history/', task_history_view, name='task-history'),
    path('tier-analytics/', tier_analytics, name='tier-analytics'),
    path('button-testing/', lambda request: render(request, 'management/button_testing_dashboard.html'), name='button-testing'),

]
