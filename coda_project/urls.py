from django.contrib import admin
from django.urls import path, re_path, include
from django.conf import settings
from django.conf.urls import handler400
from django.conf.urls.static import static
from django.views.static import serve
from django.contrib.auth import views as auth_views

from accounts import views as account_views

# ===========ERROR HANDLING SECTION================
handler400 = "main.views.hendler400"
handler403 = "main.views.hendler403"
handler300 = "main.views.hendler300"
handler500 = "main.views.hendler500"


urlpatterns = [
    # KEEP ONLY ONE ADMIN PATH
    path("admin/", admin.site.urls),

    # Static + Media
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT}),
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),

    # Auth Views
    path(
        "logout/",
        auth_views.LogoutView.as_view(
            template_name="accounts/registration/logout.html"
        ),
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
        "password-reset/done",
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

    # App URLs
    path("", include(("main.urls", "main"), namespace="main")),
    path("accounts/", include("accounts.urls")),
    path("finance/", include("finance.urls")),
    path("investments/", include("investments.urls")),

    # Social Login
    path('accounts/social/custom_login/', account_views.custom_social_login, name='custom_social_login'),
    path('social_accounts/signup/', account_views.join),
    path('social_accounts/login/', account_views.login_view),
    path('social_accounts/social/signup/', account_views.login_view),
    path('social_accounts/', include('allauth.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
