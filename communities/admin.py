from django.contrib import admin

# Register your models explicitly to avoid accidental double-imports
from .models import (
	CommunityMember,
	ForumCategory,
	Post,
	CommentP,
	EventCalendar,
	ContactMessage,
	UserProfile,
	UserSettings,
	UserPreferences,
	DirectoryProfile,
)


admin.site.register(CommunityMember)
admin.site.register(ForumCategory)
admin.site.register(Post)
admin.site.register(CommentP)
admin.site.register(EventCalendar)
admin.site.register(ContactMessage)
admin.site.register(UserProfile)
admin.site.register(UserSettings)
admin.site.register(UserPreferences)
admin.site.register(DirectoryProfile)
