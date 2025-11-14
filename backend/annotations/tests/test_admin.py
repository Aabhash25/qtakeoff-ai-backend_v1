from django.test import TestCase, SimpleTestCase
from django.contrib import admin
from annotations.models import Annotation, WallAnnotation, WindowAndDoorAnnotation
from annotations.admin import AnnotationAdmin, WallAnnotationAdmin, WindowAndDoorAnnotationAdmin

class AdminRegistrationTest(SimpleTestCase):
    def test_annotation_admin_registered(self):
        self.assertIn(Annotation, admin.site._registry)
        self.assertIsInstance(
            admin.site._registry[Annotation], AnnotationAdmin,
            msg="Annotation is registered with the wrong ModelAdmin."
        )

    def test_wall_annotation_admin_registered(self):
        self.assertIn(WallAnnotation, admin.site._registry)
        self.assertIsInstance(
            admin.site._registry[WallAnnotation], WallAnnotationAdmin,
            msg="Wall Annotation is registered with the wrong ModelAdmin."
        )

    def test_window_and_door_annotation_admin_registered(self):
        self.assertIn(WindowAndDoorAnnotation, admin.site._registry)
        self.assertIsInstance(
            admin.site._registry[WindowAndDoorAnnotation], WindowAndDoorAnnotationAdmin,
            msg="Window and Door Annotation is registered with the wrong ModelAdmin."
        )

class AdminConfigTest(SimpleTestCase):
    def test_annotation_admin_config(self):
        ma = AnnotationAdmin(Annotation, admin.site)

        self.assertEqual(
            ma.list_display,
            ('blueprint__title', 'label', 'annotation_type', 'created_at', 'updated_at'),
        )
        self.assertEqual(ma.search_fields, ('label', 'annotation_type'))
        self.assertEqual(ma.list_filter, ('annotation_type', 'created_at'))
        self.assertEqual(ma.ordering, ('-created_at',))
        self.assertEqual(ma.date_hierarchy, 'created_at')
        self.assertEqual(ma.list_per_page, 20)

    def test_wall_annotation_admin_config(self):
        ma = WallAnnotationAdmin(WallAnnotation, admin.site)

        self.assertEqual(
            ma.list_display,
            ('blueprint__title', 'label', 'annotation_type', 'created_at', 'updated_at'),
        )
        self.assertEqual(ma.search_fields, ('label', 'annotation_type'))
        self.assertEqual(ma.list_filter, ('annotation_type', 'created_at'))
        self.assertEqual(ma.ordering, ('-created_at',))
        self.assertEqual(ma.date_hierarchy, 'created_at')
        self.assertEqual(ma.list_per_page, 20)

    def test_window_door_annotation_admin_config(self):
        ma = WindowAndDoorAnnotationAdmin(WindowAndDoorAnnotation, admin.site)

        self.assertEqual(
            ma.list_display,
            ('blueprint__title', 'label', 'annotation_type', 'created_at', 'updated_at'),
        )
        self.assertEqual(ma.search_fields, ('label', 'annotation_type'))
        self.assertEqual(ma.list_filter, ('annotation_type', 'created_at'))
        self.assertEqual(ma.ordering, ('-created_at',))
        self.assertEqual(ma.date_hierarchy, 'created_at')
        self.assertEqual(ma.list_per_page, 20)
