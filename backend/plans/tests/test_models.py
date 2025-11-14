from django.test import TestCase
from projects.models import Project
from plans.models import Blueprint, BlueprintImage, Status, Category
from django.core.files.uploadedfile import SimpleUploadedFile
import uuid
from users.models import CustomUser, Role
from django.utils import timezone

class BLueprintModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email = 'testuser@gmail.com',
            username = 'testuser',
            first_name = 'Test',
            last_name = 'User',
            password = 'HelloWorld!1'
        )
        self.project = Project.objects.create(
            title = "Test Project",
            owner = self.user
        )

    def test_blueprint_create(self):
        
        pdf = SimpleUploadedFile(
            "test.pdf", b"file_content", content_type="application/pdf"
            )
        blueprint = Blueprint.objects.create(
            title = "Test Blueprint",
            description = "Blueprint Description",
            project = self.project,
            pdf_file = pdf
        )
        self.assertEqual(blueprint.title, "Test Blueprint")
        self.assertEqual(blueprint.status, Status.PENDING)
        self.assertEqual(blueprint.category, Category.PLAN)
        self.assertEqual(str(blueprint), "Test Blueprint")
        self.assertEqual(blueprint.project, self.project)

class BlueprintImageModelTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email = 'testuser@gmail.com',
            username = 'testuser',
            first_name = 'Test',
            last_name = 'User',
            password = 'HelloWorld!1'
        )
        self.project = Project.objects.create(
            title = "Test Project",
            owner = self.user
        )
        pdf = SimpleUploadedFile(
            "test.pdf", b"file_content", content_type="application/pdf"
            )
        self.blueprint = Blueprint.objects.create(
            title = 'Blueprint with Images',
            description = 'Blueprint Description',
            project = self.project,
            pdf_file = pdf
        )
    
    def test_blueprint_image_create(self):
        image = SimpleUploadedFile("blueprint_image.jpg", b"image_content", content_type="image/jpeg")
        blueprint_image = BlueprintImage.objects.create(
            blueprint = self.blueprint,
            title = "Main Floor",
            image = image,
            dpi = 200,
            scale = 0.378,
            is_verified=False,
            created_at = timezone.now(),
            updated_at = timezone.now()
        )
        self.assertEqual(blueprint_image.title, "Main Floor")
        self.assertEqual(blueprint_image.dpi, 200)
        self.assertFalse(blueprint_image.is_verified)
        self.assertEqual(str(blueprint_image), f"Image for {self.blueprint.title}")

