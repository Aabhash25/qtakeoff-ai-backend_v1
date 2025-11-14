from celery import shared_task
from django.conf import settings
from plans.models import BlueprintImage
from PIL import Image
from .utils import get_wall_model, get_window_and_door_model
from annotations.serializers import WallAnnotationSerializer, WindowAndDoorAnnotationSerializer
import json
from django.core.files.base import ContentFile
from io import BytesIO
from annotations.models import WallAnnotation, WindowAndDoorAnnotation
from .utils import compute_wall_dimensions
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Attachment, FileContent, FileName, FileType, Disposition
from django.conf import settings
import gc
from plans.utils import compute_sqft, polygon_dimension
import numpy as np

@shared_task(name='estimator_request')
def send_estimator_request_email(image_path, submitted_by_email):
    subject = "New Blueprint Image Submitted"
    body = f"A new image has been submitted by {submitted_by_email} for annotation."

    try:
        with open(image_path, 'rb') as f:
            data = f.read()
            encoded_file = base64.b64encode(data).decode()

        attached_file = Attachment(
            FileContent(encoded_file),
            FileName(image_path.split('/')[-1]),
            FileType('application/octet-stream'), 
            Disposition('attachment')
        )

        message = Mail(
            from_email=Email(submitted_by_email), 
            to_emails=To(settings.DEFAULT_FROM_EMAIL),
            subject=subject,
            html_content=body
        )
        message.attachment = attached_file

        sg = SendGridAPIClient(settings.SEND_GRID_API_KEY)
        response = sg.send(message)
        print(f"SendGrid Response: {response.status_code}")
        return response.status_code == 202
    except Exception as e:
        print(f"Error sending email with SendGrid: {e}")
        return False

    
@shared_task(name='assigned_estimator')
def send_image_email_task_to_estimator(estimator_email, estimator_name, image_id):
    subject = "New Blueprint Assignment"
    message = f"""
        <p>Dear {estimator_name},</p>
        <p>You have been assigned a new blueprint to estimate.</p>
        <p><strong>Image ID:</strong> {image_id}</p>
        <p>Please log in to your dashboard to view the request.</p>
    """

    try:
        mail = Mail(
            from_email=Email(settings.EMAIL_HOST_USER), 
            to_emails=To(estimator_email),
            subject=subject,
            html_content=message
        )

        sg = SendGridAPIClient(settings.SEND_GRID_API_KEY)
        response = sg.send(mail)
        print(f"SendGrid Response: {response.status_code}")
        return f"Email sent to {estimator_email}" if response.status_code == 202 else f"SendGrid failed with status: {response.status_code}"
    except Exception as e:
        print(f"SendGrid error: {e}")
        return f"Failed to send email: {str(e)}"
    
@shared_task(name='send_email_to_user_after_annotation')
def send_email_to_user_after_annotation(estimator_email, owner_email):
    subject = "Your Annotated Blueprint Image"
    message = "Hi, find your verified annotated blueprint image attached."

    try:
        mail = Mail(
            from_email=Email(estimator_email), 
            to_emails=To(owner_email),
            subject=subject,
            plain_text_content=message
        )
        mail.reply_to = Email(estimator_email)

        sg = SendGridAPIClient(settings.SEND_GRID_API_KEY)
        response = sg.send(mail)
        print(f"SendGrid Response: {response.status_code}")
        return f"Email sent to {owner_email}" if response.status_code == 202 else f"SendGrid failed with status: {response.status_code}"
    except Exception as e:
        print(f"SendGrid error: {e}")
        return f"Failed to send email: {str(e)}"

@shared_task(name='create_wall_annotation')
def async_create_wall_annotation(blueprint_id):
    file_io = None
    blueprint_image = None

    try:
        blueprint_images = BlueprintImage.objects.get(id=blueprint_id)
        existing_annotations = WallAnnotation.objects.filter(blueprint=blueprint_images)
        if existing_annotations.exists():
            print("Returning Existing Wall Annotation!")
            return blueprint_id

        scale = blueprint_images.scale
        dpi = blueprint_images.dpi
        model = get_wall_model()
        blueprint_image = Image.open(blueprint_images.image)
        
        results = model.predict(
            blueprint_image,
            save=True,
            project="wall_predictions",
            name="test",
            exist_ok=True
        )

        shapes = []
        for pred in results:
            if hasattr(pred, "boxes") and pred.boxes is not None:
                for i, box in enumerate(pred.boxes.xyxy):
                    class_id = int(pred.boxes.cls[i].item())
                    label = model.names[class_id].split()[0]
                    x1, y1, x2, y2 = box.tolist()
                    points = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                    length_ft, thickness_ft = compute_wall_dimensions(points, dpi, scale)
                    area = compute_sqft(points, dpi, scale)

                    shapes.append({
                        "label": label,
                        "points": points,
                        'length': length_ft,
                        'area': area,
                        'thickness': thickness_ft,
                        "group_id": None,
                        "shape_type": "rectangle",
                        "flags": {}
                    })

        for shape in shapes:
            data = {
                'blueprint': blueprint_images.id,
                'label': str(shape['label']),
                'coordinates': shape['points'],
                'annotation_type': shape['shape_type'],
                'area': shape['area'],
                'length_ft': shape['length'],  # typo fix suggestion below
                'thickness_ft': shape['thickness'],
            }
            serializer = WallAnnotationSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()

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

        filename = f"{blueprint_images.title}_wall_annotation.json"
        blueprint_images.wall_json_file.save(filename, ContentFile(file_io.read()))
        blueprint_images.save()

        return blueprint_id

    finally:
        if file_io is not None:
            file_io.close()
            del file_io
        if blueprint_image is not None:
            blueprint_image.close()
            del blueprint_image
        gc.collect()
    

