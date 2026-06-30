from __future__ import annotations

import json
import time
from typing import Any
import uuid
import logging

from app.assistant.events import sse_pipeline_step, stream_plain_answer
from app.map_intelligence.schemas import MapPayload, GeoPoint, MapMarker, MapRouteHint, MapZone
from app.map_intelligence.tools import search_places, get_osrm_routes, get_traffic_zones, get_driver_density
from app.core.llm import get_llm_client
from app.core.config import settings as config
from app.prompts.map_prompts import MAP_INTELLIGENCE_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

def map_location_payload(query: str) -> dict[str, Any]:
    return {
        "title": "Anh/chị muốn tìm đường từ đâu?",
        "query": query,
        "address_placeholder": "Nhập địa chỉ xuất phát",
        "current_location_label": "Dùng vị trí hiện tại",
        "submit_label": "Xác nhận",
    }

# Khai báo cấu trúc JSON Schema của các tools để báo cho LLM biết
MAP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_places",
            "description": "Tìm kiếm toạ độ của một địa danh cụ thể (VD: Jiro Sushi, Landmark 81).",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Tên địa điểm cần tìm kiếm"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_osrm_routes",
            "description": "Lấy thông tin lộ trình đường đi giữa 2 toạ độ (điểm xuất phát và điểm đến).",
            "parameters": {
                "type": "object",
                "properties": {
                    "end_lat": {"type": "number", "description": "Vĩ độ điểm đến"},
                    "end_lng": {"type": "number", "description": "Kinh độ điểm đến"}
                },
                "required": ["end_lat", "end_lng"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_traffic_zones",
            "description": "Lấy thông tin các điểm/vùng đang kẹt xe xung quanh.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_driver_density",
            "description": "Lấy thông tin vị trí các tài xế hoặc vùng có nhiều tài xế.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


class MapIntelligenceChain:
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
        if lat is None or lng is None:
            from app.assistant.system_log import save_system_log
            trace_id = str(uuid.uuid4())
            metrics["map_trace_id"] = trace_id
            save_system_log(
                node="map.location",
                event="missing_location",
                trace_id=trace_id,
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=query,
                intent="map_intelligence",
                payload={"food_context": food_context, "nlu_map_slots": nlu_map_slots},
            )
            location_payload = map_location_payload(query)
            answer = "Dạ, anh/chị vui lòng xác nhận vị trí xuất phát để em có thể tìm đường chính xác nhất nhé."
            yield sse_pipeline_step("map_missing_info", "Em cần thêm vị trí xuất phát...", 0.42)
            yield from stream_plain_answer(answer)
            yield f'data: {json.dumps({"type": "food_missing_info", "answer": answer, "ui_form": location_payload, "food_location_request": location_payload, "trace_id": trace_id}, ensure_ascii=False)}\n\n'
            yield f'data: {json.dumps({"metrics": metrics, "step": "map-missing-location"}, ensure_ascii=False)}\n\n'
            yield "data: [DONE]\n\n"
            return
            
        inferred_mode = user_mode or slots.get("user_mode") or "customer"

        metrics["intent"] = "map_intelligence"
        yield sse_pipeline_step("map_agent", "Đang suy luận nhu cầu bản đồ...", 0.3)
        
        # State để xây dựng MapPayload
        markers: list[MapMarker] = []
        routes: list[MapRouteHint] = []
        zones: list[MapZone] = []
        layers = set(["demand"])

        # Agent Loop
        client = get_llm_client(config.MAP_ANSWER_MODEL)
        
        system_prompt = MAP_INTELLIGENCE_SYSTEM_PROMPT.format(lat=lat, lng=lng)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]

        max_iterations = 3
        
        for iteration in range(max_iterations):
            response = client.chat.completions.create(
                model=config.MAP_ANSWER_MODEL,
                messages=messages,
                tools=MAP_TOOLS,
                tool_choice="auto",
                temperature=0.0
            )
            
            message = response.choices[0].message
            messages.append(message)
            
            if not message.tool_calls:
                break
                
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                args = {}
                try:
                    args = json.loads(tool_call.function.arguments)
                except:
                    pass
                
                tool_res_str = "{}"
                if func_name == "search_places":
                    yield sse_pipeline_step("map_search", f"Đang tìm kiếm {args.get('query')}...", 0.5)
                    res = search_places(args.get("query", ""), lat, lng)
                    if res.get("found"):
                        markers.append(MapMarker(
                            id=str(uuid.uuid4()),
                            type="restaurant", # Có thể general hơn
                            title=res["title"],
                            description="Kết quả tìm kiếm",
                            lat=res["lat"],
                            lng=res["lng"]
                        ))
                        layers.add("restaurants")
                    tool_res_str = json.dumps(res, ensure_ascii=False)
                    
                elif func_name == "get_osrm_routes":
                    yield sse_pipeline_step("map_route", "Đang tính toán lộ trình...", 0.6)
                    res = get_osrm_routes(lat, lng, args.get("end_lat", lat), args.get("end_lng", lng))
                    if res.get("success"):
                        for r in res["routes"]:
                            routes.append(MapRouteHint(
                                id=r["id"],
                                title=r["title"],
                                description=f"Khoảng cách {r['distance_km']}km, thời gian {r['duration_min']} phút",
                                points=[GeoPoint(lat=p["lat"], lng=p["lng"]) for p in r["points"]],
                                eta_saving_minutes=None
                            ))
                        layers.add("shortcuts")
                    tool_res_str = json.dumps(res, ensure_ascii=False)
                    
                elif func_name == "get_traffic_zones":
                    yield sse_pipeline_step("map_traffic", "Đang tải dữ liệu giao thông...", 0.5)
                    res = get_traffic_zones(lat, lng)
                    if res.get("success"):
                        for z in res["zones"]:
                            zones.append(MapZone(
                                id=z["id"],
                                type=z["type"],
                                title=z["title"],
                                description=z["description"],
                                center=GeoPoint(lat=z["center"]["lat"], lng=z["center"]["lng"]),
                                radius_m=z["radius_m"],
                                intensity=z.get("intensity", 0.5)
                            ))
                        layers.add("traffic")
                    tool_res_str = json.dumps(res, ensure_ascii=False)
                    
                elif func_name == "get_driver_density":
                    yield sse_pipeline_step("map_drivers", "Đang tìm kiếm tài xế...", 0.5)
                    res = get_driver_density(lat, lng)
                    if res.get("success"):
                        for m in res["markers"]:
                            markers.append(MapMarker(
                                id=m["id"],
                                type=m["type"],
                                title=m["title"],
                                description=m["description"],
                                lat=m["lat"],
                                lng=m["lng"],
                                intensity=m.get("intensity", 0.5)
                            ))
                        for z in res["zones"]:
                            zones.append(MapZone(
                                id=z["id"],
                                type=z["type"],
                                title=z["title"],
                                description=z["description"],
                                center=GeoPoint(lat=z["center"]["lat"], lng=z["center"]["lng"]),
                                radius_m=z["radius_m"]
                            ))
                        layers.add("drivers")
                    tool_res_str = json.dumps(res, ensure_ascii=False)
                else:
                    tool_res_str = json.dumps({"error": "unknown tool"})
                    
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": func_name,
                    "content": tool_res_str
                })

        # Final answer streaming
        payload = MapPayload(
            center=GeoPoint(lat=lat, lng=lng),
            zoom=14,
            layers=list(layers),
            markers=markers,
            zones=zones,
            routes=routes,
            summary="Dữ liệu tổng hợp từ Agent" # Có thể update
        )
        
        metrics["map_marker_count"] = len(payload.markers)
        metrics["map_zone_count"] = len(payload.zones)
        metrics["map_route_count"] = len(payload.routes)
        metrics["total_latency_ms"] = (time.time() - t_start) * 1000

        yield sse_pipeline_step("map_answer", "Đang trả lời...", 0.8)
        
        # Tạo stream trả lời cuối cùng dựa trên lịch sử messages
        response_stream = client.chat.completions.create(
            model=config.MAP_ANSWER_MODEL,
            messages=messages,
            temperature=0.3,
            stream=True
        )
        
        full_answer = ""
        for chunk in response_stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_answer += token
                yield f"data: {token.replace('\n', '\ndata: ')}\n\n"
                
        # Cập nhật summary bằng full_answer để lưu vào payload
        payload.summary = full_answer
        
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

    def _resolve_location(
        self,
        query: str,
        slots: dict[str, Any],
        food_context: dict[str, Any] | None,
    ) -> tuple[float | None, float | None]:
        import re
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
