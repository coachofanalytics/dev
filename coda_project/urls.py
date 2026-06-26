from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.auth import views as auth_views

from accounts import views as account_views


# =========== ERROR HANDLING SECTION ==============
handler400 = "main.views.hendler400"
handler403 = "main.views.hendler403"
handler404 = "main.views.hendler404"
handler500 = "main.views.hendler500"


urlpatterns = [
    path("admin/", admin.site.urls),

    # Main app namespace
    path("", include(("main.urls", "main"), namespace="main")),

    # Healthcare services app
    path("healthcare/", include("healthcare_services.urls")),

    # Static and media serving
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),

    # Password reset URLs
    path(
        "otp-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/registration/otp_reset.html"
        ),
        name="otp_reset",
    ),

    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/registration/password_reset.html"
        ),
        name="password_reset",
    ),

    path(
        "password-reset-email/",
        account_views.password_reset_request,
        name="password_reset_email",
    ),

    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/registration/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),

    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),

    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),

    # Other app URLs
    path("", include("main.news_urls", namespace="news")),
    path("accounts/", include("accounts.urls")),
    path("finance/", include("finance.urls")),
    path("communities/", include("main.urls_communities")),
    path("document_processing/", include("document_processing.urls")),

    # Social auth URLs
    path(
        "accounts/social/custom_login/",
        account_views.custom_social_login,
        name="custom_social_login",
    ),
    path("social_accounts/signup/", account_views.join),
    path("social_accounts/login/", account_views.login_view),
    path("social_accounts/social/signup/", account_views.login_view),
    path("social_accounts/", include("allauth.urls")),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    ) + static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT
    )