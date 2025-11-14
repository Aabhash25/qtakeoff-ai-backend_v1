from django.test import TestCase
from django.contrib import admin
from projects.models import Project
from projects.admin import ProjectAdmin

class ProjectAdminTest(TestCase):
    def test_project_admin_is_registered(self):
        self.assertIn(Project, admin.site._registry)
        self.assertIsInstance(admin.site._registry[Project], ProjectAdmin)

    def test_project_admin_configuration(self):
        model_admin = admin.site._registry[Project]

        self.assertEqual(model_admin.list_display, ('title', 'owner', 'created_at', 'updated_at'))
        self.assertEqual(model_admin.search_fields, ('title', 'description'))
        self.assertEqual(model_admin.list_filter, ('created_at', 'updated_at'))
        self.assertEqual(model_admin.ordering, ('-created_at',))
        self.assertEqual(model_admin.date_hierarchy, 'created_at')
        self.assertEqual(model_admin.list_per_page, 20)
        self.assertEqual(model_admin.readonly_fields, ('title', 'owner'))
