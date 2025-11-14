from rest_framework.permissions import BasePermission
from users.models import Role
from rest_framework import permissions

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return user.is_authenticated and (user.is_superuser or user.is_staff)

class IsCustomUser(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        # Check role or group membership
        return user.is_authenticated and (
            user.role == Role.USER or
            user.groups.filter(name='User').exists()
        )

class IsEstimator(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        # Check role or group membership
        return user.is_authenticated and (
            user.role == Role.ESTIMATOR or
            user.groups.filter(name='Estimator').exists()
        )

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        try:
            return obj.blueprint.blueprint.project.owner == user
        except AttributeError:
            pass
        
        if hasattr(obj, 'owner'):
            return obj.owner == user
        
        if hasattr(obj, 'project') and hasattr(obj.project, 'owner'):
            return obj.project.owner == user
        
        if hasattr(obj, 'blueprint') and hasattr(obj.blueprint, 'project') and hasattr(obj.blueprint.project, 'owner'):
            return obj.blueprint.project.owner == user
        
        return False