@shared_task(name="create_window_and_door_annotation")
def async_create_window_and_door_annotation(blueprint_id):
    file_io = None
    blueprint_image = None

    try:
        blueprint_images = BlueprintImage.objects.get(id=blueprint_id)
        existing_annotations = WindowAndDoorAnnotation.objects.filter(blueprint=blueprint_images)
        if existing_annotations.exists():
            print("Returning Existing Window and Door Annotation!")
            return blueprint_id

        model = get_window_and_door_model()
        scale = blueprint_images.scale
        dpi = blueprint_images.dpi
        blueprint_image = Image.open(blueprint_images.image)

        results = model.predict(
            blueprint_image,
            save=True,
            project="windows_and_doors_predictions",
            name="test",
            exist_ok=True
        )

        shapes = []
        for pred in results:
            if hasattr(pred, "boxes") and pred.boxes is not None:
                for i, box in enumerate(pred.boxes.xyxy):
                    class_id = int(pred.boxes.cls[i].item())
                    label = model.names[class_id]
                    x1, y1, x2, y2 = box.tolist()
                    points = [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
                    length_ft, breadth_ft = polygon_dimension(points, dpi, scale)
                    print(length_ft, breadth_ft)
                    shapes.append({
                        "label": label,
                        "points": points,
                        'length': length_ft,
                        'breadth': breadth_ft,
                        "group_id": None,
                        "shape_type": "rectangle",
                        "flags": {}
                    })

        for shape in shapes:
            data = {
                'blueprint': blueprint_images.id,
                'label': str(shape['label']),
                'coordinates': shape['points'],
                'annotation_type': shape['shape_type'],
                'length_ft': shape['length'],
                'breadth_ft': shape['breadth'],
            }
            serializer = WindowAndDoorAnnotationSerializer(data=data)
            if serializer.is_valid(raise_exception=True):
                serializer.save()

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

        filename = f"{blueprint_images.title}_window&door_annotation.json"
        blueprint_images.window_json_file.save(filename, ContentFile(file_io.read()))
        blueprint_images.save()

        return blueprint_id

    finally:
        if file_io is not None:
            file_io.close()
            del file_io
        if blueprint_image is not None:
            blueprint_image.close()
            del blueprint_image
        gc.collect()

# @shared_task(name="create_floor_annotation")
# def async_create_floor_annotation(blueprint_id):
#     file_io = None
#     blueprint_image = None

#     try:
#         blueprint_images = BlueprintImage.objects.get(id=blueprint_id)
#         existing_annotations = FloorAnnotation.objects.filter(blueprint=blueprint_images)
#         if existing_annotations.exists():
#             print("Returning Existing Floor Annotation!")
#             return blueprint_id

#         model = get_floor_model()
#         blueprint_image = Image.open(blueprint_images.image)

#         results = model.predict(
#             blueprint_image,
#             save=True,
#             project="floor_predictions",
#             name="test",
#             exist_ok=True
#         )

#         masks = results[0].masks
#         boxes = results[0].boxes
#         shapes = []

#         if masks is not None and boxes is not None and masks.xy:
#             for poly, cls_id in zip(masks.xy, boxes.cls.cpu().numpy().astype(int)):
#                 polygon = np.array(poly, dtype=np.int32)
#                 shapes.append({
#                     "label": "Floor",
#                     "points": polygon.tolist(),
#                     "group_id": None,
#                     "shape_type": "Polygon",
#                     "flags": {}
#                 })

#         for shape in shapes:
#             data = {
#                 'blueprint': blueprint_images.id,
#                 'label': str(shape['label']),
#                 'coordinates': shape['points'],
#                 'annotation_type': shape['shape_type'],
#             }
#             serializer = FloorAnnotationSerializer(data=data)
#             if serializer.is_valid(raise_exception=True):
#                 serializer.save()

#         json_data = {
#             "version": "4.5.6",
#             "flags": {},
#             "shapes": shapes,
#             "imagePath": blueprint_images.title,
#             "imageData": None,
#         }

#         json_str = json.dumps(json_data, indent=4)
#         file_io = BytesIO()
#         file_io.write(json_str.encode('utf-8'))
#         file_io.seek(0)

#         filename = f"{blueprint_images.title}_floor_annotation.json"
#         blueprint_images.floor_json_file.save(filename, ContentFile(file_io.read()))
#         blueprint_images.save()

#         return blueprint_id

#     finally:
#         if file_io is not None:
#             file_io.close()
#             del file_io
#         if blueprint_image is not None:
#             blueprint_image.close()
#             del blueprint_image
#         gc.collect()