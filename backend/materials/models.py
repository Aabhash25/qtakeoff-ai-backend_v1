from django.db import models
import uuid

class MaterialCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category_name = models.CharField(max_length=50, null=True, blank=True)
    division = models.CharField(max_length=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.category_name


class MaterialSubcategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(MaterialCategory, on_delete=models.CASCADE, related_name='subcategories')
    subcategory_name = models.CharField(max_length=50, null=True, blank=True)
    sub_division = models.CharField(max_length=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Subcategory'
        verbose_name_plural = 'Subcategories'

    def __str__(self):
        return self.subcategory_name


class Material(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    material_name = models.CharField(max_length=150, null=True, blank=True)
    spec_section = models.CharField(max_length=11, null=True, blank=True, db_index=True)
    subcategory = models.ForeignKey(MaterialSubcategory, on_delete=models.CASCADE, related_name='materials')
    price = models.FloatField(default=0.0)
    currency = models.CharField(max_length=5, null=True, blank=True, default='USD')
    unit = models.CharField(max_length=25, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Material'
        verbose_name_plural = 'Materials'

    def __str__(self):
        return self.material_name
