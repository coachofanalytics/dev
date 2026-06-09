from django.urls import path
from . import views
from .views import UserUpdateView, SuperuserUpdateView, register

app_name = "accounts"
urlpatterns = [
    # =============================USERS VIEWS=====================================
    path("", views.home, name="home"),
    path("join/", views.join, name="joins"),
    path("login/", views.login_view, name="account-login"),
    path("logout/", views.custom_logout, name="account-logout"),
    path("register/", register, name="register"),
    path("verify-email/<uuid:token>/", views.verify_email, name="verify-email"),
    path(
        "email-verification-notice/<int:user_id>/",
        views.email_verification_notice,
        name="email-verification-notice",
    ),
    path("select-category/", views.select_category, name="select_category"),
    # path('login/', CustomLoginView.as_view(), name='login'),
    path("users/", views.users, name="accounts-users"),
    # path('users/', views.userslistview.as_view(), name='accounts-users'),
    path("processing/", views.userlist, name="processing-users"),
    path(
        "user/update/<int:pk>",
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
    path("thank/", views.thank, name="thank-you"),
    path("security/", views.security_verification, name="security"),
    # Regions urls
    path("list_regions/", views.list_regions, name="list_regions"),
    path( "region/<int:pk>/update/", views.update_regions, name="region_update"),
    path("create_region/", views.create_region, name="create_region"),
    path( "region/<int:pk>/delete/", views.delete_region, name="region_delete"),
    # Chapter urls
    path("list_chapters/", views.list_chapters, name="list_chapters"),
    path( "chapter/<int:pk>/update/", views.update_chapters, name="chapters_update"),
    path("create_chapter/", views.create_chapter, name="create_chapter"),
    path( "chapter/<int:pk>/delete/", views.delete_chapter, name="chapter_delete"),
    path('governance_list/', views.governance_list, name='governance_list'),

]
