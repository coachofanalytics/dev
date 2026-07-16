from django.urls import path
from . import views

# urls.py

app_name = "document_processing"

urlpatterns = [
    # Dashboard
    path("", views.document_application_list, name="applications"),

    # Applications
    path("applications/", views.document_application_list, name="applications"),
    # path(
    #     "applications/<int:pk>/",
    #     views.application_detail,
    #     name="application_detail"
    # ),

    # # New application workflow
    # path(
    #     "applications/new/",
    #     views.application_form,
    #     name="application_create"
    # ),
    # path(
    #     "applications/<int:pk>/edit/",
    #     views.application_form,
    #     name="application_edit"
    # ),
    # path(
    #     "applications/<int:pk>/summary/",
    #     views.application_summary,
    #     name="application_summary"
    # ),
    # path(
    #     "applications/<int:pk>/payment/",
    #     views.application_payment,
    #     name="application_payment"
    # ),

    # # Drafts
    # path("drafts/", views.drafts, name="drafts"),
    # path(
    #     "drafts/<int:pk>/delete/",
    #     views.delete_draft,
    #     name="delete_draft"
    # ),

    # # Payments
    # path(
    #     "applications/<int:pk>/pay/",
    #     views.process_payment,
    #     name="process_payment"
    # ),

    # # Documents
    # path("documents/", views.documents, name="documents"),
    # path(
    #     "documents/<int:pk>/view/",
    #     views.view_document,
    #     name="view_document"
    # ),
    # path(
    #     "documents/<int:pk>/download/",
    #     views.download_document,
    #     name="download_document"
    # ),

    # # Audit
    # path(
    #     "access-history/",
    #     views.access_history,
    #     name="access_history"
    # ),
]