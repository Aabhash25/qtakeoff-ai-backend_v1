from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from users.models import CustomUser
from projects.models import Project
from unittest.mock import patch
import uuid

class ProjectViewsTestCase(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email = 'testuser@gmail.com',
            username = 'testuser',
            first_name = 'Test',
            last_name = 'User',
            password = 'HelloWorld!1'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(
            title = 'Test Project',
            owner = self.user
        )
        self.project_url = reverse('project-detail', kwargs={'pk': self.project.pk})
        self.list_url = reverse('project-list')
        self.create_url = reverse('project-create')
        self.update_url = reverse('project-update', kwargs={'pk': self.project.pk})
        self.delete_url = reverse('project-delete', kwargs={'pk': self.project.pk})

    def test_create_project_success(self):
        response = self.client.post(self.create_url, {'title': 'Create New Project'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 2)

    def test_list_projects_with_duplicate_title(self):
        response = self.client.post(self.create_url, {'title': 'Test Project'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("detail", response.data)

    @patch('projects.views.cache')
    def test_list_projects_with_cache(self, mock_cache):
        mock_cache.get.return_value = None
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("title", response.data[0])

    @patch('projects.views.cache')
    def test_project_detail_view(self, mock_cache):
        mock_cache.get.return_value = None
        response = self.client.get(self.project_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Test Project")
    
    def test_update_project_view(self):
        response = self.client.put(self.update_url, {'title': 'Update Project Title'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.project.refresh_from_db()
        self.assertEqual(self.project.title, 'Update Project Title')

    def test_delete_project_view(self):
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(pk=self.project.pk).exists())

    def test_project_detail_not_found(self):
        invalid_uuid = uuid.uuid4()
        url = reverse('project-detail', kwargs={'pk': invalid_uuid})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)