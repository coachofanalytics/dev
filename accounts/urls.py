from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    #=============================USERS VIEWS=====================================
    path('', views.home, name='home'),
    path('join/', views.join, name='join'),
    path('login/', views.login_view, name='account-login'),
    path('profile/', views.profile, name='account-profile'),
    path('Departments/', views.Department_list_view, name='department_create'),
    path("department_create/", views.DepartmentCreateView, name="department_create"),
    path('Credential/', views.credential_list_view, name='credential'),
    path('create/', views.Credential_CreateView, name='create'),
    path('update/<int:pk>/', views.CredentialUpdateView, name='update'),
    path('detail/<int:pk>/', views.CredentialDetailView, name='detail'),
    path('delete/<int:pk>/', views.CredentialDeleteView, name='delete'),
    path('TaskGroup/', views.taskgroup_list_view, name='TaskGroup'),
    path('TaskGroupcreate/', views.TaskGroup_create_view, name='TaskGroup_create'),
    path('TaskGroupupdate/<int:pk>/', views.TaskGroup_update_view, name='TaskGroup_update'),
    path('TaskGroup_detail/<int:pk>/', views.TaskGroup_detail_view, name='TaskGroup_detail'),

]