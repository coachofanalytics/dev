from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    #=============================USERS VIEWS=====================================
    path('', views.home, name='home'),
    path('join/', views.join, name='join'),
    path('login/', views.login_view, name='account-login'),
    path('profile/', views.profile, name='account-profile'),   

    # ✅ Correct route for transactions
    path('all_transaction_list/', views.All_transaction_list_view, name='accounts-all_transaction_list'),
    path('all_transaction_create/', views.All_transaction_create_view, name='all_transaction_create'),
    
]
