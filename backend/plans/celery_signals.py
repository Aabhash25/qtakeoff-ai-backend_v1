from celery.signals import worker_ready
from .utils import get_model


def preload_models(**kwargs):
    print("Preloading Annotation AI models in Celery worker")
    
    get_model()
    import torch
    print("CUDA available:", torch.cuda.is_available())
    print("CUDA version:", torch.version.cuda)
    print("Device name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU only")

worker_ready.connect(preload_models)
