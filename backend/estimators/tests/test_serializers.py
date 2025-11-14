from django.test import TestCase
from rest_framework.test import APIRequestFactory
from estimators.serializers import (
   EstimatorRequestSerializer
)
from projects.models import Project
from estimators.models import EstimatorRequest
from users.models import CustomUser, Role
from plans.models import Blueprint, BlueprintImage
from unittest.mock import patch
from PIL import Image
import io
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile

class EstimatorRequestSerializersTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email="testuser@gmail.com",
            username = 'testuser',
            first_name = 'test',
            last_name = 'user',
            password="testpass123"
        )
        self.estimator = CustomUser.objects.create_user(
            email = 'estimatoruser@ssnbuilders.com',
            username = 'estimatoruser',
            first_name = 'Estimator',
            last_name = 'User',
            password = 'HelloWorld!1',
            role = Role.ESTIMATOR
        )
        self.project = Project.objects.create(
            title = 'Test Project',
            owner = self.user    
        )
        self.blueprint = Blueprint.objects.create(
            title='Test Blueprint',
            description='Test description',
            project=self.project
        )

        self.image = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")

        self.blueprintimage = BlueprintImage.objects.create(
            id=uuid.uuid4(),
            blueprint=self.blueprint,  
            image=self.image,
            title='Test Image'
        )
        self.factory = APIRequestFactory()

    def test_serializer_creates_estimator_request(self):
        data = {
            "image": str(self.blueprintimage.id),
            "assigned_estimator": self.estimator.id,
        }
        request = self.factory.post("/fake-url/", data, format="multipart")
        request.user = self.user

        serializer = EstimatorRequestSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        instance = serializer.save()
        self.assertEqual(instance.requested_by, self.user)
        self.assertEqual(instance.assigned_estimator, self.estimator)
        self.assertIsNotNone(instance.created_at)
        self.assertIsNotNone(instance.updated_at)

    def test_read_only_fields_are_ignored(self):
        data = {
            "image": str(self.blueprintimage.id),
            "assigned_estimator": self.estimator.id,
            "status": "verified", 
            "created_at": "2023-01-01T00:00:00Z",  
            "updated_at": "2023-01-01T00:00:00Z", 
        }
        request = self.factory.post("/fake-url/", data, format="multipart")
        request.user = self.user

        serializer = EstimatorRequestSerializer(data=data, context={"request": request})
        self.assertTrue(serializer.is_valid(), serializer.errors)

        instance = serializer.save()
        self.assertNotEqual(instance.status, data["status"])
        self.assertEqual(instance.requested_by, self.user)

    def test_missing_image_fails_validation(self):
        data = {
            "assigned_estimator": self.estimator.id,
        }
        request = self.factory.post("/fake-url/", data, format="multipart")
        request.user = self.user

        serializer = EstimatorRequestSerializer(data=data, context={"request": request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("image", serializer.errors)
