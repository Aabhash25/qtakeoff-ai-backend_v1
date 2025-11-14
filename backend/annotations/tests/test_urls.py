from django.urls import reverse, resolve
from rest_framework.test import APITestCase
from annotations.views import AnnotationViewSet, WallAnnotationViewSet, WindowandDoorAnnotationViewSet

class AnnotationURLsTest(APITestCase):
    def test_annotation_list_url_resolves(self):
        url = reverse('annotation-list')
        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, AnnotationViewSet)

    def test_wall_annotation_list_url_resolves(self):
        url = reverse('wall_annotation-list')
        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, WallAnnotationViewSet)

    def test_window_and_door_annotation_list_url_resolves(self):
        url = reverse('window_and_door_annotation-list')
        resolver = resolve(url)
        self.assertEqual(resolver.func.cls, WindowandDoorAnnotationViewSet)