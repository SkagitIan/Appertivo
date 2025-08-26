"""Helpers to remove specials from various distribution platforms."""
from __future__ import annotations

from app.models import Connection, Special
from app.integrations import google


def remove_special_from_distributions(special: Special) -> None:
    """Remove a special from all connected distribution channels."""
    connections = Connection.objects.filter(user=special.user, is_connected=True)
    for conn in connections:
        if conn.platform == "google_business":
            google.remove_special(special, connection=conn)
        # Future platforms (POS, delivery apps, etc.) can be handled here.
