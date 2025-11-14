from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import ProjectSerializer, ProjectDetailSerializer
from .models import Project
from config.permissions import IsCustomUser, IsOwnerOrReadOnly
from rest_framework.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache


class ProjectCreateView(generics.CreateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsCustomUser]

    def perform_create(self, serializer):
        user = self.request.user
        title = serializer.validated_data.get("title")
        if Project.objects.filter(title=title, owner=user).exists():
            raise ValidationError(
                {"detail": "You already have a project with this title."}
            )
        serializer.save(owner=user)
        cache.delete(f"project_list_{user.id}")


class ProjectUpdateView(generics.UpdateAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self):
        obj = Project.objects.get(pk=self.kwargs["pk"])
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_update(self, serializer):
        instance = self.get_object()
        serializer.save()
        cache.delete(f"project_detail_{instance.id}")
        cache.delete(f"project_list_{self.request.user.id}")


class ProjectListView(generics.ListAPIView):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    @method_decorator(cache_page(60 * 15, key_prefix="project_list"))  # 2 hours
    def get(self, request, format=None):
        user = request.user
        cache_key = f"project_list_{user.id}"
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data, status=status.HTTP_200_OK)
        project = Project.objects.filter(owner=request.user)
        serializer = ProjectSerializer(project, many=True)
        cache.set(cache_key, serializer.data, timeout=60 * 60 * 2)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get(self, request, pk, format=None):
        cache_key = f"project_detail_{pk}"
        project = cache.get(cache_key)
        if not project:
            try:
                project = (
                    Project.objects.prefetch_related("blueprints")
                    .select_related("owner")
                    .get(id=pk)
                )
                cache.set(cache_key, project, timeout=60 * 15)
            except Project.DoesNotExist:
                return Response(status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, project)
        serializer = ProjectDetailSerializer(project)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProjectDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]

    def get_object(self, pk):
        try:
            return Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return None

    def delete(self, request, pk, format=None):
        project = self.get_object(pk)
        if project is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, project)
        project.delete()
        cache.delete(f"project_detail_{pk}")
        cache.delete(f"project_list_{request.user.id}")
        return Response(
            {"message": "Project successfully deleted!"},
            status=status.HTTP_204_NO_CONTENT,
        )
