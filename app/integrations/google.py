"""Google Business Profile integration helpers."""

from __future__ import annotations

from typing import Any, Dict, Tuple, List
from datetime import datetime
from urllib.parse import urlencode
import logging
import os
import requests
from django.conf import settings
from dotenv import load_dotenv
load_dotenv()
from app.models import Connection

logger = logging.getLogger(__name__)

AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
SCOPES = ["https://www.googleapis.com/auth/business.manage"]
API_BASE_URL = "https://mybusiness.googleapis.com/v4"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

def get_authorization_url(state: str | None = None) -> str:
    """Return the URL to begin the Google OAuth flow."""
    params = {
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "redirect_uri": "https://appertivo.com/dashboard",
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
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return {"year": dt.year, "month": dt.month, "day": dt.day}


def publish_special(special: Any) -> None:
    """Post a special to Google Business Profile as an Offer post."""
    logger.info("Attempting to publish special to Google for user %s", special.user)
    try:
        connection = Connection.objects.get(
            user=special.user, platform="google_business", is_connected=True
        )
    except Connection.DoesNotExist:  # pragma: no cover - defensive
        logger.warning("No Google connection found for user %s", special.user)
        return

    settings_data = connection.settings or {}
    access_token = settings_data.get("access_token")
    account_id = settings_data.get("account_id")
    location_id = settings_data.get("location_id")
    if not (access_token and account_id and location_id):
        logger.warning(
            "Missing Google credentials for user %s; cannot publish", special.user
        )
        return

    parent = f"accounts/{account_id}/locations/{location_id}"
    url = f"{API_BASE_URL}/{parent}/localPosts?key={settings.GOOGLE_API_KEY}"
    logger.info("Posting special to Google for location %s", location_id)

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
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        logger.info(
            "Google response %s: %s", response.status_code, response.text
        )
    except Exception as exc:  # pragma: no cover - network failure shouldn't crash
        logger.exception("Failed to publish special to Google: %s", exc)
        return


def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """Exchange an authorization code for access and refresh tokens."""
    data = {
        "client_id": os.getenv('GOOGLE_CLIENT_ID'),
        "client_secret": os.getenv('GOOGLE_CLIENT_SECRET'),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "https://appertivo.com/dashboard/",
    }
    response = requests.post(TOKEN_ENDPOINT, data=data, timeout=10)
    return response.json()


def get_accounts_and_locations(access_token: str) -> Tuple[str, List[Dict[str, str]]]:
    """Return account ID and all available locations for the authenticated user."""
    logger.info("Fetching Google accounts and locations")
    headers = {"Authorization": f"Bearer {access_token}"}
    accounts = requests.get(
        f"{API_BASE_URL}/accounts", headers=headers, timeout=10
    ).json()
    account_name = accounts["accounts"][0]["name"]
    account_id = account_name.split("/")[1]
    locations_resp = requests.get(
        f"{API_BASE_URL}/{account_name}/locations", headers=headers, timeout=10
    ).json()
    locations: List[Dict[str, str]] = []
    for loc in locations_resp.get("locations", []):
        loc_name = loc["name"]
        loc_id = loc_name.split("/")[-1]
        locations.append({"id": loc_id, "name": loc.get("title", loc_id)})
    logger.info("Found %d Google locations for account %s", len(locations), account_id)
    if not locations:
        logger.warning("No Google locations found for account %s", account_id)
    return account_id, locations
