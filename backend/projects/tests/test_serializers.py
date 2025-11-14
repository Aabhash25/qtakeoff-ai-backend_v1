from django.test import TestCase
from projects.models import Project
from users.models import CustomUser
from projects.serializers import ProjectSerializer, ProjectDetailSerializer
from plans.models import Blueprint, BlueprintImage
import uuid

class ProjectSerializerTestCase(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email = 'testuser@gmail.com',
            username = 'testuser',
            first_name = 'Test',
            last_name = 'User',
            password = 'HelloWorld!1'
        )
        self.project = Project.objects.create(
            title = 'Test Project',
            owner = self.user
        )

    def test_project_serializer(self):
        serializer = ProjectSerializer(instance=self.project)
        data = serializer.data
        self.assertEqual(data['id'], str(self.project.id))
        self.assertEqual(data['title'], self.project.title)
        self.assertEqual(data['owner'], self.user.username)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)
        
    def test_project_detail_serializer(self):
        blueprint = Blueprint.objects.create(project=self.project, title='Test Blueprint')

        serializer = ProjectDetailSerializer(instance=self.project)
        data = serializer.data

        self.assertEqual(data['id'], str(self.project.id))
        self.assertEqual(data['title'], self.project.title)
        self.assertEqual(data['owner'], self.user.username)
        self.assertIn('blueprints', data)
        self.assertEqual(len(data['blueprints']), 1)
        self.assertEqual(data['blueprints'][0]['title'], 'Test Blueprint')
