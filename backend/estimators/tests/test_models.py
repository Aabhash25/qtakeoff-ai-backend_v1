from django.test import TestCase
from django.utils import timezone
from users.models import CustomUser, Role
from projects.models import Project
from plans.models import BlueprintImage, Blueprint
from estimators.models import EstimatorRequest, Process
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile

class EstimatorRequestModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email = 'testuser@gmail.com',
            username = 'testuser',
            first_name = 'Test',
            last_name = 'User',
            password = 'HelloWorld!1',
            role = Role.USER
        )
        self.estimator = CustomUser.objects.create_user(
            email = 'estimatoruser@ssnbuilders.com',
            username = 'estimatoruser',
            first_name = 'Estimator',
            last_name = 'User',
            password = 'HelloWorld!1',
            role = Role.ESTIMATOR
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

        self.blueprintimage = BlueprintImage.objects.create(
            id=uuid.uuid4(),
            blueprint=self.blueprint,  
            image=self.image,
            title='Test Image'
        )

    def test_create_estimator_request(self):
        request = EstimatorRequest.objects.create(
            image=self.blueprintimage,
            requested_by=self.user,
            assigned_estimator=self.estimator,
            status=Process.ASSIGNED
        )

        self.assertEqual(request.requested_by, self.user)
        self.assertEqual(request.assigned_estimator, self.estimator)
        self.assertEqual(request.image, self.blueprintimage)
        self.assertEqual(request.status, Process.ASSIGNED)
        self.assertIsNotNone(request.created_at)
        self.assertIsNotNone(request.updated_at)
        self.assertIsInstance(request.id, uuid.UUID)

    def test_default_status_pending(self):
        request = EstimatorRequest.objects.create(
            image=self.blueprintimage,
            requested_by=self.user
        )
        self.assertEqual(request.status, Process.PENDING)

    def test_str_method(self):
        request = EstimatorRequest.objects.create(
            image=self.blueprintimage,
            requested_by=self.user,
            assigned_estimator=self.estimator
        )
        self.assertEqual(str(request), f'This is Requested by: {self.user}')

    # def test_ordering_by_created_at_desc(self):
    #     old_request = EstimatorRequest.objects.create(
    #         image=self.blueprintimage,
    #         requested_by=self.user,
    #         created_at=timezone.now() - timezone.timedelta(days=1)
    #     )
    #     new_request = EstimatorRequest.objects.create(
    #         image=self.blueprintimage,
    #         requested_by=self.user,
    #     )
    #     print("Old Request Created At:", old_request.created_at)
    #     print("New Request Created At:", new_request.created_at)
    #     requests = EstimatorRequest.objects.all().order_by('-created_at')
    #     self.assertEqual(requests.first(), new_request)
    #     self.assertEqual(requests.last(), old_request)
