from django.urls import path
from . import views
from .views import (
    user_update_view,
    superuser_update_view,
    register,
    custom_login_view,
    join,
    login_view,
    home,
    verify_email,
    email_verification_notice,
    select_category,
    users,
    userlist,
    thank
)
app_name = 'accounts'
urlpatterns = [
    #=============================USERS VIEWS=====================================
    path('', views.home, name='home'),
    path('join/',views.join, name ='joins'),
     path('login/', views.login_view, name='account-login'),
  
    # path('register/', register, name='register'),

    # path('verify-email/<uuid:token>/', views.verify_email, name='verify-email'),
    # path('email-verification-notice/<int:user_id>/', views.email_verification_notice, name='email-verification-notice'),
    # path('select-category/', views.select_category, name='select_category'),
    # #path('login/', CustomLoginView.as_view(), name='login'),
    # path('users/', views.users, name='accounts-users'),
    # # path('users/', views.userslistview.as_view(), name='accounts-users'),
    # path('processing/', views.userlist, name='processing-users'),
   
    # path('thank/',views.thank, name='thank-you'),

    # path('membership/', views.membership_registration, name = 'membership_registration'),

    # # Member CRUD
    # path('members/', views.MemberListView.as_view(), name='member-list'),
    # path('members/add/', views.MemberCreateView.as_view(), name='member-create'),
    # path('members/<int:pk>/edit/', views.MemberUpdateView.as_view(), name='member-update'),
    # path('members/<int:pk>/delete/', views.MemberDeleteView.as_view(), name='member-delete'),
    # path('account-list/', views.account_list, name='account_list'),
    # path('create-account/', views.create_account, name='create_account'),
    # path('user/<int:pk>/update/', user_update_view, name='user-update'),
    # path('superuser/<int:pk>/update/', superuser_update_view, name='superuser-update'),

]