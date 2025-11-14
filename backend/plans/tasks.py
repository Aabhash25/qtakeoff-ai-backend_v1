from celery import shared_task
from .models import Blueprint, BlueprintImage, Status
from users.models import CustomUser, Role
from annotations.models import Annotation
from annotations.serializers import AnnotationSerializer
from PIL import Image
from pdf2image import convert_from_bytes
from io import BytesIO
from django.core.files.base import ContentFile
from .utils import get_model, compute_sqft, polygon_dimension
from django.core.exceptions import PermissionDenied
import traceback
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import traceback
import json
import gc
from PyPDF2 import PdfReader # type: ignore
import psutil
import os
Image.MAX_IMAGE_PIXELS = None

from .extract_scale import extract_scale_from_image_subprocess, is_pdf_file_bytes, is_image_file_bytes

def log_memory_usage(note=""):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / 1024 / 1024
    print(f"[MEMORY] {note} - RAM usage: {mem:.2f} MB")


@shared_task(name='process_blueprint')
def process_blueprint_file(blueprint_id):
    try:
        blueprint = Blueprint.objects.get(id=blueprint_id)
        blueprint.status = Status.PROCESSING
        blueprint.save()

        if not blueprint.pdf_file:
            raise ValueError("No file found for the blueprint.")

        file = blueprint.pdf_file
        file.open()
        file_bytes = file.read()
        file.close()

        if is_pdf_file_bytes(file_bytes):
            reader = PdfReader(BytesIO(file_bytes))
            total_pages = len(reader.pages)
            process_pdf_sequentially(file_bytes, blueprint, total_pages)

        elif is_image_file_bytes(file_bytes):
            img = Image.open(BytesIO(file_bytes))
            process_page_image(img, idx=1, blueprint=blueprint)
            img.close()

        else:
            raise ValueError("Unsupported file format. Only PDFs and image files are allowed.")

        del file_bytes
        gc.collect()

        blueprint.status = Status.COMPLETE
        blueprint.save()
        return blueprint.id

    except Exception as e:
        print(f"[ERROR] Failed to process blueprint: {e}")
        traceback.print_exc()
        if 'blueprint' in locals():
            blueprint.status = Status.FAILED
            blueprint.save()
        return {"status": "error", "message": str(e)}

    finally:
        gc.collect()


def process_pdf_sequentially(file_bytes, blueprint, total_pages):
    for page_number in range(1, total_pages + 1):
        try:
            images = convert_from_bytes(
                file_bytes, dpi=300,
                first_page=page_number, last_page=page_number
            )
            for img in images:
                process_page_image(img, idx=page_number, blueprint=blueprint)
                img.close()
            print(f"[INFO] Processed page {page_number}")
        except Exception as e:
            print(f"[ERROR] Page {page_number} failed: {e}")
        finally:
            gc.collect()
            log_memory_usage(f"After processing page {page_number}")


def process_page_image(image, idx, blueprint):
    try:
        buffer = BytesIO()

        # Extract scale (before any conversion)
        scale = extract_scale_from_image_subprocess(image)

        # Ensure image is in RGB mode
        image = image.convert("RGB")

        # Optional: keep full resolution for accurate annotation prediction
        resized = image  # No resizing for max quality

        # Determine DPI
        dpi_tuple = image.info.get('dpi')
        raw_dpi = dpi_tuple[0] if dpi_tuple else 300
        dpi = round(raw_dpi)

        # Save to in-memory buffer
        resized.save(buffer, format='JPEG', quality=85)
        image_file = ContentFile(buffer.getvalue(), name=f"{blueprint.title}_page_{idx}.jpg")
        image_title = f"{blueprint.title} - Page {idx}"

        # Save to database
        BlueprintImage.objects.create(
            title=image_title,
            blueprint=blueprint,
            image=image_file,
            dpi=dpi,
            scale=scale,
        )

        print(f"[INFO] Stored page {idx}")
    except Exception as e:
        print(f"[ERROR] Failed to process page {idx}: {e}")
        traceback.print_exc()
    finally:
        buffer.close()
        del buffer
        del image
        gc.collect()

