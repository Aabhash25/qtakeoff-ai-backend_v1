from django.urls import path
from .views import (
    EstimatorImageListView,
    EstimatorImageDetailView,
    SendVerifiedImageToCustomUser,
    ImportExcelExtraInfoView,
    PreviewExcelDataView,
)

urlpatterns = [
    path("image/", EstimatorImageListView.as_view(), name="estimator_image_list"),
    path(
        "image/detail/<uuid:pk>/",
        EstimatorImageDetailView.as_view(),
        name="estimator_image_detail",
    ),
    path(
        "image/<uuid:blueprint_id>/send-verified/",
        SendVerifiedImageToCustomUser.as_view(),
        name="send_email_after_annotation",
    ),
    path(
        "preview-excel/",
        PreviewExcelDataView.as_view(),
        name="preview_excel_data",
    ),
    path(
        "blueprint/<uuid:blueprint_id>/import-excel/",
        ImportExcelExtraInfoView.as_view(),
        name="import_excel_extra_info",
    ),
]
