from django.urls import path
from main.views import AboutView
from main.views import registration_update,membershirp_registration_delete,membershipplan_update,delete_membershipplan,membershipplan_detail,news_update,ContactMessage_list,ContactMessage_create


from . import views

 
app_name = 'main'
urlpatterns = [
    path('', views.layout, name='layout'),
    path('history',views.History, name ='history'),    
    path('registration',views.registration_list, name ='registration_list'),
    path('registration_create',views.registration_create, name ='registration_create'),
    path('registration/<int:pk>/update/', registration_update, name='registration_update'), 
    path('registration/<int:pk>/delete/', membershirp_registration_delete, name='membershirp_registration_delete'),
    path('MembershipPlan_list',views.MembershipPlan_list, name ='Me mbershipPlan_list'),
    path('membershipplan_create',views.membershipplan_create, name ='membershipplan_create'),
    path('membershipplan/<int:pk>/update/', membershipplan_update, name='membershipplan_update'),
    path('membershipplan_delete/<int:pk>/delete/', delete_membershipplan, name='delete_membershipplan'),
    path('membershipplan_detail/<int:pk>/detail/', membershipplan_detail, name='membershipplan_detail'),
    path('news',views.News_list, name ='News_list'),    
    path('news_create',views.NEWS_create, name ='NEWS_create'), 
    path('news/<int:pk>/update/', news_update, name='news_update'), 
    path('ContactMessage_list',views.ContactMessage_list, name ='ContactMessage_list'),
    path('ContactMessage_create',views.ContactMessage_create, name ='ContactMessage_create'),
    path('ContactMessage_update/<int:pk>/',views.ContactMessage_update, name='ContactMessage_update'),
    path('ContactMessage_delete/<int:pk>/',views.ContactMessage_delete, name='ContactMessage_delete'),
    path('ContactMessage_detail/<int:pk>/',views.ContactMessage_detail, name='ContactMessage_detail'),
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
