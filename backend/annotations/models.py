from django.db import models
from plans.models import BlueprintImage
import uuid
from materials.models import Material


class Annotation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blueprint = models.ForeignKey(
        BlueprintImage, on_delete=models.CASCADE, related_name="annotations"
    )
    label = models.CharField(max_length=255, verbose_name="Annotation Label")
    coordinates = models.JSONField(
        verbose_name="Coordinates", help_text="Polygon or point data for the annotation"
    )
    area = models.FloatField(
        verbose_name="Area Size",
        help_text="Size of the area in square units",
        blank=True,
        null=True,
        default=None,
    )
    annotation_type = models.CharField(
        max_length=50,
        verbose_name="Annotation Type",
        help_text="Shape Type (e.g., polygon, point or rectangle)",
    )
    width = models.FloatField(
        verbose_name="Width",
        help_text="Width of the annotation in sqft",
        blank=True,
        null=True,
        default=None,
    )
    height = models.FloatField(
        verbose_name="Height",
        help_text="Height of the annotation in sqft",
        blank=True,
        null=True,
        default=None,
    )
    materials = models.ManyToManyField(
        Material, through="AnnotationMaterial", related_name="annotations"
    )
    confidence_score = models.FloatField(
        verbose_name="Prediction Percentage",
        help_text="Confidence score of the annotation",
        blank=True,
        null=True,
        default=None,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Annotation on {self.blueprint.blueprint}"

    class Meta:
        verbose_name = "Annotation"
        verbose_name_plural = "Annotations"
        ordering = ["-created_at"]


class WallAnnotation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blueprint = models.ForeignKey(
        BlueprintImage, on_delete=models.CASCADE, related_name="wall_annotations"
    )
    label = models.CharField(max_length=255, verbose_name="Wall Annotation Label")
    coordinates = models.JSONField(
        verbose_name="Coordinates", help_text="Rectangle point for the annotation"
    )
    annotation_type = models.CharField(
        max_length=50,
        verbose_name="Annotation Type",
        help_text="Shape Type (e.g., polygon, point or rectangle)",
    )
    area = models.FloatField(
        verbose_name="Area",
        help_text="Size of the area in square units",
        blank=True,
        null=True,
        default=None,
    )
    materials = models.ManyToManyField(
        Material, through="WallAnnotationMaterial", related_name="wall_annotations"
    )
    length_ft = models.FloatField(
        verbose_name="Length in Feet",
        help_text="Length of the wall in feet",
        blank=True,
        null=True,
        default=None,
    )
    thickness_ft = models.FloatField(
        verbose_name="Thickness in Feet",
        help_text="Thickness of the wall in feet",
        blank=True,
        null=True,
        default=None,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wall Annotation on {self.blueprint.blueprint}"

    class Meta:
        verbose_name = "Wall Annotation"
        verbose_name_plural = "Wall Annotations"
        ordering = ["-created_at"]


class WindowAndDoorAnnotation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blueprint = models.ForeignKey(
        BlueprintImage,
        on_delete=models.CASCADE,
        related_name="window_and_door_annotations",
    )
    label = models.CharField(
        max_length=255, verbose_name="Window and Door Annotation Label"
    )
    coordinates = models.JSONField(
        verbose_name="Coordinates", help_text="Polygon or point data for the annotation"
    )
    annotation_type = models.CharField(
        max_length=50,
        verbose_name="Annotation Type",
        help_text="Shape Type (e.g., polygon, point or rectangle)",
    )
    length_ft = models.FloatField(
        verbose_name="Length in Feet",
        help_text="Length of the wall in feet",
        blank=True,
        null=True,
        default=None,
    )
    breadth_ft = models.FloatField(
        verbose_name="Breadth in Feet",
        help_text="Breadth of the wall in feet",
        blank=True,
        null=True,
        default=None,
    )
    materials = models.ManyToManyField(
        Material,
        through="WindowAndDoorAnnotationMaterial",
        related_name="window_and_door_annotations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Window and Door Annotation on {self.blueprint.blueprint}"

    class Meta:
        verbose_name = "Window & Door Annotation"
        verbose_name_plural = "Windows & Doors Annotations"
        ordering = ["-created_at"]


# ---------- Add Notes Field to All Material Relations ----------


class AnnotationMaterial(models.Model):
    annotation = models.ForeignKey(
        Annotation, on_delete=models.CASCADE, related_name="annotation_materials"
    )
    material = models.ForeignKey(
        Material, on_delete=models.CASCADE, related_name="room_materials"
    )
    quantity = models.FloatField(default=1.0)
    notes = models.TextField(blank=True, null=True)  # ✅ Added notes field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.annotation} has {self.material} ({self.notes or 'No notes'})"

    class Meta:
        unique_together = ("annotation", "material")


class WallAnnotationMaterial(models.Model):
    wall_annotation = models.ForeignKey(
        WallAnnotation,
        on_delete=models.CASCADE,
        related_name="wall_annotation_materials",
    )
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.FloatField(default=1.0)
    notes = models.TextField(blank=True, null=True)  # ✅ Added notes field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.wall_annotation} has {self.material} ({self.notes or 'No notes'})"
        )

    class Meta:
        unique_together = ("wall_annotation", "material")


class WindowAndDoorAnnotationMaterial(models.Model):
    window_and_door_annotation = models.ForeignKey(
        WindowAndDoorAnnotation,
        on_delete=models.CASCADE,
        related_name="window_and_door_annotation_materials",
    )
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    quantity = models.FloatField(default=1.0)
    notes = models.TextField(blank=True, null=True)  # ✅ Added notes field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.window_and_door_annotation} has {self.material} ({self.notes or 'No notes'})"

    class Meta:
        unique_together = ("window_and_door_annotation", "material")
