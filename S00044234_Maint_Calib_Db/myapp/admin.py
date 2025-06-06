from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Item

# Register your models here.

admin.site.register(Item)
admin.site.unregister(User)  # Unregister the default

# Custom UserAdmin class
class CustomUserAdmin(BaseUserAdmin):
    # Fields to display in the user list
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'date_joined')
    
    # Fields to filter by in the sidebar
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    
    # Fields to search
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    # Order by username
    ordering = ('username',)

# Register the User model with our custom admin
admin.site.register(User, CustomUserAdmin)