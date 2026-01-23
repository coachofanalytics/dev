from django.urls import path
from . import views

app_name = 'shareholders'

urlpatterns = [
    path('dashboard/', views.shareholders_dashboard, name='shareholders_dashboard'),
    path('ledgers/', views.ledgers_view, name='ledgers_view'),
]
