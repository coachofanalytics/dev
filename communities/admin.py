from django.contrib import admin

# Register your models here.
from .models import *

# Register your models here.
admin.site.register(CommunityMember)
admin.site.register(ForumCategory) 
admin.site.register(Post)
admin.site.register(CommentP)
admin.site.register(EventCalendar)
admin.site.register(ContactMessage)
admin.site.register(UserProfile)
admin.site.register(UserSettings)   
admin.site.register(UserPreferences)

from .models import DirectoryMember

@admin.register(DirectoryMember)
class DirectoryMemberAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'profession', 'region', 'category', 'membership_type', 'is_verified', 'is_active', 'created_at']
    list_filter = ['category', 'membership_type', 'is_verified', 'is_active', 'region']
    search_fields = ['full_name', 'profession', 'expertise']
    list_editable = ['is_verified', 'is_active']
    readonly_fields = ['created_at', 'updated_at', 'initials']