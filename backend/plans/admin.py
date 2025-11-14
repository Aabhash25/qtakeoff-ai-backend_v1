from django.contrib import admin
from .models import Blueprint, BlueprintImage
# from unfold.admin import ModelAdmin

@admin.register(Blueprint)
class BlueprintAdmin(admin.ModelAdmin):
    list_display = ('title', 'project', 'project__owner', 'category', 'status', 'created_at', 'updated_at')
    search_fields = ('title', 'project__title')
    list_filter = ('category',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    prepopulated_fields = {'title': ('description',)}

@admin.register(BlueprintImage)
class BlueprintImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'blueprint', 'dpi', 'scale', 'is_verified', 'created_at')
    search_fields = ('blueprint__title',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
