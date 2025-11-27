from django.urls import path
from . import views

urlpatterns = [
    path("pay", views.home_view, name="home"),
    path("overboughtsold/", views.OverBoughtSold, name="OverBoughtSold_list"),
    path(
        "payments_information/",
        views.PaymentInformation_list,
        name="PaymentInformation_list",
    ),
    path(
        "Default_Payment_Fees_list/",
        views.Default_Payment_Fees_list,
        name="Default_Payment_Fees_list",
    ),
    path(
        "Default_Payment_Fees_create/",
        views.Default_Payment_Fees_create,
        name="Default_Payment_Fees_create",
    ),
    path(
        "payments/<int:pk>/edit/",
        views.Default_Payment_Fees_update,
        name="Default_Payment_Fees_update",
    ),
    path(
        "payments/<int:pk>/delete/",
        views.Default_Payment_Fees_delete,
        name="Default_Payment_Fees_delete",
    ),
    path(
        "payments/<int:pk>/detail/",
        views.Default_Payment_Fees_detail,
        name="Default_Payment_Fees_detail",
    ),
    path('PayslipConfig_list/', views.PayslipConfig_list, name='payslip_config_list'),
]