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
        nlu_res = self.classifier.unified_nlu(
            normalized_query,
            chat_history,
            image_base64=image_base64,
            food_context=food_context,
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
        metrics["nlu_missing_fields"] = nlu_res.get("missing_fields", [])
        metrics["total_tokens"] += nlu_usage.get("prompt_tokens", 0) + nlu_usage.get("completion_tokens", 0)
        metrics["cost_usd"] += self._calculate_llm_cost(
            nlu_usage.get("prompt_tokens", 0),
            nlu_usage.get("completion_tokens", 0),
        )["cost_usd"]

        if intent == "food_recommendation":
            yield sse_pipeline_step("food_context_load", "Đang xem lại khẩu vị và vị trí của bạn...", 0.24)
            yield from self.food_chain.stream(
                query=query,
                metrics=metrics,
                t_start=t_start,
                nlu_food_slots=nlu_res.get("food_slots"),
                food_context=food_context,
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
            )
            return

        if intent == "sensitive":
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
        )

    def run_debug(self, query: str, chat_history: list[dict[str, str]] | None = None) -> dict[str, Any]:
        chunks = []
        for event in self.stream_run(query=query, chat_history=chat_history or [], bypass_cache=True):
            chunks.append(event)
            if len(chunks) > 200:
                break
        return {"query": query, "events": chunks}
