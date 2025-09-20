from django.contrib import admin
from ai_services.models import (
	CashappMail, DynamicExcelData, GotoMeetings,ReplyMail,
    Editable,UseCase,CaseCategory,OpenaiPrompt,UpworkConnects
)

class CaseCategoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
    )

# Register your models here.
admin.site.register(CaseCategory, CaseCategoryAdmin)
admin.site.register(CashappMail)
admin.site.register(ReplyMail)
admin.site.register(Editable)
admin.site.register(OpenaiPrompt)
admin.site.register(UseCase)
admin.site.register(UpworkConnects)
admin.site.register(DynamicExcelData)
admin.site.register(GotoMeetings)