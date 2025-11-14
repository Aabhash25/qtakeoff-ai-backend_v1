from rest_framework import serializers
from .models import (
    Annotation,
    WallAnnotation,
    WindowAndDoorAnnotation,
    AnnotationMaterial,
    WallAnnotationMaterial,
    WindowAndDoorAnnotationMaterial,
)
from materials.serializers import MaterialSerializer


class AnnotationMaterialSerializer(serializers.ModelSerializer):
    material_detail = MaterialSerializer(source="material", read_only=True)

    class Meta:
        model = AnnotationMaterial
        fields = [
            "id",
            "annotation",
            "material",
            "quantity",
            "notes",
            "material_detail",
        ]


class WallAnnotationMaterialSerializer(serializers.ModelSerializer):
    wall_material_detail = MaterialSerializer(source="material", read_only=True)

    class Meta:
        model = WallAnnotationMaterial
        fields = [
            "id",
            "wall_annotation",
            "material",
            "quantity",
            "notes",
            "wall_material_detail",
        ]


class WindowAndDoorAnnotationMaterialSerializer(serializers.ModelSerializer):
    window_and_door_material_detail = MaterialSerializer(
        source="material", read_only=True
    )

    class Meta:
        model = WindowAndDoorAnnotationMaterial
        fields = [
            "id",
            "window_and_door_annotation",
            "material",
            "quantity",
            "notes",
            "window_and_door_material_detail",
        ]


class AnnotationSerializer(serializers.ModelSerializer):
    materials = AnnotationMaterialSerializer(
        source="annotation_materials", many=True, read_only=True
    )

    class Meta:
        model = Annotation
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {
            "blueprint": {"required": True},
        }


class WallAnnotationSerializer(serializers.ModelSerializer):
    materials = WallAnnotationMaterialSerializer(
        source="wall_annotation_materials", many=True, read_only=True
    )

    class Meta:
        model = WallAnnotation
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {
            "blueprint": {"required": True},
        }


class WindowAndDoorAnnotationSerializer(serializers.ModelSerializer):
    materials = WindowAndDoorAnnotationMaterialSerializer(
        source="window_and_door_annotation_materials", many=True, read_only=True
    )

    class Meta:
        model = WindowAndDoorAnnotation
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {
            "blueprint": {"required": True},
        }
