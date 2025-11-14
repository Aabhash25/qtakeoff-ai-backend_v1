from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status
from users.models import CustomUser
from projects.models import Project
from plans.models import Blueprint, BlueprintImage
from rest_framework.authtoken.models import Token
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import io

class BlueprintViewTestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email = 'testuser@gmail.com',
            username = 'testuser',
            first_name = 'Test',
            last_name = 'User',
            password = 'HelloWorld!1'
        )
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(
            title = 'Test Project',
            owner = self.user
        )
        self.blueprint = Blueprint.objects.create(
            title="Test Blueprint", 
            project=self.project, 
            description="A test blueprint.",
            pdf_file = SimpleUploadedFile(
            "test.pdf", b"file_content", content_type="application/pdf"
            )
        )
        self.image = BlueprintImage.objects.create(
            blueprint=self.blueprint,
            title="Test Image",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )

    def test_blueprint_create_view(self):
        url = reverse('blueprint-create')
        data = {
            'title': 'New Blueprint',
            'description': 'Some Description',
            'project': str(self.project.id),
            'pdf_file': SimpleUploadedFile(
            "test.pdf", b"file_content", content_type="application/pdf"
            )
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Blueprint")

    def test_blueprint_list_view(self):
        url = reverse('blueprint-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_blueprint_detail_view(self):
        url = reverse('blueprint-detail', args=[str(self.blueprint.id)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)
        
    def test_blueprint_delete_view(self):
        url = reverse('blueprint-delete', args=[str(self.blueprint.id)])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Blueprint.objects.filter(id=self.blueprint.id).exists(),
            "Blueprint object should be deleted from the database",
        )

    def test_blueprint_update_view(self):
        url = reverse('blueprint-update', args=[str(self.blueprint.id)])
        data = {'title': 'Update Title'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_blueprint_image_create_view(self):
        url = reverse('blueprint-image-create')
        img = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)

        image = SimpleUploadedFile("blueprint_image.jpg", img_io.read(), content_type="image/jpeg")
        data = {
            'blueprint': str(self.blueprint.id),
            'title': 'Upload Test Image',
            'image' : image,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_blueprint_image_detail_view(self):
        url = reverse('blueprint-image-detail', args=[str(self.image.id)])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)

    def test_blueprint_image_update_view(self):
        url = reverse('blueprint-image-detail', args=[str(self.image.id)])
        data = {'scale': 0.5}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["scale"], 0.5)

    def test_blueprint_image_delete_view(self):
        url = reverse('blueprint-image-detail', args=[str(self.image.id)])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    

    
from unittest.mock import patch
from estimators.models import EstimatorRequest 

class EstimatorRequestViewTestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email = 'testuser@gmail.com',
            username = 'testuser',
            first_name = 'Test',
            last_name = 'User',
            password = 'HelloWorld!1'
        )
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(
            title = 'Test Project',
            owner = self.user
        )
        self.blueprint = Blueprint.objects.create(
            title="Test Blueprint", 
            project=self.project, 
            description="A test blueprint.",
            pdf_file = SimpleUploadedFile(
            "test.pdf", b"file_content", content_type="application/pdf"
            )
        )
        self.image = BlueprintImage.objects.create(
            blueprint=self.blueprint,
            title="Test Image",
            image=SimpleUploadedFile("test.jpg", b"file_content", content_type="image/jpeg")
        )
        self.url = reverse('estimator_request')

    @patch("estimators.tasks.send_estimator_request_email.delay")
    @patch("celery.result.AsyncResult")
    def test_estimator_request_create_success(self, mock_async_result, mock_send_email_task):
        mock_task_result = mock_send_email_task.return_value
        mock_task_result.id = 'mock-task-id'
        mock_async_result.return_value.get.return_value = True

        data = {
            "image_id": str(self.image.id)
        }

        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['success'], "Image sent and request saved.")
        self.assertTrue(EstimatorRequest.objects.filter(image=self.image, requested_by=self.user).exists())

    def test_missing_image_id(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_invalid_image_id(self):
        response = self.client.post(self.url, {"image_id": "00000000-0000-0000-0000-000000000000"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)

    def test_unauthorized_image_access(self):
        other_user = CustomUser.objects.create_user(
            email = 'anothertestuser@gmail.com',
            username = 'anothertestuser',
            first_name = 'Test',
            last_name = 'User',
            password = 'HelloWorld!1'
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.post(self.url, {"image_id": str(self.image.id)})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("error", response.data)
