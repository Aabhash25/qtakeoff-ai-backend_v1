from django.utils.translation import gettext_lazy as _
from .base import *
from decouple import config


ALLOWED_HOSTS = ['127.0.0.1', 'localhost']


CORS_ALLOWED_ORIGINS = []

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True


FRONTEND_URL = config('FRONTEND_URL')


