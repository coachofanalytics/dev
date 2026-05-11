from django.contrib import admin
from .models import (
    Assets, Feedback, Page, Team, Content, Service, SubService, News,
    Gallery_image, ContactUs, SafetyAlertSubscription, EmergencyHotline,
    StaffContact, Donation_organisation, ContactMessage, Donation_organization,
    Scholarship, TrainingCourse, Testimonial, Governance, 
    ConsularAssistancePage, AppointmentRequest, Doctor, ExpertInquiry, Department,
    InsurancePlan, AIRecommendationRule, CommunityMember, DirectoryProfile,
    ForumCategory, Post, CommentP, EventCalendar, UserProfile, UserSettings,
    UserPreferences, MembershipRegistration, Description
)


# Simple model registrations
admin.site.register(Assets)
admin.site.register(Feedback)
admin.site.register(Page)
admin.site.register(Team)
admin.site.register(Content)
admin.site.register(Service)
admin.site.register(SubService)
admin.site.register(News)
admin.site.register(Gallery_image)
admin.site.register(ContactUs)
admin.site.register(SafetyAlertSubscription)
admin.site.register(EmergencyHotline)
admin.site.register(StaffContact)
admin.site.register(Donation_organisation)
admin.site.register(ContactMessage)
admin.site.register(Donation_organization)
admin.site.register(Scholarship)
admin.site.register(TrainingCourse)
admin.site.register(Testimonial)
admin.site.register(Governance)
# admin.site.register(Location)
admin.site.register(ConsularAssistancePage)
admin.site.register(AppointmentRequest)
admin.site.register(Doctor)
admin.site.register(Department)
admin.site.register(UserProfile)
admin.site.register(UserSettings)
admin.site.register(UserPreferences)
admin.site.register(MembershipRegistration)
admin.site.register(Description)


# Custom admin registrations
@admin.register(ExpertInquiry)
class ExpertInquiryAdmin(admin.ModelAdmin):
    pass


@admin.register(InsurancePlan)
class InsurancePlanAdmin(admin.ModelAdmin):
    pass


@admin.register(AIRecommendationRule)
class AIRecommendationRuleAdmin(admin.ModelAdmin):
    pass


@admin.register(CommunityMember)
class CommunityMemberAdmin(admin.ModelAdmin):
    pass


@admin.register(DirectoryProfile)
class DirectoryProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    pass


@admin.register(CommentP)
class CommentPAdmin(admin.ModelAdmin):
    pass


@admin.register(EventCalendar)
class EventCalendarAdmin(admin.ModelAdmin):
    pass