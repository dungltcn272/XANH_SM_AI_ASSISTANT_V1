from __future__ import annotations

import json
import re
import time
from typing import Any

from openai import OpenAI

from app.assistant.events import sse_pipeline_step
from app.core.config import settings as config
from app.core.logger import log_warn, log_error
from app.rag.prompt import RAG_ANSWER_SYSTEM_PROMPT, RAG_ANSWER_USER_PROMPT_TEMPLATE
from app.retrieval.hybrid_search import XanhSMHybridSearch
from app.retrieval.reranker import XanhSMReranker


class RagAnswerChain:
    """RAG capability chain: retrieve, rerank, expand context, synthesize answer."""

    IMAGE_MARKDOWN_RE = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)\)')

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

    def _build_prompt_messages(self, query: str, context_docs: list[Any], chat_history: list[dict[str, str]] | None = None):
        compressed_context = self._compress_context(context_docs)
        messages = [{"role": "system", "content": RAG_ANSWER_SYSTEM_PROMPT.format(context=compressed_context)}]
        history_messages = []
        for turn in (chat_history or [])[-6:]:
            if isinstance(turn, dict) and turn.get("role") and turn.get("content"):
                history_messages.append({"role": turn["role"], "content": turn["content"]})
        messages.extend(history_messages)
        messages.append({"role": "user", "content": RAG_ANSWER_USER_PROMPT_TEMPLATE.format(query=query)})
        return messages, compressed_context

    def select_retrieval_strategy(self, query: str) -> str:
        return "Hybrid Search"

    def stream(
        self,
        *,
        rewritten_query: str,
        normalized_query: str,
        expanded_queries: list[str],
        chat_history: list[dict[str, str]] | None,
        metrics: dict[str, Any],
        t_start: float,
        bypass_cache: bool = False,
        is_deep_search: bool = False,
    ):
        def finalize_generation(final_answer: str, top_docs: list[Any], messages: list[dict[str, str]]):
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

        try:
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
            top_docs = self.reranker.rerank(
                query=rewritten_query,
                docs=retrieved_candidates,
                top_n=rerank_top_n,
            )
            metrics["rerank_latency_ms"] = (time.time() - t_rerank_start) * 1000
            metrics["num_chunks_before_expansion"] = len(top_docs)

            yield sse_pipeline_step("context_expansion", "Đang gọi thêm tài liệu đầy đủ...", 0.64, top_docs=len(top_docs))
            top_docs = self.search_engine.expand_context(top_docs)
            messages, compressed_context = self._build_prompt_messages(
                query=rewritten_query,
                context_docs=top_docs,
                chat_history=chat_history,
            )
            metrics["compressed_context_len"] = len(compressed_context)

            yield sse_pipeline_step("answer_prepare", "Đang chuẩn bị trả lời...", 0.78)
            t_gen_start = time.time()
            final_answer = ""
            client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=config.OPENAI_TIMEOUT_SECONDS)
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=config.LLM_MAX_TOKENS,
                stream=True,
            )
            first_token_received = False
            stream_failed = False
            try:
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        if not first_token_received:
                            metrics["generation_latency_ms"] = (time.time() - t_gen_start) * 1000
                            metrics["total_latency_ms"] = (time.time() - t_start) * 1000
                            first_token_received = True
                        text = chunk.choices[0].delta.content
                        final_answer += text
                        yield f"data: {text.replace('\n', '\ndata: ')}\n\n"
            except Exception as stream_error:
                stream_failed = True
                log_warn("CHAT", f"Streaming generation interrupted: {stream_error}")

            if stream_failed and not final_answer:
                log_warn("CHAT", "Retrying generation once without streaming.")
                retry_response = client.chat.completions.create(
                    model=config.LLM_MODEL,
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

            yield from finalize_generation(final_answer, top_docs, messages)
        except Exception as exc:
            log_error("CHAT", f"RAG chain execution error: {exc}")
            metrics["total_latency_ms"] = (time.time() - t_start) * 1000
            yield "data: Xin loi, he thong dang ban. Vui long thu lai sau.\n\n"
            yield f'data: {json.dumps({"metrics": metrics})}\n\n'
        yield "data: [DONE]\n\n"
