from django.contrib import admin

from .models import *


class FeaturedSubCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'title')
    list_editable = ('order',)


class TrainingResponsesTrackingAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'featuredsubcategory')

class ActivityLinksAdmin(admin.ModelAdmin):
    list_display = ('link_name',  'Featuredsubcategory')


class Prep_QuestionsAdmin(admin.ModelAdmin):
    list_display = ('question','position', 'is_featured','is_tech')
    
  

admin.site.register(ActivityLinks, ActivityLinksAdmin)
'''
# Register your models here.

'''
admin.site.register(Prep_Questions, Prep_QuestionsAdmin)
admin.site.register(FeaturedSubCategory, FeaturedSubCategoryAdmin)
admin.site.register(TrainingResponsesTracking, TrainingResponsesTrackingAdmin)
admin.site.register(FeaturedCategory)
admin.site.register(FeaturedActivity)
admin.site.register(BackgroundCheck)
admin.site.register(Correct_answers)
admin.site.register(Training_Responses)
admin.site.register(Interviews)
admin.site.register(JobRoles)
admin.site.register(JobRole)
admin.site.register(ClientAssessment)
admin.site.register(UserAnswerStatus)
