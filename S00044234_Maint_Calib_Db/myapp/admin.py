from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import UserProfile

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