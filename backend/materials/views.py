from rest_framework import viewsets, permissions
from .models import MaterialCategory, MaterialSubcategory, Material
from .serializers import MaterialCategorySerializer, MaterialSubcategorySerializer, MaterialSerializer
from config.permissions import IsEstimator

class MaterialCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MaterialCategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsEstimator]

    def get_queryset(self):
        return MaterialCategory.objects.prefetch_related('subcategories__materials')


class MaterialSubcategoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MaterialSubcategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsEstimator]

    def get_queryset(self):
        return MaterialSubcategory.objects.prefetch_related('materials')


class MaterialViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MaterialSerializer
    permission_classes = [permissions.IsAuthenticated, IsEstimator]
    
    def get_queryset(self):
        return Material.objects.select_related('subcategory__category')
