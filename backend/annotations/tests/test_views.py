from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import CustomUser, Role
from projects.models import Project
from annotations.models import Annotation, WallAnnotation, WindowAndDoorAnnotation
from plans.models import BlueprintImage, Blueprint
from io import BytesIO
from django.core.files.uploadedfile import SimpleUploadedFile
import json
from PIL import Image
import uuid

def generate_test_image():
    image = Image.new('RGB', (100, 100))
    buffer = BytesIO()
    image.save(buffer, format='JPEG')
    return SimpleUploadedFile("test_image.jpg", buffer.getvalue(), content_type="image/jpeg")

class AnnotationAPIViewSetTest(APITestCase):
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
            project=self.project,
            
        )

        self.image = SimpleUploadedFile("blueprint_image.jpg", b"image_content", content_type="image/jpeg")

        self.blueprintimage = BlueprintImage.objects.create(
            id=uuid.uuid4(),
            blueprint=self.blueprint,  
            image=self.image,
            title='Test Image',
             dpi=300,
            scale=0.375

        )
        self.annotation_url = reverse('annotation-list')

    def test_estimator_can_create_annotation(self):
        self.client.force_authenticate(user=self.estimator)
        data = {
            "blueprint": str(self.blueprintimage.id),
            "label": "Test Annotation",
            "coordinates": [[0, 0], [1, 1]],
            "annotation_type": "polygon",
        }
        response = self.client.post(self.annotation_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("area_size", response.data)
        self.assertEqual(response.data['label'], "Test Annotation")

    def test_user_cannot_create_annotation(self):
        another_user = CustomUser.objects.create_user(
            email = 'anothertestuser@gmail.com',
            username = 'anothertestuser',
            first_name = 'Test',
            last_name = 'User',
            password = 'HelloWorld!1',
            role = Role.USER
        )
        self.client.force_authenticate(user=another_user)
        data = {
            "blueprint": str(self.blueprintimage.id),
            "label": "Test Annotation",
            "coordinates": [[0, 0], [1, 1]],
            "annotation_type": "polygon",
        }
        response = self.client.post(self.annotation_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_annotation_list_access_by_estimator(self):
        Annotation.objects.all().delete() 
        Annotation.objects.create(
            blueprint=self.blueprintimage,
            label='Test Annotation',
            coordinates=[[0, 0], [1, 1]],
            area_size=10.0,
            annotation_type='polygon',
            width=5.0,
            height=5.0,
            confidence_score=0.95
        )
        self.client.force_authenticate(user=self.estimator)
        response = self.client.get(self.annotation_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)

    def test_estimator_can_update_annotation(self):
        annotation = Annotation.objects.create(
            blueprint=self.blueprintimage,
            label='Original',
            coordinates=[[0, 0], [1, 1]],
            area_size=1.0,
            annotation_type='polygon',
            width=1.0,
            height=1.0,
        )

        self.client.force_authenticate(user=self.estimator)
        url = reverse('annotation-detail', args=[str(annotation.id)])
        new_coords = [[0, 0], [2, 2]]
        payload = {"coordinates": new_coords}
        response = self.client.patch(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        annotation.refresh_from_db()
        self.assertEqual(annotation.coordinates, new_coords)
        self.assertNotEqual(annotation.area_size, 1.0)
        self.assertNotEqual(annotation.width, 1.0)
        self.assertNotEqual(annotation.height, 1.0)

    def test_estimator_can_delete_annotation(self):
        annotation = Annotation.objects.create(
            blueprint=self.blueprintimage,
            label='To delete',
            coordinates=[[0, 0], [1, 1]],
            area_size=1.0,
            annotation_type='polygon',
            width=1.0,
            height=1.0,
        )
        self.client.force_authenticate(user=self.estimator)
        url = reverse('annotation-detail', args=[str(annotation.id)])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Annotation.objects.filter(id=annotation.id).exists(),
            "Annotation should be removed from the database",
        )

    def test_owner_can_only_access_own_annotations(self):
        Annotation.objects.all().delete() 
        Annotation.objects.create(
            blueprint=self.blueprintimage,
            label='Test Annotation',
            coordinates=[[0, 0], [1, 1]],
            area_size=10.0,
            annotation_type='polygon',
            width=5.0,
            height=5.0,
            confidence_score=0.95
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.annotation_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)

class WallAnnotationAPIViewSetTest(APITestCase):
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
            project=self.project,
            
        )

        self.image = SimpleUploadedFile("blueprint_image.jpg", b"image_content", content_type="image/jpeg")

        self.blueprintimage = BlueprintImage.objects.create(
            id=uuid.uuid4(),
            blueprint=self.blueprint,  
            image=self.image,
            title='Test Image',
             dpi=300,
            scale=0.375

        )
        self.wall_url = reverse('wall_annotation-list')

    def test_create_wall_annotation_by_estimator(self):
        self.client.force_authenticate(user=self.estimator)
        data = {
            "blueprint": str(self.blueprintimage.id),
            "label": "Test Wall Annotation",
            "coordinates": [[0, 0], [1, 1]],
            "annotation_type": "rectangle",
        }
        response = self.client.post(self.wall_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['label'], "Test Wall Annotation")

    def test_update_wall_annotation_by_estimator(self):
        wall = WallAnnotation.objects.create(
            blueprint=self.blueprintimage,
            label="Original",
            coordinates=[[0, 0], [1, 1]],
            annotation_type="rectangle",
        )
        self.client.force_authenticate(user=self.estimator)
        url = reverse('wall_annotation-detail', args=[str(wall.id)])
        resp = self.client.patch(url, {"label": "Updated"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        wall.refresh_from_db()
        self.assertEqual(wall.label, "Updated")

    def test_delete_wall_annotation_by_estimator(self):
        wall = WallAnnotation.objects.create(
            blueprint=self.blueprintimage,
            label="To Delete",
            coordinates=[[0, 0], [1, 1]],
            annotation_type="rectangle",
        )
        self.client.force_authenticate(user=self.estimator)
        url = reverse('wall_annotation-detail', args=[str(wall.id)])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(WallAnnotation.objects.filter(id=wall.id).exists())

# from django.test.utils import override_settings

# @override_settings(REST_FRAMEWORK={"DEFAULT_PAGINATION_CLASS": None})
class WindowAndDoorAnnotationAPIViewSetTest(APITestCase):
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
            project=self.project,
            
        )

        self.image = SimpleUploadedFile("blueprint_image.jpg", b"image_content", content_type="image/jpeg")

        self.blueprintimage = BlueprintImage.objects.create(
            id=uuid.uuid4(),
            blueprint=self.blueprint,  
            image=self.image,
            title='Test Image',
             dpi=300,
            scale=0.375

        )
        self.window_and_door_url = reverse('window_and_door_annotation-list')


    def test_window_and_door_annotation_queryset_access(self):
        WindowAndDoorAnnotation.objects.all().delete()
        annotation_by_estimator = WindowAndDoorAnnotation.objects.create(
            blueprint=self.blueprintimage,
            label="Estimator Annotation",
            coordinates={"points": [[0, 0], [1, 1]]},
            annotation_type="polygon",
        )
        self.client.force_authenticate(user=self.estimator)
        response = self.client.get(self.window_and_door_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['label'], "Estimator Annotation")


    def test_create_wall_annotation_by_estimator(self):
        self.client.force_authenticate(user=self.estimator)
        data = {
            "blueprint": str(self.blueprintimage.id),
            "label": "Door",
            "coordinates": {"points": [[1, 1], [1, 5], [5, 5], [5, 1]]},
            "annotation_type": "polygon"
        }
        response = self.client.post(self.window_and_door_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['label'], "Door")

    def test_update_window_and_door_annotation_by_estimator(self):
        annotation = WindowAndDoorAnnotation.objects.create(
            blueprint=self.blueprintimage,
            label="Old Label",
            coordinates={"points": [[1, 1], [1, 5], [5, 5], [5, 1]]},
            annotation_type="polygon",
        )
        self.client.force_authenticate(user=self.estimator)
        url = reverse('window_and_door_annotation-detail', args=[str(annotation.id)])
        response = self.client.patch(url, {"label": "Updated Label"}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        annotation.refresh_from_db()
        self.assertEqual(annotation.label, "Updated Label")

    def test_delete_window_and_door_annotation_by_estimator(self):
        annotation = WindowAndDoorAnnotation.objects.create(
            blueprint=self.blueprintimage,
            label="To Be Deleted",
            coordinates={"points": [[1, 1], [1, 5], [5, 5], [5, 1]]},
            annotation_type="polygon",
        )
        self.client.force_authenticate(user=self.estimator)
        url = reverse('window_and_door_annotation-detail', args=[str(annotation.id)])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(WindowAndDoorAnnotation.objects.filter(id=annotation.id).exists())
