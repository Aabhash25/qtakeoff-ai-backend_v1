from django.test import TestCase, RequestFactory
from unittest.mock import patch
from users.models import CustomUser, Role
from plans.models import BlueprintImage, Blueprint
from estimators.models import EstimatorRequest
from estimators.admin import AnnotationRequestAdmin
from projects.models import Project
from django.contrib.admin.sites import AdminSite
from django.core.files.uploadedfile import SimpleUploadedFile
import uuid
from django.contrib.admin.sites import site

class MockRequest:
    def __init__(self, user):
        self.user = user


class AnnotationRequestAdminTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = AnnotationRequestAdmin(EstimatorRequest, self.site)
        
        self.estimator = CustomUser.objects.create_user(
            email='estimator@ssnbuilders.com',
            username = 'estimatoruser',
            password='test1234',
            role=Role.ESTIMATOR,
            first_name='estimator',
            last_name='user'
        )

        self.user = CustomUser.objects.create_user(
            email='testuser@example.com',
            username = 'testuser',
            password='test1234',
            role=Role.USER,
            first_name='test',
            last_name='user'
        )
        self.project = Project.objects.create(
            title = 'Test Project',
            owner = self.user    
        )
        self.blueprint = Blueprint.objects.create(
            title='Test Blueprint',
            description='Test description',
            project=self.project
        )

        self.image = SimpleUploadedFile("blueprint_image.jpg", b"image_content", content_type="image/jpeg")

        self.image = BlueprintImage.objects.create(
            id=uuid.uuid4(),
            blueprint=self.blueprint,  
            image=self.image,
            title='Test Image'
        )

    def test_estimator_request_admin_is_registered(self):
        self.assertIn(EstimatorRequest, site._registry)

    def test_list_display(self):
        self.assertEqual(
            self.admin.list_display,
            ('image__title', 'requested_by', 'assigned_estimator', 'status', 'created_at')
        )

    def test_list_filter(self):
        self.assertEqual(self.admin.list_filter, ('status',))

    def test_search_fields(self):
        self.assertEqual(self.admin.search_fields, ('blueprint__id', 'requested_by__email', 'assigned_estimator__email'))

    def test_readonly_fields(self):
        self.assertEqual(self.admin.readonly_fields, ('image', 'requested_by'))


    @patch('estimators.admin.send_image_email_task_to_estimator')
    def test_save_model_triggers_email_on_new_assignment(self, mock_send_email):
        obj = EstimatorRequest(
            image=self.image,
            requested_by=self.user,
            assigned_estimator=self.estimator
        )

        request = MockRequest(self.user)
        form = None
        change = False

        self.admin.save_model(request, obj, form, change)
        full_name = f"{self.estimator.first_name} {self.estimator.last_name}"
        mock_send_email.delay.assert_called_once_with(
            estimator_email=self.estimator.email,
            estimator_name=full_name,
            image_id=self.image.id
        )

    @patch('estimators.admin.send_image_email_task_to_estimator')
    def test_save_model_triggers_email_on_change_assignment(self, mock_send_email):
        obj = EstimatorRequest.objects.create(
            image=self.image,
            requested_by=self.user,
            assigned_estimator=None
        )

        obj.assigned_estimator = self.estimator
        request = MockRequest(self.user)
        form = None
        change = True

        self.admin.save_model(request, obj, form, change)

        mock_send_email.delay.assert_called_once()

    @patch('estimators.admin.send_image_email_task_to_estimator')
    def test_save_model_does_not_trigger_email_if_not_assigned(self, mock_send_email):
        obj = EstimatorRequest(
            image=self.image,
            requested_by=self.user,
            assigned_estimator=None
        )

        request = MockRequest(self.user)
        form = None
        change = False

        self.admin.save_model(request, obj, form, change)

        mock_send_email.delay.assert_not_called()
