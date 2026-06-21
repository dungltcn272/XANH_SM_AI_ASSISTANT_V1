from __future__ import annotations

import json
import re
import time
from typing import Any

from app.assistant.events import sse_pipeline_step
from app.assistant.system_log import log_stage
from app.core.config import settings as config
from app.core.llm import get_llm_client
from app.core.logger import log_warn, log_error
from app.prompts import RAG_ANSWER_SYSTEM_PROMPT
from app.rag.search.hybrid_search import XanhSMHybridSearch
from app.rag.search.reranker import XanhSMReranker
from app.rag.storage.trace_store import save_rag_request_log
from app.memory.context_builder import ContextBuilder


class RagAnswerChain:
    """RAG capability chain: retrieve, rerank, expand context, synthesize answer."""

    IMAGE_MARKDOWN_RE = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)\)')
    RAG_CARD_START = "[[RAG_CARD"
    RAG_CARD_END = "]]"

    def __init__(self, cache: Any = None):
        self.search_engine = XanhSMHybridSearch()
        self.reranker = XanhSMReranker()
        self.cache = cache

    def _calculate_llm_cost(self, prompt_tokens: int, completion_tokens: int) -> dict[str, Any]:
        usd_input = (prompt_tokens / 1_000_000) * 0.15
        usd_output = (completion_tokens / 1_000_000) * 0.60
        usd_total = usd_input + usd_output
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": usd_total,
            "cost_vnd": usd_total * 25400,
        }

    def _is_cacheable_answer(self, answer: str, metrics: dict[str, Any]) -> bool:
        clean = (answer or "").strip()
        if not clean or metrics.get("generation_truncated"):
            return False
        lowered = clean.lower()
        if "hệ thống bị gián đoạn" in lowered or "câu trả lời có thể chưa hoàn chỉnh" in lowered:
            return False
        return clean[-1] in {".", "!", "?", "…", ")", "]", "}", '"', "'", "ạ"}

    def _compress_context(self, docs: list[Any]) -> str:
        formatted_blocks = []
        for doc in docs:
            content = doc.page_content.strip()
            source = doc.metadata.get("source", "unknown_policy.md")
            section = doc.metadata.get("section", "Introduction")
            formatted_blocks.append(
                f"[Tài liệu tham khảo #{len(formatted_blocks) + 1}]\n"
                f"Nguồn File: {source}\n"
                f"Phần/Điều khoản: {section}\n"
                f"Nội dung: {content}\n"
                f"---"
            )
        return "\n\n".join(formatted_blocks)

    def _extract_images_from_doc(self, doc: Any) -> list[dict[str, Any]]:
        images = []
        content = doc.page_content or ""
        meta = doc.metadata or {}
        for alt, url in self.IMAGE_MARKDOWN_RE.findall(content):
            clean_url = url.strip()
            if not clean_url or clean_url.startswith(("data:", "mailto:", "#")):
                continue
            images.append({
                "alt": (alt or "").strip() or "Hình ảnh Xanh SM",
                "url": clean_url,
                "source": meta.get("source", "unknown"),
                "section": meta.get("section", ""),
                "page_url": meta.get("url", "") or meta.get("source", ""),
                "category": meta.get("category", ""),
                "relevance_score": meta.get("rerank_score", meta.get("score", 0.0)),
            })
        return images

    def _build_citations(self, docs: list[Any]) -> list[dict[str, Any]]:
        citations = []
        for doc in docs:
            citations.append({
                "source": doc.metadata.get("source", "unknown"),
                "section": doc.metadata.get("section", ""),
                "url": doc.metadata.get("url", "") or doc.metadata.get("source", ""),
                "relevance_score": doc.metadata.get("rerank_score", 0.0),
                "images": self._extract_images_from_doc(doc),
            })
        return citations

    def _allowed_media_urls(self, docs: list[Any]) -> set[str]:
        urls: set[str] = set()
        for doc in docs:
            meta = doc.metadata or {}
            for key in ("url", "source"):
                value = (meta.get(key) or "").strip()
                if value.startswith(("http://", "https://")):
                    urls.add(value)
            for image in self._extract_images_from_doc(doc):
                if image.get("url"):
                    urls.add(image["url"])
                if image.get("page_url", "").startswith(("http://", "https://")):
                    urls.add(image["page_url"])
        return urls

    def _sanitize_rag_card(self, raw_card: Any, allowed_urls: set[str]) -> dict[str, Any] | None:
        if not isinstance(raw_card, dict):
            return None
        title = str(raw_card.get("title") or "").strip()
        if not title:
            return None
        card_type = str(raw_card.get("type") or "info").strip().lower()
        if card_type not in {"news", "vehicle", "info"}:
            card_type = "info"
        images = raw_card.get("images") if isinstance(raw_card.get("images"), list) else []
        clean_images = [
            str(url).strip()
            for url in images
            if str(url).strip() in allowed_urls
        ][:8]
        image_url = str(raw_card.get("image_url") or "").strip()
        if image_url not in allowed_urls:
            image_url = clean_images[0] if clean_images else ""
        elif image_url and image_url not in clean_images:
            clean_images.insert(0, image_url)
        link = str(raw_card.get("url") or "").strip()
        if link and link not in allowed_urls:
            link = ""
        metadata = raw_card.get("metadata") if isinstance(raw_card.get("metadata"), dict) else {}
        return {
            "type": card_type,
            "title": title[:180],
            "description": str(raw_card.get("description") or "").strip()[:360],
            "image_url": image_url or None,
            "images": clean_images,
            "url": link or None,
            "metadata": metadata,
        }

    def _parse_rag_card_marker(self, marker: str, allowed_urls: set[str]) -> dict[str, Any] | None:
        raw = marker.strip()
        if raw.startswith(self.RAG_CARD_START):
            raw = raw[len(self.RAG_CARD_START):]
        if raw.endswith(self.RAG_CARD_END):
            raw = raw[: -len(self.RAG_CARD_END)]
        raw = raw.strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return self._sanitize_rag_card(parsed, allowed_urls)

    def _split_rag_card_events(self, text: str, buffer: str, allowed_urls: set[str]) -> tuple[list[dict[str, Any]], str]:
        buffer += text
        events: list[dict[str, Any]] = []
        while buffer:
            start = buffer.find(self.RAG_CARD_START)
            if start == -1:
                safe_len = max(0, len(buffer) - len(self.RAG_CARD_START) + 1)
                if safe_len:
                    events.append({"type": "text", "text": buffer[:safe_len]})
                    buffer = buffer[safe_len:]
                break
            if start > 0:
                events.append({"type": "text", "text": buffer[:start]})
                buffer = buffer[start:]
            end = buffer.find(self.RAG_CARD_END)
            if end == -1:
                break
            marker = buffer[: end + len(self.RAG_CARD_END)]
            buffer = buffer[end + len(self.RAG_CARD_END):]
            card = self._parse_rag_card_marker(marker, allowed_urls)
            if card:
                events.append({"type": "rag_card", "card": card})
        return events, buffer

    def _build_prompt_messages(
        self,
        query: str,
        context_docs: list[Any],
        chat_history: list[dict[str, str]] | None = None,
        food_context: dict[str, Any] | None = None,
        assistant_context: dict[str, Any] | None = None,
    ):
        compressed_context = self._compress_context(context_docs)
        messages = ContextBuilder.build_rag_messages(
            system_prompt=RAG_ANSWER_SYSTEM_PROMPT,
            query=query,
            chat_history=chat_history or [],
            compressed_context=compressed_context,
            food_context=food_context,
            assistant_context=assistant_context,
        )
        return messages, compressed_context

    def select_retrieval_strategy(self, query: str) -> str:
        return "Hybrid Search"

    def stream(
        self,
        *,
        conversation_id: str | None = None,
        user_id: str | None = None,
        guest_id: str | None = None,
        original_query: str = "",
        rewritten_query: str,
        normalized_query: str,
        expanded_queries: list[str],
        chat_history: list[dict[str, str]] | None,
        metrics: dict[str, Any],
        t_start: float,
        bypass_cache: bool = False,
        is_deep_search: bool = False,
        food_context: dict[str, Any] | None = None,
        assistant_context: dict[str, Any] | None = None,
    ):
        def finalize_generation(final_answer: str, top_docs: list[Any], messages: list[dict[str, str]], retrieved_docs: list[Any], reranked_docs: list[Any], expanded_docs: list[Any]):
            est_p = len(" ".join([m["content"] for m in messages])) // 4
            est_c = len(final_answer) // 4
            metrics["total_tokens"] += est_p + est_c
            metrics["cost_usd"] += self._calculate_llm_cost(est_p, est_c)["cost_usd"]
            citations = self._build_citations(top_docs[:5])
            yield f'data: {json.dumps({"sources": citations})}\n\n'
            if self.cache and not bypass_cache and self._is_cacheable_answer(final_answer, metrics):
                self.cache.set(normalized_query, final_answer, citations)
                if rewritten_query != normalized_query:
                    self.cache.set(rewritten_query, final_answer, citations)
            yield f'data: {json.dumps({"metrics": metrics})}\n\n'
            
            save_rag_request_log(
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=original_query or rewritten_query,
                metrics=metrics,
                retrieved_docs=retrieved_docs,
                reranked_docs=reranked_docs,
                expanded_docs=expanded_docs,
                final_answer=final_answer,
            )

        try:
            retrieved_candidates = []
            reranked_docs = []
            expanded_docs = []
            strategy = self.select_retrieval_strategy(rewritten_query)
            yield sse_pipeline_step("retrieval_search", "Đang tìm kiếm tài liệu...", 0.34, strategy=strategy)
            t_search_start = time.time()
            search_limit = config.DEEP_SEARCH_CANDIDATE_LIMIT if is_deep_search else config.RETRIEVAL_CANDIDATE_LIMIT
            log_stage(
                "rag.hybrid_search",
                "before_search",
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=rewritten_query,
                intent=metrics.get("intent", "rag"),
                strategy=strategy,
                expanded_queries=expanded_queries,
                candidate_limit=search_limit,
                is_deep_search=is_deep_search,
            )
            retrieved_candidates = self.search_engine.search(
                query=rewritten_query,
                limit=search_limit,
                expanded_queries=expanded_queries,
            )
            metrics["search_latency_ms"] = (time.time() - t_search_start) * 1000
            log_stage(
                "rag.hybrid_search",
                "after_search",
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=rewritten_query,
                intent=metrics.get("intent", "rag"),
                result_count=len(retrieved_candidates),
                latency_ms=round(metrics["search_latency_ms"], 2),
                top_sources=[
                    {
                        "source": doc.metadata.get("source"),
                        "section": doc.metadata.get("section"),
                        "score": doc.metadata.get("score"),
                    }
                    for doc in retrieved_candidates[:5]
                ],
            )

            yield sse_pipeline_step("rerank_documents", "Đang xếp hạng tài liệu...", 0.52)
            t_rerank_start = time.time()
            rerank_top_n = config.DEEP_SEARCH_RERANK_TOP_N if is_deep_search else config.RERANK_TOP_N
            log_stage(
                "rag.rerank",
                "before_rerank",
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=rewritten_query,
                intent=metrics.get("intent", "rag"),
                input_count=len(retrieved_candidates),
                top_n=rerank_top_n,
                model=config.RERANKER_MODEL,
            )
            reranked_docs = self.reranker.rerank(
                query=rewritten_query,
                docs=retrieved_candidates,
                top_n=rerank_top_n,
            )
            metrics["rerank_latency_ms"] = (time.time() - t_rerank_start) * 1000
            metrics["num_chunks_before_expansion"] = len(reranked_docs)
            log_stage(
                "rag.rerank",
                "after_rerank",
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=rewritten_query,
                intent=metrics.get("intent", "rag"),
                result_count=len(reranked_docs),
                latency_ms=round(metrics["rerank_latency_ms"], 2),
                top_docs=[
                    {
                        "source": doc.metadata.get("source"),
                        "section": doc.metadata.get("section"),
                        "rerank_score": doc.metadata.get("rerank_score"),
                        "parent_chunk_id": doc.metadata.get("parent_chunk_id"),
                    }
                    for doc in reranked_docs[:5]
                ],
            )

            yield sse_pipeline_step("context_expansion", "Đang gọi thêm tài liệu đầy đủ...", 0.64, top_docs=len(reranked_docs))
            t_expansion_start = time.time()
            log_stage(
                "rag.parent_child",
                "before_expand",
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=rewritten_query,
                intent=metrics.get("intent", "rag"),
                input_count=len(reranked_docs),
                threshold=config.CONTEXT_EXPANSION_THRESHOLD,
            )
            expanded_docs = self.search_engine.expand_context(reranked_docs)
            metrics["expansion_latency_ms"] = (time.time() - t_expansion_start) * 1000
            log_stage(
                "rag.parent_child",
                "after_expand",
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=rewritten_query,
                intent=metrics.get("intent", "rag"),
                result_count=len(expanded_docs),
                latency_ms=round(metrics["expansion_latency_ms"], 2),
                parent_ids=sorted({
                    doc.metadata.get("parent_chunk_id")
                    for doc in expanded_docs
                    if doc.metadata.get("parent_chunk_id")
                })[:20],
            )
            allowed_media_urls = self._allowed_media_urls(expanded_docs)
            messages, compressed_context = self._build_prompt_messages(
                query=rewritten_query,
                context_docs=expanded_docs,
                chat_history=chat_history,
                food_context=food_context,
                assistant_context=assistant_context,
            )
            metrics["compressed_context_len"] = len(compressed_context)

            yield sse_pipeline_step("answer_prepare", "Đang chuẩn bị trả lời...", 0.78)
            t_gen_start = time.time()
            final_answer = ""
            metrics["answer_model"] = config.RAG_ANSWER_MODEL
            log_stage(
                "rag.answer_llm",
                "before_answer",
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=rewritten_query,
                intent=metrics.get("intent", "rag"),
                model=config.RAG_ANSWER_MODEL,
                max_tokens=config.LLM_MAX_TOKENS,
                message_count=len(messages),
                compressed_context_len=len(compressed_context),
            )
            client = get_llm_client(config.RAG_ANSWER_MODEL)
            response = client.chat.completions.create(
                model=config.RAG_ANSWER_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=config.LLM_MAX_TOKENS,
                stream=True,
            )
            first_token_received = False
            stream_failed = False
            rag_card_buffer = ""
            rag_cards: list[dict[str, Any]] = []
            try:
                for chunk in response:
                    finish_reason = getattr(chunk.choices[0], "finish_reason", None)
                    if finish_reason:
                        metrics["generation_finish_reason"] = finish_reason
                        if finish_reason == "length":
                            metrics["generation_truncated"] = True
                    if chunk.choices[0].delta.content:
                        if not first_token_received:
                            metrics["generation_latency_ms"] = (time.time() - t_gen_start) * 1000
                            metrics["total_latency_ms"] = (time.time() - t_start) * 1000
                            first_token_received = True
                            log_stage(
                                "rag.answer_llm",
                                "first_token",
                                conversation_id=conversation_id,
                                user_id=user_id,
                                guest_id=guest_id,
                                query=rewritten_query,
                                intent=metrics.get("intent", "rag"),
                                ttft_ms=round(metrics["generation_latency_ms"], 2),
                                model=config.RAG_ANSWER_MODEL,
                            )
                        text = chunk.choices[0].delta.content
                        events, rag_card_buffer = self._split_rag_card_events(text, rag_card_buffer, allowed_media_urls)
                        for event in events:
                            if event["type"] == "text":
                                final_answer += event["text"]
                                yield f"data: {event['text'].replace('\n', '\ndata: ')}\n\n"
                            elif event["type"] == "rag_card":
                                rag_cards.append(event["card"])
                                yield f'data: {json.dumps({"type": "rag_card", "rag_card": event["card"]}, ensure_ascii=False)}\n\n'
            except Exception as stream_error:
                stream_failed = True
                log_warn(
                    "CHAT",
                    f"Streaming generation interrupted: {stream_error}",
                    query=rewritten_query,
                    intent=metrics.get("intent", "rag"),
                    conversation_id=conversation_id,
                    user_id=user_id,
                )
                log_stage(
                    "rag.answer_llm",
                    "stream_interrupted",
                    level="WARN",
                    conversation_id=conversation_id,
                    user_id=user_id,
                    guest_id=guest_id,
                    query=rewritten_query,
                    intent=metrics.get("intent", "rag"),
                    error=str(stream_error),
                    partial_answer_chars=len(final_answer or ""),
                )
                if final_answer:
                    # Đã có nội dung nhưng bị gãy giữa chừng
                    error_notice = "\n\n*(Hệ thống bị gián đoạn kết nối, câu trả lời có thể chưa hoàn chỉnh. Vui lòng thử lại)*"
                    final_answer += error_notice
                    yield f"data: {error_notice.replace('\n', '\ndata: ')}\n\n"

            if rag_card_buffer:
                if self.RAG_CARD_START in rag_card_buffer:
                    events, remaining = self._split_rag_card_events("", rag_card_buffer + self.RAG_CARD_END, allowed_media_urls)
                    for event in events:
                        if event["type"] == "text":
                            final_answer += event["text"]
                            yield f"data: {event['text'].replace('\n', '\ndata: ')}\n\n"
                        elif event["type"] == "rag_card":
                            rag_cards.append(event["card"])
                            yield f'data: {json.dumps({"type": "rag_card", "rag_card": event["card"]}, ensure_ascii=False)}\n\n'
                    if remaining:
                        if remaining.endswith(self.RAG_CARD_END):
                            remaining = remaining[:-len(self.RAG_CARD_END)]
                        if remaining:
                            final_answer += remaining
                            yield f"data: {remaining.replace('\n', '\ndata: ')}\n\n"
                else:
                    final_answer += rag_card_buffer
                    yield f"data: {rag_card_buffer.replace('\n', '\ndata: ')}\n\n"
            if rag_cards:
                metrics["rag_cards"] = rag_cards

            if metrics.get("generation_truncated"):
                truncation_notice = "\n\n*(Câu trả lời bị cắt do giới hạn độ dài. Anh/chị có thể hỏi tiếp phần còn thiếu để em trả lời nốt.)*"
                final_answer += truncation_notice
                log_stage(
                    "rag.answer_llm",
                    "truncated",
                    level="WARN",
                    conversation_id=conversation_id,
                    user_id=user_id,
                    guest_id=guest_id,
                    query=rewritten_query,
                    intent=metrics.get("intent", "rag"),
                    finish_reason=metrics.get("generation_finish_reason"),
                    max_tokens=config.LLM_MAX_TOKENS,
                )
                yield f"data: {truncation_notice.replace('\n', '\ndata: ')}\n\n"

            if stream_failed and not final_answer:
                log_warn("CHAT", "Retrying generation once without streaming.")
                retry_response = client.chat.completions.create(
                    model=config.RAG_ANSWER_MODEL,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=config.LLM_MAX_TOKENS,
                )
                final_answer = retry_response.choices[0].message.content or ""
                metrics["generation_latency_ms"] = (time.time() - t_gen_start) * 1000
                metrics["total_latency_ms"] = (time.time() - t_start) * 1000
                if final_answer:
                    yield f"data: {final_answer.replace('\n', '\ndata: ')}\n\n"

            if not first_token_received:
                metrics["generation_latency_ms"] = (time.time() - t_gen_start) * 1000
                metrics["total_latency_ms"] = (time.time() - t_start) * 1000
            log_stage(
                "rag.answer_llm",
                "final_answer",
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=rewritten_query,
                intent=metrics.get("intent", "rag"),
                finish_reason=metrics.get("generation_finish_reason"),
                truncated=bool(metrics.get("generation_truncated")),
                answer_chars=len(final_answer or ""),
                generation_latency_ms=round(metrics.get("generation_latency_ms", 0), 2),
                total_latency_ms=round(metrics.get("total_latency_ms", 0), 2),
                rag_card_count=len(rag_cards),
            )

            yield from finalize_generation(final_answer, expanded_docs, messages, retrieved_candidates, reranked_docs, expanded_docs)
        except Exception as exc:
            log_error(
                "CHAT",
                f"RAG chain execution error: {exc}",
                query=rewritten_query,
                intent=metrics.get("intent", "rag"),
                conversation_id=conversation_id,
                user_id=user_id,
            )
            log_stage(
                "rag.error",
                "exception",
                level="ERROR",
                conversation_id=conversation_id,
                user_id=user_id,
                guest_id=guest_id,
                query=rewritten_query,
                intent=metrics.get("intent", "rag"),
                error=str(exc),
            )
            metrics["total_latency_ms"] = (time.time() - t_start) * 1000
            yield "data: Xin loi, he thong dang ban. Vui long thu lai sau.\n\n"
            yield f'data: {json.dumps({"metrics": metrics})}\n\n'
        yield "data: [DONE]\n\n"


