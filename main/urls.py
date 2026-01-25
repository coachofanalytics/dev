from django.urls import path
from . import views

app_name = "main"

urlpatterns = [
    path("service-categories/", views.all_service_categories, name="all_service_categories"),
    path("service-categories/create/", views.servicecategory_create, name="servicecategory_create"),

    path("service-categories/<int:pk>/", views.service_category_detail, name="service_category_detail"),
    path("service-categories/<int:pk>/update/", views.servicecategory_update, name="servicecategory_update"),
    path("service-categories/<int:pk>/delete/", views.servicecategory_delete, name="servicecategory_delete"),

    path("services/<int:service_id>/categories/", views.service_category_list, name="servicecategory_by_service"),
]
