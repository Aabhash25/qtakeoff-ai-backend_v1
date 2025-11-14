from django.contrib import admin
from .models import (Annotation, 
                     WallAnnotation, 
                     WindowAndDoorAnnotation, 
                     AnnotationMaterial, 
                    #  FloorAnnotation, 
                     WallAnnotationMaterial, 
                     WindowAndDoorAnnotationMaterial)
# from unfold.admin import ModelAdmin 


class AnnotationMaterialInline(admin.TabularInline):
    model = AnnotationMaterial
    extra = 1  
    autocomplete_fields = ['material']

@admin.register(Annotation)
class AnnotationAdmin(admin.ModelAdmin):
    list_display = ('blueprint_title', 'label', 'annotation_type', 'created_at', 'updated_at')
    inlines = [AnnotationMaterialInline]
    search_fields = ('label', 'annotation_type', 'blueprint__title')
    list_filter = ('annotation_type', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 20

    def blueprint_title(self, obj):
        return obj.blueprint.title
    blueprint_title.short_description = 'Blueprint Title'

class WallAnnotationMaterialInline(admin.TabularInline):
    model = WallAnnotationMaterial
    extra = 1 
    autocomplete_fields = ['material']

@admin.register(WallAnnotation)
class WallAnnotationAdmin(admin.ModelAdmin):
    list_display = ('blueprint__title', 'label', 'annotation_type', 'created_at', 'updated_at')
    search_fields = ('label', 'annotation_type')
    inlines = [WallAnnotationMaterialInline]
    list_filter = ('annotation_type', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 20

class WindowAndDoorAnnotationMaterialInline(admin.TabularInline):
    model = WindowAndDoorAnnotationMaterial
    extra = 1 
    autocomplete_fields = ['material']

@admin.register(WindowAndDoorAnnotation)
class WindowAndDoorAnnotationAdmin(admin.ModelAdmin):
    list_display = ('blueprint__title', 'label', 'annotation_type', 'created_at', 'updated_at')
    search_fields = ('label', 'annotation_type')
    inlines = [WindowAndDoorAnnotationMaterialInline]
    list_filter = ('annotation_type', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 20


# @admin.register(FloorAnnotation)
# class FloorAnnotationAdmin(admin.ModelAdmin):
#     list_display = ('blueprint__title', 'label', 'annotation_type', 'created_at', 'updated_at')
#     search_fields = ('label', 'annotation_type')
#     list_filter = ('annotation_type', 'created_at')
#     ordering = ('-created_at',)
#     date_hierarchy = 'created_at'
#     list_per_page = 20