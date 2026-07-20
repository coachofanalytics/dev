from django.urls import path
from . import views

# urls.py

app_name = "document_processing"

urlpatterns = [
    # Dashboard
    path("", views.document_application_list, name="applications"),

    # Applications
    path("applications/", views.document_application_list, name="applications"),
    path(
        "applications/<int:pk>/",
        views.application_detail,
        name="application_detail",
    ),

    # New application workflow (3 steps)
    path(
        "applications/new/",
        views.application_create,
        name="application_create",
    ),
    path(
        "applications/<int:pk>/edit/",
        views.application_edit,
        name="application_edit",
    ),
    path(
        "applications/<int:pk>/summary/",
        views.application_summary,
        name="application_summary",
    ),
    path(
        "applications/<int:pk>/payment/",
        views.application_payment,
        name="application_payment",
    ),
    path(
        "applications/<int:pk>/pay/",
        views.process_payment,
        name="process_payment",
    ),

    # Drafts
    path("drafts/", views.drafts_list, name="drafts"),
    path(
        "drafts/<int:pk>/delete/",
        views.delete_draft,
        name="delete_draft",
    ),

    # Documents
    path("documents/", views.documents_list, name="documents"),
    path(
        "documents/<int:pk>/view/",
        views.view_document,
        name="view_document",
    ),
    path(
        "documents/<int:pk>/download/",
        views.download_document,
        name="download_document",
    ),

    # Audit
    path(
        "access-history/",
        views.access_history,
        name="access_history",
    ),

    # AJAX
    path(
        "api/subcounties/",
        views.subcounties_json,
        name="subcounties_json",
    ),
]