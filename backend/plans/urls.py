from django.urls import path
from .views import (
    BlueprintCreateView,
    BlueprintUpdateView,
    BlueprintListView,
    BlueprintDetailView,
    BlueprintDeleteView,
    BlueprintImageDetailView,
    BlueprintImageCreateView,
    EstimatorRequestCreateView
)

urlpatterns = [
    path('create/', BlueprintCreateView.as_view(), name='blueprint-create'),
    path('update/<uuid:pk>/', BlueprintUpdateView.as_view(), name='blueprint-update'),
    path('list/', BlueprintListView.as_view(), name='blueprint-list'),
    path('detail/<uuid:pk>/', BlueprintDetailView.as_view(), name='blueprint-detail'),
    path('delete/<uuid:pk>/', BlueprintDeleteView.as_view(), name='blueprint-delete'),
    path('blueprint-images/', BlueprintImageCreateView.as_view(), name='blueprint-image-create'),
    path('blueprint-images/<uuid:pk>/', BlueprintImageDetailView.as_view(), name='blueprint-image-detail'),
    path('estimator-request/', EstimatorRequestCreateView.as_view(), name='estimator_request'),
]