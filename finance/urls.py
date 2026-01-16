from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('transact/', views.transact, name='finance-transact'),
    path('transaction/', views.TransactionListView.as_view(), name='transaction-list'),
    path('transaction/<int:pk>/', views.TransanctionDetailView.as_view(), name='transaction-detail'),
    path('transaction/<int:pk>/update/', views.TransactionUpdateView.as_view(), name='transaction-update'),
  
    path('contract_form/', views.contract_form_submission, name='finance-contract_form_submission'),
    path('mycontract/<str:username>/', views.mycontract, name='mycontract'),
    path('Payment_Review/', views.Payment_Review, name='Payment_Review'),

    path('pay/', views.pay, name='pay'),
    path('payment/<int:service>/', views.pay, name='service_pay'),
    path('payment/create/', views.PaymentCreateView.as_view(), name='payment-create'),

    path('payment_method/<str:method>/', views.payment, name='payment_method'),
    path("process-payment/", views.process_payment, name="process_payment"),
    path("payment-success/", views.payment_success, name="payment_success"),
    path('payments/', views.payments, name='payments'),
    path('pay/<int:pk>/', views.PaymentInformationUpdateView.as_view(), name='updatepay'),
    
    path('defaultpayments/', views.DefaultPaymentListView.as_view(), name='defaultpayments'),
    path('newpayment/', views.PaymentCreateView.as_view(), name='newpayment'),
    path('payment/<int:pk>/update/', views.DefaultPaymentUpdateView.as_view(), name='payment-update'),

    path('budget/', views.budget, name='company_budget'),
    path("budget/<str:subtitle>/<str:duration>/", views.budget_projection, name="budget_projection"),
    
    # Financial Planning CRUD
    path('planning/', views.financial_planning_list, name='planning_list'),
    path('planning/<int:pk>/update/', views.financial_planning_update, name='planning_update'),
    path('planning/<int:pk>/delete/', views.financial_planning_delete, name='planning_delete'),
]
