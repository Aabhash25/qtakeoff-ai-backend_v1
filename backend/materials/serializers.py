from rest_framework import serializers
from materials.models import MaterialCategory, MaterialSubcategory, Material

class MaterialCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = MaterialCategory
        fields = ['id', 'category_name', 'division']

class MaterialSubcategorySerializer(serializers.ModelSerializer):
    category = MaterialCategorySerializer(read_only=True)

    class Meta:
        model = MaterialSubcategory
        fields = ['id', 'subcategory_name', 'sub_division', 'category']

class MaterialSerializer(serializers.ModelSerializer):
    subcategory = MaterialSubcategorySerializer(read_only=True)

    class Meta:
        model = Material
        fields = ['id', 'material_name', 'spec_section', 'subcategory', 'price', 'currency', 'unit', 'created_at']