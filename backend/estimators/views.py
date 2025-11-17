from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
from config.permissions import IsEstimator
from .serializers import EstimatorRequestSerializer, BlueprintExtraInfoSerializer
from .models import EstimatorRequest, Process, BlueprintExtraInfo
from plans.models import BlueprintImage
from plans.serializers import BlueprintImageDetailSerializer
from plans.tasks import async_create_annotation
from .tasks import (
    send_email_to_user_after_annotation,
    async_create_wall_annotation,
    async_create_window_and_door_annotation,
)
from celery import chain
from annotations.models import Annotation, WallAnnotation, WindowAndDoorAnnotation
from django.db import transaction
import numpy as np
from annotations.serializers import (
    WallAnnotationSerializer,
    AnnotationSerializer,
    WindowAndDoorAnnotationSerializer,
)
from .utils import compute_wall_dimensions
from plans.utils import compute_sqft, polygon_dimension
from users.models import Role

import csv
import io
import pandas as pd
import math


def clean_dataframe_for_json(df):
    """
    Thoroughly clean DataFrame for JSON serialization.
    Handles NaN, inf, -inf, and converts numpy types to Python types.
    """
    df = df.replace([np.inf, -np.inf], np.nan)

    for col in df.columns:
        if df[col].dtype in ["float64", "float32", "int64", "int32"]:
            df[col] = df[col].apply(
                lambda x: (
                    None
                    if pd.isna(x)
                    or (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))
                    else x
                )
            )
        else:
            df[col] = df[col].apply(lambda x: None if pd.isna(x) else x)

    return df


class EstimatorImageListView(APIView):
    serializer_class = EstimatorRequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsEstimator]

    def get(self, request, format=None):
        blueprint = EstimatorRequest.objects.filter(assigned_estimator=request.user)
        serializer = EstimatorRequestSerializer(blueprint, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EstimatorImageDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsEstimator]

    def get_object(self, pk):
        return BlueprintImage.objects.filter(pk=pk).first()

    def get(self, request, pk):
        image = self.get_object(pk)
        if not image:
            return Response(
                {"error": "Image not found!"}, status=status.HTTP_404_NOT_FOUND
            )

        if not EstimatorRequest.objects.filter(
            assigned_estimator=request.user, image=image
        ).exists():
            return Response(
                {"error": "You are not assigned to this image!"},
                status=status.HTTP_403_FORBIDDEN,
            )

        self.check_object_permissions(request, image)

        serializer = BlueprintImageDetailSerializer(image)

        # Fetch extra info safely using filter().first()
        extra_info = BlueprintExtraInfo.objects.filter(blueprint=image).first()
        extra_info_serialized = (
            BlueprintExtraInfoSerializer(extra_info).data if extra_info else None
        )

        # Start annotation tasks
        chain(
            async_create_annotation.s(image.pk, request.user.id),
            async_create_wall_annotation.s(),
            async_create_window_and_door_annotation.s(),
        ).apply_async()

        return Response(
            {
                "message": "Blueprint Image Detail!",
                "data": {
                    **serializer.data,
                    "extra_info": extra_info_serialized,  # ⬅ will be None if deleted
                },
            },
            status=status.HTTP_200_OK,
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0",
            },
        )


def get(self, request, pk):
    image = self.get_object(pk)
    if not image:
        return Response({"error": "Image not found!"}, status=status.HTTP_404_NOT_FOUND)

    if not EstimatorRequest.objects.filter(
        assigned_estimator=request.user, image=image
    ).exists():
        return Response(
            {"error": "You are not assigned to this image!"},
            status=status.HTTP_403_FORBIDDEN,
        )

    self.check_object_permissions(request, image)

    serializer = BlueprintImageDetailSerializer(image)

    # Fetch extra info safely using filter().first()
    extra_info = BlueprintExtraInfo.objects.filter(blueprint=image).first()
    extra_info_serialized = (
        BlueprintExtraInfoSerializer(extra_info).data if extra_info else None
    )

    # Start annotation tasks
    chain(
        async_create_annotation.s(image.pk, request.user.id),
        async_create_wall_annotation.s(),
        async_create_window_and_door_annotation.s(),
    ).apply_async()

    return Response(
        {
            "message": "Blueprint Image Detail!",
            "data": {
                **serializer.data,
                "extra_info": extra_info_serialized,  # ⬅ will be None if deleted
            },
        },
        status=status.HTTP_200_OK,
    )


