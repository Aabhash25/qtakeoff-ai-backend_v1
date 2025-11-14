import os
from ultralytics import YOLO
import numpy as np
import threading

_model_instance = None
_model_lock = threading.Lock()

def get_model():
    global _model_instance
    if _model_instance is None:
        with _model_lock:
            if _model_instance is None:
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                _model_path = os.path.join(BASE_DIR, 'models', 'room_best.pt')
                _model_instance = YOLO(_model_path)
                print("Model task:", _model_instance.task)
    return _model_instance

def compute_sqft(points, dpi, scale):
    points = np.round(points).astype(int)
    x = points[:, 0]
    y = points[:, 1]
    pixel_area = 0.5 * np.abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    scale_inch = scale
    inch_per_pixel = 1 / dpi
    feet_per_pixel = inch_per_pixel / scale_inch
    pixel_square = feet_per_pixel ** 2
    area_sqft = pixel_area * pixel_square
    return area_sqft

def polygon_dimension(points, dpi, scale):
    points = np.round(points).astype(int)
    x = points[:, 0]
    y = points[:, 1]
    width_px = x.max() - x.min()
    height_px = y.max() - y.min()
    inch_per_pixel = 1 / dpi
    feet_per_pixel = inch_per_pixel / scale
    width_sqft = width_px * feet_per_pixel
    height_sqft = height_px * feet_per_pixel
    return round(width_sqft, 2), round(height_sqft, 2)