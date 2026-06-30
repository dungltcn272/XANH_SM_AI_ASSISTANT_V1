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
        conversation_id: str | None = None,
        user_id: str | None = None,
        guest_id: str | None = None,
        query: str = "",
        metrics: dict[str, Any] = None,
        t_start: float = 0.0,
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

        answer_stream = self._answer_text(payload.summary, inferred_mode, query)
        full_answer = ""
        for token in answer_stream:
            full_answer += token
            yield f'data: {token}\n\n'
        
        metrics["generation_latency_ms"] = (time.time() - t_start) * 1000 - metrics["total_latency_ms"]
        metrics["total_latency_ms"] = (time.time() - t_start) * 1000
        
        yield f'data: {json.dumps({"type": "map_payload", "map_payload": payload.model_dump()}, ensure_ascii=False)}\n\n'
        yield f'data: {json.dumps({"metrics": metrics, "step": "map-intelligence"}, ensure_ascii=False)}\n\n'
        yield "data: [DONE]\n\n"

        from app.rag.storage.trace_store import save_rag_request_log
        save_rag_request_log(
            conversation_id=conversation_id,
            user_id=user_id,
            guest_id=guest_id,
            query=query,
            intent="map_intelligence",
            metrics=metrics,
            retrieved_docs=[],
            reranked_docs=[],
            expanded_docs=[],
            final_answer=full_answer,
        )

    def _answer_text(self, summary: str, user_mode: str, query: str):
        # Hàm này đổi thành stream generator
        from app.core.llm import get_llm_client
        from app.core.config import settings as config
        
        client = get_llm_client(config.MAP_ANSWER_MODEL)
        
        prompt = f"""Bạn là trợ lý ảo của hãng taxi thuần điện Xanh SM.
Người dùng đang hỏi các thông tin liên quan đến bản đồ, địa điểm, tuyến đường.
Dưới đây là DỮ LIỆU BẢN ĐỒ thực tế mà hệ thống vừa truy xuất được:
{summary}

Nhiệm vụ của bạn là dựa vào DỮ LIỆU BẢN ĐỒ trên để trực tiếp TRẢ LỜI CÂU HỎI của người dùng một cách tự nhiên, lịch sự và súc tích (dưới 4 câu).
Nếu người dùng hỏi về đường đi hoặc quán ăn, hãy nhắc đến TÊN ĐIỂM ĐẾN nếu có trong dữ liệu (ví dụ quán Jiro Sushi, toà nhà Landmark...).
Nếu dữ liệu báo có tuyến đường (khoảng cách, thời gian), hãy thông báo chi tiết cho người dùng biết.
Tuyệt đối KHÔNG tự bịa ra thông tin đường đi nếu không có trong dữ liệu trên.
"""
        try:
            response = client.chat.completions.create(
                model=config.MAP_ANSWER_MODEL,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query if query else "Hãy tổng hợp thông tin bản đồ cho tôi."}
                ],
                temperature=0.3,
                stream=True
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            from app.core.logger import log_error
            log_error("MAP_LLM", str(e))
            yield f"Dạ, em đã tổng hợp bản đồ từ hệ thống vận hành. {summary} Anh/chị có thể bật/tắt từng lớp để xem chi tiết."

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