class SendVerifiedImageToCustomUser(APIView):
    permission_classes = [permissions.IsAuthenticated, IsEstimator]

    def post(self, request, blueprint_id):
        user = request.user

        try:
            blueprint = BlueprintImage.objects.get(id=blueprint_id)
        except BlueprintImage.DoesNotExist:
            return Response(
                {"error": "Blueprint not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if blueprint.blueprint.project.owner != user and user.role != Role.ESTIMATOR:
            return Response(
                {"error": "You do not have permission."},
                status=status.HTTP_403_FORBIDDEN,
            )

        has_floor = Annotation.objects.filter(blueprint=blueprint).exists()
        has_wall = WallAnnotation.objects.filter(blueprint=blueprint).exists()
        has_window = WindowAndDoorAnnotation.objects.filter(
            blueprint=blueprint
        ).exists()

        if not (has_floor and has_wall and has_window):
            missing = []
            if not has_floor:
                missing.append("general annotation")
            if not has_wall:
                missing.append("wall annotation")
            if not has_window:
                missing.append("window/door annotation")

            return Response(
                {"error": f"Cannot verify blueprint – missing {', '.join(missing)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        send_email_to_user_after_annotation.delay(
            user.email, blueprint.blueprint.project.owner.email
        )

        blueprint.is_verified = True
        blueprint.save(update_fields=["is_verified"])
        EstimatorRequest.objects.filter(image=blueprint).update(status=Process.COMPLETE)

        return Response(
            {"message": "Annotated image emailed and blueprint marked as verified."},
            status=status.HTTP_200_OK,
        )


class PreviewExcelDataView(APIView):
    """API endpoint for previewing Excel/CSV data before importing"""

    permission_classes = [permissions.IsAuthenticated, IsEstimator]

    def post(self, request):
        try:
            excel_file = request.FILES.get("excel_file")
            if not excel_file:
                return Response(
                    {"error": "Excel file is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not excel_file.name.lower().endswith((".xlsx", ".xls", ".xlsm", ".csv")):
                return Response(
                    {
                        "error": "Only Excel files (.xls, .xlsx, .xlsm) or CSV files (.csv) are allowed."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if excel_file.name.lower().endswith(".csv"):
                try:
                    df = pd.read_csv(excel_file, keep_default_na=True)
                except UnicodeDecodeError:
                    df = pd.read_csv(
                        excel_file, encoding="ISO-8859-1", keep_default_na=True
                    )
            else:
                if excel_file.name.lower().endswith((".xlsx", ".xlsm")):
                    df = pd.read_excel(excel_file, engine="openpyxl")
                else:
                    df = pd.read_excel(excel_file, engine="xlrd")

            if df.empty:
                return Response(
                    {"error": "File contains no data."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            df = clean_dataframe_for_json(df)

            preview_data = df.head(10).to_dict(orient="records")
            columns = df.columns.tolist()

            return Response(
                {
                    "columns": columns,
                    "preview_data": preview_data,
                    "total_rows": len(df),
                    "file_name": excel_file.name,
                    "message": f"Preview of {excel_file.name} - showing first 10 rows of {len(df)} total rows",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Error reading file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ImportExcelExtraInfoView(APIView):
    """API endpoint for estimators to import/view/delete Excel/CSV data for blueprints"""

    permission_classes = [permissions.IsAuthenticated, IsEstimator]

    REQUIRED_COLUMNS = ["CSI Division", "Description", "Unit", "Quantity", "Notes"]

    def get(self, request, blueprint_id):
        try:
            blueprint = BlueprintImage.objects.get(id=blueprint_id)
        except BlueprintImage.DoesNotExist:
            return Response(
                {"error": "Blueprint not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            extra_info = BlueprintExtraInfo.objects.get(blueprint=blueprint)
            serializer = BlueprintExtraInfoSerializer(extra_info)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BlueprintExtraInfo.DoesNotExist:
            return Response(
                {"error": "No CSV data found for this blueprint."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def _validate_headers(self, df):
        df_cols = [str(c).strip().lower() for c in df.columns]
        required = [c.strip().lower() for c in self.REQUIRED_COLUMNS]

        missing = [col for col in required if col not in df_cols]

        if missing:
            return False, missing
        return True, None

    @transaction.atomic
    def post(self, request, blueprint_id):
        try:
            blueprint = BlueprintImage.objects.get(id=blueprint_id)
        except BlueprintImage.DoesNotExist:
            return Response(
                {"error": "Blueprint not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        excel_file = request.FILES.get("excel_file")
        if not excel_file:
            return Response(
                {"error": "Excel file is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not excel_file.name.lower().endswith((".xlsx", ".xls", ".xlsm", ".csv")):
            return Response(
                {
                    "error": "Only Excel files (.xls, .xlsx, .xlsm) or CSV files (.csv) are allowed."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if BlueprintExtraInfo.objects.filter(blueprint=blueprint).exists():
            return Response(
                {"error": "Excel data already uploaded for this blueprint."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Read the file into a DataFrame
        try:
            if excel_file.name.lower().endswith(".csv"):
                try:
                    df = pd.read_csv(excel_file, keep_default_na=True)
                except UnicodeDecodeError:
                    df = pd.read_csv(
                        excel_file, encoding="ISO-8859-1", keep_default_na=True
                    )
            else:
                if excel_file.name.lower().endswith((".xlsx", ".xlsm")):
                    df = pd.read_excel(excel_file, engine="openpyxl")
                else:
                    df = pd.read_excel(excel_file, engine="xlrd")

            if df.empty:
                return Response(
                    {"error": "File is empty or contains no data."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            df = clean_dataframe_for_json(df)

            # Validate headers
            is_valid, missing = self._validate_headers(df)
            if not is_valid:
                return Response(
                    {
                        "error": "Invalid Excel/CSV format.",
                        "missing_columns": missing,
                        "required_columns": self.REQUIRED_COLUMNS,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            excel_data = df.to_dict(orient="records")

        except Exception as e:
            return Response(
                {"error": f"Error reading file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        extra_info = BlueprintExtraInfo.objects.create(
            blueprint=blueprint,
            csv_data=excel_data,
            imported_by=request.user,
        )

        serializer = BlueprintExtraInfoSerializer(extra_info)
        return Response(
            {"message": "File data uploaded successfully.", "data": serializer.data},
            status=status.HTTP_201_CREATED,
        )

    @transaction.atomic
    def delete(self, request, blueprint_id):
        try:
            blueprint = BlueprintImage.objects.get(id=blueprint_id)
        except BlueprintImage.DoesNotExist:
            return Response(
                {"error": "Blueprint not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            extra_info = BlueprintExtraInfo.objects.get(blueprint=blueprint)
            extra_info.delete()

            return Response(
                {"message": "CSV data deleted successfully."},
                status=status.HTTP_200_OK,
            )
        except BlueprintExtraInfo.DoesNotExist:
            return Response(
                {"error": "No CSV data found for this blueprint."},
                status=status.HTTP_404_NOT_FOUND,
            )
