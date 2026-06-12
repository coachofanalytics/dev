from django.contrib import admin
from .models import (
    DocumentService,
    DocumentApplication,
    ApplicationDraft,
    DocumentDraft,
    GeneratedDocument,
    DataAccessLog,
    Payment,
)


@admin.register(DocumentService)
class DocumentServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "fee", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(DocumentApplication)
class DocumentApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "application_number",
        "service",
        "first_name",
        "last_name",
        "status",
        "fee",
        "submitted_at",
        "created_at",
    )
    list_filter = ("status", "service")
    search_fields = ("application_number", "first_name", "last_name", "id_number")


@admin.register(ApplicationDraft)
class ApplicationDraftAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "application",
        "completion_percentage",
        "last_completed_step",
        "last_modified",
    )
    list_filter = ("completion_percentage",)
    search_fields = ("application__application_number",)


@admin.register(DocumentDraft)
class DocumentDraftAdmin(admin.ModelAdmin):
    list_display = ("id", "application", "completion_percentage")
    search_fields = ("application__application_number",)


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "application",
        "title",
        "document_type",
        "issue_date",
        "status",
        "created_at",
    )
    list_filter = ("status", "document_type")
    search_fields = ("title", "application__application_number")


@admin.register(DataAccessLog)
class DataAccessLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "institution",
        "data_accessed",
        "purpose",
        "access_type",
        "timestamp",
    )
    list_filter = ("access_type", "institution")
    search_fields = ("institution", "data_accessed", "purpose")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "application",
        "method",
        "status",
        "amount",
        "bill_reference",
        "transaction_id",
        "paid_at",
        "created_at",
    )
    list_filter = ("status", "method")
    search_fields = ("bill_reference", "transaction_id")