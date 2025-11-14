from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import EstimatorRequest
from users.models import CustomUser
from .tasks import send_image_email_task_to_estimator
from django.utils.translation import gettext_lazy as _
import logging
logger = logging.getLogger(__name__)


@admin.register(EstimatorRequest)
class AnnotationRequestAdmin(admin.ModelAdmin):
    list_display = ('image__title', 'requested_by', 'assigned_estimator', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('blueprint__id', 'requested_by__email', 'assigned_estimator__email')

    readonly_fields = (
        'image', 'requested_by',
    )
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "assigned_estimator":
            kwargs["queryset"] = CustomUser.objects.filter(role='estimator')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        is_new_assignment = False
        if change:
            old_obj = EstimatorRequest.objects.get(pk=obj.pk)
            if obj.assigned_estimator and (
                not old_obj.assigned_estimator or old_obj.assigned_estimator != obj.assigned_estimator
            ):
                is_new_assignment = True
        elif obj.assigned_estimator:
            is_new_assignment = True
        super().save_model(request, obj, form, change)
        if is_new_assignment and obj.assigned_estimator and obj.assigned_estimator.email:
            full_name = f"{obj.assigned_estimator.first_name} {obj.assigned_estimator.last_name}"
            send_image_email_task_to_estimator.delay(
                estimator_email=obj.assigned_estimator.email,
                estimator_name=full_name,
                image_id=obj.image.id
            )

    