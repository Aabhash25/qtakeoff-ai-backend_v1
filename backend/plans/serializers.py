from rest_framework import serializers
from .models import Blueprint, Status, BlueprintImage
from .tasks import process_blueprint_file
from rest_framework.exceptions import PermissionDenied
from PIL import Image
from .extract_scale import extract_scale_from_image
from annotations.serializers import (
    AnnotationSerializer,
    WallAnnotationSerializer,
    WindowAndDoorAnnotationSerializer,
    WallAnnotationMaterialSerializer,
    WindowAndDoorAnnotationMaterialSerializer,
)
from annotations.models import WallAnnotationMaterial, WindowAndDoorAnnotationMaterial


class BlueprintSerializer(serializers.ModelSerializer):
    class Meta:
        model = Blueprint
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {"pdf_file": {"required": True}, "project": {"required": True}}

    def create(self, validated_data):
        blueprint = Blueprint.objects.create(**validated_data)
        blueprint.status = Status.PROCESSING
        blueprint.save(update_fields=["status"])
        process_blueprint_file.delay(blueprint.id)
        return blueprint


class BlueprintImageDetailSerializer(serializers.ModelSerializer):
    annotations = AnnotationSerializer(many=True, read_only=True)
    wall_annotations = serializers.SerializerMethodField()
    window_and_door_annotations = serializers.SerializerMethodField()

    class Meta:
        model = BlueprintImage
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_wall_annotations(self, obj):
        wall_annotations_data = []
        for wall_annotation in obj.wall_annotations.all():
            serializer = WallAnnotationSerializer(wall_annotation)
            data = serializer.data
            materials = WallAnnotationMaterial.objects.filter(wall_annotation=wall_annotation)
            material_serializer = WallAnnotationMaterialSerializer(materials, many=True)
            data["materials"] = material_serializer.data
            wall_annotations_data.append(data)
        return wall_annotations_data

    def get_window_and_door_annotations(self, obj):
        window_door_annotations_data = []
        for window_door_annotation in obj.window_and_door_annotations.all():
            serializer = WindowAndDoorAnnotationSerializer(window_door_annotation)
            data = serializer.data
            materials = WindowAndDoorAnnotationMaterial.objects.filter(window_and_door_annotation=window_door_annotation)
            material_serializer = WindowAndDoorAnnotationMaterialSerializer(materials, many=True)
            data["materials"] = material_serializer.data
            window_door_annotations_data.append(data)
        return window_door_annotations_data


class BlueprintDetailSerializer(serializers.ModelSerializer):
    images = BlueprintImageDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Blueprint
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {"pdf_file": {"required": True}, "project": {"required": True}}


class BlueprintImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlueprintImage
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user if request else None
        blueprint = validated_data.get("blueprint")
        if not user or blueprint.project.owner != user:
            raise PermissionDenied(
                "You do not have permission to upload an image to this blueprint."
            )
        image_file = validated_data.get("image")
        image_pil = Image.open(image_file)
        dpi_tuple = image_pil.info.get("dpi")
        raw_dpi = dpi_tuple[0] if dpi_tuple else 300
        dpi = round(raw_dpi)
        scale = extract_scale_from_image(image_pil)
        validated_data["dpi"] = dpi
        validated_data["scale"] = scale
        image = BlueprintImage.objects.create(**validated_data)
        return image
