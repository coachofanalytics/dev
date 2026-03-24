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
    path('book_consultation/', views.book_consultation, name='book_consultation'),
    path('success/', views.booking_success, name='booking_success'),
    path('pre_assessment/', views.pre_assessment, name='pre_assessment'),
    path('eligibility/', views.eligibility_check, name='eligibility_check'),
    path('path/<str:path_name>/', views.path_detail, name='path_detail'),
    path('eligibility/form/', views.eligibility_form, name='eligibility_form'),
    path('find-attorney/', views.find_attorney, name='find_attorney'),
    path('attorney_success/',views.attorney_success, name='attorney_success'),
    path('contacts/', views.contacts, name='contacts'),
    ]