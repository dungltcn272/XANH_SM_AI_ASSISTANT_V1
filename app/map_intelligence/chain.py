from __future__ import annotations

import json
import re
import time
from typing import Any

from app.assistant.events import sse_pipeline_step, stream_plain_answer
from app.map_intelligence.schemas import MapQuery
from app.map_intelligence.service import MapIntelligenceService


class MapIntelligenceChain:
    def __init__(self):
        self.service = MapIntelligenceService()

    def stream(
        self,
        query: str,
        metrics: dict[str, Any],
        t_start: float,
        nlu_map_slots: dict[str, Any] | None = None,
        food_context: dict[str, Any] | None = None,
        user_mode: str | None = None,
    ):
        slots = nlu_map_slots or {}
        lat, lng = self._resolve_location(query, slots, food_context)
        inferred_mode = user_mode or slots.get("user_mode") or self._infer_user_mode(query)
        radius_km = float(slots.get("radius_km") or 5.0)
        layers = slots.get("layers") if isinstance(slots.get("layers"), list) else None

        metrics["intent"] = "map_intelligence"
        metrics["map_layers"] = layers
        metrics["map_user_mode"] = inferred_mode
        yield sse_pipeline_step("map_fake_api", "Đang lấy dữ liệu bản đồ mô phỏng...", 0.42)
        payload = self.service.get_payload(
            MapQuery(
                query=query,
                lat=lat,
                lng=lng,
                radius_km=radius_km,
                layers=layers,
                user_mode=inferred_mode if inferred_mode in {"customer", "driver"} else "customer",
            )
        )
        metrics["map_marker_count"] = len(payload.markers)
        metrics["map_zone_count"] = len(payload.zones)
        metrics["map_route_count"] = len(payload.routes)
        metrics["total_latency_ms"] = (time.time() - t_start) * 1000

        answer = self._answer_text(payload.summary, inferred_mode)
        yield from stream_plain_answer(answer)
        yield f'data: {json.dumps({"type": "map_payload", "map_payload": payload.model_dump()}, ensure_ascii=False)}\n\n'
        yield f'data: {json.dumps({"metrics": metrics, "step": "map-intelligence"}, ensure_ascii=False)}\n\n'
        yield "data: [DONE]\n\n"

    def _answer_text(self, summary: str, user_mode: str) -> str:
        if user_mode == "driver":
            return f"Dạ, em đang dùng dữ liệu demo để xem bản đồ vận hành. {summary} Anh/chị xem các lớp điểm đông khách, tắc đường và đường tắt trên bản đồ bên dưới nhé."
        return f"Dạ, em đã dựng nhanh bản đồ từ dữ liệu demo. {summary} Anh/chị có thể bật/tắt từng lớp để xem tài xế, quán ăn, điểm đông khách và tình trạng đường."

    def _infer_user_mode(self, query: str) -> str:
        text = (query or "").lower()
        if any(term in text for term in ["tài xế nên", "tai xe nen", "đón khách", "don khach", "chạy xe", "chay xe"]):
            return "driver"
        return "customer"

    def _resolve_location(
        self,
        query: str,
        slots: dict[str, Any],
        food_context: dict[str, Any] | None,
    ) -> tuple[float | None, float | None]:
        lat = slots.get("lat")
        lng = slots.get("lng")
        if lat is not None and lng is not None:
            return float(lat), float(lng)

        match = re.search(r"(-?\d{1,2}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)", query or "")
        if match:
            return float(match.group(1)), float(match.group(2))

        current = (food_context or {}).get("current_location") or {}
        if current.get("lat") is not None and current.get("lng") is not None:
            return float(current["lat"]), float(current["lng"])
        return None, None
