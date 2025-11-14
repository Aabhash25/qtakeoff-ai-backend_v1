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
    # Replace inf and -inf with NaN first
    df = df.replace([np.inf, -np.inf], np.nan)

    # Convert all columns to handle NaN properly
    for col in df.columns:
        # Check if column has numeric data
        if df[col].dtype in ["float64", "float32", "int64", "int32"]:
            # Replace NaN with None
            df[col] = df[col].apply(
                lambda x: (
                    None
                    if pd.isna(x)
                    or (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))
                    else x
                )
            )
        else:
            # For non-numeric columns, replace NaN with None or empty string
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

    @staticmethod
    def _has_changed(old, new, tol=0.01):
        if old is None or new is None:
            return old != new
        return abs(float(old) - float(new)) > tol

    @staticmethod
    @transaction.atomic
    def _recalculate_all(image: BlueprintImage, dpi: float, scale: float) -> None:
        for ann in Annotation.objects.filter(blueprint=image):
            pts = np.asarray(ann.coordinates)
            ann.area = compute_sqft(pts, dpi, scale)
            ann.width, ann.height = polygon_dimension(pts, dpi, scale)
            ann.save(update_fields=["area", "width", "height"])
        for wall in WallAnnotation.objects.filter(blueprint=image):
            pts = np.asarray(wall.coordinates)
            wall.length_ft, wall.thickness_ft = compute_wall_dimensions(pts, dpi, scale)
            print(wall.length_ft, wall.thickness_ft)
            wall.save(update_fields=["length_ft", "thickness_ft"])
        for windowanddoors in WindowAndDoorAnnotation.objects.filter(blueprint=image):
            pts = np.asarray(windowanddoors.coordinates)
            windowanddoors.length_ft, windowanddoors.breadth_ft = (
                compute_wall_dimensions(pts, dpi, scale)
            )
            print(windowanddoors.length_ft, windowanddoors.breadth_ft)
            windowanddoors.save(update_fields=["length_ft", "breadth_ft"])

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

        chain(
            async_create_annotation.s(image.pk, request.user.id),
            async_create_wall_annotation.s(),
            async_create_window_and_door_annotation.s(),
        ).apply_async()

        return Response(
            {"message": "Blueprint Image Detail!", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def put(self, request, pk):
        image = self.get_object(pk)
        if not image:
            return Response(
                {"detail": "Image not found."}, status=status.HTTP_404_NOT_FOUND
            )

        self.check_object_permissions(request, image)

        old_scale, old_dpi = image.scale, image.dpi
        ser = BlueprintImageDetailSerializer(image, data=request.data, partial=True)

        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        ser.save()
        new_scale = ser.validated_data.get("scale", old_scale)
        new_dpi = ser.validated_data.get("dpi", old_dpi)

        annotations = list(Annotation.objects.filter(blueprint=image))
        walls = list(WallAnnotation.objects.filter(blueprint=image))
        windows_and_doors = list(
            WindowAndDoorAnnotation.objects.filter(blueprint=image)
        )

        if (
            self._has_changed(old_scale, new_scale)
            or self._has_changed(old_dpi, new_dpi)
        ) and (annotations or walls or windows_and_doors):
            self._recalculate_all(image, new_dpi, new_scale)
        return Response(
            {"message": "Image updated!", "data": ser.data},
            status=status.HTTP_200_OK,
        )


class SendVerifiedImageToCustomUser(APIView):
    permission_classes = [permissions.IsAuthenticated, IsEstimator]

    def post(self, request, blueprint_id):
        user = request.user
        print(user)
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
        """Preview Excel/CSV file data without saving"""
        try:
            excel_file = request.FILES.get("excel_file")
            if not excel_file:
                return Response(
                    {"error": "Excel file is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate file type
            if not excel_file.name.lower().endswith((".xlsx", ".xls", ".xlsm", ".csv")):
                return Response(
                    {
                        "error": "Only Excel files (.xls, .xlsx, .xlsm) or CSV files (.csv) are allowed."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Read file based on type
            if excel_file.name.lower().endswith(".csv"):
                try:
                    df = pd.read_csv(excel_file, keep_default_na=True)
                except UnicodeDecodeError:
                    df = pd.read_csv(
                        excel_file, encoding="ISO-8859-1", keep_default_na=True
                    )
            else:
                # Excel files
                if excel_file.name.lower().endswith((".xlsx", ".xlsm")):
                    df = pd.read_excel(excel_file, engine="openpyxl")
                else:  # .xls
                    df = pd.read_excel(excel_file, engine="xlrd")

            if df.empty:
                return Response(
                    {"error": "File contains no data."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Clean DataFrame thoroughly
            df = clean_dataframe_for_json(df)

            # Get preview data (first 10 rows)
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
            print(f"Error in PreviewExcelDataView: {e}")
            import traceback

            traceback.print_exc()
            return Response(
                {"error": f"Error reading file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ImportExcelExtraInfoView(APIView):
    """API endpoint for estimators to import/view/delete Excel/CSV data for blueprints"""

    permission_classes = [permissions.IsAuthenticated, IsEstimator]

    def get(self, request, blueprint_id):
        """Get existing Excel/CSV data for a blueprint"""
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

    @transaction.atomic
    def post(self, request, blueprint_id):
        """Import Excel/CSV data and save to BlueprintExtraInfo"""
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

        try:
            # Read file based on type
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
                else:  # .xls
                    df = pd.read_excel(excel_file, engine="xlrd")

            if df.empty:
                return Response(
                    {"error": "File is empty or contains no data."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Clean DataFrame thoroughly
            df = clean_dataframe_for_json(df)

            excel_data = df.to_dict(orient="records")

        except Exception as e:
            print(f"Error in ImportExcelExtraInfoView: {e}")
            import traceback

            traceback.print_exc()
            return Response(
                {"error": f"Error reading file: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Save data to BlueprintExtraInfo
        extra_info = BlueprintExtraInfo.objects.create(
            blueprint=blueprint,
            csv_data=excel_data,
            imported_by=request.user,
        )

        serializer = BlueprintExtraInfoSerializer(extra_info)
        return Response(
            {
                "message": "File data uploaded successfully.",
                "data": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )

    @transaction.atomic
    def delete(self, request, blueprint_id):
        """Delete existing Excel/CSV data for a blueprint"""
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
