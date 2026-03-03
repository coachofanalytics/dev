from django.contrib import admin


# Register your models here.
from .models import *

admin.site.register(CommunityMember)
admin.site.register(ForumCategory)
admin.site.register(Post)
admin.site.register(CommentP)
admin.site.register(EventCalendar)
admin.site.register(ContactMessage)
admin.site.register(UserProfile)
admin.site.register(UserSettings)
admin.site.register(UserPreferences)
