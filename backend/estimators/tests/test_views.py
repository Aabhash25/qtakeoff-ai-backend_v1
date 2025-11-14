from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch
from users.models import CustomUser, Role
from plans.models import BlueprintImage, Blueprint
from estimators.models import EstimatorRequest, Process
from projects.models import Project
from django.core.files.uploadedfile import SimpleUploadedFile
import uuid

class EstimatorViewsTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = CustomUser.objects.create_user(
            email = 'testuser@gmail.com',
            username = 'testuser',
            first_name = 'Test',
            last_name = 'User',
            password = 'HelloWorld!1',
            role = Role.USER
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

        self.image = SimpleUploadedFile("blueprint_image.jpg", b"image_content", content_type="image/jpeg")

        self.blueprintimage = BlueprintImage.objects.create(
            id=uuid.uuid4(),
            blueprint=self.blueprint,  
            image=self.image,
            title='Test Image'
        )
        self.request = EstimatorRequest.objects.create(
            image=self.blueprintimage,
            requested_by=self.user,
            assigned_estimator=self.estimator,
            status=Process.ASSIGNED
        )

        self.client.force_authenticate(user=self.estimator)

    def test_estimator_image_list_view(self):
        url = reverse('estimator_image_list')
        response = self.client.get(url) 
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    @patch('estimators.views.async_create_annotation.delay')
    @patch('estimators.views.chain')
    def test_estimator_image_detail_get_view(self, mock_chain, mock_async):
        mock_chain.return_value.apply_async.return_value = None
        url = reverse('estimator_image_detail', args=[self.blueprintimage.id]) 
        response = self.client.get(url) 
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        mock_chain.assert_called_once()

    @patch('estimators.views.async_create_annotation.delay')
    def test_estimator_image_detail_put_triggers_update(self, mock_async):
        data = {
            'scale': 2.0,
            'dpi': 600
        }
        url = reverse('estimator_image_detail', args=[self.blueprintimage.id]) 
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_async.assert_called_once_with(self.blueprintimage.id, self.estimator.id)

    @patch('estimators.views.send_email_to_user_after_annotation.delay')
    def test_send_verified_image_to_custom_user(self, mock_send_email):
        url = reverse('send_email_after_annotation', args=[self.blueprintimage.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.blueprintimage.refresh_from_db()
        self.assertTrue(self.blueprintimage.is_verified)
        mock_send_email.assert_called_once_with(self.estimator.email)

