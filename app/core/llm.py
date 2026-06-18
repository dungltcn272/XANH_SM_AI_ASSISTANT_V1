from __future__ import annotations

from typing import Any, Literal

import httpx
from openai import OpenAI

from app.core.config import settings

Provider = Literal["openai", "groq"]

shared_http_client = httpx.Client(
    timeout=httpx.Timeout(settings.OPENAI_TIMEOUT_SECONDS, read=120.0),
    limits=httpx.Limits(max_keepalive_connections=50, max_connections=100),
    http2=True,
)

openai_client = OpenAI(
    api_key=settings.OPENAI_API_KEY or "missing-openai-key",
    http_client=shared_http_client,
)

# Groq exposes an OpenAI-compatible API, so the OpenAI SDK is enough here.
groq_client = OpenAI(
    api_key=settings.GROQ_API_KEY or "missing-groq-key",
    base_url="https://api.groq.com/openai/v1",
    http_client=shared_http_client,
)

GROQ_MODEL_HINTS = (
    "llama",
    "mixtral",
    "gemma",
    "qwen",
    "deepseek",
    "groq/",
    "meta-llama/",
    "openai/gpt-oss",
)

GROQ_VISION_MODELS = {
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
}

OPENAI_VISION_MODEL_HINTS = (
    "gpt-4o",
    "gpt-4.1",
    "gpt-5",
    "o3",
    "o4",
)


def get_llm_provider(model_name: str) -> Provider:
    name = (model_name or "").lower()
    if any(hint in name for hint in GROQ_MODEL_HINTS):
        return "groq"
    return "openai"


def get_llm_client(model_name: str) -> Any:
    return groq_client if get_llm_provider(model_name) == "groq" else openai_client


def has_api_key_for_model(model_name: str) -> bool:
    if get_llm_provider(model_name) == "groq":
        return bool(settings.GROQ_API_KEY and "YOUR_GROQ_API_KEY" not in settings.GROQ_API_KEY)
    return bool(settings.OPENAI_API_KEY and "YOUR_OPENAI_API_KEY" not in settings.OPENAI_API_KEY)


def supports_vision(model_name: str) -> bool:
    name = (model_name or "").lower()
    if get_llm_provider(model_name) == "groq":
        return name in GROQ_VISION_MODELS
    return any(hint in name for hint in OPENAI_VISION_MODEL_HINTS)


def select_model_for_multimodal(preferred_model: str, fallback_model: str | None = None) -> str | None:
    if supports_vision(preferred_model) and has_api_key_for_model(preferred_model):
        return preferred_model
    if fallback_model and supports_vision(fallback_model) and has_api_key_for_model(fallback_model):
        return fallback_model
    return None
