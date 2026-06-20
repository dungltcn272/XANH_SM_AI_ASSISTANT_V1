"""Backward-compatible import path for the assistant NLU classifier.

The classifier now lives in ``app.nlu.classifier`` because it owns intent,
memory-candidate extraction, and query rewriting rather than RAG retrieval.
Keep this wrapper so older admin/eval imports continue to work.
"""

from app.nlu.classifier import XanhSMClassifier

__all__ = ["XanhSMClassifier"]
