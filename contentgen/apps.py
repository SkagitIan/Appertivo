"""App configuration for the content generation app."""
from django.apps import AppConfig

class ContentgenConfig(AppConfig):
    """Config for contentgen app."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "contentgen"
