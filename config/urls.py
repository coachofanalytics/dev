"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from accounts import views as accounts_views

urlpatterns = [
    path('admin/', admin.site.urls),
     path('', TemplateView.as_view(template_name='landing.html'), name='home'),

    # Authentication URLs
    path('register/', accounts_views.register, name='register'),
    path('login/', accounts_views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),

    # Profile and Dashboard URLs
    path('profile/', accounts_views.profile, name='profile'),
    path('edit-profile/', accounts_views.edit_profile, name='edit_profile'),
    path('settings/', accounts_views.user_settings, name='settings'),
    path('profile/<str:username>/', accounts_views.profile, name='profile'),
    path('dashboard/investor/', accounts_views.investor_dashboard, name='investor_dashboard'),
    path('dashboard/business/', accounts_views.business_dashboard, name='business_dashboard'),
    path('dashboard/individual/', accounts_views.individual_dashboard, name='individual_dashboard'),

    # Staff Dashboard URLs
    path('staff/dashboard/', accounts_views.staff_dashboard, name='staff_dashboard'),
    path('staff/users/', accounts_views.staff_users_list, name='staff_users_list'),
    path('staff/categories/', accounts_views.staff_categories_list, name='staff_categories_list'),

    # Payment and Wallet URLs
    path('payments/', include('payments.urls')),
    # Marketplace URLs
    path('marketplace/', include('marketplace.urls')),
    # Password Management URLs
    path('password-change/',
         auth_views.PasswordChangeView.as_view(template_name='registration/password_change_form.html', success_url='/password-change/done/'),
         name='password_change'),
    path('password-change/done/',
         auth_views.PasswordChangeDoneView.as_view(template_name='registration/password_change_done.html'),
         name='password_change_done'),
    path('password-reset/',
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
