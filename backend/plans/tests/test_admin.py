from django.test import TestCase
from django.contrib.admin.sites import site
from plans.models import Blueprint, BlueprintImage
from plans.admin import BlueprintAdmin, BlueprintImageAdmin


class BlueprintAdminTest(TestCase):
    def setUp(self):
        self.model_admin = BlueprintAdmin(Blueprint, site)

    def test_blueprint_admin_is_registered(self):
        self.assertIn(Blueprint, site._registry)

    def test_list_display(self):
        self.assertEqual(
            self.model_admin.list_display,
            ('title', 'project', 'project__owner', 'category', 'status', 'created_at', 'updated_at')
        )

    def test_search_fields(self):
        self.assertEqual(self.model_admin.search_fields, ('title', 'project__title'))

    def test_list_filter(self):
        self.assertEqual(self.model_admin.list_filter, ('category',))

    def test_ordering(self):
        self.assertEqual(self.model_admin.ordering, ('-created_at',))

    def test_date_hierarchy(self):
        self.assertEqual(self.model_admin.date_hierarchy, 'created_at')

    def test_prepopulated_fields(self):
        self.assertEqual(self.model_admin.prepopulated_fields, {'title': ('description',)})


class BlueprintImageAdminTest(TestCase):
    def setUp(self):
        self.model_admin = BlueprintImageAdmin(BlueprintImage, site)

    def test_blueprint_image_admin_is_registered(self):
        self.assertIn(BlueprintImage, site._registry)

    def test_list_display(self):
        self.assertEqual(
            self.model_admin.list_display,
            ('title', 'blueprint', 'dpi', 'scale', 'is_verified', 'created_at')
        )

    def test_search_fields(self):
        self.assertEqual(self.model_admin.search_fields, ('blueprint__title',))

    def test_ordering(self):
        self.assertEqual(self.model_admin.ordering, ('-created_at',))

    def test_date_hierarchy(self):
        self.assertEqual(self.model_admin.date_hierarchy, 'created_at')







