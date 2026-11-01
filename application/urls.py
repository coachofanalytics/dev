
from django.urls import path
from . import views

app_name = "application"

urlpatterns = [
    path("", views.home, name="home"),

    path("career/", views.career, name="career"),

    path("joblist/", views.job_list, name="job_list"),

    path(
        "job/<int:pk>/",
        views.job_detail,
        name="job_detail",
    ),

    path(
        "job/<int:pk>/apply/",
        views.job_apply,
        name="job_apply",
    ),

    path("apply/", views.apply, name="apply"),
]
