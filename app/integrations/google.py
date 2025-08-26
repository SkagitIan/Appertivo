"""Google Business Profile integration helpers."""

from __future__ import annotations

from typing import Any, Dict, Tuple, List, Optional
from datetime import datetime
from urllib.parse import urlencode
import logging
import os
import requests

from django.conf import settings
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(*args, **kwargs):
        return False

from app.models import Connection

load_dotenv()
logger = logging.getLogger(__name__)

# --- OAuth and API constants ---
AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
API_BASE_URL = "https://mybusiness.googleapis.com/v4"
SCOPES = ["https://www.googleapis.com/auth/business.manage"]

REDIRECT_URI = "https://appertivo.com/dashboard"  # must match Google console


# ------------------------------------------------------------------------------
# OAuth flow
# ------------------------------------------------------------------------------

def get_authorization_url(state: Optional[str] = None) -> str:
    """Return the URL to begin the Google OAuth flow."""
    params = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "include_granted_scopes": "true",
        "prompt": "consent",
    }
    if state:
        params["state"] = state
    url = f"{AUTH_ENDPOINT}?{urlencode(params)}"
    logger.info("Generated Google OAuth URL with state=%s", state)
    return url


def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
    """Exchange an authorization code for access and refresh tokens."""
    data = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }
    response = requests.post(TOKEN_ENDPOINT, data=data, timeout=10)
    logger.info("Exchanged code for tokens; status=%s", response.status_code)
    return response.json()


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """Use a refresh token to obtain a new access token."""
    data = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
    }
    try:
        response = requests.post(TOKEN_ENDPOINT, data=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        new_token = result.get("access_token")
        if new_token:
            logger.info("Successfully refreshed Google access token")
            return new_token
        else:
            logger.error("Failed to refresh token: %s", result)
            return None
    except Exception as exc:
        logger.exception("Error refreshing Google token: %s", exc)
        return None


# ------------------------------------------------------------------------------
# Google API helpers
# ------------------------------------------------------------------------------

def _date_dict(dt) -> Dict[str, int]:
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    return {"year": dt.year, "month": dt.month, "day": dt.day}

ACCOUNT_MGMT_URL = "https://mybusinessaccountmanagement.googleapis.com/v1"
BUSINESS_INFO_URL = "https://mybusinessbusinessinformation.googleapis.com/v1"
def get_accounts_and_locations(access_token: str) -> Tuple[str, str, List[Dict[str, Any]], Dict[str, Any]]:
    """Return account and location details for the authenticated user."""
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        # --- Get Accounts ---
        resp = requests.get(f"{ACCOUNT_MGMT_URL}/accounts", headers=headers, timeout=10)
        logger.debug("Accounts API raw response [%s]: %s", resp.status_code, resp.text[:500])

        if resp.status_code != 200:
            logger.error("Failed to fetch accounts: %s", resp.text)
            return "", "", [], {}

        accounts_resp = resp.json()
        accounts = accounts_resp.get("accounts", [])
        if not accounts:
            logger.warning("No Google accounts found for this user")
            return "", "", [], {}

        account = accounts[0]
        account_resource_name = account["name"]   # e.g. "accounts/123456"
        account_id = account_resource_name.split("/")[1]
        account_name = account.get("accountName") or account.get("name")

        # --- Get Locations ---
        read_mask = "name,title,websiteUri,latlng,profile,metadata"
        loc_url = f"{BUSINESS_INFO_URL}/{account_resource_name}/locations?readMask={read_mask}"
        print(loc_url)
        loc_resp = requests.get(loc_url, headers=headers, timeout=10)
        logger.debug("Locations API raw response [%s]: %s", loc_resp.status_code, loc_resp.text[:500])

        if loc_resp.status_code != 200:
            logger.error("Failed to fetch locations for %s: %s", account_id, loc_resp.text)
            return account_id, account_name, [], {}

        locations_resp = loc_resp.json()
        locations: List[Dict[str, Any]] = []
        for loc in locations_resp.get("locations", []):
            loc_name = loc["name"]   # e.g. "accounts/123456/locations/654321"
            loc_id = loc_name.split("/")[-1]
            locations.append(
                {
                    "id": loc_id,
                    "name": loc.get("title", loc_id) or loc.get("storeCode", loc_id),
                    "address": loc.get("address", {}),
                    "primaryPhone": loc.get("primaryPhone", ""),
                }
            )

        logger.info("Found %d Google locations for account %s", len(locations), account_id)
        return account_id, account_name, locations, locations_resp

    except Exception as exc:
        logger.exception("Exception while fetching accounts/locations: %s", exc)
        return "", "", [], {}


# ------------------------------------------------------------------------------
# Persistence
# ------------------------------------------------------------------------------

def complete_google_auth(user, code: str) -> Optional[Connection]:
    """Finish OAuth flow: exchange code, fetch accounts/locations, save Connection."""
    tokens = exchange_code_for_tokens(code)
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")

    if not access_token:
        logger.error("Google token exchange failed: %s", tokens)
        return None

    account_id, account_name, locations, raw_locations = get_accounts_and_locations(access_token)

    conn, _ = Connection.objects.update_or_create(
        user=user,
        platform="google_business",
        defaults={
            "is_connected": True,
            "settings": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "account_id": account_id,
                "account_name": account_name,
                "locations": locations,  # persist all locations
                "locations_raw": raw_locations,
                "location_id": None,
            },
        },
    )
    logger.info("Saved Google connection for user=%s account=%s", user, account_id)
    return conn

