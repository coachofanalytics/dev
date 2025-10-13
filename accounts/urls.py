from django.urls import path
from . import views

app_name = 'accounts'
urlpatterns = [
    #=============================USERS VIEWS=====================================
    path('', views.home, name='home'),
    path('join/', views.join, name='join'),
    path('login/', views.login_view, name='account-login'),
    path('profile/', views.profile, name='account-profile'),
    # path('Departments/', views.Department_list_view, name='department_create'),
    # path("department_create/", views.DepartmentCreateView, name="department_create"),
    path('Credential/', views.credential_list_view, name='credential'),
    path('create/', views.Credential_CreateView, name='create'),
    path('update/<int:pk>/', views.CredentialUpdateView, name='update'),
    path('detail/<int:pk>/', views.CredentialDetailView, name='detail'),
    path('delete/<int:pk>/', views.CredentialDeleteView, name='delete'),
    path('TaskGroup/', views.taskgroup_list_view, name='TaskGroup'),
    path('TaskGroupcreate/', views.TaskGroup_create_view, name='TaskGroup_create'),
    path('TaskGroupupdate/<int:pk>/', views.TaskGroup_update_view, name='TaskGroup_update'),
    path('TaskGroup_detail/<int:pk>/', views.TaskGroup_detail_view, name='TaskGroup_detail'),
    path('teammember_list/', views.teammember_list_view, name='teammember_list'),
    path('teammember_create/', views.teammember_create_view, name='teammember_create'),
    path('teammember_update/<int:pk>/', views.teammember_update_view, name='teammember_update'),
    path('teammember_detail/<int:pk>/', views.teammember_detail_view, name='teammember_detail'),
    path('teammember_delete/<int:pk>/', views.teammember_delete_view, name='teammember_delete'),
    path('credentialcategoryy_list/', views.CredentialCategory_list_view, name='credentialcategoryy_list'),
    path('CredentialCategory_create/', views.CredentialCategory_create_view, name='CredentialCategory_create'),
    path('CredentialCategory_update/<int:pk>/', views.CredentialCategory_update_view, name='CredentialCategory_update'),


    path('accounts:Sprintplanning_lis/', views.Sprintplanning_list, name='accounts_Sprintplanning_list'),
    path('Sprintplanning_create/', views.Sprintplanning_create, name='Sprintplanning_create'),
    path('Sprintplanning_update/<int:pk>/', views.Sprintplanning_update, name='Sprintplanning_update'),
    path('Sprintplanning_Details/<int:pk>/', views.Sprintplanning_Details, name='Sprintplanning_Details'),
    path('Sprintplanning_Delete/<int:pk>/', views.Sprintplanning_Delete_view, name='Sprintplanning_Delete'),
    path('account:CapacityBuilding_list/', views.CapacityBuilding_list_view, name='accounts-capacity_building_list'),
    path('CapacityBuilding_create/', views.CapacityBuilding_list_view, name='accounts-CapacityBuilding_create'),
    path('CapacityBuilding_update/<int:pk>/', views.CapacityBuilding_update_view, name='CapacityBuilding_update'),
    path('CapacityBuilding_detail/<int:pk>/', views.CapacityBuildingDetailView, name='CapacityBuilding_detail'),

    path('CapacityBuilding_delete/<int:pk>/', views.CapacityBuilding_delete_view, name='CapacityBuilding_delete'),

    path('Evidence_list/', views.Evidence_list_view, name='Evidence_list'),





    


]