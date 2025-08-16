"""Google Business Profile integration helpers."""

from __future__ import annotations

from typing import Any, Dict
from urllib.parse import urlencode

import requests
from django.conf import settings

from app.models import Integration

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
SCOPES = ["https://www.googleapis.com/auth/business.manage"]
API_BASE_URL = "https://mybusiness.googleapis.com/v4"


def get_authorization_url(state: str | None = None) -> str:
    """Return the URL to begin the Google OAuth flow."""
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
    }
    if state:
        params["state"] = state
    return f"{AUTH_ENDPOINT}?{urlencode(params)}"


def _date_dict(dt) -> Dict[str, int]:
    return {"year": dt.year, "month": dt.month, "day": dt.day}


def publish_special(special: Any) -> None:
    """Post a special to Google Business Profile as an Offer post."""
    try:
        integration = Integration.objects.get(
            user_profile=special.user_profile, provider="google", enabled=True
        )
    except Integration.DoesNotExist:  # pragma: no cover - defensive
        return

    if not (integration.access_token and integration.account_id and integration.location_id):
        return

    parent = f"accounts/{integration.account_id}/locations/{integration.location_id}"
    url = f"{API_BASE_URL}/{parent}/localPosts?key={settings.GOOGLE_API_KEY}"

    payload: Dict[str, Any] = {
        "summary": special.description or special.title,
        "languageCode": "en-US",
        "topicType": "OFFER",
        "callToAction": {
            "actionType": "LEARN_MORE",
            "url": special.order_url or special.mobile_order_url or "",
        },
        "offer": {
            "couponCode": "",
            "redeemOnlineUrl": special.order_url or special.mobile_order_url or "",
            "termsConditions": "",
        },
    }
    if special.start_date:
        payload["offer"]["startDate"] = _date_dict(special.start_date)
    if special.end_date:
        payload["offer"]["endDate"] = _date_dict(special.end_date)

    headers = {"Authorization": f"Bearer {integration.access_token}"}
    try:
        requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception:  # pragma: no cover - network failure shouldn't crash
        return