@shared_task(name='create_annotation')
def async_create_annotation(blueprint_id, user_id):
    # sourcery skip: low-code-quality
    try:
        blueprint_images = BlueprintImage.objects.get(id=blueprint_id)
        user = CustomUser.objects.get(id=user_id)
        if not user.is_authenticated or user.role != Role.ESTIMATOR:
            raise PermissionDenied("You do not have permission to create annotation")
        existing_annotations = Annotation.objects.filter(blueprint=blueprint_images)
        if existing_annotations.exists():
            print("Returning Existing Annotation!")
            return blueprint_id

        scale = blueprint_images.scale
        dpi = blueprint_images.dpi
        model = get_model()

        if not blueprint_images.image:
            raise ValueError("No image is found for this blueprint!")
        blueprint_image = Image.open(blueprint_images.image)
        if blueprint_image is not None:
            results = model.predict(
                blueprint_image,
                save=True,
                # boxes=False,
                # show_labels=False,
                # show_conf=True,
                project="room_predictions",
                name="test",
                exist_ok=True
            )
            masks = results[0].masks
            if masks is None:
                raise ValueError("No segmentation masks found.")

            height, width = results[0].orig_img.shape[:2]
            shapes = []
            for i, poly in enumerate(masks.xy):
                class_id = int(masks.cls[i].item()) if hasattr(masks, "cls") and masks.cls is not None \
                    else int(results[0].boxes[i].cls.item())
                label = model.names[class_id]
                confidence = (
                    float(results[0].probs[i].item()) if results[0].probs and len(results[0].probs) > i
                    else float(results[0].boxes[i].conf.item()) if hasattr(results[0].boxes[i], "conf")
                    else None
                )

                temp_mask = np.zeros((height, width), dtype=np.uint8)
                poly_int = np.array([poly], dtype=np.int32)
                cv2.fillPoly(temp_mask, poly_int, 255)
                eroded = cv2.erode(temp_mask, np.ones((3, 3), np.uint8), iterations=1)
                contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if not contours:
                    continue

                contour = max(contours, key=cv2.contourArea)
                epsilon = 0.01 * cv2.arcLength(contour, True)
                simplified = cv2.approxPolyDP(contour, epsilon, True)
                new_points = np.round(simplified.reshape(-1, 2).astype(float), 2).tolist()

                area = compute_sqft(new_points, dpi, scale)
                width_ft, height_ft = polygon_dimension(new_points, dpi, scale)

                shapes.append({
                    "label": label,
                    "points": new_points,
                    "confidence_score": confidence,
                    "measurement": area,
                    "width": width_ft,
                    "height": height_ft,
                    "group_id": None,
                    "shape_type": "polygon",
                    "flags": {}
                })
            for shape in shapes:
                data = {
                    'blueprint': blueprint_images.id,
                    'label': shape["label"],
                    'coordinates': shape["points"],
                    'area': shape["measurement"],
                    'annotation_type': shape["shape_type"],
                    'height': shape["height"],
                    'width': shape["width"],
                    'confidence_score': shape["confidence_score"],
                }
                serializer = AnnotationSerializer(data=data)
                if serializer.is_valid(raise_exception=True):
                    serializer.save()

                else:
                    print("Invalid Shape Data: ", serializer.data)
            json_data = {
                "version": "4.5.6",
                "flags": {},
                "shapes": shapes,
                "imagePath": blueprint_images.title,
                "imageData": None,
                "imageHeight": blueprint_image.height,
                "imageWidth": blueprint_image.width,
            }
            json_str = json.dumps(json_data, indent=4)
            file_io = BytesIO()
            file_io.write(json_str.encode('utf-8'))
            file_io.seek(0)

            # Save to the FileField on the model
            filename = f"{blueprint_images.title}_floor_annotation.json"
            blueprint_images.floor_json_file.save(filename, ContentFile(file_io.read()))
            blueprint_images.save()
            blueprint_image.close()
            del json_str, json_data, shapes, results, file_io, blueprint_image
            gc.collect()
            return blueprint_id

    except BlueprintImage.DoesNotExist:
        return {
            'status': 'error',
            'message': f"Blueprint with ID {blueprint_id} not found"
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f"Unexpected error: {str(e)}",
            'trace': traceback.format_exc()
        }
    finally:
        gc.collect()