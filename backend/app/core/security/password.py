from __future__ import annotations

import hmac


def verify_plain_password(plain_password: str, expected_password: str) -> bool:
    return hmac.compare_digest(plain_password, expected_password)
