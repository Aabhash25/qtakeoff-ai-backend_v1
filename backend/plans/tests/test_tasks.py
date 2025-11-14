from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from plans.models import Blueprint, BlueprintImage, Status
from users.models import CustomUser, Role     
from plans.tasks import process_blueprint_file, async_create_annotation, process_page_image
import uuid
from projects.models import Project
from PIL import Image
import io
from unittest.mock import patch, PropertyMock, MagicMock
import numpy as np
from annotations.models import Annotation
from django.core.files.base import ContentFile

class BlueprintTaskTestCase(TestCase):
    def setUp(self):
        self.estimator = CustomUser.objects.create_user(
            email="testestimator@ssnbuilders.com",
            username = 'testestimator',
            first_name = 'test',
            last_name = 'estimator',
            password="testpass123",
            role=Role.ESTIMATOR
        )
        self.project = Project.objects.create(
            title = 'Test Project',
            owner = self.estimator
        )
        
        self.blueprint = Blueprint.objects.create(
            title="Test Blueprint",
            project=self.project,
            description="A test blueprint.",
            pdf_file=SimpleUploadedFile("test.pdf", b"fake pdf content", content_type="application/pdf")
        )
        img = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG')
        img_io.seek(0)

        image = SimpleUploadedFile("blueprint_image.jpg", img_io.read(), content_type="image/jpeg")
        self.blueprint_image = BlueprintImage.objects.create(
            title="Test Image",
            blueprint=self.blueprint,
            image=image,
            dpi=300,
            scale=1.0,
        )

    def test_process_blueprint_file_invalid_file(self):
        blueprint = Blueprint.objects.create(title="Invalid File Blueprint", project = self.project)
        result = process_blueprint_file(blueprint.id)
        self.assertFalse(result)
        blueprint.refresh_from_db()
        self.assertEqual(blueprint.status, Status.FAILED)

    def test_async_create_annotation_invalid_user(self):
        self.blueprint_image.dpi = 300
        self.blueprint_image.scale = 1.0
        self.blueprint_image.save()

        invalid_user = CustomUser.objects.create_user(
            email="invalid@ssnbuilders.com", 
            username='invaliduser', 
            first_name='test', 
            last_name='estimator',
            password="testpass123", 
            role=Role.ESTIMATOR  # still estimator
        )

        with patch("plans.tasks.CustomUser.objects.get", return_value=invalid_user):
            with patch.object(type(invalid_user), "is_authenticated", new_callable=PropertyMock) as mock_auth:
                mock_auth.return_value = False
                result = async_create_annotation(self.blueprint_image.id, invalid_user.id)

        self.assertEqual(result['status'], 'error')
        self.assertIn("permission", result['message'].lower())


    def test_async_create_annotation_not_found(self):
        invalid_id = uuid.uuid4()
        result = async_create_annotation(invalid_id, self.estimator.id)
        self.assertEqual(result['status'], 'error')
        self.assertIn("not found", result['message'].lower())

    @patch("plans.tasks.BlueprintImage.objects.create")
    @patch("plans.tasks.extract_scale_from_image", return_value=1.5)
    def test_process_page_image_creates_blueprint_image(self, mock_extract_scale, mock_create):
        # Create an RGB image without DPI info
        image = Image.new("RGB", (100, 100), color="blue")

        process_page_image(image, idx=1, blueprint=self.blueprint)

        # Assert extract_scale_from_image was called once
        mock_extract_scale.assert_called_once_with(image)

        # Assert BlueprintImage.objects.create was called once with expected args
        args, kwargs = mock_create.call_args
        self.assertEqual(kwargs["title"], "Test Blueprint - Page 1")
        self.assertEqual(kwargs["blueprint"], self.blueprint)
        self.assertIsInstance(kwargs["image"], ContentFile)
        self.assertEqual(kwargs["dpi"], 300)  # default dpi fallback
        self.assertEqual(kwargs["scale"], 1.5)

    @patch("plans.tasks.BlueprintImage.objects.create")
    @patch("plans.tasks.extract_scale_from_image", return_value=2.0)
    def test_process_page_image_with_dpi_info(self, mock_extract_scale, mock_create):
        # Create an image with dpi info
        image = Image.new("RGB", (50, 50), color="green")
        image.info["dpi"] = (150, 150)

        process_page_image(image, idx=2, blueprint=self.blueprint)

        _, kwargs = mock_create.call_args
        self.assertEqual(kwargs["dpi"], 150)
        self.assertEqual(kwargs["scale"], 2.0)

    @patch("plans.tasks.BlueprintImage.objects.create")
    @patch("plans.tasks.extract_scale_from_image", side_effect=Exception("Scale extraction failed"))
    def test_process_page_image_handles_exceptions(self, mock_extract_scale, mock_create):
        # Use an image
        image = Image.new("RGB", (30, 30), color="yellow")

        # Should not raise, just print error and traceback
        process_page_image(image, idx=3, blueprint=self.blueprint)

        # create should not be called due to exception
        mock_create.assert_not_called()

    @patch("plans.tasks.is_pdf_file", return_value=False)
    @patch("plans.tasks.is_image_file", return_value=False)
    def test_process_blueprint_file_invalid_file(self, mock_is_image, mock_is_pdf):
        """Test processing fails if blueprint file is neither PDF nor image."""
        blueprint = Blueprint.objects.create(title="Invalid File Blueprint", project=self.project)
        blueprint.pdf_file = SimpleUploadedFile("file.txt", b"not an image or pdf", content_type="text/plain")
        blueprint.save()

        result = process_blueprint_file(blueprint.id)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "error")
        self.assertIn("unsupported", result.get("message", "").lower())

        blueprint.refresh_from_db()
        self.assertEqual(blueprint.status, Status.FAILED)

    @patch("plans.tasks.convert_from_bytes")
    @patch("plans.tasks.is_pdf_file", return_value=True)
    @patch("plans.tasks.is_image_file", return_value=False)
    @patch("plans.tasks.process_page_image")
    def test_process_blueprint_file_success(
        self, mock_process_page_image, mock_is_image, mock_is_pdf, mock_convert
    ):
        """Test successful processing of a PDF blueprint file."""
        # Mock convert_from_bytes to return a list of 2 mock PIL images
        mock_img1 = MagicMock()
        mock_img2 = MagicMock()
        mock_convert.return_value = [mock_img1, mock_img2]

        result = process_blueprint_file(self.blueprint.id)

        self.assertEqual(result, self.blueprint.id)
        self.blueprint.refresh_from_db()
        self.assertEqual(self.blueprint.status, Status.COMPLETE)

        # Confirm process_page_image called twice (once per page)
        self.assertEqual(mock_process_page_image.call_count, 2)

    @patch("django.db.models.fields.files.FieldFile.save")              # no real I/O
    @patch("plans.tasks.compute_sqft", return_value=25.0)
    @patch("plans.tasks.polygon_dimension", return_value=(5.0, 5.0))
    @patch("plans.tasks.cv2")                                           # stub OpenCV
    @patch("plans.tasks.get_model")                                     # stub YOLO
    def test_async_create_annotation_success(
        self,
        mock_get_model,
        mock_cv2,
        mock_polygon_dim,
        mock_compute_sqft,
        mock_fieldfile_save,
    ):
        
        mock_model = MagicMock()
        mock_model.names = {0: "floor"} 

        mask_obj = MagicMock()
        mask_obj.xy = [
            np.array([[10, 10], [60, 10], [60, 60], [10, 60]], dtype=float)
        ]
        mask_obj.cls = [np.array(0)] 
        box_mock = MagicMock()
        box_mock.conf.item.return_value = 0.9
        box_mock.cls.item.return_value = 0

        pred = MagicMock()
        pred.masks = mask_obj
        pred.orig_img = np.zeros((100, 100, 3), dtype=np.uint8)
        pred.probs = None           
        pred.boxes = [box_mock]

        mock_model.predict.return_value = [pred]
        mock_get_model.return_value = mock_model
        contour = np.array([[[10, 10]], [[60, 10]], [[60, 60]], [[10, 60]]])
        mock_cv2.findContours.return_value = ([contour], None)
        mock_cv2.approxPolyDP.side_effect = lambda c, eps, closed: c
        mock_cv2.arcLength.side_effect = lambda c, closed: 100
        mock_cv2.erode.side_effect = lambda img, kernel, iterations=1: img
        mock_cv2.fillPoly.side_effect = lambda *a, **k: None
        mock_cv2.RETR_EXTERNAL = mock_cv2.CHAIN_APPROX_SIMPLE = 0
        before = Annotation.objects.count()
        result = async_create_annotation(self.blueprint_image.id, self.estimator.id)

        self.assertEqual(result, self.blueprint_image.id)            
        self.assertGreater(Annotation.objects.count(), before) 