# ------------------------------------------------------------------------------
# Posting specials (using legacy v4 localPosts API)
# ------------------------------------------------------------------------------
def publish_special(special: Any, location_id: Optional[str] = None) -> None:
    """Post a special to Google Business Profile as an Offer post (v4 API)."""
    try:
        connection = Connection.objects.get(
            user=special.user, platform="google_business", is_connected=True
        )
    except Connection.DoesNotExist:
        logger.warning("No Google connection found for user %s", special.user)
        return

    settings_data = connection.settings or {}
    access_token = settings_data.get("access_token")
    refresh_token = settings_data.get("refresh_token")
    account_id = settings_data.get("account_id")

    # allow override from user selection
    location_id = location_id or settings_data.get("location_id")
    if not (access_token and account_id and location_id):
        logger.warning("Missing Google credentials for user %s; cannot publish", special.user)
        return

    # Refresh token if needed
    if refresh_token and not access_token:
        new_token = refresh_access_token(refresh_token)
        if new_token:
            access_token = new_token
            settings_data["access_token"] = new_token
            connection.settings = settings_data
            connection.save(update_fields=["settings"])

    parent = f"accounts/{account_id}/locations/{location_id}"
    url = f"https://mybusiness.googleapis.com/v4/{parent}/localPosts"
    logger.info("Posting special to Google (v4) for location %s", location_id)

    # --- Build payload ---
    payload: Dict[str, Any] = {
    "summary": special.description or special.title,
    "languageCode": "en-US",
    "callToAction": {
        "actionType": "ORDER" if getattr(special, "cta_type", "").upper() == "ORDER" else "LEARN_MORE",
        "url": getattr(special, "cta_url", ""),
    },
    }

    if getattr(special, "start_date", None) and getattr(special, "end_date", None):
        # Treat as EVENT post
        payload["topicType"] = "EVENT"
        payload["event"] = {
            "title": special.title,
            "schedule": {
                "startDate": _date_dict(special.start_date),
                "endDate": _date_dict(special.end_date),
            },
        }
    else:
        # Default to OFFER post
        payload["topicType"] = "OFFER"
        payload["offer"] = {
            "couponCode": getattr(special, "coupon_code", ""),
            "redeemOnlineUrl": getattr(special, "cta_url", ""),
            "termsConditions": getattr(special, "terms_conditions", ""),
        }

    # Optional image
    if getattr(special, "image_url", None):
        payload["media"] = [
            {"mediaFormat": "PHOTO", "sourceUrl": special.image_url}
        ]


    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code >= 400:
            logger.error("Google publish failed %s: %s", response.status_code, response.text)
        else:
            data = response.json()
            logger.info("Successfully published special to Google: %s", data)
            post_name = data.get("name")
            if post_name and hasattr(special, "google_post_name"):
                setattr(special, "google_post_name", post_name)
                try:
                    special.save(update_fields=["google_post_name"])
                except Exception:
                    logger.exception("Unable to save google_post_name for %s", special)
    except Exception as exc:
        logger.exception("Failed to publish special to Google: %s", exc)

<<<<<<< HEAD
=======

def remove_special(special: Any, connection: Optional[Connection] = None) -> None:
    """Delete a previously published special from Google Business Profile."""
    try:
        if connection is None:
            connection = Connection.objects.get(user=special.user, platform="google_business", is_connected=True)
    except Connection.DoesNotExist:
        logger.warning("No Google connection found for user %s", special.user)
        return

    settings_data = connection.settings or {}
    access_token = settings_data.get("access_token")
    post_name = getattr(special, "google_post_name", None)
    if not (access_token and post_name):
        logger.warning("Missing Google data; cannot remove special for user %s", special.user)
        return

    url = f"{API_BASE_URL}/{post_name}"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        response = requests.delete(url, headers=headers, timeout=10)
        if response.status_code >= 400:
            logger.error("Google removal failed %s: %s", response.status_code, response.text)
        else:
            logger.info("Removed Google post %s", post_name)
    except Exception as exc:
        logger.exception("Failed to remove special from Google: %s", exc)
>>>>>>> ab66825a2a1ac99335d10c8a103203825ceae349
