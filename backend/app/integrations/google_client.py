from __future__ import annotations

import logging

from app.config.settings import settings


logger = logging.getLogger(__name__)


def verify_google_credential(token: str) -> dict | None:
    if not settings.GOOGLE_CLIENT_ID or settings.GOOGLE_CLIENT_ID == "your-google-client-id-here":
        logger.warning("Google credential verification skipped because GOOGLE_CLIENT_ID is not configured")
        return None
    try:
        from google.auth.transport import requests
        from google.oauth2 import id_token
    except ModuleNotFoundError as exc:
        logger.warning("Google auth libraries are not installed: %s", exc)
        return None
    try:
        payload = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_CLIENT_ID)
    except ValueError as exc:
        logger.warning("Google credential rejected: %s", exc)
        return None
    except Exception as exc:
        logger.warning("Google credential verification failed: %s", exc)
        return None
    if not payload.get("sub"):
        return None
    return {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name") or payload.get("email") or "Google User",
        "picture": payload.get("picture"),
        "email_verified": payload.get("email_verified"),
    }
