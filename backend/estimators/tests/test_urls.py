from django.test import SimpleTestCase
from django.urls import reverse, resolve
from estimators.views import (
    EstimatorImageListView,
    EstimatorImageDetailView,
    SendVerifiedImageToCustomUser
)
import uuid

class EstimatorUrlsTestCase(SimpleTestCase):

    def test_estimator_image_list_url_resolves(self):
        url = reverse('estimator_image_list')
        self.assertEqual(resolve(url).func.view_class, EstimatorImageListView)

    def test_estimator_image_detail_url_resolves(self):
        test_uuid = uuid.uuid4()
        url = reverse('estimator_image_detail', args=[test_uuid])
        resolved_view = resolve(url)
        self.assertEqual(resolved_view.func.view_class, EstimatorImageDetailView)
        self.assertEqual(str(resolved_view.kwargs['pk']), str(test_uuid))

    def test_send_verified_image_url_resolves(self):
        test_uuid = uuid.uuid4()
        url = reverse('send_email_after_annotation', args=[test_uuid])
        resolved_view = resolve(url)
        self.assertEqual(resolved_view.func.view_class, SendVerifiedImageToCustomUser)
        self.assertEqual(str(resolved_view.kwargs['blueprint_id']), str(test_uuid))

