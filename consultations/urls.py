from django.urls import path
from . import views

app_name = 'consultations'

urlpatterns = [
    path('book_consultations/', views.book_consultations, name='book_consultations'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('visa_applicationform/', views.visa_applicationform, name='visa_applicationform'),
    path('submit_application/', views.submit_application, name='submit_application'),
    path('application_success/<int:application_id>/', views.application_success, name='application_success'),
    ]