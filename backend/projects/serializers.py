from .models import Project
from rest_framework import serializers
from plans.serializers import BlueprintSerializer

class ProjectSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    class Meta:
        model = Project
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'owner')

    def get_owner(self, obj):
        return obj.owner.username if obj.owner else None


class ProjectDetailSerializer(serializers.ModelSerializer):
    owner = serializers.SerializerMethodField()
    blueprints = BlueprintSerializer(many=True, read_only=True)
    class Meta:
        model = Project
        fields = ['id', 'title', 'created_at', 'updated_at', 'owner', 'blueprints']
        read_only_fields = ['created_at', 'updated_at']

    def get_owner(self, obj):
        return obj.owner.username if obj.owner else None