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
    path('all_transaction_list/', views.All_transaction_list_view, name='accounts-transaction_list'),
    path('all_transaction_create/', views.All_transaction_create_view, name='all_transaction_create'),
    path('all_transaction_update/<int:pk>/', views.All_transaction_update_view, name='all_transaction_update'),
    path('all_transaction_detail/<int:pk>/', views.All_transaction_detail_view, name='all_transaction_detail'),
    path('CODA_Transaction/', views.transaction_list_view, name='accounts-transaction_list'),
    path('CODA_Transaction_create/', views.transaction_create_view, name='transaction_create'),
    path('CODA_Transaction_update/<int:pk>/', views.transaction_update_view, name='transaction_update'),
    path('CODA_Transaction_detail/<int:pk>/', views.transaction_detail_view, name='transaction_detail'),
    path('CODA_Transaction_delete/<int:pk>/', views.transaction_delete_view, name='transaction_delete'),

     path('payment_list/', views.payment_list_view, name='payment_list'),

    # ✅ Correct route for paymenthistory
    path('paymenthistory_list/', views.payment_history_list_view, name='accounts-paymenthistory_list'),
    path('paymenthistory_create/', views.payment_history_create_view, name='paymenthistory_create'),


    path("paymentshistory_update/<int:pk>/update/", views.payment_history_update_view, name="paymenthistory_update")

    # path('paymenthistory_update/<int:pk>/', views.payment_history_update_view, name='paymenthistory_update'),
    
     
]
    

    


    

