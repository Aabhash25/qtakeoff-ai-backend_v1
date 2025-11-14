from django.test import SimpleTestCase
from django.urls import reverse, resolve
from plans.views import (
    BlueprintCreateView,
    BlueprintUpdateView,
    BlueprintListView,
    BlueprintDetailView,
    BlueprintDeleteView,
    BlueprintImageDetailView,
    BlueprintImageCreateView,
    EstimatorRequestCreateView
)
import uuid

class TestBlueprintUrls(SimpleTestCase):

    def test_blueprint_create_url_resolves(self):
        url = reverse('blueprint-create')
        self.assertEqual(resolve(url).func.view_class, BlueprintCreateView)

    def test_blueprint_update_url_resolves(self):
        fake_uuid = uuid.uuid4()
        url = reverse('blueprint-update', args=[fake_uuid])
        self.assertEqual(resolve(url).func.view_class, BlueprintUpdateView)

    def test_blueprint_list_url_resolves(self):
        url = reverse('blueprint-list')
        self.assertEqual(resolve(url).func.view_class, BlueprintListView)

    def test_blueprint_detail_url_resolves(self):
        fake_uuid = uuid.uuid4()
        url = reverse('blueprint-detail', args=[fake_uuid])
        self.assertEqual(resolve(url).func.view_class, BlueprintDetailView)

    def test_blueprint_delete_url_resolves(self):
        fake_uuid = uuid.uuid4()
        url = reverse('blueprint-delete', args=[fake_uuid])
        self.assertEqual(resolve(url).func.view_class, BlueprintDeleteView)

    def test_blueprint_image_create_url_resolves(self):
        url = reverse('blueprint-image-create')
        self.assertEqual(resolve(url).func.view_class, BlueprintImageCreateView)

    def test_blueprint_image_detail_url_resolves(self):
        fake_uuid = uuid.uuid4()
        url = reverse('blueprint-image-detail', args=[fake_uuid])
        self.assertEqual(resolve(url).func.view_class, BlueprintImageDetailView)

    def test_estimator_request_url_resolves(self):
        url = reverse('estimator_request')
        self.assertEqual(resolve(url).func.view_class, EstimatorRequestCreateView)


