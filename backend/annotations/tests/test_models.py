from django.test import TestCase
from annotations.models import Annotation, WallAnnotation, WindowAndDoorAnnotation
from plans.models import BlueprintImage, Blueprint
from users.models import CustomUser, Role
from projects.models import Project
from uuid import UUID
import uuid
from django.core.files.uploadedfile import SimpleUploadedFile


class AnnotationModelTest(TestCase):
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

    def test_create_annotation(self):
        annotation = Annotation.objects.create(
            blueprint=self.blueprintimage,
            label='Test Annotation',
            coordinates=[(0, 0), (1, 1)],
            area_size=10.0,
            annotation_type='polygon',
            width=5.0,
            height=5.0,
            confidence_score=0.95
            )
        self.assertIsInstance(annotation.id, UUID)
        self.assertEqual(annotation.label, 'Test Annotation')
        self.assertEqual(annotation.area_size, 10.0)
        self.assertEqual(annotation.annotation_type, 'polygon')
        self.assertEqual(annotation.width, 5.0)
        self.assertEqual(annotation.height, 5.0)
        self.assertEqual(annotation.confidence_score, 0.95)
        self.assertEqual(str(annotation), f"Annotation on {self.blueprintimage.blueprint}")

    def test_create_wall_annotation(self):
        wall_annotation = WallAnnotation.objects.create(
            blueprint=self.blueprintimage,
            label='Test Wall Annotation',
            coordinates=[(0, 0), (1, 1)],
            annotation_type='rectangle'
        )
        self.assertIsInstance(wall_annotation.id, UUID)
        self.assertEqual(wall_annotation.label, 'Test Wall Annotation')
        self.assertEqual(wall_annotation.annotation_type, 'rectangle')
        self.assertEqual(str(wall_annotation), f"Wall Annotation on {self.blueprintimage.blueprint}")

    def test_create_window_and_door_annotation(self):
        window_and_door_annotation = WindowAndDoorAnnotation.objects.create(
            blueprint=self.blueprintimage,
            label='Test Window and Door Annotation',
            coordinates=[(0, 0), (1, 1)],
            annotation_type='polygon'
        )
        self.assertIsInstance(window_and_door_annotation.id, UUID)
        self.assertEqual(window_and_door_annotation.label, 'Test Window and Door Annotation')
        self.assertEqual(window_and_door_annotation.annotation_type, 'polygon')
        self.assertEqual(str(window_and_door_annotation), f"Window and Door Annotation on {self.blueprintimage.blueprint}")

        