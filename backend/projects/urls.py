from django.urls import path
from .views import (
    ProjectCreateView,
    ProjectListView,
    ProjectDeleteView,
    ProjectUpdateView,
    ProjectDetailView,
)

urlpatterns = [
    path("create/", ProjectCreateView.as_view(), name="project-create"),
    path("update/<uuid:pk>/", ProjectUpdateView.as_view(), name="project-update"),
    path("list/", ProjectListView.as_view(), name="project-list"),
    path("detail/<uuid:pk>/", ProjectDetailView.as_view(), name="project-detail"),
    path("delete/<uuid:pk>/", ProjectDeleteView.as_view(), name="project-delete"),
]
