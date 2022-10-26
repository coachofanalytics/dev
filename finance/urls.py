from django.urls import path
from . import views
from .views import (
                    PaymentCreateView,PaymentListView,
                    TransanctionDetailView,TransactionListView,
                    TransactionUpdateView,TransactionDeleteView,
                    UserInflowListView,InflowDetailView,InflowUpdateView,InflowDeleteView,
                    DefaultPaymentUpdateView,DefaultPaymentListView,
                    LoanListView,LoanUpdateView,LoanCreateView,userLoanListView
)
app_name = 'finance'
urlpatterns = [
    #=============================FINANCES=====================================
    path('transact/', views.transact, name='finance-transact'),
    path('finance/', views.finance, name='finance'),
    path('transaction/', TransactionListView.as_view(), name='transaction-list'),
    path('transaction/<int:pk>/', TransanctionDetailView.as_view(), name='transaction-detail'),
    path('transaction/<int:pk>/update/', TransactionUpdateView.as_view(template_name="finance/payments/transaction_form.html"), name='transaction-update'),
    path('transaction/<int:pk>/delete/', TransactionDeleteView.as_view(template_name="finance/payments/transaction_confirm_delete.html"), name='transaction-delete'),
     #-----------CASHINFLOW---------------------------------------
    path('inflow_entry/', views.inflow, name='entry_inflow'),
    #path('inflow/', InflowListView.as_view(), name='inflow-list'),
    path('inflows/', views.inflows, name='inflow-list'),
    path('user_inflow/', UserInflowListView.as_view(), name='user-list'),
    #path('inflow/new/', InflowCreateView.as_view(), name='inflow-create'),
    path('inflow/<int:pk>/', InflowDetailView.as_view(), name='inflow-detail'),
    path('inflow/<int:pk>/delete/', InflowDeleteView.as_view(), name='inflow-delete'),
    path('inflow/<int:pk>/update/', InflowUpdateView.as_view(), name='inflow-update'),
    
    #=============================CLIENT CONTRACT FORM SUBMISSIONS=====================================
    path('contract_form/', views.contract_form_submission, name='finance-contract_form_submission'),
    path('mycontract/<str:username>/', views.mycontract, name='mycontract'),
    path('new_contract/<str:username>/', views.newcontract, name='newcontract'),
    #Pay URLS
    path('payments/', PaymentListView.as_view(template_name='finance/payments/payments.html'), name='payments'),
    path('defaultpayments/', DefaultPaymentListView.as_view(template_name='finance/payments/defaultpayments.html'), name='defaultpayments'),
    path('newpayment/', PaymentCreateView.as_view(template_name='finance/payments/payment_form.html'), name='newpayment'),
    path('payment/<int:pk>/update/', DefaultPaymentUpdateView.as_view(template_name='finance/payments/payment_form.html'), name='payment-update'),
    #Pay configs URLS
    path('newpaymentconfigs/',views.PaymentConfigCreateView.as_view(template_name='finance/payments/payment_form.html'), name='newpaymentconfigs'),
    path('paymentconfigs/', views.PaymentConfigListView.as_view(), name='paymentconfigs'),
    path('paymentconfigs/<int:pk>/update/', views.PaymentConfigUpdateView.as_view(template_name='finance/payments/payment_form.html'), name='paymentconfigs-update'),
    #Loans URLS
    path('loans/', LoanListView.as_view(template_name='finance/payments/loans.html'), name='trainingloans'),
    # path('newpay/', views.loan, name='newpay'),
    path('newpay/', LoanCreateView.as_view(template_name='finance/payments/payment_form.html'), name='newpay'),
    path('loanuser/', views.userLoanListView, name='loanuser'),
    path('loan/<int:pk>/update/', LoanUpdateView.as_view(template_name='finance/payments/payment_form.html'), name='loan-update'),
     #FOOD & SUPPLIERS
    path(
        "newsupplies/",
        views.FoodCreateView.as_view(
            template_name='main/snippets_templates/generalform.html'
        ),
        name="newsupplies",
    ),
    path(
        "newsupplier/",
        views.SupplierCreateView.as_view(
            template_name='main/snippets_templates/generalform.html'
        ),
        name="newsupplier",
    ),
    path("update/<int:pk>/",views.SupplierUpdateView.as_view(template_name='main/snippets_templates/generalform.html'),name="update-supplier"),
    path("food/<int:pk>/update",views.FoodUpdateView.as_view(template_name='main/snippets_templates/generalform.html'),name="update-food"),
    path("suppliers/",views.SupplierListView.as_view(),name="suppliers"),
    path("food/",views.FoodListView.as_view(),name="supplies"),
]