from __future__ import annotations

import json
import time
from typing import Any

from app.core.config import settings as config
from app.core.logger import log_info
from app.food_recommendation.answer_llm import stream_food_answer_with_llm
from app.food_recommendation.payloads import (
    food_location_payload,
    food_recommendations_payload,
    format_food_answer,
    missing_location_answer,
)
from app.food_recommendation.trace_store import save_food_request_log
from app.assistant.events import sse_pipeline_step, stream_plain_answer
from app.food_recommendation.geocode import geocode_address
from app.food_recommendation.nlu import slots_from_nlu
from app.food_recommendation.tool import recommend_food


class FoodRecommendationChain:
    """Food recommendation capability chain."""

    def stream(
        self,
        query: str,
        metrics: dict[str, Any],
        t_start: float,
        nlu_food_slots: dict[str, Any] | None = None,
        food_context: dict[str, Any] | None = None,
        conversation_id: str | None = None,
        user_id: str | None = None,
        guest_id: str | None = None,
    ):
        slots = slots_from_nlu(nlu_food_slots, raw_query=query)
        sse_steps: list[str] = []
        metrics["intent"] = "food_recommendation"
        metrics["food_slots"] = {
            "has_location": slots.lat is not None and slots.lng is not None,
            "category": slots.category,
            "taste_tags": slots.taste_tags,
            "budget_min": slots.budget_min,
            "budget_max": slots.budget_max,
            "meal_time": slots.meal_time,
            "max_distance_km": slots.max_distance_km,
            "address_text": slots.address_text,
        }

        if slots.lat is None or slots.lng is None:
            geocode_target = slots.address_text
            if geocode_target:
                try:
                    sse_steps.append("food_geocode")
                    yield sse_pipeline_step("food_geocode", "Đang xác định vị trí trên bản đồ...", 0.32, address_text=geocode_target)
                    geocoded = geocode_address(geocode_target)
                    if geocoded:
                        slots.lat = float(geocoded["lat"])
                        slots.lng = float(geocoded["lng"])
                        metrics["food_geocoded_address"] = geocode_target
                        metrics["food_geocode_source"] = geocoded.get("source")
                except Exception as exc:
                    metrics["food_geocode_error"] = str(exc)

        if slots.lat is None or slots.lng is None:
            answer = missing_location_answer()
            metrics["total_latency_ms"] = (time.time() - t_start) * 1000
            sse_steps.append("food_missing_info")
            trace_id = save_food_request_log(
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=query,
                metrics=metrics,
                food_context=food_context,
                slots=slots,
                items=[],
                answer_meta={"answer": answer, "missing_fields": ["location"]},
                sse_steps=sse_steps,
            )
            metrics["food_trace_id"] = trace_id
            location_payload = food_location_payload(query)
            yield sse_pipeline_step("food_missing_info", "Em cần thêm một chút thông tin để gợi ý chính xác hơn...", 0.42)
            yield from stream_plain_answer(answer)
            yield f'data: {json.dumps({"type": "food_missing_info", "answer": answer, "ui_form": location_payload, "food_location_request": location_payload, "trace_id": trace_id}, ensure_ascii=False)}\n\n'
            yield f'data: {json.dumps({"metrics": metrics, "step": "food-missing-location"}, ensure_ascii=False)}\n\n'
            yield "data: [DONE]\n\n"
            return

        from app.db.database import SessionLocal

        t_tool_start = time.time()
        db = SessionLocal()
        try:
            sse_steps.append("food_candidate_search")
            yield sse_pipeline_step("food_candidate_search", "Đang tìm các món ăn phù hợp...", 0.42)
            items = recommend_food(
                lat=slots.lat,
                lng=slots.lng,
                query_text=query,
                category=slots.category,
                taste_tags=slots.taste_tags,
                budget_min=slots.budget_min,
                budget_max=slots.budget_max,
                meal_time=slots.meal_time,
                max_distance_km=slots.max_distance_km,
                limit=8,
                db=db,
                metrics=metrics,
                food_context=food_context,
            )
            if not items:
                metrics["food_fallback"] = "expanded_radius"
                sse_steps.append("food_candidate_filter")
                yield sse_pipeline_step("food_candidate_filter", "Đang lọc quán theo vị trí, ngân sách và khẩu vị...", 0.52, radius_km=max(slots.max_distance_km, 25))
                items = recommend_food(
                    lat=slots.lat,
                    lng=slots.lng,
                    query_text=query,
                    category=slots.category,
                    taste_tags=slots.taste_tags,
                    budget_min=slots.budget_min,
                    budget_max=slots.budget_max,
                    meal_time=slots.meal_time,
                    max_distance_km=max(slots.max_distance_km, 25),
                    limit=8,
                    db=db,
                    metrics=metrics,
                    food_context=food_context,
                )
            if not items and slots.category:
                metrics["food_fallback"] = "expanded_radius_relaxed_category"
                sse_steps.append("food_ml_rank")
                yield sse_pipeline_step("food_ml_rank", "Đang xếp hạng món ăn phù hợp nhất...", 0.62, relaxed_category=True)
                items = recommend_food(
                    lat=slots.lat,
                    lng=slots.lng,
                    query_text=query,
                    category=None,
                    taste_tags=slots.taste_tags,
                    budget_min=slots.budget_min,
                    budget_max=slots.budget_max,
                    meal_time=slots.meal_time,
                    max_distance_km=max(slots.max_distance_km, 25),
                    limit=8,
                    db=db,
                    metrics=metrics,
                    food_context=food_context,
                )
                if items:
                    # Save the original category so LLM can explain the fallback
                    slots.original_category = slots.category
                    slots.category = None
                    metrics["relaxed_category_triggered"] = True
        finally:
            db.close()

        metrics["search_latency_ms"] = (time.time() - t_tool_start) * 1000
        metrics["food_result_count"] = len(items)
        log_info(
            "FOOD_RECOMMENDATION",
            "Food retrieval and ranking completed",
            {
                "retrieval": metrics.get("food_retrieval"),
                "ranker_version": "food_weighted_ranker_v2_bm25_geo_profile_ready",
                "result_count": len(items),
                "fallback": metrics.get("food_fallback"),
            },
        )
        if items:
            sse_steps.append("food_found")
            yield sse_pipeline_step("food_found", "Yeah, đã tìm được quán ăn phù hợp, đang chuẩn bị lên món...", 0.78, result_count=len(items))
            sse_steps.append("food_answer_llm")
            yield sse_pipeline_step("food_answer_llm", "Đang viết lời gợi ý dễ hiểu hơn cho bạn...", 0.86)

        t_food_answer_start = time.time()
        metrics["answer_model"] = config.FOOD_ANSWER_MODEL
        answer_generator = stream_food_answer_with_llm(items, query, slots, food_context)
        first_token_received = False
        answer_meta = None
        for chunk in answer_generator:
            if chunk["type"] == "chunk":
                if not first_token_received:
                    metrics["ttft_ms"] = (time.time() - t_food_answer_start) * 1000
                    first_token_received = True
                text = chunk["text"]
                yield f"data: {text.replace('\n', '\ndata: ')}\n\n"
            elif chunk["type"] == "done":
                answer_meta = chunk["answer_meta"]
                
        metrics["generation_latency_ms"] = (time.time() - t_food_answer_start) * 1000
                
        if not first_token_received:
            metrics["generation_latency_ms"] = (time.time() - t_food_answer_start) * 1000

        metrics["food_answer_llm_used"] = bool(answer_meta.get("llm_used"))
        metrics["food_answer_llm_error"] = answer_meta.get("error")
        metrics["total_latency_ms"] = (time.time() - t_start) * 1000
        trace_id = save_food_request_log(
            conversation_id=conversation_id,
            user_id=user_id,
            guest_id=guest_id,
            query=query,
            metrics=metrics,
            food_context=food_context,
            slots=slots,
            items=items,
            answer_meta=answer_meta,
            sse_steps=sse_steps,
        )
        metrics["food_trace_id"] = trace_id
        answer = answer_meta.get("answer") or format_food_answer(items, slots.category)
        
        # We already streamed the text, but if it failed or returned empty we might need fallback
        if not answer_meta.get("llm_used"):
            yield from stream_plain_answer(answer)
            
        if items:
            payload = food_recommendations_payload(items, slots.category, query, answer_meta=answer_meta, trace_id=trace_id)
            metrics["food_recommendations"] = payload
            yield f'data: {json.dumps({"type": "food_recommendation_result", "answer": answer, "food_recommendations": payload, "trace_id": trace_id}, ensure_ascii=False)}\n\n'
        else:
            location_payload = food_location_payload(query)
            yield f'data: {json.dumps({"type": "food_no_result", "answer": answer, "ui_form": location_payload, "food_location_request": location_payload, "trace_id": trace_id}, ensure_ascii=False)}\n\n'
        yield f'data: {json.dumps({"metrics": metrics, "step": "food-recommendation"}, ensure_ascii=False)}\n\n'
        yield "data: [DONE]\n\n"
