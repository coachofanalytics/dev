from django.urls import path
from . import views
from .views import *
from mail.search_mail import parse_mail, search_job_mail

app_name = 'getdata'
urlpatterns = [
    path('getrating/', views.getrating, name='data-getrating'),
    path('enter_question/', views.enter_prompt, name='enter_prompt'),
    path('groups/', views.fetch_whatsapp_groups, name='whatsappgroups'),
    path('index/', views.index, name='data-index'),
    path('bigdata/', views.bigdata, name='generate-data'),
    path('bigdata/presentation/', views.bigdata_presentation, name='bigdata-presentation'),
    path('connects',views.connects_suggestion, name='upwork_connects'),
    #-----------------------DATA UPLOAD/MIGRATION-------------------------#
    path('upload/', views.upload_csv, name='upload'),
    path('upload_daily_trades/', views.upload_daily_trades, name='upload_daily_trades'),
    path('dataupload/', views.uploaddata, name='upload-data'),
    path('migrate_transactions/', views.migrate_transactions_to_codabudget, name='migrate_transactions'),
    #-----------------------README-------------------------#
    path('newusecasecategory/', views.CaseCategoryCreateView.as_view(template_name='main/form.html'), name='newusecase'),
    path('newusecase/', views.UseCaseCreateView, name='newusecase'),
    path('display_usecases/<int:pk>', views.display_usecases, name='display_usecases'),
    path('all_apps/<str:app>', views.all_apps, name='all_apps'),
    path('update_usecases/<int:pk>/', views.use_case_update_view, name='update_usecases'),

    path('download_daily_trades/', views.download_daily_trades, name='upl'),
    path('datauploadcsv/', views.stocks_upload_csv, name='upload-data'),
    path('cashapp/',parse_mail, name='cashapp-email'),
    path('cashappdata/', views.CashappListView.as_view(), name='cashapp-data'),
    path('cashappdetail/',views.CashappMailDetailSlugView.as_view(), name='cashappdetail'),
   
    path('positions/', views.refetch_data, name='fetch_and_insert_data'),
    path('replies/',search_job_mail, name='replies-email'),
    path('getmeetingresponse/', getmeetingresponse, name='getmeetingresponse'),
    path('meetingFormView/', meetingFormView, name='meetingFormView'),
    path('testselinum/', views.selinum_test, name='testselinum'),
    path('all_logs/', views.LogsViewSet, name='all_logs'),
    
    #Excel data fetching urls
     path('dashboard/', views.dashboard, name='dashboard'),
    path('send_email/', views.send_email, name='send_email'),
    path('uploads/', views.upload_excel, name='upload_excel'),
    path('uploads/<str:folder_name>/', views.upload_excel, name='upload_folder'),
    path('uploads/<str:folder_name>/<str:file_name>/', views.upload_excel, name='upload_file'),
    path('add-today-meetings/', views.add_today_meetings, name='add_today_meetings'),

    path('download-upload-recordings/', views.download_and_upload_recordings, name='download_upload_recordings'),

    # ==============================DIASPORA AI PLATFORM URLS=============================
    path('diaspora/', views.diaspora_dashboard, name='diaspora_dashboard'),
    path('diaspora/presentation/', views.diaspora_dashboard, name='presentation_dashboard'),
    path('diaspora/create-session/', views.create_session, name='create_session'),
    path('diaspora/analysis/<str:analysis_type>/', views.analysis_form_view, name='analysis_form'),
    path('diaspora/process/<str:analysis_type>/', views.process_analysis, name='process_analysis'),
    path('diaspora/results/<int:analysis_id>/', views.analysis_results, name='analysis_results'),
    path('diaspora/session/<str:session_id>/', views.session_analytics, name='session_analytics'),
    path('diaspora/analytics/', views.analytics_dashboard, name='analytics_dashboard'),
    path('diaspora/advanced-analytics/', views.advanced_analytics_dashboard, name='advanced_analytics_dashboard'),
    path('diaspora/ai-configuration/', views.ai_configuration_dashboard, name='ai_configuration_dashboard'),
    path('diaspora/my-analytics/', views.user_analytics, name='user_analytics'),
    path('diaspora/ai-health/', views.ai_health_check, name='ai_health_check'),
    path('diaspora/presentation-guide/', views.presentation_guide, name='presentation_guide'),

]