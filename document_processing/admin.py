from django.contrib import admin
from .models import Application, Payment, GeneratedDocument, DataAccessLog
# Register your models here.


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'application_number', 'service',
        'first_name', 'last_name', 'id_number', 'status', 'fee',
    )
    list_filter = ('status', 'service', 'certified')
    search_fields = (
        'user__username', 'first_name', 'last_name',
        'id_number', 'application_number',
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'application', 'method', 'amount',
        'bill_id', 'transaction_id', 'status',
    )
    list_filter = ('method', 'status')
    search_fields = ('bill_id', 'transaction_id', 'payer_phone')


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'title', 'status', 'issued_at')
    list_filter = ('status',)
    search_fields = ('title',)


@admin.register(DataAccessLog)
class DataAccessLogAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'institution', 'data_accessed',
        'access_type', 'created_at',
    )
    list_filter = ('access_type',)
    search_fields = ('institution', 'data_accessed', 'purpose')
