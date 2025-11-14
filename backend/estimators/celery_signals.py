from celery.signals import worker_ready
from .utils import get_wall_model, get_window_and_door_model

def preload_models(**kwargs):
    print("Preloading Wall and Windows and Doors AI models in Celery worker")
    get_wall_model()
    get_window_and_door_model()

worker_ready.connect(preload_models)
