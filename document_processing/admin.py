<<<<<<< HEAD
# from django.contrib import admin

# # Register your models here.

# @admin.register(ApplicationDraft)
# class ApplicationDraftAdmin(admin.ModelAdmin):
#     list_display = (
#         "id",
#         "user",
#         "application",
#         "completion_percentage",
#         "last_completed_step",
#         "last_modified",
#     )
#     search_fields = ("application__application_number",)
=======
from django.contrib import admin
from .models import Document_Application
# Register your models here.

# @admin.register(DocumentApplication)
# class DocumentApplicationsAdmin(admin.ModelAdmin):
#     list_display = ('id', 'user', 'service_type', 'reason', 'status','fee', 'last_modified', 'submitted_at')
#     list_filter = ('status', 'service_type')
#     search_fields = ('user__username', 'first_name', 'last_name', 'id_number')
@admin.register(Document_Application)
class Document_ApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service_type', 'reason', 'status','fee', 'last_modified', 'submitted_at')
    list_filter = ('status', 'service_type')
    search_fields = ('user__username', 'first_name', 'last_name', 'id_number')
>>>>>>> 6b38594f704780076e59319dcf0696de541774a1
