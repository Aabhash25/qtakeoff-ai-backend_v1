from django.contrib import admin
from .models import MaterialCategory, MaterialSubcategory, Material
from unfold.admin import ModelAdmin
from import_export.admin import ImportExportModelAdmin  # type: ignore
from .resources import MaterialCategoryResource, MaterialResource


class MaterialCategoryAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = MaterialCategoryResource
    list_display = ('category_name', 'division')
    search_fields = ('category_name', 'division')


class MaterialSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('subcategory_name', 'sub_division', 'category',)
    search_fields = ('subcategory_name', 'category__category_name', 'sub_division')
    list_filter = ('category', 'sub_division')


class MaterialAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = MaterialResource
    list_display = ('material_name', 'spec_section', 'get_category', 'subcategory', 'currency', 'price', 'unit')
    search_fields = ('material_name', 'subcategory__subcategory_name', 'subcategory__category__category_name')
    list_filter = ('subcategory', 'subcategory__category')
    ordering = ('-created_at',)

    def get_category(self, obj):
        return obj.subcategory.category if obj.subcategory else None
    get_category.short_description = 'Category'


admin.site.register(MaterialCategory, MaterialCategoryAdmin)
admin.site.register(MaterialSubcategory, MaterialSubcategoryAdmin)
admin.site.register(Material, MaterialAdmin)
