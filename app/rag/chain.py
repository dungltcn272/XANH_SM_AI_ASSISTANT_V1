from __future__ import annotations

import json
import re
import time
from typing import Any

from app.assistant.events import sse_pipeline_step
from app.core.config import settings as config
from app.core.llm import get_llm_client
from app.core.logger import log_warn, log_error
from app.prompts import RAG_ANSWER_SYSTEM_PROMPT
from app.rag.hybrid_search import XanhSMHybridSearch
from app.rag.reranker import XanhSMReranker
from app.rag.trace_store import save_rag_request_log
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
            if self.cache and not bypass_cache and final_answer:
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
            retrieved_candidates = self.search_engine.search(
                query=rewritten_query,
                limit=search_limit,
                expanded_queries=expanded_queries,
            )
            metrics["search_latency_ms"] = (time.time() - t_search_start) * 1000

            yield sse_pipeline_step("rerank_documents", "Đang xếp hạng tài liệu...", 0.52)
            t_rerank_start = time.time()
            rerank_top_n = config.DEEP_SEARCH_RERANK_TOP_N if is_deep_search else config.RERANK_TOP_N
            reranked_docs = self.reranker.rerank(
                query=rewritten_query,
                docs=retrieved_candidates,
                top_n=rerank_top_n,
            )
            metrics["rerank_latency_ms"] = (time.time() - t_rerank_start) * 1000
            metrics["num_chunks_before_expansion"] = len(reranked_docs)

            yield sse_pipeline_step("context_expansion", "Đang gọi thêm tài liệu đầy đủ...", 0.64, top_docs=len(reranked_docs))
            expanded_docs = self.search_engine.expand_context(reranked_docs)
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
                    if chunk.choices[0].delta.content:
                        if not first_token_received:
                            metrics["generation_latency_ms"] = (time.time() - t_gen_start) * 1000
                            metrics["total_latency_ms"] = (time.time() - t_start) * 1000
                            first_token_received = True
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
                log_warn("CHAT", f"Streaming generation interrupted: {stream_error}")
                if final_answer:
                    # Đã có nội dung nhưng bị gãy giữa chừng
                    error_notice = "\n\n*(Hệ thống bị gián đoạn kết nối, câu trả lời có thể chưa hoàn chỉnh. Vui lòng thử lại)*"
                    final_answer += error_notice
                    yield f"data: {error_notice.replace('\n', '\ndata: ')}\n\n"

            if rag_card_buffer:
                events, _ = self._split_rag_card_events("", rag_card_buffer + self.RAG_CARD_END if self.RAG_CARD_START in rag_card_buffer else rag_card_buffer, allowed_media_urls)
                for event in events:
                    if event["type"] == "text":
                        final_answer += event["text"]
                        yield f"data: {event['text'].replace('\n', '\ndata: ')}\n\n"
                    elif event["type"] == "rag_card":
                        rag_cards.append(event["card"])
                        yield f'data: {json.dumps({"type": "rag_card", "rag_card": event["card"]}, ensure_ascii=False)}\n\n'
            if rag_cards:
                metrics["rag_cards"] = rag_cards

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

            yield from finalize_generation(final_answer, expanded_docs, messages, retrieved_candidates, reranked_docs, expanded_docs)
        except Exception as exc:
            log_error("CHAT", f"RAG chain execution error: {exc}")
            metrics["total_latency_ms"] = (time.time() - t_start) * 1000
            yield "data: Xin loi, he thong dang ban. Vui long thu lai sau.\n\n"
            yield f'data: {json.dumps({"metrics": metrics})}\n\n'
        yield "data: [DONE]\n\n"
