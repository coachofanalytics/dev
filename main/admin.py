from django.contrib import admin
from .models import *

class DescriptionAdmin(admin.ModelAdmin):
    list_display = ("page", "name", "content")

    search_fields = ("page", "name")
    list_filter = ("name",)
    ordering = ("name",)
    filter_horizontal = ()


class DescriptionGovernance(admin.ModelAdmin):
    list_display = ("governance_category", "members", "title", "ui_order")

    # search_fields = ("page", "name")
    list_filter = ("governance_category",)
    # ordering = ("name",)
    # filter_horizontal = ()

# Register your models here.
# admin.site.register(Assets)
#admin.site.register(Feedback)
admin.site.register(Description, DescriptionAdmin)
# admin.site.register(Page)
#admin.site.register(Team)
#admin.site.register(Content)
#admin.site.register(Service)
#admin.site.register(SubService)
admin.site.register(News)
admin.site.register(Gallery)
admin.site.register(ContactUs)
#admin.site.register(Faq)
admin.site.register(GetHelp)
admin.site.register(Governance, DescriptionGovernance)
#admin.site.register(DonationOrganization)
admin.site.register(CommunityMember)
admin.site.register(DirectoryProfile)
admin.site.register(ForumCategory)
admin.site.register(CommunityPost)
admin.site.register(CommentP)
admin.site.register(EventCalendar)
admin.site.register(ContactMessage)


@admin.register(CommunityMessage)
class CommunityMessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['sender__name', 'recipient__name', 'subject', 'body']
    readonly_fields = ['created_at']
    raw_id_fields = ['sender', 'recipient', 'parent_message']
    fieldsets = (
        ('Participants', {
            'fields': ('sender', 'recipient')
        }),
        ('Content', {
            'fields': ('subject', 'body', 'parent_message')
        }),
        ('Status', {
            'fields': ('is_read', 'created_at')
        }),
    )
