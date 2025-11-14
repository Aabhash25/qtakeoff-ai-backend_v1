from django.test import TestCase
from django.forms.models import model_to_dict
from model_bakery import baker
from annotations.models import Annotation, WallAnnotation, WindowAndDoorAnnotation
from annotations.serializers import AnnotationSerializer, WallAnnotationSerializer, WindowAndDoorAnnotationSerializer

class SerializerTestMixin:
    """
    Provides helpers to (1) build a valid payload from a baked
    instance and (2) drop read‑only fields so validation succeeds.
    """
    read_only = {'id', 'created_at', 'updated_at'}
    def payload_from_instance(self, instance):
        data = model_to_dict(instance)
        for field in self.read_only:
            data.pop(field, None)
        # Use PK for foreign keys (e.g., blueprint) because DRF expects the ID
        for key, value in data.items():
            if hasattr(value, "pk"):
                data[key] = value.pk

        return data
    
class AnnotationSerializerTest(SerializerTestMixin, TestCase):
    def setUp(self):
        self.annotation = baker.make('annotations.Annotation')

    def test_annotaiton_serializer_accet_valid_payload(self):
        payload = self.payload_from_instance(self.annotation)
        serializer = AnnotationSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertEqual(serializer.validated_data['label'], self.annotation.label)

    def test_annotation_serializer_requires_blueprint(self):
        payload = self.payload_from_instance(self.annotation)
        payload.pop('blueprint', None)
        serializer = AnnotationSerializer(data=payload)
        self.assertFalse(serializer.is_valid())
        self.assertIn('blueprint', serializer.errors)

    def test_annotaiton_serializer_read_only_fields_ignored(self):
        payload = self.payload_from_instance(self.annotation)
        payload['created_at'] = "2000-01-01T00:00:00Z"
        serializer = AnnotationSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertNotIn('created_at', serializer.validated_data)

class WallAnnotationSerializerTests(SerializerTestMixin, TestCase):
    def setUp(self):
        self.wall = baker.make("annotations.WallAnnotation")

    def test_wall_serializer_accepts_valid_payload(self):
        payload = self.payload_from_instance(self.wall)
        ser = WallAnnotationSerializer(data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)

    def test_wall_serializer_requires_blueprint(self):
        payload = self.payload_from_instance(self.wall)
        payload.pop("blueprint")
        ser = WallAnnotationSerializer(data=payload)
        self.assertFalse(ser.is_valid())
        self.assertIn("blueprint", ser.errors)

class WindowAndDoorAnnotationSerializerTests(SerializerTestMixin, TestCase):
    def setUp(self):
        self.win_door = baker.make("annotations.WindowAndDoorAnnotation")

    def test_win_door_serializer_accepts_valid_payload(self):
        payload = self.payload_from_instance(self.win_door)
        ser = WindowAndDoorAnnotationSerializer(data=payload)
        self.assertTrue(ser.is_valid(), ser.errors)

    def test_win_door_serializer_requires_blueprint(self):
        payload = self.payload_from_instance(self.win_door)
        payload.pop("blueprint")
        ser = WindowAndDoorAnnotationSerializer(data=payload)
        self.assertFalse(ser.is_valid())
        self.assertIn("blueprint", ser.errors)

