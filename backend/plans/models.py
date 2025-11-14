from django.db import models
from projects.models import Project
import uuid

class Category(models.TextChoices):
    ELEVATION = 'elevation', 'Elevation'
    PLAN = 'plan', 'Plan'

class Status(models.TextChoices):
    PENDING = 'pending', 'Pending'
    PROCESSING = 'processing', 'Processing'
    COMPLETE = 'complete', 'Complete'
    FAILED = 'failed', 'Failed'

class Blueprint(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name="Blueprint Title")
    description = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='blueprints')
    pdf_file = models.FileField(upload_to='blueprints/')
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.PLAN)

    def __str__(self):
        return self.title
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Blueprint'
        verbose_name_plural = 'Blueprints'

class BlueprintImage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blueprint = models.ForeignKey(Blueprint, on_delete=models.CASCADE, related_name='images', verbose_name="Blueprint Title")
    title = models.CharField(max_length=150, null=True, blank=True)
    image = models.ImageField(upload_to='blueprints/images/', default="Untitled Image")
    dpi = models.IntegerField(null=True, blank=True, default=None, verbose_name='DPI', help_text='Dots per inch of the image')
    scale = models.FloatField(null=True, blank=True, default=2.1, verbose_name='Scale', help_text='Scale of the image in inches per pixel')
    floor_json_file = models.FileField(upload_to='json/floor/', null=True, blank=True)
    wall_json_file = models.FileField(upload_to='json/wall/', null=True, blank=True)
    window_json_file = models.FileField(upload_to='json/window&door/', null=True, blank=True)
    is_verified = models.BooleanField(null=True, blank=True, default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Image for {self.blueprint.title}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Blueprint Image'
        verbose_name_plural = 'Blueprint Images'