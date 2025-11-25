from django import forms
from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from shared_core.users import CustomerUser
from accounts.models import TaskGroups
from management.models import *
from django.contrib import messages

# Register your models here.
class CsvImportForm(forms.Form):
    csv_upload = forms.FileField()


class AdsAdmin(admin.ModelAdmin):
    list_display = ("post_description","created_at")


class TaskHistoryAdmin(admin.ModelAdmin):
    list_display = ('id', 
                    "employee",
                    "group",
                    "category",
                    "activity_name",
                    "description",
                    "point",
                    "mxpoint",
                    "mxearning",)
    
    list_filter = ('employee', 'activity_name', 'group')
    search_fields = ('employee__username',"activity_name",)
    filter_horizontal = ()

    def save_model(self, request, obj, form, change):
        if obj.employee.is_staff:
            super().save_model(request, obj, form, change)
        else:
            messages.set_level(request, messages.ERROR)
            messages.error(request, 'User is not an Employee')

class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'activity_name', )

    def save_model(self, request, obj, form, change):
        if obj.employee.is_staff:
            super().save_model(request, obj, form, change)
        else:
            messages.set_level(request, messages.ERROR)
            messages.error(request, 'User is not an Employee')

def create_task(group, groupname, cat, user, activity, description, duration, point, mxpoint, mxearning):
    x = Task()
    x.group = group
    x.groupname = groupname
    x.category = cat
    x.employee = user
    x.activity_name = activity
    x.description = description
    x.duration = duration
    x.point = point
    x.mxpoint = mxpoint
    x.mxearning = mxearning
    x.save()
class TrainingAdmin(admin.ModelAdmin):
    list_display = ('id', 'presenter')

    def save_model(self, request, obj, form, change):
        obj.save()
        user = obj.presenter
        print(user)
        try:
            session = Training.objects.filter(presenter=user).count()
            print(session)

            if session >= 35 and user.category == 1:  # Job_Applicant category
                user.is_staff = True
                # REMOVED: user.is_applicant = False  # Field no longer exists
                user.save()

                try:
                    group = TaskGroups.objects.all().first()
                    cat = TaskCategory.objects.all().first()
                    try:
                        max_point = Task.objects.filter(groupname=group, category=cat).first()
                        max_point = max_point.mxpoint
                    except:
                        max_point = 0

                    create_task('Group A', group, cat, user, 'General Meeting', 'General Meeting description, auto added', '0', '0', max_point, '0')
                    create_task('Group A', group, cat, user, 'BI Session', 'BI Session description, auto added', '0', '0', max_point, '0')
                    create_task('Group A', group, cat, user, 'One on One', 'One on One description, auto added', '0', '0', max_point, '0')
                    create_task('Group A', group, cat, user, 'Video Editing', 'Video Editing description, auto added', '0', '0', max_point, '0')
                    create_task('Group A', group, cat, user, 'Dev Recruitment', 'Dev Recruitment description, auto added', '0', '0', max_point, '0')
                    create_task('Group A', group, cat, user, 'Sprint', 'Sprint description, auto added', '0', '0', max_point, '0')
                except:
                    print("Something wrong in task creation")
                if user == request.user:
                    return redirect("management:employee_contract")
        except:
            pass

admin.site.register(Training, TrainingAdmin)
# admin.site.register(TaskHistory)
admin.site.register(TaskHistory, TaskHistoryAdmin)
admin.site.register(Task, TaskAdmin)
admin.site.register(Policy)
admin.site.register(Meetings)
admin.site.register(TaskLinks)
admin.site.register(TaskCategory)
admin.site.register(Requirement)
admin.site.register(Advertisement, AdsAdmin)
admin.site.register(ProcessJustification)
admin.site.register(ProcessBreakdown)
admin.site.register(TaskGroups)
admin.site.register(Grievance)
admin.site.register(Conflict_Resolution)
admin.site.register(BaseContract)


class LinkInline(admin.TabularInline):
    model = Link
    extra = 1

class SubCategoryInline(admin.TabularInline):
    model = SubCategory
    inlines = [LinkInline]
    extra = 1

# class CategoryAdmin(admin.ModelAdmin):
#     inlines = [SubCategoryInline]

#     def get_inline_instances(self, request, obj=None):
#         # Dynamically adjust inlines based on the currently selected object
#         if obj:
#             return [inline(self.model, self.admin_site) for inline in self.inlines]
#         else:
#             return super(CategoryAdmin, self).get_inline_instances(request, obj)

# admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory)
admin.site.register(Link)


"""
admin.site.register(Employee)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Category,MPTTModelAdmin)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

class ActivityAdmin(admin.ModelAdmin):
    list_display = ['activity_name','description', 'point','mxpoint', 'mxearning']
    list_filter = ['activity_name', 'is_active']
    list_editable = ['description', 'point','mxpoint','mxearning']
    prepopulated_fields = {'slug': ('activity_name',)}

    def get_urls(self):
        urls = super().get_urls()
        new_urls = [path('upload-csv/', self.upload_csv),]
        return new_urls + urls
  
    def upload_csv(self, request):
        if request.method == "POST":
            csv_file = request.FILES["csv_upload"]
            
            if not csv_file.name.endswith('.csv'):
                messages.warning(request, 'The wrong file type was uploaded, it should be a csv file')
                return HttpResponseRedirect(request.path_info)
            
            #file= csv_file.read().decode("utf-8")
            file= csv_file.read().decode("ISO-8859-1") 
            file_data = file.split("\n")
            csv_data=[line for line in file_data if line.strip() != ""]
            print(csv_data)
             for x in csv_data:
                fields = x.split(",")
                created = Activity.objects.update_or_create(
                                    category=fields[0],
                                    group=fields[1],
                                    activity_name=fields[2],
                                    created_by=fields[3],
                                    description=fields[4],
                                    submission=fields[5],
                                    slug=fields[6],
                                    point=fields[7],
                                    mxpoint=fields[8],
                                    mxearning=fields[9],
                         )
            url = reverse('admin:index')
            return HttpResponseRedirect(url)
           
        form = CsvImportForm()
        data = {"form": form}
        return render(request, "admin/csv_upload.html", data)

admin.site.register(Activity, ActivityAdmin)

"""