from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import UserProfile, Equipment, MACHINE_TYPE_CHOICES

# Register your models here.

#User profile class
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Information'
    fields = ('role', 'employee_id', 'department', 'phone_number')
    extra = 0

# Custom UserAdmin class
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    # Fields to display in the user list
    list_display = ('username', 'email', 'first_name', 'last_name', 'get_role', 'get_role_badge', 'is_active', 'date_joined')
    
    # Fields to filter by in the sidebar
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'profile__role','date_joined')
    
    # Fields to search
    search_fields = ('username', 'email', 'first_name', 'last_name' 'profile__employee_id')
    
    # Order by username
    ordering = ('username',)

    def get_role(self, obj):
        """Display the user's role"""
        try:
            return obj.profile.get_role_display()
        except UserProfile.DoesNotExist:
            return "No Profile"
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'profile__role'

    def get_role_badge(self, obj):
        
    #Each Role to have a different colour   
        try:
            role = obj.profile.role
            colors = {
                'administrator': '#dc3545',  # Red
                'maintenance': '#28a745',    # Green
                'quality': '#007bff',        # Blue
            }
            color = colors.get(role, '#6c757d')
            return format_html(
                '<span style="background-color: {}; color: white; padding: 3px 8px; '
                'border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
                color,
                obj.profile.get_role_display() if hasattr(obj, 'profile') else 'No Role'
            )
        except UserProfile.DoesNotExist:
            return format_html('<span style="color: #dc3545;">No Profile</span>')
        get_role_badge.short_description = 'Role Badge'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_full_name', 'role', 'employee_id', 'department', 'created_at')
    list_filter = ('role', 'department', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id')
    list_editable = ('role',)  # Allows quick role editing from the list view
    ordering = ('-created_at',)
    
    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}" if obj.user.first_name else obj.user.username
    get_full_name.short_description = 'Full Name'

# Unregister the original User admin and register the new one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Customize admin site header
admin.site.site_header = "Maintenance & Calibration System Administration"
admin.site.site_title = "M&C Admin"
admin.site.index_title = "System Administration"

#Equipment Database Class
@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = [
        'machine_id', 
        'machine_name', 
        'machine_type', 
        'machine_location',
        'last_calibration_date',
        'last_maintenance_date',
        'next_calibration_date',
        'next_maintenance_date',
        'is_calibration_overdue',
        'is_maintenance_overdue'
    ]
    
    list_filter = [
        'machine_type',
        'last_calibration_date',
        'last_maintenance_date',
        'created_at'
    ]
    
    search_fields = [
        'machine_id',
        'machine_name',
        'machine_location'
    ]
    
    readonly_fields = [
        'next_calibration_date',
        'next_maintenance_date',
        'is_calibration_overdue',
        'is_maintenance_overdue',
        'days_until_calibration',
        'days_until_maintenance',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('machine_id', 'machine_name', 'machine_type', 'machine_location')
        }),
        ('Maintenance & Calibration', {
            'fields': (
                'last_calibration_date', 
                'calibration_interval_days',
                'last_maintenance_date', 
                'maintenance_interval_days'
            )
        }),
        ('Status (Read Only)', {
            'fields': (
                'next_calibration_date',
                'next_maintenance_date',
                'is_calibration_overdue',
                'is_maintenance_overdue',
                'days_until_calibration',
                'days_until_maintenance'
            ),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Set created_by field when creating new equipment"""
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    # Custom admin methods for better display
    def next_calibration_date(self, obj):
        return obj.next_calibration_date
    next_calibration_date.short_description = 'Next Calibration'
    next_calibration_date.admin_order_field = 'last_calibration_date'
    
    def next_maintenance_date(self, obj):
        return obj.next_maintenance_date
    next_maintenance_date.short_description = 'Next Maintenance'
    next_maintenance_date.admin_order_field = 'last_maintenance_date'
    
    def is_calibration_overdue(self, obj):
        return obj.is_calibration_overdue
    is_calibration_overdue.short_description = 'Cal Overdue'
    is_calibration_overdue.boolean = True
    
    def is_maintenance_overdue(self, obj):
        return obj.is_maintenance_overdue
    is_maintenance_overdue.short_description = 'Maint Overdue'
    is_maintenance_overdue.boolean = True