from __future__ import annotations

import json
from typing import Any


def compose_response(*, persona: str, intent: str, tool_results: list[dict[str, Any]]) -> str:
    if not tool_results:
        return "Mình chưa có đủ dữ liệu để trả lời. Bạn có thể nói rõ hơn không?"

    primary = tool_results[0].get("output", {})
    if isinstance(primary, dict) and "answer" in primary:
        return str(primary["answer"])

    payload = json.dumps(tool_results, ensure_ascii=False, indent=2, default=str)
    return f"Kết quả demo cho persona `{persona}` / intent `{intent}`:\n\n```json\n{payload}\n```"
