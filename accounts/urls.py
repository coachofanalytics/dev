from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    #=============================USERS VIEWS=====================================
    path('', views.home, name='home'),
    path('join/', views.join, name='join'),
    path('login/', views.login_view, name='account-login'),
    path('profile/', views.profile, name='account-profile'),
    path('departments/', views.Department_list_view, name='department_list'),
    path('department/create/', views.DepartmentCreateView, name='department_create'),

    path('credential/', views.credential_list_view, name='credential'),
    path('credential/create/', views.Credential_CreateView, name='create'),
    path('credential/update/<int:pk>/', views.CredentialUpdateView, name='update'),
    path('credential/detail/<int:pk>/', views.CredentialDetailView, name='detail'),
    path('credential/delete/<int:pk>/', views.CredentialDeleteView, name='delete'),

    path('taskgroup/', views.taskgroup_list_view, name='taskgroup_list'),
    path('taskgroup/create/', views.TaskGroup_create_view, name='taskgroup_create'),
    path('taskgroup/update/<int:pk>/', views.TaskGroup_update_view, name='taskgroup_update'),
    path('taskgroup/detail/<int:pk>/', views.TaskGroup_detail_view, name='taskgroup_detail'),

    path('teammember/list/', views.teammember_list_view, name='teammember_list'),
    path('teammember/create/', views.teammember_create_view, name='teammember_create'),
    path('teammember/update/<int:pk>/', views.teammember_update_view, name='teammember_update'),
    path('teammember/detail/<int:pk>/', views.teammember_detail_view, name='teammember_detail'),
    path('teammember/delete/<int:pk>/', views.teammember_delete_view, name='teammember_delete'),


    path('credentialcategory_list/', views.credentialcategory_list, name='credentialcategory_list'),
    path('credentialcategory_create/', views.credentialcategory_create, name='credentialcategory_create'),
    path('category_update/update/<int:pk>/', views.credentialcategory_update, name='credentialcategory_update'),
    path('category_delete/delete/<int:pk>/', views.credentialcategory_delete, name='credentialcategory_delete'),
    path('credentialcategory_detail/<int:pk>/', views.credentialcategory_detail, name='credentialcategory_detail'),




    path('tracker_list/', views.tracker_list, name='tracker_list'),
    path('Trackers_create/', views.Trackers_create, name='Trackers_create'),
]


