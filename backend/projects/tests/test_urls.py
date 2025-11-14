from django.test import SimpleTestCase
from django.urls import reverse, resolve
from projects.views import (ProjectCreateView,
                    ProjectListView,
                    ProjectDeleteView,
                    ProjectUpdateView,
                    ProjectDetailView)
import uuid

class ProjectURLsSimpleTestCase(SimpleTestCase):
    def test_project_create_url_resolves(self):
        url = reverse('project-create')
        self.assertEqual(resolve(url).func.view_class, ProjectCreateView)

    def test_project_update_url_resolves(self):
        fake_uuid = uuid.uuid4()
        url = reverse('project-update', args=[fake_uuid])
        self.assertEqual(resolve(url).func.view_class, ProjectUpdateView)

    def test_project_list_url_resolves(self):
        url = reverse('project-list')
        self.assertEqual(resolve(url).func.view_class, ProjectListView)

    def test_project_detail_url_resolves(self):
        fake_uuid = uuid.uuid4()
        url = reverse('project-detail', args=[fake_uuid])
        self.assertEqual(resolve(url).func.view_class, ProjectDetailView)

    def test_project_delete_url_resolves(self):
        fake_uuid = uuid.uuid4()
        url = reverse('project-delete', args=[fake_uuid])
        self.assertEqual(resolve(url).func.view_class, ProjectDeleteView)

