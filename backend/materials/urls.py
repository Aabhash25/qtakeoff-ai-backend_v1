from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MaterialCategoryViewSet, MaterialSubcategoryViewSet, MaterialViewSet

router = DefaultRouter()
router.register(r'categories', MaterialCategoryViewSet, basename='category')
router.register(r'subcategories', MaterialSubcategoryViewSet, basename='subcategory')
router.register(r'materials', MaterialViewSet, basename='material')

urlpatterns = [
    path('', include(router.urls)),
]
