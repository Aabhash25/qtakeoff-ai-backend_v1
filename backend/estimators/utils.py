import threading
import os
from ultralytics import YOLO
import numpy as np


_wall_model_instance = None
_window_and_door_model_instance = None
_floor_model_instance = None
_model_lock = threading.Lock()

def get_wall_model():
    global _wall_model_instance
    if _wall_model_instance is None:
        with _model_lock:
            if _wall_model_instance is None:
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                _model_path = os.path.join(BASE_DIR, 'models', 'wall.pt')
                _wall_model_instance = YOLO(_model_path)
                print("Model task:", _wall_model_instance.task)
    return _wall_model_instance

def get_window_and_door_model():
    global _window_and_door_model_instance
    if _window_and_door_model_instance is None:
        with _model_lock:
            if _window_and_door_model_instance is None:
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                _model_path = os.path.join(BASE_DIR, 'models', 'window_door_best.pt')
                _window_and_door_model_instance = YOLO(_model_path)
                print("Model task:", _window_and_door_model_instance.task)
    return _window_and_door_model_instance

# def get_floor_model():
#     global _floor_model_instance
#     if _floor_model_instance is None:
#         with _model_lock:
#             if _floor_model_instance is None:
#                 BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#                 _model_path = os.path.join(BASE_DIR, 'models', 'floor_best.pt')
#                 _floor_model_instance = YOLO(_model_path)
#                 print("Model task:", _floor_model_instance.task)
#     return _floor_model_instance


def compute_wall_dimensions(points, dpi, scale):
    points = np.round(points).astype(int)
    x = points[:, 0]
    y = points[:, 1]
    length_px = x.max() - x.min()
    thickness_px = y.max() - y.min()
    # pts = np.array(points, dtype=float)
    # d1 = np.linalg.norm(pts[0] - pts[1])
    # d2 = np.linalg.norm(pts[1] - pts[2])
    # length_px = max(d1, d2)
    # thickness_px = min(d1, d2)
    inch_per_pixel = 1 / dpi
    feet_per_pixel = inch_per_pixel / scale
    length_ft = length_px * feet_per_pixel
    thickness_ft = thickness_px * feet_per_pixel
    return float(round(length_ft, 2)), float(round(thickness_ft, 2))