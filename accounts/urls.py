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
    path('all_transaction_update/<int:pk>/', views.All_transaction_update_view, name='all_transaction_update'),
    path('all_transaction_detail/<int:pk>/', views.All_transaction_detail_view, name='all_transaction_detail'),
    path("all_transaction_delete/<int:pk>/", views.all_transaction_delete_view, name="all_transaction_delete"),
    path('CODA_Transaction/', views.transaction_list_view, name='accounts-transaction_list'),
    path('CODA_Transaction_create/', views.transaction_create_view, name='transaction_create'),

    
]
