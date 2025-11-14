from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, CustomUserProfile
# from unfold.admin import ModelAdmin

@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin, admin.ModelAdmin):
    ordering = ('email',)
    list_display = ('email', 'username', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'role')}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'role', 'password1', 'password2')}
        ),
    )

    filter_horizontal = ('groups', 'user_permissions')

@admin.register(CustomUserProfile)
class CustomUserProfileAdmin(admin.ModelAdmin):
    pass
