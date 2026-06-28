from __future__ import annotations


SENSITIVE_ACTIONS = {"payment_stub", "promotion_advisor", "booking_create"}


def needs_confirmation(tool_name: str) -> bool:
    return tool_name in SENSITIVE_ACTIONS
