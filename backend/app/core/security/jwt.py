from __future__ import annotations

import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Any

from fastapi.security import OAuth2PasswordBearer

from app.config.settings import settings

try:
    from jose import jwt as jose_jwt
except ModuleNotFoundError:
    jose_jwt = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False)


def _b64encode(payload: bytes) -> str:
    return base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")


def _b64decode(payload: str) -> bytes:
    padding = "=" * (-len(payload) % 4)
    return base64.urlsafe_b64decode(payload + padding)


def _sign(payload: str) -> str:
    digest = hmac.new(settings.SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return _b64encode(digest)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {**data, "exp": int(expire.timestamp())}
    if jose_jwt is not None:
        return jose_jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    encoded_payload = _b64encode(json.dumps(payload, separators=(",", ":"), default=str).encode("utf-8"))
    return f"dev.{encoded_payload}.{_sign(encoded_payload)}"


def decode_access_token(token: str) -> dict[str, Any]:
    if jose_jwt is not None:
        return jose_jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    prefix, encoded_payload, signature = token.split(".", 2)
    if prefix != "dev" or not hmac.compare_digest(signature, _sign(encoded_payload)):
        raise ValueError("Invalid token")
    payload = json.loads(_b64decode(encoded_payload))
    if int(payload.get("exp", 0)) < int(datetime.utcnow().timestamp()):
        raise ValueError("Expired token")
    return payload
