import json
from app.db.models import RagRequestLog, BasicRequestLog, FoodInteraction, FoodRequestLog, SystemLog, CrawlSource, UserReview
from app.api.admin.utils import _iso, _json_text_with_defaults

def serialize_rag_log(row: RagRequestLog) -> dict:
    return {
        "id": row.id,
        "conversation_id": row.conversation_id,
        "user_id": row.user_id,
        "guest_id": row.guest_id,
        "original_query": row.original_query,
        "rewritten_query": row.rewritten_query,
        "final_answer": row.final_answer,
        "search_latency_ms": row.search_latency_ms or 0,
        "generation_latency_ms": row.generation_latency_ms or 0,
        "total_latency_ms": row.total_latency_ms or 0,
        "rewrite_latency_ms": row.rewrite_latency_ms or 0,
        "classification_latency_ms": row.classification_latency_ms or 0,
        "expansion_latency_ms": row.expansion_latency_ms or 0,
        "rerank_latency_ms": row.rerank_latency_ms or 0,
        "cache_latency_ms": getattr(row, "cache_latency_ms", 0) or 0,
        "total_tokens": row.total_tokens or 0,
        "cost_usd": row.cost_usd or 0,
        "blocked_by_guardrail": bool(row.blocked_by_guardrail),
        "retrieval_result_json": row.retrieval_result_json,
        "rerank_result_json": row.rerank_result_json,
        "parent_child_result_json": row.parent_child_result_json,
        "created_at": _iso(row.created_at),
    }

def serialize_basic_log(row: BasicRequestLog) -> dict:
    return {
        "id": row.id,
        "conversation_id": row.conversation_id,
        "user_id": row.user_id,
        "guest_id": row.guest_id,
        "original_query": row.original_query,
        "rewritten_query": row.rewritten_query,
        "intent": row.intent,
        "final_answer": row.final_answer,
        "model_name": row.model_name,
        "nlu_latency_ms": row.nlu_latency_ms,
        "cache_latency_ms": getattr(row, "cache_latency_ms", 0) or 0,
        "generation_latency_ms": getattr(row, "generation_latency_ms", 0) or 0,
        "total_latency_ms": row.total_latency_ms,
        "cost_usd": row.cost_usd,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }

def serialize_food_interaction(row: FoodInteraction) -> dict:
    return {
        "event_id": row.event_id,
        "id": row.event_id,
        "user_id": row.user_id,
        "session_id": row.session_id,
        "conversation_id": row.conversation_id,
        "message_id": row.message_id,
        "event_type": row.event_type,
        "item_id": row.item_id,
        "merchant_id": row.merchant_id,
        "rank_position": row.rank_position,
        "query": row.query,
        "request_context_json": row.request_context_json,
        "created_at": _iso(row.created_at),
    }

def serialize_food_request_log(row: FoodRequestLog) -> dict:
    candidate_stats_json = _json_text_with_defaults(row.candidate_stats_json, {
        "returned_count": lambda data: data.get("result_count", 0),
        "total_candidates": lambda data: data.get("result_count", 0),
    })
    return {
        "trace_id": row.trace_id,
        "id": row.trace_id,
        "conversation_id": row.conversation_id,
        "user_id": row.user_id,
        "guest_id": row.guest_id,
        "original_query": row.original_query,
        "rewritten_query": row.rewritten_query,
        "final_answer": row.final_answer,
        "intent": row.intent,
        "search_latency_ms": row.search_latency_ms or 0,
        "generation_latency_ms": row.generation_latency_ms or 0,
        "total_latency_ms": row.total_latency_ms or 0,
        "rewrite_latency_ms": row.rewrite_latency_ms or 0,
        "classification_latency_ms": row.classification_latency_ms or 0,
        "total_tokens": row.total_tokens or 0,
        "cost_usd": row.cost_usd or 0,
        "nlu_json": row.nlu_json,
        "user_context_json": row.user_context_json,
        "location_json": row.location_json,
        "candidate_stats_json": candidate_stats_json,
        "ranking_json": row.ranking_json,
        "answer_llm_json": row.answer_llm_json,
        "sse_events_json": row.sse_events_json,
        "latency_json": json.dumps({
            "search_latency_ms": row.search_latency_ms or 0,
            "generation_latency_ms": row.generation_latency_ms or 0,
            "total_latency_ms": row.total_latency_ms or 0,
            "rewrite_latency_ms": row.rewrite_latency_ms or 0,
            "classification_latency_ms": row.classification_latency_ms or 0,
        }),
        "created_at": _iso(row.created_at),
    }

def serialize_system_log(row: SystemLog) -> dict:
    return {
        "id": row.id,
        "trace_id": row.trace_id,
        "conversation_id": row.conversation_id,
        "user_id": row.user_id,
        "guest_id": row.guest_id,
        "level": row.level,
        "node": row.node,
        "event": row.event,
        "query": row.query,
        "intent": row.intent,
        "payload_json": row.payload_json,
        "created_at": _iso(row.created_at),
    }

def serialize_crawl_source(row: CrawlSource) -> dict:
    return {
        "id": row.id,
        "url": row.url,
        "title": row.title,
        "source_profile": row.source_profile,
        "source_type": row.source_type,
        "category": row.category,
        "document_type": row.document_type,
        "output_dir": row.output_dir,
        "crawl_strategy": row.crawl_strategy,
        "enabled": row.enabled,
        "priority": row.priority,
        "notes": row.notes,
        "last_crawled_at": _iso(row.last_crawled_at),
        "last_status": row.last_status,
        "last_error": row.last_error,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }

def serialize_user_review(row: UserReview, query_text: str | None, answer: str | None, conversation_id: str | None, pipeline_trace: str | None = None) -> dict:
    res = {
        "id": row.id,
        "conversation_id": conversation_id,
        "message_id": row.message_id,
        "user_id": None,
        "query": query_text,
        "answer": answer,
        "rating": row.rating,
        "reason_tags": json.loads(row.reason_tags) if row.reason_tags else [],
        "comment": row.comment,
        "status": row.status,
        "admin_note": row.admin_note,
        "created_at": _iso(row.created_at),
        "updated_at": None,
    }
    if pipeline_trace is not None:
        res["pipeline_trace"] = json.loads(pipeline_trace) if pipeline_trace else None
    return res
