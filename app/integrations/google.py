"""Google Business Profile integration helpers."""

from __future__ import annotations

from typing import Any, Dict, Tuple
from urllib.parse import urlencode

import requests
from django.conf import settings

from app.models import Connection

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
        connection = Connection.objects.get(
            user=special.user, platform="google_business", is_connected=True
        )
    except Connection.DoesNotExist:  # pragma: no cover - defensive
        return

    settings_data = connection.settings or {}
    access_token = settings_data.get("access_token")
    account_id = settings_data.get("account_id")
    location_id = settings_data.get("location_id")
    if not (access_token and account_id and location_id):
        return

    parent = f"accounts/{account_id}/locations/{location_id}"
    url = f"{API_BASE_URL}/{parent}/localPosts?key={settings.GOOGLE_API_KEY}"

    payload: Dict[str, Any] = {
        "summary": special.description or special.title,
        "languageCode": "en-US",
        "topicType": "OFFER",
        "callToAction": {
            "actionType": "LEARN_MORE",
            "url": getattr(special, "cta_url", ""),
        },
        "offer": {
            "couponCode": "",
            "redeemOnlineUrl": getattr(special, "cta_url", ""),
            "termsConditions": "",
        },
    }
    if getattr(special, "start_date", None):
        payload["offer"]["startDate"] = _date_dict(special.start_date)
    if getattr(special, "end_date", None):
        payload["offer"]["endDate"] = _date_dict(special.end_date)

    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        requests.post(url, headers=headers, json=payload, timeout=10)
    except Exception:  # pragma: no cover - network failure shouldn't crash
        return


TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """Exchange an authorization code for access and refresh tokens."""
    data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }
    response = requests.post(TOKEN_ENDPOINT, data=data, timeout=10)
    return response.json()


def get_account_and_location(access_token: str) -> Tuple[str, str]:
    """Return the first account and location IDs for the authenticated user."""
    headers = {"Authorization": f"Bearer {access_token}"}
    accounts = requests.get(f"{API_BASE_URL}/accounts", headers=headers, timeout=10).json()
    account_name = accounts["accounts"][0]["name"]
    account_id = account_name.split("/")[1]
    locations = requests.get(f"{API_BASE_URL}/{account_name}/locations", headers=headers, timeout=10).json()
    location_name = locations["locations"][0]["name"]
    location_id = location_name.split("/")[-1]
    return account_id, location_id
