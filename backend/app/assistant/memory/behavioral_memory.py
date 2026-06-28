from __future__ import annotations


def build_behavioral_signal(*, signal_type: str, evidence: dict, confidence: float = 0.6) -> dict:
    return {
        "memory_type": "behavior",
        "source": "behavioral_signal",
        "signal_type": signal_type,
        "evidence_json": evidence,
        "confidence": max(0.0, min(1.0, confidence)),
    }
