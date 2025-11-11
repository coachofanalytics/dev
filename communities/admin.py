from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(CommunityMember)
admin.site.register(ForumCategory) 
admin.site.register(Post)
admin.site.register(CommentP)
admin.site.register(EventCalendar)
admin.site.register(ContactMessage)