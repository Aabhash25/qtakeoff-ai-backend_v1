from rest_framework import viewsets, permissions, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from .models import (Annotation, 
                     WallAnnotation, 
                     WindowAndDoorAnnotation, 
                     AnnotationMaterial, 
                     WallAnnotationMaterial,
                     WindowAndDoorAnnotationMaterial)
from .serializers import (AnnotationSerializer, 
                          WallAnnotationSerializer, 
                          WindowAndDoorAnnotationSerializer, 
                          AnnotationMaterialSerializer, 
                          WallAnnotationMaterialSerializer,
                          WindowAndDoorAnnotationMaterialSerializer)
from config.permissions import IsEstimator
from plans.utils import compute_sqft, polygon_dimension
from rest_framework.response import Response
from users.models import Role
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from materials.models import Material
from estimators.models import EstimatorRequest
import numpy as np
from estimators.utils import compute_wall_dimensions

class AnnotationViewSet(viewsets.ModelViewSet):
    serializer_class = AnnotationSerializer
    permission_classes = [permissions.IsAuthenticated, IsEstimator]

    def get_queryset(self):
        user = self.request.user
        if user.role == Role.ESTIMATOR:
            return Annotation.objects.all()
        return Annotation.objects.filter(
            blueprint__blueprint__project__owner=user
        )
    
    def perform_create(self, serializer):
        blueprint = serializer.validated_data['blueprint']
        points = serializer.validated_data['coordinates']
        if not points:
            raise PermissionDenied("Missing coordinates to compute dimensions.")
        area = compute_sqft(points, blueprint.dpi, blueprint.scale)
        width, height  = polygon_dimension(points, blueprint.dpi, blueprint.scale)
        if blueprint.blueprint.project.owner == self.request.user or self.request.user.role == Role.ESTIMATOR:
            serializer.save(area=area, height=height, width=width)
        else:
            raise PermissionDenied("You cannot Owner of this Image to add annotation!")

    def perform_update(self, serializer):
        blueprint = serializer.instance.blueprint
        coordinates = serializer.validated_data.get('coordinates', serializer.instance.coordinates)
        if blueprint.blueprint.project.owner == self.request.user or self.request.user.role == Role.ESTIMATOR:
            area = compute_sqft(coordinates, blueprint.dpi, blueprint.scale)
            width, height = polygon_dimension(coordinates, blueprint.dpi, blueprint.scale)
            print(area, width, height)
            serializer.save(area=area, width=width, height=height)
        else:
            raise PermissionDenied("You cannot edit annotations on this image.")

    def perform_destroy(self, instance):
        blueprint = instance.blueprint
        if blueprint.blueprint.project.owner == self.request.user or self.request.user.role == Role.ESTIMATOR:
            instance.delete()
        else:
            raise PermissionDenied("You cannot delete annotations on this image.")
        return Response({"message": "Blueprint successfully deleted!"}, status=status.HTTP_204_NO_CONTENT)
    
class WallAnnotationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsEstimator]
    serializer_class = WallAnnotationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == Role.ESTIMATOR:
            return WallAnnotation.objects.all()
        return WallAnnotation.objects.filter(
            blueprint__blueprint__project__owner=user
        )
    
    def perform_create(self, serializer):
        blueprint = serializer.validated_data['blueprint']
        points = serializer.validated_data['coordinates']
        if not points:
            raise PermissionDenied("Missing coordinates to compute dimensions.")
        area = compute_sqft(points, blueprint.dpi, blueprint.scale)
        length_ft, thickness_ft = compute_wall_dimensions(points, blueprint.dpi, blueprint.scale)
        if blueprint.blueprint.project.owner == self.request.user or self.request.user.role == Role.ESTIMATOR:
            serializer.save(area=area, length_ft=length_ft, thickness_ft=thickness_ft)
        else:
            raise PermissionDenied("You do not have permission to add wall annotations to this image.")

    def perform_update(self, serializer):
        blueprint = serializer.instance.blueprint
        if blueprint.blueprint.project.owner == self.request.user or self.request.user.role == Role.ESTIMATOR:
            instance = serializer.save()
            dpi = blueprint.dpi
            scale = blueprint.scale
            pts = np.asarray(instance.coordinates)

            length_ft, thickness_ft = compute_wall_dimensions(pts, dpi, scale)
            instance.length_ft = length_ft
            instance.thickness_ft = thickness_ft
            area_sqft = compute_sqft(pts, dpi, scale)
            instance.area = area_sqft
            instance.save(update_fields=["length_ft", "thickness_ft", "area"])

        else:
            raise PermissionDenied("You do not have permission to update this wall annotation.")

    def perform_destroy(self, instance):
        blueprint = instance.blueprint
        if blueprint.blueprint.project.owner == self.request.user or self.request.user.role == Role.ESTIMATOR:
            instance.delete()
        else:
            raise PermissionDenied("You do not have permission to delete this wall annotation.")
        
class WindowandDoorAnnotationViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, IsEstimator]
    serializer_class = WindowAndDoorAnnotationSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == Role.ESTIMATOR:
            return WindowAndDoorAnnotation.objects.all()
        return WindowAndDoorAnnotation.objects.filter(
            blueprint__blueprint__project__owner=user
        )
    
    def perform_create(self, serializer):
        blueprint = serializer.validated_data['blueprint']
        points = serializer.validated_data['coordinates']
        if not points:
            raise PermissionDenied("Missing coordinates to compute dimensions.")
        length_ft, breadth_ft = polygon_dimension(points, blueprint.dpi, blueprint.scale)
        if blueprint.blueprint.project.owner == self.request.user or self.request.user.role == Role.ESTIMATOR:
            serializer.save(length_ft=length_ft, breadth_ft=breadth_ft)
        else:
            raise PermissionDenied("You are not allowed to add window & door annotations to this image.")
    
    def perform_update(self, serializer):
        blueprint = serializer.instance.blueprint
        user = self.request.user

        if blueprint.blueprint.project.owner == user or user.role == Role.ESTIMATOR:
            try:
                instance = serializer.save()
                dpi = blueprint.dpi
                scale = blueprint.scale

                pts = np.asarray(instance.coordinates)
                length_ft, breadth_ft = polygon_dimension(pts, dpi, scale)

                instance.length_ft = length_ft
                instance.breadth_ft = breadth_ft
                instance.save(update_fields=["length_ft", "breadth_ft"])

            except Exception as e:
                print(f"[Update Error]: {e}")
                raise ValidationError({"detail": f"Failed to compute dimensions: {str(e)}"})
        else:
            raise PermissionDenied("You are not allowed to update window & door annotations on this image.")

    def perform_destroy(self, instance):
        blueprint = instance.blueprint
        if blueprint.blueprint.project.owner == self.request.user or self.request.user.role == Role.ESTIMATOR:
            instance.delete()
        else:
            raise PermissionDenied("You are not allowed to delete window & door annotations on this image.")

