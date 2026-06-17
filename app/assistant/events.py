from __future__ import annotations

import json
import re
from typing import Any, Iterator


def sse_pipeline_step(step: str, message: str, progress: float | None = None, **debug: Any) -> str:
    payload: dict[str, Any] = {
        "type": "pipeline_step",
        "step": step,
        "message": message,
    }
    if progress is not None:
        payload["progress"] = progress
    if debug:
        payload["debug"] = debug
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def stream_plain_answer(answer: str) -> Iterator[str]:
    for token in re.split(r"(\s+)", answer or ""):
        if token:
            yield f"data: {token.replace('\n', '\ndata: ')}\n\n"

