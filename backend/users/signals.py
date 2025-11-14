import contextlib
from django.db.models.signals import post_migrate, post_save
from django.contrib.auth.models import Group, Permission
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import CustomUser, Role, CustomUserProfile
from projects.models import Project
from plans.models import Blueprint, BlueprintImage
from estimators.models import EstimatorRequest
from annotations.models import Annotation
from django.conf import settings

@receiver(post_migrate)
def create_user_groups(sender, **kwargs):
    user_group, _ = Group.objects.get_or_create(name='User')
    estimator_group, _ = Group.objects.get_or_create(name='Estimator')
    admin_group, _ = Group.objects.get_or_create(name='Admin')

    project_ct = ContentType.objects.get_for_model(Project)
    blueprint_ct = ContentType.objects.get_for_model(Blueprint)
    blueprint_image_ct = ContentType.objects.get_for_model(BlueprintImage)
    annotation_ct = ContentType.objects.get_for_model(Annotation)
    estimator_request_ct = ContentType.objects.get_for_model(EstimatorRequest)

    project_perms = Permission.objects.filter(content_type=project_ct)
    blueprint_perms = Permission.objects.filter(content_type=blueprint_ct)
    blueprint_image_perms = Permission.objects.filter(content_type=blueprint_image_ct)
    annotation_perms = Permission.objects.filter(content_type=annotation_ct)
    estimator_request_perms = Permission.objects.filter(content_type=estimator_request_ct)
    user_group.permissions.set(
        project_perms.union(blueprint_perms, blueprint_image_perms)
    )
    estimator_group.permissions.set(
        annotation_perms.union(blueprint_image_perms, estimator_request_perms)
    )

    all_permissions = Permission.objects.all()
    admin_group.permissions.set(all_permissions)
    
    for user in CustomUser.objects.filter(is_superuser=True):
        user.groups.add(admin_group)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def sync_user_group(sender, instance, created, **kwargs):

    groups_to_clear = ['User', 'Estimator', 'Admin']
    instance.groups.remove(*Group.objects.filter(name__in=groups_to_clear))
    
    if instance.role == Role.USER:
        group, _ = Group.objects.get_or_create(name='User')
        instance.groups.add(group)
    elif instance.role == Role.ESTIMATOR:
        group, _ = Group.objects.get_or_create(name='Estimator')
        instance.groups.add(group)
    elif instance.role == Role.ADMIN or instance.is_superuser or instance.is_staff:
        group, _ = Group.objects.get_or_create(name='Admin')
        instance.groups.add(group)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_custom_user_profile(sender, instance, created, **kwargs):
    if created:
        CustomUserProfile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_custom_user_profile(sender, instance, created, **kwargs):
    if not created:
        with contextlib.suppress(CustomUserProfile.DoesNotExist):
            instance.user_profile.save()
