from django.contrib import admin
from .models import Project
# from unfold.admin import ModelAdmin

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 20

    readonly_fields = (
        'title', 'owner',
    )