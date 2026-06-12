from django.contrib import admin
from .models import DocumentApplication
# Register your models here.

@admin.register(DocumentApplication)
class DocumentApplicationAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'service_type', 'reason', 'status','fee', 'last_modified', 'submitted_at')
    list_filter = ('status', 'service_type')
    search_fields = ('user__username', 'first_name', 'last_name', 'id_number')