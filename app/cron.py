"""Scheduled tasks for the application."""
from django.utils import timezone

from app.models import Special
from app import distribution


def unpublish_expired_specials() -> None:
    """Unpublish specials whose end date has passed.

    For each special that is currently active and whose end date is in the past,
    mark it as expired and trigger removal from any connected distributions.
    """
    expired = Special.objects.filter(status="active", end_date__lt=timezone.now())
    for special in expired:
        special.status = "expired"
        special.save(update_fields=["status"])
        distribution.remove_special_from_distributions(special)
