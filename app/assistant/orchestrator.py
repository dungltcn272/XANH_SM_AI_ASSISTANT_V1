from __future__ import annotations

import json
import re
import time
from typing import Any

from app.food_recommendation.chain import FoodRecommendationChain
from app.rag.chain import RagAnswerChain
from app.assistant.events import sse_pipeline_step, stream_plain_answer
from app.core.config import settings as config
from app.core.logger import log_warn
from app.assistant.system_log import save_system_log
from app.rag.classifier import XanhSMClassifier
from app.rag.gateway import XanhSMGateway
class XanhSMAssistantOrchestrator:
    """
    Assistant-level orchestrator.

    Owns cross-capability flow: cache, gateway safety, NLU intent routing, and
    high-level SSE progress. Capability-specific chains own their own mandatory
    steps: RAG retrieval/rerank/answer and Food recommendation.
    """

    def __init__(self):
        self.gateway = XanhSMGateway()
        self.classifier = XanhSMClassifier()
        try:
            from app.rag.cache import XanhSMRAGCache
            self.cache = XanhSMRAGCache()
        except Exception as exc:
            log_warn("CACHE", f"Failed to load cache: {exc}")
            self.cache = None
        self.rag_chain = RagAnswerChain(cache=self.cache)
        self.food_chain = FoodRecommendationChain()

    def _calculate_llm_cost(self, prompt_tokens: int, completion_tokens: int) -> dict[str, Any]:
        usd_input = (prompt_tokens / 1_000_000) * 0.15
        usd_output = (completion_tokens / 1_000_000) * 0.60
        return {"cost_usd": usd_input + usd_output}

    def _gateway_refusal_message(self, safety_res: dict[str, Any]) -> str:
        reason = (safety_res or {}).get("reason") or "Nội dung này chưa phù hợp để em hỗ trợ trực tiếp."
        return (
            f"Dạ, em xin phép chưa hỗ trợ nội dung này. {reason} "
            "Anh/chị có thể hỏi em về dịch vụ, giá cước, chính sách hoặc cách xử lý sự cố khi sử dụng Xanh SM ạ."
        )

    def _is_greeting_or_thanks(self, query: str) -> dict[str, Any]:
        return self.gateway.is_greeting_or_thanks(query)

    def stream_run(
        self,
        query: str,
        chat_history: list[dict[str, str]] | None = None,
        bypass_cache: bool = False,
        image_base64: str | None = None,
        is_deep_search: bool = False,
        food_context: dict[str, Any] | None = None,
        assistant_context: dict[str, Any] | None = None,
        conversation_id: str | None = None,
        user_id: str | None = None,
        guest_id: str | None = None,
    ):
        t_start = time.time()
        metrics = {
            "search_latency_ms": 0,
            "generation_latency_ms": 0,
            "rewrite_latency_ms": 0,
            "classification_latency_ms": 0,
            "expansion_latency_ms": 0,
            "rerank_latency_ms": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
            "expanded_queries": [],
            "rewritten_query": "",
            "num_chunks_before_expansion": 0,
            "compressed_context_len": 0,
        }

        if is_deep_search:
            bypass_cache = True

        yield sse_pipeline_step("received", "Chờ một chút...", 0.03)
        normalized_query = self.gateway.normalize_input(query)
        if self.classifier.is_memory_related_query(normalized_query):
            bypass_cache = True
        save_system_log(
            node="orchestrator",
            event="received",
            conversation_id=conversation_id,
            user_id=user_id,
            guest_id=guest_id,
            query=query,
            payload={"normalized_query": normalized_query, "has_image": bool(image_base64), "is_deep_search": is_deep_search},
        )

        yield sse_pipeline_step("gateway_safety", "Đang kiểm tra an toàn nội dung...", 0.06)
        safety_res = self.gateway.safety_precheck(normalized_query)
        if not safety_res["safe"]:
            refusal_msg = self._gateway_refusal_message(safety_res)
            yield from stream_plain_answer(refusal_msg)
            yield "data: [DONE]\n\n"
            return

        yield sse_pipeline_step("cache_lookup", "Đang kiểm tra câu trả lời đã có...", 0.1)
        if self.cache and not bypass_cache:
            is_hit, hit_res, _hit_type = self.cache.get(normalized_query)
            if is_hit:
                metrics["total_latency_ms"] = (time.time() - t_start) * 1000
                metrics["intent"] = "faq"
                metrics["rewritten_query"] = normalized_query
                metrics["answer_model"] = "semantic_cache"
                yield from stream_plain_answer(hit_res["answer"])
                yield f'data: {json.dumps({"sources": hit_res.get("citations", [])})}\n\n'
                yield f'data: {json.dumps({"metrics": metrics, "step": "cache-hit"})}\n\n'
                yield "data: [DONE]\n\n"
                return

        if is_deep_search:
            yield 'data: {"step": "Đang phân tích chuyên sâu (Deep Search)..."}\n\n'
        else:
            yield 'data: {"step": "Phân tích ngữ cảnh & Ý định..."}\n\n'

        t_nlu_start = time.time()
        yield sse_pipeline_step("nlu_intent", "Đang phân tích ý định...", 0.18)
        save_system_log(
            node="nlu.context",
            event="before_nlu",
            conversation_id=conversation_id,
            user_id=user_id,
            guest_id=guest_id,
            query=normalized_query,
            payload={
                "chat_history_tail": (chat_history or [])[-6:],
                "food_context": food_context,
                "assistant_context": assistant_context,
            },
        )
        nlu_res = self.classifier.unified_nlu(
            normalized_query,
            chat_history,
            image_base64=image_base64,
            food_context=food_context,
            assistant_context=assistant_context,
        )
        metrics["rewrite_latency_ms"] = (time.time() - t_nlu_start) * 1000

        rewritten_query = nlu_res["rewritten_query"]
        intent = nlu_res["intent"]
        expanded_queries = nlu_res["expanded_queries"]
        nlu_usage = nlu_res.get("usage", {"prompt_tokens": 0, "completion_tokens": 0})

        metrics["rewritten_query"] = rewritten_query
        metrics["intent"] = intent
        metrics["answer_model"] = config.NLU_MODEL
        metrics["expanded_queries"] = expanded_queries
        metrics["nlu_fast_path"] = bool(nlu_res.get("fast_path"))
        metrics["nlu_fast_path_reason"] = nlu_res.get("fast_path_reason")
        metrics["food_user_context"] = food_context
        metrics["assistant_memory_context"] = assistant_context
        metrics["nlu_missing_fields"] = nlu_res.get("missing_fields", [])
        metrics["memory_candidates"] = nlu_res.get("memory_candidates", [])
        metrics["total_tokens"] += nlu_usage.get("prompt_tokens", 0) + nlu_usage.get("completion_tokens", 0)
        metrics["cost_usd"] += self._calculate_llm_cost(
            nlu_usage.get("prompt_tokens", 0),
            nlu_usage.get("completion_tokens", 0),
        )["cost_usd"]
        save_system_log(
            node="nlu.result",
            event="after_nlu",
            conversation_id=conversation_id,
            user_id=user_id,
            guest_id=guest_id,
            query=normalized_query,
            intent=intent,
            payload={
                "rewritten_query": rewritten_query,
                "expanded_queries": expanded_queries,
                "food_slots": nlu_res.get("food_slots"),
                "missing_fields": nlu_res.get("missing_fields"),
                "ui_form": nlu_res.get("ui_form"),
                "user_context": nlu_res.get("user_context"),
                "fast_path": nlu_res.get("fast_path"),
                "fast_path_reason": nlu_res.get("fast_path_reason"),
                "model": nlu_res.get("nlu_model_used"),
                "usage": nlu_usage,
            },
        )

        if intent == "food_recommendation":
            save_system_log(
                node="orchestrator.route",
                event="route_food",
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=normalized_query,
                intent=intent,
                payload={"rewritten_query": rewritten_query, "missing_fields": nlu_res.get("missing_fields", [])},
            )
            yield sse_pipeline_step("food_context_load", "Đang xem lại khẩu vị và vị trí của bạn...", 0.24)
            yield from self.food_chain.stream(
                query=query,
                metrics=metrics,
                t_start=t_start,
                nlu_food_slots=nlu_res.get("food_slots"),
                food_context=food_context,
                assistant_context=assistant_context,
                chat_history=chat_history,
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
            )
            return

        if intent == "sensitive":
            save_system_log(
                node="orchestrator.route",
                event="route_sensitive",
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=normalized_query,
                intent=intent,
                payload={"suggested_answer": nlu_res.get("suggested_answer")},
            )
            refusal_msg = nlu_res.get("suggested_answer") or (
                "Dạ, em rất tiếc nhưng em không thể thực hiện yêu cầu này. "
                "Anh/chị có thể hỏi em về dịch vụ, giá cước hoặc chính sách của Xanh SM ạ."
            )
            metrics["total_latency_ms"] = (time.time() - t_start) * 1000
            yield from stream_plain_answer(refusal_msg)
            yield f'data: {json.dumps({"metrics": metrics, "step": "sensitive"})}\n\n'
            yield "data: [DONE]\n\n"
            return

        if intent == "small-talk":
            save_system_log(
                node="orchestrator.route",
                event="route_small_talk",
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=normalized_query,
                intent=intent,
                payload={"suggested_answer": nlu_res.get("suggested_answer")},
            )
            answer = nlu_res.get("suggested_answer")
            if not answer:
                intercept = self._is_greeting_or_thanks(rewritten_query)
                answer = intercept["answer"] if intercept["type"] != "none" else (
                    "Dạ, em là Trợ lý ảo chuyên hỗ trợ các dịch vụ của Xanh SM. "
                    "Anh/chị có thể hỏi em về giá cước taxi, chính sách hủy chuyến hoặc cách đặt xe ạ!"
                )
            metrics["total_latency_ms"] = (time.time() - t_start) * 1000
            yield from stream_plain_answer(answer)
            yield f'data: {json.dumps({"metrics": metrics, "step": "small-talk"})}\n\n'
            yield "data: [DONE]\n\n"
            return

        if intent == "missing_info":
            save_system_log(
                node="orchestrator.route",
                event="route_missing_info",
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=normalized_query,
                intent=intent,
                payload={"suggested_answer": nlu_res.get("suggested_answer"), "missing_fields": nlu_res.get("missing_fields")},
            )
            answer = nlu_res.get("suggested_answer") or (
                "Dạ anh/chị muốn em làm rõ thông tin nào ạ? Anh/chị có thể nói thêm tên xe, dịch vụ, món ăn hoặc mục muốn xem chi tiết giúp em."
            )
            metrics["total_latency_ms"] = (time.time() - t_start) * 1000
            yield from stream_plain_answer(answer)
            yield f'data: {json.dumps({"metrics": metrics, "step": "missing-info"})}\n\n'
            yield "data: [DONE]\n\n"
            return

        if self.cache and not bypass_cache and rewritten_query != normalized_query:
            is_hit, hit_res, _hit_type = self.cache.get(rewritten_query)
            if is_hit:
                metrics["total_latency_ms"] = (time.time() - t_start) * 1000
                metrics["intent"] = "faq"
                metrics["rewritten_query"] = rewritten_query
                metrics["answer_model"] = "semantic_cache"
                yield from stream_plain_answer(hit_res["answer"])
                yield f'data: {json.dumps({"sources": hit_res.get("citations", [])})}\n\n'
                yield f'data: {json.dumps({"metrics": metrics, "step": "cache-hit"})}\n\n'
                yield "data: [DONE]\n\n"
                return

        yield from self.rag_chain.stream(
            conversation_id=conversation_id,
            user_id=user_id,
            guest_id=guest_id,
            original_query=query,
            rewritten_query=rewritten_query,
            normalized_query=normalized_query,
            expanded_queries=expanded_queries,
            chat_history=chat_history,
            metrics=metrics,
            t_start=t_start,
            bypass_cache=bypass_cache,
            is_deep_search=is_deep_search,
            food_context=food_context,
            assistant_context=assistant_context,
        )

    def run_debug(self, query: str, chat_history: list[dict[str, str]] | None = None) -> dict[str, Any]:
        chunks = []
        for event in self.stream_run(query=query, chat_history=chat_history or [], bypass_cache=True):
            chunks.append(event)
            if len(chunks) > 200:
                break
        return {"query": query, "events": chunks}
