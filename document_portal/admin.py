from django.contrib import admin
from .models import DocumentApplication, DocumentDraft


@admin.register(DocumentApplication)
class DocumentApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "service_type",
        "first_name",
        "last_name",
        "status",
        "fee",
        "submitted_at",
    )
    search_fields = ("first_name", "last_name", "id_number", "service_type")
    list_filter = ("status", "service_type")


@admin.register(DocumentDraft)
class DocumentDraftAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "application",
        "completion_percentage",
    )
    search_fields = ("application__first_name", "application__last_name")