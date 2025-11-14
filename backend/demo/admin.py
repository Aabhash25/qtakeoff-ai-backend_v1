from django.contrib import admin
from .models import BookDemo

@admin.register(BookDemo)
class BookDemoAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'email', 'company', 'preferred_date'
    )