from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import MaterialCategory, MaterialSubcategory, Material


class MaterialCategoryResource(resources.ModelResource):
    category_name = fields.Field(attribute='category_name', column_name='Category Name')
    division = fields.Field(attribute='division', column_name='Division')

    class Meta:
        model = MaterialCategory
        import_id_fields = ['category_name', 'division']
        fields = ('category_name', 'division')
        skip_unchanged = True
        report_skipped = True


class CategoryWidget(ForeignKeyWidget):
    """Returns existing category or creates it on the fly."""
    def clean(self, value, row=None, *args, **kwargs):
        if not value:
            return None
        value = value.strip()
        obj, _created = MaterialCategory.objects.get_or_create(category_name=value)
        return obj


class SubcategoryWidget(ForeignKeyWidget):
    def clean(self, value, row=None, *args, **kwargs):
        print("ROW:", row)
        print("VALUE:", value)

        if not value:
            return None

        value = value.strip()
        category_name = (row.get('Category') or '').strip()
        sub_division = (row.get('Sub Division') or '').strip() or None

        if not category_name:
            raise ValueError(f"[IMPORT ERROR] Missing 'Category' for subcategory '{value}'.")

        category, _ = MaterialCategory.objects.get_or_create(category_name=category_name)
        obj, _created = MaterialSubcategory.objects.get_or_create(
            subcategory_name=value,
            category=category,
            defaults={'sub_division': sub_division}
        )
        return obj

class MaterialResource(resources.ModelResource):
    material_name = fields.Field(attribute='material_name', column_name='Material Name')
    
    subcategory = fields.Field(
        attribute='subcategory',
        column_name='Subcategory',
        widget=SubcategoryWidget(MaterialSubcategory, 'subcategory_name')
    )
    
    # sub_division = fields.Field(attribute='subcategory__sub_division', column_name='Sub Division')
    spec_section = fields.Field(attribute='spec_section', column_name='Spec Name')
    currency = fields.Field(attribute='currency', column_name='Currency')
    price = fields.Field(attribute='price', column_name='Price')
    unit = fields.Field(attribute='unit', column_name='Unit')

    def dehydrate_sub_division(self, material):
        return material.subcategory.sub_division if material.subcategory else None

    def skip_row(self, instance, original, row, import_validation_errors=None):
        # Skip completely empty rows
        if not row or all(not (str(v).strip()) for v in row.values()):
            return True
        return super().skip_row(instance, original, row, import_validation_errors)

    class Meta:
        model = Material
        fields = (
            'material_name', 'category', 'subcategory',
            'sub_division', 'spec_section', 'currency', 'price', 'unit'
        )
        import_id_fields = ('material_name', 'subcategory')
        skip_unchanged = True
        report_skipped = True
