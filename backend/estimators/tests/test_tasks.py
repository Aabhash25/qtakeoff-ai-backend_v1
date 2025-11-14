from unittest.mock import patch, MagicMock
import uuid, io
from PIL import Image
import numpy as np
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from users.models import CustomUser, Role
from projects.models import Project
from plans.models import Blueprint, BlueprintImage
from annotations.models import WallAnnotation, WindowAndDoorAnnotation
from estimators.tasks import (
    send_estimator_request_email,
    send_image_email_task_to_estimator,
    send_email_to_user_after_annotation,
    async_create_wall_annotation,
    async_create_window_and_door_annotation,
)


class EstimatorTasksTest(TestCase):
    """All tasks in estimators.tasks"""

    @classmethod
    def setUpTestData(cls):
        cls.estimator = CustomUser.objects.create_user(
            email=f"{uuid.uuid4()}@ssnbuilders.com",
            username=f"est_{uuid.uuid4().hex[:8]}",
            first_name="Test",
            last_name="Estimator",
            password="testpass123",
            role=Role.ESTIMATOR,
        )
        cls.user = CustomUser.objects.create_user(
            email=f"{uuid.uuid4()}@example.com",
            username=f"user_{uuid.uuid4().hex[:8]}",
            first_name="Test",
            last_name="User",
            password="testpass123",
            role=Role.USER,
        )

        cls.project = Project.objects.create(title="Test Project", owner=cls.estimator)
        cls.blueprint = Blueprint.objects.create(
            title="Test Blueprint",
            project=cls.project,
            description="Demo blueprint",
            pdf_file=SimpleUploadedFile(
                "test.pdf", b"%PDF-1.4 fake", content_type="application/pdf"
            ),
        )

        img = Image.new("RGB", (100, 100), "red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        cls.blueprint_image = BlueprintImage.objects.create(
            title="Test Image",
            blueprint=cls.blueprint,
            image=SimpleUploadedFile("img.jpg", buf.read(), content_type="image/jpeg"),
            dpi=300,
            scale=1.0,
        )

    @patch("django.core.mail.EmailMessage")
    def test_send_estimator_request_email(self, email_cls):
        email_obj = MagicMock()
        email_cls.return_value = email_obj
        email_obj.send.return_value = True

        ok = send_estimator_request_email("dummy/path.jpg", self.user.email)

        self.assertTrue(ok)
        email_obj.attach_file.assert_called_once_with("dummy/path.jpg")
        email_obj.send.assert_called_once()

    @patch("django.core.mail.send_mail")
    def test_send_image_email_task_to_estimator(self, send_mail):
        send_mail.return_value = 1
        res = send_image_email_task_to_estimator(
            self.estimator.email, "Test Blueprint", "img‑123"
        )
        self.assertIn("Email sent", res)

    @patch("django.core.mail.send_mail")
    def test_send_email_to_user_after_annotation(self, send_mail):
        send_mail.return_value = 1
        res = send_email_to_user_after_annotation(self.user.email)
        self.assertIn("Email sent", res)

    @patch("estimators.tasks.get_wall_model")
    def test_async_create_wall_annotation(self, mock_get_model):
        from numpy import array
        import torch

        mock_model = MagicMock()
        mock_model.names = {0: "wall"}      #  ←  **add this line**

        mock_pred = MagicMock()
        mock_pred.boxes.xyxy = [array([10, 10, 50, 50])]
        mock_pred.boxes.cls = [torch.tensor(0)]

        mock_model.predict.return_value = [mock_pred]
        mock_get_model.return_value = mock_model

        before = WallAnnotation.objects.count()
        async_create_wall_annotation(self.blueprint_image.id)
        self.assertGreater(WallAnnotation.objects.count(), before)



    @patch("estimators.tasks.get_window_and_door_model")
    def test_async_create_window_and_door_annotation(self, mock_get_model):
        from numpy import array
        import torch

        mock_model = MagicMock()
        mock_model.names = {0: "window", 1: "door"}   #  ←  **add this line**

        mock_pred = MagicMock()
        mock_pred.boxes.xyxy = [
            array([0, 0, 100, 100]),
            array([200, 200, 300, 300]),
        ]
        mock_pred.boxes.cls = [torch.tensor(0), torch.tensor(1)]

        mock_model.predict.return_value = [mock_pred]
        mock_get_model.return_value = mock_model

        before = WindowAndDoorAnnotation.objects.count()
        async_create_window_and_door_annotation(self.blueprint_image.id)
        self.assertGreater(WindowAndDoorAnnotation.objects.count(), before)