class BaseAnnotationMaterialView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    annotation_model = None
    material_model = None
    annotation_material_model = None
    annotation_field = ''  # e.g. 'annotation', 'wall_annotation', etc.
    annotation_lookup_kwarg = ''  # e.g. 'annotation_id', 'wall_annotation_id'
    serializer_class = None

    def _get_annotation(self, kwargs):
        return get_object_or_404(self.annotation_model, pk=kwargs.get(self.annotation_lookup_kwarg))

    def _is_estimator_assigned(self, user, annotation):
        return EstimatorRequest.objects.filter(
            assigned_estimator=user,
            image=annotation.blueprint
        ).exists()

    def get(self, request, **kwargs):
        annotation = self._get_annotation(kwargs)
        if not self._is_estimator_assigned(request.user, annotation):
            return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        materials_qs = self.annotation_material_model.objects.filter(**{self.annotation_field: annotation})

        # Optional filters by category/subcategory id passed as query params
        category_id = request.query_params.get('category')
        subcategory_id = request.query_params.get('subcategory')

        if category_id:
            materials_qs = materials_qs.filter(material__subcategory__category_id=category_id)
        if subcategory_id:
            materials_qs = materials_qs.filter(material__subcategory_id=subcategory_id)

        serializer = self.serializer_class(materials_qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, **kwargs):
        annotation = self._get_annotation(kwargs)
        if not self._is_estimator_assigned(request.user, annotation):
            return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        input_data = request.data if isinstance(request.data, list) else [request.data]
        created = []
        existing = []

        for item in input_data:
            material_id = item.get('material')
            if not material_id:
                return Response({"error": "Material ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            if self.annotation_material_model.objects.filter(
                **{self.annotation_field: annotation, 'material_id': material_id}
            ).exists():
                existing.append(material_id)
                continue

            item[self.annotation_field] = annotation.id
            serializer = self.serializer_class(data=item)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            saved_instance = serializer.save()
            if hasattr(annotation, 'area') and annotation.area is not None:
                saved_instance.quantity = annotation.area
                saved_instance.save()

            created.append(self.serializer_class(saved_instance).data)

        result = {"added": created}
        if existing:
            result["already_exists"] = [f"Material ID {m} is already assigned." for m in existing]

        return Response(result, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def patch(self, request, material_id, **kwargs):
        annotation = self._get_annotation(kwargs)
        if not self._is_estimator_assigned(request.user, annotation):
            return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        ann_material = self.annotation_material_model.objects.filter(
            **{self.annotation_field: annotation, 'material_id': material_id}
        ).first()

        if not ann_material:
            return Response({"error": "Material not found for this annotation."}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(ann_material, data=request.data, partial=True)
        if serializer.is_valid():
            saved_instance = serializer.save()
  
            sync_with_area = request.query_params.get("sync_with_area", "").lower() == "true"
            if sync_with_area and hasattr(annotation, 'area') and annotation.area is not None:
                saved_instance.quantity = annotation.area
                saved_instance.save()

            return Response(self.serializer_class(saved_instance).data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




    def delete(self, request, material_id, **kwargs):
        annotation = self._get_annotation(kwargs)
        if not self._is_estimator_assigned(request.user, annotation):
            return Response({"error": "Access denied."}, status=status.HTTP_403_FORBIDDEN)

        material = get_object_or_404(self.material_model, pk=material_id)
        mapping = self.annotation_material_model.objects.filter(
            **{self.annotation_field: annotation, 'material': material}
        ).first()

        if not mapping:
            return Response({"error": "Material not linked to this annotation."}, status=status.HTTP_404_NOT_FOUND)

        mapping.delete()
        return Response({"message": "Material removed from annotation."}, status=status.HTTP_204_NO_CONTENT)


class AnnotationMaterialView(BaseAnnotationMaterialView):
    annotation_model = Annotation
    material_model = Material
    annotation_material_model = AnnotationMaterial
    annotation_field = 'annotation'
    annotation_lookup_kwarg = 'annotation_id'
    serializer_class = AnnotationMaterialSerializer


class WallAnnotationMaterialView(BaseAnnotationMaterialView):
    annotation_model = WallAnnotation
    material_model = Material
    annotation_material_model = WallAnnotationMaterial
    annotation_field = 'wall_annotation'
    annotation_lookup_kwarg = 'wall_annotation_id'
    serializer_class = WallAnnotationMaterialSerializer


class WindowAndDoorAnnotationMaterialView(BaseAnnotationMaterialView):
    annotation_model = WindowAndDoorAnnotation
    material_model = Material
    annotation_material_model = WindowAndDoorAnnotationMaterial
    annotation_field = 'window_and_door_annotation'
    annotation_lookup_kwarg = 'window_and_door_annotation_id'
    serializer_class = WindowAndDoorAnnotationMaterialSerializer

