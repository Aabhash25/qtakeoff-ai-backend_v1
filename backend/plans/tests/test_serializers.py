from django.test import TestCase
from rest_framework.exceptions import PermissionDenied
from rest_framework.test import APIRequestFactory
from plans.serializers import (
    BlueprintSerializer,
    BlueprintImageSerializer,
    BlueprintDetailSerializer,
    BlueprintImageDetailSerializer
)
from projects.models import Project
from plans.models import Blueprint, BlueprintImage
from users.models import CustomUser
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from PIL import Image
import io

class BlueprintSerializersTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="test@example.com", 
            username = 'testuser',
            first_name = 'test',
            last_name = 'user',
            password="testpass123"
            )
        self.project = Project.objects.create(title="Test Project", owner=self.user)
        self.blueprint_file = SimpleUploadedFile("blueprint.pdf", b"file_content", content_type="application/pdf")
        self.factory = APIRequestFactory()

    @patch("plans.serializers.process_blueprint_file.delay")
    def test_blueprint_serializer_create(self, mock_process):
        serializer = BlueprintSerializer(data={
            "title": "Test Blueprint",
            "description": "Testing",
            "pdf_file": self.blueprint_file,
            "project": str(self.project.id)
        })
        serializer.is_valid(raise_exception=True)
        blueprint = serializer.save()
        self.assertEqual(blueprint.title, "Test Blueprint")
        self.assertTrue(mock_process.called)

    @patch("plans.serializers.extract_scale_from_image", return_value=1.0)
    def test_blueprint_image_serializer_create_valid_owner(self, mock_extract):
        image_file = self.create_test_image()
        request = self.factory.post("/")
        request.user = self.user

        serializer = BlueprintImageSerializer(data={
            "blueprint": str(Blueprint.objects.create(title="B1", description="desc", project=self.project).id),
            "title": "Test Image",
            "image": image_file
        }, context={'request': request})

        serializer.is_valid(raise_exception=True)
        image = serializer.save()
        self.assertEqual(image.title, "Test Image")
        self.assertEqual(image.dpi, 300)
        self.assertEqual(image.scale, 1.0)

    def test_blueprint_image_serializer_create_invalid_user(self):
        image_file = self.create_test_image()
        other_user = CustomUser.objects.create_user(
            email="other@gmail.com",
            username = 'othertestuser',
            first_name = 'other',
            last_name = 'testuser',
            password="pass")
        other_project = Project.objects.create(title="Other Project", owner=other_user)
        other_blueprint = Blueprint.objects.create(title="B2", description="desc", project=other_project)

        request = self.factory.post("/")
        request.user = self.user

        serializer = BlueprintImageSerializer(data={
            "blueprint": str(other_blueprint.id),
            "title": "Test Image",
            "image": image_file
        }, context={'request': request})

        with self.assertRaises(PermissionDenied):
            serializer.is_valid(raise_exception=True)
            serializer.save()

    def create_test_image(self):
        img = Image.new('RGB', (100, 100), color='white')
        byte_io = io.BytesIO()
        img.save(byte_io, format='JPEG', dpi=(300, 300))
        byte_io.seek(0)
        return SimpleUploadedFile("test.jpg", byte_io.read(), content_type="image/jpeg")
