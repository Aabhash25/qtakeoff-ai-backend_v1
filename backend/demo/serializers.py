from rest_framework import serializers
from .models import BookDemo

class BookDemoSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookDemo
        fields = ['id', 'full_name', 'email', 'company', 'preferred_date', 'description']