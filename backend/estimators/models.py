from django.db import models
from plans.models import BlueprintImage
from users.models import CustomUser
import uuid


class Process(models.TextChoices):
    PENDING = "pending", "Pending"
    ASSIGNED = "assigned", "Assigned"
    COMPLETE = "complete", "Complete"


class EstimatorRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    image = models.ForeignKey(
        BlueprintImage, on_delete=models.CASCADE, related_name="estimator_request"
    )
    requested_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="request_by"
    )
    assigned_estimator = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_request",
    )
    status = models.CharField(
        max_length=10, choices=Process.choices, default=Process.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"This is Requested by: {self.requested_by}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Estimator Request"
        verbose_name_plural = "Estimator Requests"


class BlueprintExtraInfo(models.Model):
    """Model to store extra information imported via CSV for blueprints"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blueprint = models.OneToOneField(
        BlueprintImage, on_delete=models.CASCADE, related_name="extra_info"
    )
    csv_data = models.JSONField(
        verbose_name="CSV Data", help_text="Imported CSV data as JSON"
    )
    imported_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="imported_csv_files"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Extra info for {self.blueprint.title}"

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Blueprint Extra Info"
        verbose_name_plural = "Blueprint Extra Info"
