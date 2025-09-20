from django.urls import path
from . import views
from .views import (
    UserUpdateView,
    UserDeleteView,
    SuperuserUpdateView,
    ClientListView,
    ClientUpdateView,
    ClientDeleteView,
    ClientDetailView,
    EmployeeListView,
    CredentialUpdateView,
    TrackCreateView,
    TrackDeleteView,
    TrackDetailView,
    TrackListView,
    TrackUpdateView,
    populate_tokens_view,
    verify_email,
)

app_name = "accounts"
urlpatterns = [
    # =============================USERS VIEWS=====================================
    path("", views.home, name="home"),
    path("home/", views.home, name="home"),
    path("join/", views.join, name="join"),
    # Zero Bounce email validations
    # path('validate-emails/', validate_emails_view, name='validate_emails'),
    path("populate-tokens/", populate_tokens_view, name="populate_tokens"),
    path("verify-email/<uuid:token>/", verify_email, name="verify-email"),
    path(
        "email-verification-notice/<int:user_id>/",
        views.email_verification_notice,
        name="email-verification-notice",
    ),
    path("login/", views.login_view, name="account-login"),
    # path('changepassword/',PasswordsChangeView.as_view(template_name='accounts/registration/password_Change_Form.html'), name='password_Change_Form'),
    path("profile/<str:username>", views.profile, name="account-profile"),
    path(
        "profile/<int:pk>/update/",
        views.UserProfileUpdateView.as_view(
            template_name="accounts/admin/user_update_form.html"
        ),
        name="profile-update",
    ),
    path(
        "login_history/<str:username>", views.user_login_history, name="login_history"
    ),
    path("time/<int:pk>/update/", views.edit_login_logout_time, name="time-update"),
    path("users/", views.users, name="accounts-users"),
    path(
        "user/<int:pk>/update/",
        UserUpdateView.as_view(template_name="accounts/admin/user_update_form.html"),
        name="user-update",
    ),
    path(
        "superuser/<int:pk>/update/",
        SuperuserUpdateView.as_view(
            template_name="accounts/admin/user_update_form.html"
        ),
        name="superuser-update",
    ),
    # path('user/<int:pk>/update/', UserUpdateView.as_view(template_name='accounts/registration/join.html'), name='user-update'),
    path(
        "user/<int:pk>/delete/",
        UserDeleteView.as_view(template_name="accounts/admin/user_delete.html"),
        name="user-delete",
    ),
    # =============================CREDENTIALS VIEWS=====================================
    path("credentials/", views.credential_view, name="account-crendentials"),
    path(
        "newcredentialcategory/",
        views.newcredentialCategory,
        name="account-newcredentialcategory",
    ),
    path("newcredential/", views.newcredential, name="account-newcredentials"),
    path(
        "credential/update/<int:pk>/",
        CredentialUpdateView.as_view(
            template_name="accounts/admin/forms/credential_form.html"
        ),
        name="credential-update",
    ),
    path(
        "security_verification/",
        views.security_verification,
        name="security_verification",
    ),
    # =============================CLIENTS VIEWS=====================================
    path("clients/", ClientListView.as_view(), name="clients"),
    path("client/<int:pk>/update/", ClientUpdateView.as_view(), name="client-update"),
    path("client/<int:pk>/", ClientDetailView.as_view(), name="client-detail"),
    path("client/<int:pk>/delete/", ClientDeleteView.as_view(), name="client-delete"),
    # =============================EMPLOYEES VIEWS=====================================
    path("employees/", EmployeeListView.as_view(), name="employees"),
    # =============================CLIENTS WORK=====================================
    path("tracker/", TrackListView.as_view(), name="tracker-list"),
    path("client/<str:username>/", views.usertracker, name="user-list"),
    path("track/new/", TrackCreateView.as_view(), name="tracker-create"),
    path("track/<int:pk>/", TrackDetailView.as_view(), name="tracker-detail"),
    path("track/<int:pk>/update/", TrackUpdateView.as_view(), name="tracker-update"),
    path("track/<int:pk>/delete/", TrackDeleteView.as_view(), name="tracker-delete"),
    path("thank/", views.thank, name="thank-you"),
    # student
    path(
        "register-and-login/",
        views.register_and_login_user,
        name="register_and_login_user",
    ),
    path("email_code/", views.one_time_code, name="one_time_code"),
    # =============================TESTING VIEWS=====================================
    #    path('createtestusers/', views.CustomUserCreateView.as_view(template_name="accounts/customeruser_form.html"),name='testusers'),
]
