from .views import BookDemoAPIView
from django.urls import path

urlpatterns = [
    path('', BookDemoAPIView.as_view(), name='book-demo'),
]
