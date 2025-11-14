from django.utils.translation import gettext_lazy as _
from .base import *

ALLOWED_HOSTS = ['localhost','127.0.0.1']



CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8000",
]


CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

FRONTEND_URL = config('FRONTEND_URL')
