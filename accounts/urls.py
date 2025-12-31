# from django.urls import path
# from . import views

# app_name = 'accounts'
# urlpatterns = [
#     path('', views.home, name='home'),
#     path('auth/join/', views.join, name='join'),
#     path('auth/login/', views.login_view, name='login'),
#     path('account/profile/', views.profile, name='profile'),
# ]
#  path('payments/', views.payment_history_list, name='payments'),
from django.urls import path
from . import views 


app_name = "accounts"

urlpatterns = [
    path("payments/", views.payment_history_list, name="payment-history-list"),


    path("login/", views.login_history_list_view, name="accounts-login_history_list"),
    path("login_create/", views.login_history_create_view, name="login_history-create"),
    path("login/", views.login_history_detail_view, name="login_history_detail"),
    path("login/", views.login_history_update_view, name="login_history_update"),
    path("login_delete/", views.login_history_delete_view, name="login_history_delete"),
    path("trackers/", views.tracker_list_view, name="tracker_list"),
    path("Trackers_create/", views.tracker_create_view, name="accounts-tracker_create"),
    path("Trackers/", views.tracker_detail_view, name="tracker_detail"),
    path("Trackers/", views.tracker_update_view, name="tracker_update"),
    path("trackers/<int:pk>/delete/", views.tracker_delete_view, name="tracker_delete"),
]




