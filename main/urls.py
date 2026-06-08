from django.urls import path
from main.views import AboutView

from . import views

# from .utils import convert_html_to_pdf

app_name = 'main'
urlpatterns = [
    path('', views.layout, name='layout'),
    path('team/', views.team_list, name='team_view'),
    path('history',views.history, name ='history'),
    path('services/', views.service_list, name='service_list'),
    path('gallery/', views.gallery_list, name='gallery_list'),
    path('news/', views.news_list, name='news_list'),
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
    path('emergency_help_line/', views.emergency_help_line, name='emergency_help_line'),
    path('activate_helpline/', views.activate_helpline, name='activate_helpline'),

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
