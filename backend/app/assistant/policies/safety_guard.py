from __future__ import annotations


def is_safe_query(query: str) -> bool:
    blocked_terms = ("hack", "malware", "đánh cắp", "token")
    return not any(term in query.casefold() for term in blocked_terms)
