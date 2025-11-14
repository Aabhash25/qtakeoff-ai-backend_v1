from rest_framework.routers import DefaultRouter
from .views import (AnnotationViewSet, 
                    WallAnnotationViewSet, 
                    WindowandDoorAnnotationViewSet, 
                    AnnotationMaterialView, 
                    # FloorAnnotationViewSet, 
                    WallAnnotationMaterialView,
                    WindowAndDoorAnnotationMaterialView)
from django.urls import path


router = DefaultRouter()
router.register(r'annotations', AnnotationViewSet, basename='annotation')
router.register(r'wall-annotations', WallAnnotationViewSet, basename='wall_annotation')
router.register(r'window-door-annotations', WindowandDoorAnnotationViewSet, basename='window_and_door_annotation')
# router.register(r'floor-annotations', FloorAnnotationViewSet, basename='floor_annotation')
urlpatterns = [
    path('room/<uuid:annotation_id>/materials/', AnnotationMaterialView.as_view()),
    path('room/<uuid:annotation_id>/materials/<uuid:material_id>/', AnnotationMaterialView.as_view()),
    path('wall/<uuid:wall_annotation_id>/materials/', WallAnnotationMaterialView.as_view()),
    path('wall/<uuid:wall_annotation_id>/materials/<uuid:material_id>/', WallAnnotationMaterialView.as_view()),
    path('window-and-door/<uuid:window_and_door_annotation_id>/materials/', WindowAndDoorAnnotationMaterialView.as_view()),
    path('window-and-door/<uuid:window_and_door_annotation_id>/materials/<uuid:material_id>/', WindowAndDoorAnnotationMaterialView.as_view()),
] + router.urls
