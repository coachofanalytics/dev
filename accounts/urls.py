from django.urls import path
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
]


app_name = 'accounts'
urlpatterns = [
    #=============================USERS VIEWS=====================================
    path('', views.home, name='home'),
    path('join/', views.join, name='join'),
    path('login/', views.login_view, name='account-login'),
    path('profile/', views.profile, name='account-profile'),
    path('Tracker/', views.tracker_list, name='tracker'),
     path('Tracker/', views.tracker_list, name='CAHistory'),

    path('Department/',views.DepartmentListView.as_view(), name='department-list')

]