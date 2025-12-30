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
    path("login/", views.login_history_list_view, name="login_history-list"),

]



