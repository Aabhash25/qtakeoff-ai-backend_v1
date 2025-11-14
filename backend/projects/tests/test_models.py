from django.test import TestCase
from django.utils import timezone
from users.models import CustomUser
from projects.models import Project
import uuid

class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email = 'testuser@gmail.com',
            username = 'testuser',
            first_name = 'Test',
            last_name = 'User',
            password = 'HelloWorld!1'
        )
    
    def test_create_project(self):
        project = Project.objects.create(
            title = 'Test Project',
            owner = self.user
        )
        self.assertEqual(project.title, 'Test Project')
        self.assertEqual(project.owner, self.user)
        self.assertIsInstance(project.id, uuid.UUID)
        self.assertLessEqual(project.created_at, timezone.now())
        self.assertLessEqual(project.updated_at, timezone.now())
        self.assertEqual(str(project), 'Test Project')

    def test_project_ordering(self):
        Project.objects.create(title='Test Project 1', owner=self.user)
        Project.objects.create(title='Test Project 2', owner=self.user)
        projects = Project.objects.all()
        created_dates = [project.created_at for project in projects]
        self.assertEqual(created_dates, sorted(created_dates, reverse=True))

    def test_unique_together_constraint(self):
        Project.objects.create(title='Test Unique Project', owner=self.user)
        with self.assertRaises(Exception):
            Project.objects.create(title='Test Unique Project', owner=self.user)