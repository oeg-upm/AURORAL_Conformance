from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.db.models.signals import post_migrate


class ValidationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "validation"


