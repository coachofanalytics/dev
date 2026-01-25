from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.auth import views as auth_views

from accounts import views as account_views
from django.shortcuts import render


def handler400(request, exception=None):
    return render(request, "errors/400.html", status=400)


def handler403(request, exception=None):
    return render(request, "errors/403.html", status=403)


def handler500(request):
    return render(request, "errors/500.html", status=500)


# ✅ ERROR HANDLERS (spelling must match your views.py functions)
handler400 = "main.views.handler400"
handler403 = "main.views.handler403"
handler500 = "main.views.handler500"


urlpatterns = [
    # ✅ Admin
    path("admin/", admin.site.urls),

    # ✅ Static & Media (optional - you already also have static() below)
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),

    # ✅ Auth routes
    path(
        "logout/",
        auth_views.LogoutView.as_view(template_name="accounts/registration/logout.html"),
        name="account-logout",
    ),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/registration/password_reset.html"
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/registration/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-complete/",
        account_views.PasswordResetCompleteView,
        name="password_reset_complete",
    ),

    # ✅ Main app
    path("main/", include(("main.urls", "main"), namespace="main")),

    # ✅ Accounts + Application
    path("accounts/", include("accounts.urls")),
    path("application/", include(("application.urls", "application"), namespace="data")),

    # ✅ Social auth (allauth)
    path("accounts/social/custom_login/", account_views.custom_social_login, name="custom_social_login"),
    path("social_accounts/signup/", account_views.join),
    path("social_accounts/login/", account_views.login_view),
    path("social_accounts/social/signup/", account_views.login_view),
    path("social_accounts/", include("allauth.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
