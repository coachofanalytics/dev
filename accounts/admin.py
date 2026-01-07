from django.contrib import admin
from .models import UserProfile, Category, Role, Staff


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'can_manage_users', 'can_manage_categories', 'can_manage_staff', 'can_moderate_content']
    list_filter = ['can_manage_users', 'can_manage_categories', 'can_manage_staff']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description')
        }),
        ('Permissions', {
            'fields': ('can_manage_users', 'can_manage_categories', 'can_manage_staff', 'can_view_reports', 'can_moderate_content')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'role', 'department', 'is_active', 'hired_date']
    list_filter = ['is_active', 'role', 'department', 'hired_date']
    search_fields = ['user__username', 'user__email', 'employee_id', 'department']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'employee_id', 'role')
        }),
        ('Employment Details', {
            'fields': ('department', 'hired_date', 'is_active')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'phone', 'location', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone', 'location']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'category')
        }),
        ('Profile Details', {
            'fields': ('bio', 'phone', 'location', 'website')
        }),
        ('Documents', {
            'fields': ('document',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
