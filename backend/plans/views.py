from django.shortcuts import render
from rest_framework import permissions, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import BlueprintSerializer, BlueprintDetailSerializer, BlueprintImageDetailSerializer, BlueprintImageSerializer
from .models import Blueprint, BlueprintImage
from config.permissions import IsCustomUser, IsOwnerOrReadOnly
from rest_framework.exceptions import ValidationError
from estimators.serializers import EstimatorRequestSerializer
from estimators.tasks import send_estimator_request_email
from annotations.serializers import AnnotationSerializer, WallAnnotationSerializer, WindowAndDoorAnnotationSerializer
from annotations.models import Annotation, WallAnnotation, WindowAndDoorAnnotation
import numpy as np
from .utils import compute_sqft, polygon_dimension
from rest_framework.parsers import MultiPartParser, FormParser
class BlueprintCreateView(generics.CreateAPIView):
    serializer_class = BlueprintSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomUser]
    parser_classes = [MultiPartParser, FormParser] 
    def post(self, request, format=None):
        serializer = BlueprintSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = self.request.user
            title = serializer.validated_data.get('title')
            project = serializer.validated_data.get('project')
            if Blueprint.objects.filter(project__owner=user, project=project, title__iexact=title).exists():
                raise ValidationError({"detail": "You already have a blueprint with this title in this project."})
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class BlueprintUpdateView(generics.UpdateAPIView):
    serializer_class = BlueprintSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    def get_object(self):
        obj = Blueprint.objects.get(pk=self.kwargs['pk'])
        self.check_object_permissions(self.request, obj)
        return obj
    
class BlueprintListView(generics.ListAPIView):
    serializer_class = BlueprintSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    def get(self, request, format=None):
        blueprint = Blueprint.objects.filter(project__owner = request.user)
        serializer = BlueprintSerializer(blueprint, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class BlueprintDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    def get_object(self):
        try:
            return Blueprint.objects.select_related('project__owner').prefetch_related('images').get(pk=self.kwargs['pk'])
        except Blueprint.DoesNotExist:
            return None
    def get(self, request, pk, format=None):
        blueprint = self.get_object()
        if blueprint is None:
            return Response({"detail": "Blueprint not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, blueprint)
        serializer = BlueprintDetailSerializer(blueprint)
        return Response({
            "message": "Blueprint Detail!",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

class BlueprintDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    def get_object(self):
        try:
            return Blueprint.objects.get(pk=self.kwargs['pk'])
        except Blueprint.DoesNotExist:
            return None
    
    def delete(self, request, pk, format=None):
        blueprint = self.get_object()
        if blueprint is None:
            return Response({"detail": "Blueprint not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, blueprint)
        blueprint.delete()
        return Response({"message": "Blueprint successfully deleted!"}, status=status.HTTP_204_NO_CONTENT)
    
class BlueprintImageCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [MultiPartParser, FormParser] 
    def post(self, request):
        serializer = BlueprintImageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            blueprint = serializer.validated_data.get('blueprint')
            self.check_object_permissions(request, blueprint)
            serializer.save()
            return Response({"message": "Image uploaded!", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BlueprintImageDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly, IsCustomUser]
    def get_object(self, pk):
        try:
            return BlueprintImage.objects.select_related('blueprint__project__owner').get(pk=pk)
        except BlueprintImage.DoesNotExist:
            return None
    def get(self, request, pk):
        # sourcery skip: extract-method, inline-immediately-returned-variable
        image = self.get_object(pk)
        if not image:
            return Response({"Detail": "Image not found!"}, status = status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, image)
        serializer = BlueprintImageDetailSerializer(image)
        response_data = {
            "Message": "Blueprint Image Detail!",
            "data": serializer.data
        }

        if image.is_verified:
            annotations = Annotation.objects.filter(blueprint=image)
            wall_annotation = WallAnnotation.objects.filter(blueprint=image)
            window_and_door_annotation = WindowAndDoorAnnotation.objects.filter(blueprint=image)
            annotation_serializer = AnnotationSerializer(annotations, many=True)
            wall_annotation_serializer = WallAnnotationSerializer(wall_annotation, many=True)
            window_and_door_annotation_serializer = WindowAndDoorAnnotationSerializer(window_and_door_annotation, many=True)
            response_data = {
                'annotations': annotation_serializer.data,
                'wall_annotations': wall_annotation_serializer.data,
                'window_and_door_annotations': window_and_door_annotation_serializer.data,
            }
        return Response(response_data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        image = self.get_object(pk)
        if not image:
            return Response({"detail": "Image not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, image)
        image.delete()
        return Response({"message": "Image deleted!"}, status=status.HTTP_204_NO_CONTENT)

class SendEmailToAdminView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly, IsCustomUser]

    def post(self, request, *args, **kwargs):
        user = request.user
        image_id = request.data.get('image_id')
        print(user, image_id)



class EstimatorRequestCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsCustomUser]
    def post(self, request, *args, **kwargs):
        try:
            return self._extracted_from_post_3(request)
        except ValidationError as exc:
            error_messages = {field: messages[0] if isinstance(messages, list) else messages
                              for field, messages in exc.detail.items()}
            return Response(error_messages, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # TODO Rename this here and in `post`
    def _extracted_from_post_3(self, request):
        image_id = request.data.get('image_id')
        if not image_id:
            return Response({"error": "Image ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            image = BlueprintImage.objects.get(id=image_id)
        except BlueprintImage.DoesNotExist:
            return Response({"error": "Image not found."}, status=status.HTTP_404_NOT_FOUND)
        if image.blueprint.project.owner != request.user:
            return Response({"error": "You are not allowed to send this image."}, status=status.HTTP_403_FORBIDDEN)
        image_path = image.image.path
        submitted_by_email = request.user.email
        result = send_estimator_request_email.delay(image_path, submitted_by_email)

        data = {
            "image": image.id,
            "requested_by": request.user.id  
        }
        serializer = EstimatorRequestSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            saved = serializer.save()
            return Response({
                "success": "Image sent and request saved.",
                "image_id": saved.id
            }, status=status.HTTP_201_CREATED)
        return Response({"error": "Failed to send email."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)