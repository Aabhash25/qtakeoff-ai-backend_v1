from rest_framework import serializers
from .models import EstimatorRequest, BlueprintExtraInfo


class EstimatorRequestSerializer(serializers.ModelSerializer):
    requested_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = EstimatorRequest
        fields = [
            "image",
            "requested_by",
            "assigned_estimator",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "created_at", "updated_at"]


class BlueprintExtraInfoSerializer(serializers.ModelSerializer):
    imported_by = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = BlueprintExtraInfo
        fields = [
            "id",
            "blueprint",
            "csv_data",
            "imported_by",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