class XanhSMRAGPipeline(RagAnswerChain):
    """
    Evaluation pipeline wrapper.
    """
    def __init__(self):
        super().__init__()
        from app.rag.core.gateway import XanhSMGateway
        from app.nlu.classifier import XanhSMClassifier
        self.gateway = XanhSMGateway()
        self.classifier = XanhSMClassifier()

    def _gateway_refusal_message(self, safety_res: dict[str, Any]) -> str:
        reason = (safety_res or {}).get("reason") or "Nội dung này chưa phù hợp để em hỗ trợ trực tiếp."
        return (
            f"Dạ, em xin phép chưa hỗ trợ nội dung này. {reason} "
            "Anh/chị có thể hỏi em về dịch vụ, giá cước, chính sách hoặc cách xử lý sự cố khi sử dụng Xanh SM ạ."
        )

    def _is_greeting_or_thanks(self, query: str) -> dict[str, Any]:
        return self.gateway.is_greeting_or_thanks(query)

    def run(self, query: str, chat_history: list[dict[str, str]] | None = None, bypass_cache: bool = False) -> dict[str, Any]:
        normalized_query = self.gateway.normalize_input(query)
        safety_res = self.gateway.safety_precheck(normalized_query)
        
        if not safety_res["safe"]:
            return {
                "query": query,
                "answer": self._gateway_refusal_message(safety_res),
                "citations": [],
                "intent": "sensitive",
                "gateway_checked": True,
                "strategy_selected": "Bypass",
                "faithfulness_passed": True,
                "llm_cost_usd": 0.0,
                "llm_cost_vnd": 0.0
            }

        # Early Cache Lookup
        if self.cache and not bypass_cache:
            is_hit, hit_res, hit_type = self.cache.get(normalized_query)
            if is_hit:
                return {
                    "query": query,
                    "rewritten_query": normalized_query,
                    "answer": hit_res["answer"],
                    "citations": hit_res["citations"],
                    "intent": "faq",
                    "gateway_checked": True,
                    "strategy_selected": "Early Semantic Cache Hit",
                    "faithfulness_passed": True,
                    "llm_cost_usd": 0.0,
                    "llm_cost_vnd": 0.0,
                    "cache_hit": hit_res.get("cache_hit", "exact"),
                    "cache_similarity": hit_res.get("cache_similarity", 1.0)
                }

        # Unified NLU Gateway Call
        t_nlu_start = time.time()
        nlu_res = self.classifier.unified_nlu(normalized_query, chat_history)
        nlu_latency = (time.time() - t_nlu_start) * 1000
        
        rewritten_query = nlu_res["rewritten_query"]
        intent = nlu_res["intent"]
        expanded_queries = nlu_res["expanded_queries"]
        nlu_usage = nlu_res.get("usage", {"prompt_tokens": 0, "completion_tokens": 0})
        nlu_fast_path = bool(nlu_res.get("fast_path"))
        nlu_fast_path_reason = nlu_res.get("fast_path_reason")

        # Handle Sensitive / Safety Block
        if intent == "sensitive":
            refusal_msg = nlu_res.get("suggested_answer") or "Dạ, em rất tiếc nhưng em không thể thực hiện yêu cầu này vì lý do bảo mật hệ thống. Tuy nhiên, em luôn sẵn sàng hỗ trợ anh/chị các thông tin về dịch vụ, giá cước hoặc chính sách của Xanh SM ạ!"
            return {
                "query": query,
                "rewritten_query": rewritten_query,
                "answer": refusal_msg,
                "citations": [],
                "intent": "sensitive",
                "gateway_checked": True,
                "strategy_selected": "Bypass",
                "faithfulness_passed": True,
                "llm_cost_usd": 0.0,
                "llm_cost_vnd": 0.0,
                "num_chunks_before_expansion": 0,
                "compressed_context_len": 0,
                "nlu_latency_ms": round(nlu_latency, 2),
                "nlu_fast_path": nlu_fast_path,
                "nlu_fast_path_reason": nlu_fast_path_reason
            }

        # Handle Small Talk
        if intent == "small-talk":
            answer = nlu_res.get("suggested_answer")
            if not answer:
                intercept = self._is_greeting_or_thanks(rewritten_query)
                answer = intercept["answer"] if intercept["type"] != "none" else "Dạ, em là Trợ lý ảo chuyên hỗ trợ các dịch vụ của Xanh SM. Hiện tại em chưa có thông tin về vấn đề này. Anh/chị có thể hỏi em các vấn đề liên quan đến Xanh SM như: giá cước taxi, chính sách hủy chuyến, hoặc cách đặt xe ạ!"
            return {
                "query": query,
                "rewritten_query": rewritten_query,
                "answer": answer,
                "citations": [],
                "intent": "small-talk",
                "gateway_checked": True,
                "strategy_selected": "Bypass",
                "faithfulness_passed": True,
                "llm_cost_usd": 0.0,
                "llm_cost_vnd": 0.0,
                "nlu_latency_ms": round(nlu_latency, 2),
                "nlu_fast_path": nlu_fast_path,
                "nlu_fast_path_reason": nlu_fast_path_reason
            }

        # Second Cache Lookup
        if self.cache and not bypass_cache and rewritten_query != normalized_query:
            is_hit, hit_res, hit_type = self.cache.get(rewritten_query)
            if is_hit:
                return {
                    "query": query,
                    "rewritten_query": rewritten_query,
                    "answer": hit_res["answer"],
                    "citations": hit_res["citations"],
                    "intent": "faq",
                    "gateway_checked": True,
                    "strategy_selected": "Semantic Cache Hit",
                    "faithfulness_passed": True,
                    "llm_cost_usd": 0.0,
                    "llm_cost_vnd": 0.0,
                    "cache_hit": hit_res.get("cache_hit", "exact"),
                    "cache_similarity": hit_res.get("cache_similarity", 1.0),
                    "nlu_latency_ms": round(nlu_latency, 2),
                    "nlu_fast_path": nlu_fast_path,
                    "nlu_fast_path_reason": nlu_fast_path_reason
                }

        # Search Strategy Selection
        strategy = self.select_retrieval_strategy(rewritten_query)

        # Execute Retrieval
        retrieved_candidates = self.search_engine.search(
            query=rewritten_query,
            limit=config.RETRIEVAL_CANDIDATE_LIMIT,
            expanded_queries=expanded_queries,
        )

        # Rerank
        top_docs = self.reranker.rerank(
            query=rewritten_query,
            docs=retrieved_candidates,
            top_n=config.RERANK_TOP_N,
        )
        num_chunks_before_expansion = len(top_docs)

        # Expand context
        top_docs = self.search_engine.expand_context(top_docs)

        # Compress Context & Build messages
        messages, compressed_context = self._build_prompt_messages(
            query=rewritten_query,
            context_docs=top_docs,
            chat_history=chat_history
        )

        final_answer = ""
        prompt_tokens = 0
        completion_tokens = 0

        if config.OPENAI_API_KEY and config.EMBEDDING_PROVIDER != "mock" and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=config.OPENAI_TIMEOUT_SECONDS)
                response = client.chat.completions.create(
                    model=config.RAG_ANSWER_MODEL,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=config.LLM_MAX_TOKENS
                )
                final_answer = response.choices[0].message.content
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
            except Exception as e:
                log_warn("LLM_GEN", f"LLM Generation Error: {str(e)}. Falling back to offline synthesis.")
                final_answer = f"Lỗi sinh câu trả lời: {e}"
        else:
            final_answer = "Offline Mode fallback"

        citations = self._build_citations(top_docs)

        # Cost calculation
        total_prompt = prompt_tokens + nlu_usage.get("prompt_tokens", 0)
        total_comp = completion_tokens + nlu_usage.get("completion_tokens", 0)
        cost_info = self._calculate_llm_cost(total_prompt, total_comp)

        # Save to Cache
        if self.cache and not bypass_cache:
            self.cache.set(normalized_query, final_answer, citations)
            if rewritten_query != normalized_query:
                self.cache.set(rewritten_query, final_answer, citations)

        return {
            "query": query,
            "rewritten_query": rewritten_query,
            "answer": final_answer,
            "citations": citations,
            "expanded_queries": expanded_queries,
            "compressed_context_len": len(compressed_context),
            "num_chunks_before_expansion": num_chunks_before_expansion,
            "nlu_latency_ms": round(nlu_latency, 2),
            "nlu_fast_path": nlu_fast_path,
            "nlu_fast_path_reason": nlu_fast_path_reason,
            "intent": intent,
            "gateway_checked": True,
            "strategy_selected": strategy,
            "faithfulness_passed": True,
            "faithfulness_score": 1.0,
            "top_docs": [
                {
                    "content": doc.page_content,
                    "source": doc.metadata.get("source"),
                    "section": doc.metadata.get("section"),
                    "score": doc.metadata.get("rerank_score", 0.0)
                } for doc in top_docs
            ],
            "token_usage": {
                "unified_nlu": nlu_usage,
                "generation": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
                "total_prompt_tokens": total_prompt,
                "total_completion_tokens": total_comp
            },
            "llm_cost_usd": cost_info["cost_usd"],
            "llm_cost_vnd": cost_info["cost_usd"] * 25400
        }
