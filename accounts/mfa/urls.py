"""
URL configuration for MFA app.
"""

from django.urls import path

from accounts.mfa import views

app_name = "mfa"

urlpatterns = [
    # MFA Setup
    path("setup/", views.MFASetupView.as_view(), name="setup"),
    path("backup-codes/", views.MFABackupCodesView.as_view(), name="backup_codes"),
    path(
        "regenerate-codes/",
        views.MFARegenerateCodesView.as_view(),
        name="regenerate_codes",
    ),
    path("disable/", views.MFADisableView.as_view(), name="disable"),
    # MFA Verification (during login)
    path("verify/", views.MFAVerifyView.as_view(), name="verify"),
    path(
        "verify/backup/",
        views.MFABackupCodeVerifyView.as_view(),
        name="verify_backup",
    ),
]
