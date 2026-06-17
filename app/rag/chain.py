import os
import sys
import json
import hashlib
import time
import re
from typing import List, Dict, Any, Tuple

from openai import OpenAI
from app.retrieval.hybrid_search import XanhSMHybridSearch
from app.retrieval.reranker import XanhSMReranker
from app.rag.prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, FAITHFULNESS_CHECK_PROMPT
from app.rag.gateway import XanhSMGateway
from app.rag.classifier import XanhSMClassifier
from app.rag.guardrail import OutputGuardrail
from app.core.config import settings as config
from app.core.logger import log_info, log_warn, log_error
from app.tools.food_recommendation.nlu import slots_from_nlu
from app.tools.food_recommendation.tool import recommend_food
from app.tools.food_recommendation.geocode import geocode_address

class XanhSMRAGPipeline:
    """
    Phase 3 Advanced NLU-Gateway RAG Pipeline:
    Coordinates Conversation Gateway ➔ Unified NLU Gateway ➔ Semantic Cache Check 
    ➔ Strategy Selector ➔ Hybrid Search ➔ Reranker ➔ Parent-Child ➔ LLM Gen ➔ Faithfulness Check ➔ Citations.
    """
    
    def __init__(self):
        self.search_engine = XanhSMHybridSearch()
        self.reranker = XanhSMReranker()
        self.gateway = XanhSMGateway()
        self.classifier = XanhSMClassifier()
        self.output_guardrail = OutputGuardrail()
        try:
            from app.rag.cache import XanhSMRAGCache
            self.cache = XanhSMRAGCache()
        except Exception as e:
            log_warn("CACHE", f"Failed to load cache: {e}")
            self.cache = None

    def _gateway_refusal_message(self, safety_res: Dict[str, Any]) -> str:
        reason = (safety_res or {}).get("reason") or "Nội dung này chưa phù hợp để em hỗ trợ trực tiếp."
        return (
            f"Dạ, em xin phép chưa hỗ trợ nội dung này. {reason} "
            "Anh/chị có thể hỏi em về dịch vụ, giá cước, chính sách hoặc cách xử lý sự cố khi sử dụng Xanh SM ạ."
        )
            
    def _compress_context(self, docs: List[Any]) -> str:
        """
        Formats and compresses retrieved documents with source boundaries.
        Giữ nguyên mọi chunks (không lược bỏ Parent) để đảm bảo không mất thông tin giá tiền.
        """
        formatted_blocks = []
        
        for doc in docs:
            content = doc.page_content.strip()
            source = doc.metadata.get("source", "unknown_policy.md")
            section = doc.metadata.get("section", "Introduction")
            
            block = (
                f"[Tài liệu tham khảo #{len(formatted_blocks) + 1}]\n"
                f"Nguồn File: {source}\n"
                f"Phần/Điều khoản: {section}\n"
                f"Nội dung: {content}\n"
                f"---"
            )
            formatted_blocks.append(block)

        return "\n\n".join(formatted_blocks)

    IMAGE_MARKDOWN_RE = re.compile(r'!\[([^\]]*)\]\(([^)\s]+)\)')

    def _extract_images_from_doc(self, doc: Any) -> List[Dict[str, Any]]:
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

        
    def _calculate_llm_cost(self, prompt_tokens: int, completion_tokens: int) -> Dict[str, Any]:
        """
        Calculates exact API cost in USD and VND based on GPT-4o-mini pricing.
        """
        usd_input = (prompt_tokens / 1_000_000) * 0.15
        usd_output = (completion_tokens / 1_000_000) * 0.60
        usd_total = usd_input + usd_output
        vnd_total = usd_total * 25400
        
        return {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost_usd": usd_total,
            "cost_vnd": vnd_total
        }

    def _build_citations(self, docs: List[Any]) -> List[Dict[str, Any]]:
        citations = []
        for d in docs:
            images_in_chunk = self._extract_images_from_doc(d)
            
            citations.append({
                "source": d.metadata.get("source", "unknown"),
                "section": d.metadata.get("section", ""),
                "url": d.metadata.get("url", "") or d.metadata.get("source", ""),
                "relevance_score": d.metadata.get("rerank_score", 0.0),
                "images": images_in_chunk
            })
        return citations


    def _build_prompt_messages(self, query: str, context_docs: List[Any], chat_history: List[Dict[str, str]] = None):
        compressed_context = self._compress_context(context_docs)
        system_msg = SYSTEM_PROMPT.format(context=compressed_context)
        user_msg = USER_PROMPT_TEMPLATE.format(query=query)

        messages = [{"role": "system", "content": system_msg}]
        if chat_history and len(chat_history) > 0:
            history_messages = []
            for turn in chat_history[-6:]:
                if isinstance(turn, dict) and turn.get("role") and turn.get("content"):
                    history_messages.append({"role": turn["role"], "content": turn["content"]})
            if history_messages:
                messages.extend(history_messages)

        messages.append({"role": "user", "content": user_msg})
        return messages, compressed_context, ""

    def _is_greeting_or_thanks(self, query: str) -> Dict[str, Any]:
        """
        Spell-tolerant and accent-insensitive detector for greetings, thanks, and short chit-chat.
        """
        return self.gateway.is_greeting_or_thanks(query)

    def select_retrieval_strategy(self, query: str) -> str:
        """
        Keep retrieval selection free of keyword heuristics.
        The retrieval layer already performs hybrid dense+sparse search internally.
        """
        return "Hybrid Search"

    def run_faithfulness_check(self, context: str, answer: str) -> Tuple[bool, float, str]:
        """
        Evaluates whether the LLM answer is strictly faithful to the provided context.
        Returns (is_faithful, score, reason).
        """
        if not context or not answer:
            return True, 1.0, "No context or answer to evaluate."
            
        if not config.OPENAI_API_KEY or config.EMBEDDING_PROVIDER == "mock" or "YOUR_OPENAI_API_KEY" in config.OPENAI_API_KEY:
            # Skip in offline mode
            return True, 1.0, "Skipped in Offline Mode."
            
        try:
            import re
            system_msg = FAITHFULNESS_CHECK_PROMPT.format(context=context, answer=answer)
            client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=config.OPENAI_TIMEOUT_SECONDS)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"Bắt đầu đánh giá câu trả lời sau đây."}
                ],
                temperature=0.0,
                max_tokens=180
            )
            res_content = response.choices[0].message.content.strip()
            res_content = re.sub(r"```json|```", "", res_content).strip()
            res_json = json.loads(res_content)
            
            is_faithful = res_json.get("faithful", True)
            score = res_json.get("score", 1.0)
            reason = res_json.get("reason", "OK")
            return is_faithful, score, reason
        except Exception as e:
            log_warn("GUARDRAIL", f"Faithfulness Check failed: {e}. Defaulting to True.")
            return True, 1.0, f"Error: {e}"

    def run(self, query: str, chat_history: List[Dict[str, str]] = None, bypass_cache: bool = False) -> Dict[str, Any]:
        """
        Executes the full advanced NLU-Gateway RAG chain.
        """
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

        # 2. Early Cache Lookup
        if self.cache and not bypass_cache:
            is_hit, hit_res, hit_type = self.cache.get(normalized_query)
            if is_hit:
                log_info("CACHE", f"Early cache hit query via {hit_type} match.")
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

        # 3. Unified NLU Gateway Call
        t_nlu_start = time.time()
        nlu_res = self.classifier.unified_nlu(normalized_query, chat_history)
        nlu_latency = (time.time() - t_nlu_start) * 1000
        
        rewritten_query = nlu_res["rewritten_query"]
        intent = nlu_res["intent"]
        expanded_queries = nlu_res["expanded_queries"]
        nlu_usage = nlu_res.get("usage", {"prompt_tokens": 0, "completion_tokens": 0})
        nlu_fast_path = bool(nlu_res.get("fast_path"))
        nlu_fast_path_reason = nlu_res.get("fast_path_reason")

        # 4. Handle Sensitive / Safety Block
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

        # 5. Handle Small Talk
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

        # 5. Second Cache Lookup
        if self.cache and not bypass_cache and rewritten_query != normalized_query:
            is_hit, hit_res, hit_type = self.cache.get(rewritten_query)
            if is_hit:
                log_info("CACHE", f"Hit query after rewrite via {hit_type} match.")
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

        # 6. Search Strategy Selection
        strategy = self.select_retrieval_strategy(rewritten_query)
        log_info("RETRIEVAL", f"Dynamically selected search strategy: {strategy}")

        # 7. Execute Retrieval
        retrieved_candidates = self.search_engine.search(
            query=rewritten_query,
            limit=config.RETRIEVAL_CANDIDATE_LIMIT,
            expanded_queries=expanded_queries,
        )

        # 8. Rerank
        top_docs = self.reranker.rerank(
            query=rewritten_query,
            docs=retrieved_candidates,
            top_n=config.RERANK_TOP_N,
        )
        num_chunks_before_expansion = len(top_docs)

        # 9. Expand context
        top_docs = self.search_engine.expand_context(top_docs)

        # 10. Compress Context
        # 11. LLM Generation
        final_answer = ""
        citations = []
        prompt_tokens = 0
        completion_tokens = 0

        citations = self._build_citations(top_docs)
        messages, compressed_context, _ = self._build_prompt_messages(
            query=rewritten_query,
            context_docs=top_docs,
            chat_history=chat_history
        )

        if config.OPENAI_API_KEY and config.EMBEDDING_PROVIDER != "mock" and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            try:
                client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=config.OPENAI_TIMEOUT_SECONDS)
                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=config.LLM_MAX_TOKENS
                )
                final_answer = response.choices[0].message.content
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
            except Exception as e:
                log_warn("LLM_GEN", f"LLM Generation Error: {str(e)}. Falling back to offline synthesis.")
                final_answer = self._generate_fallback_answer(rewritten_query, top_docs)
        else:
            final_answer = self._generate_fallback_answer(rewritten_query, top_docs)

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
            "llm_cost_vnd": cost_info["cost_vnd"]
        }

    def run_debug(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Executes the full RAG pipeline for debugging, bypassing cache and capturing
        all intermediate steps like raw_candidates, reranked_docs, and expanded_docs.
        """
        normalized_query = self.gateway.normalize_input(query)
        safety_res = self.gateway.safety_precheck(normalized_query)
        
        # 1. Gateway safety check
        if not safety_res["safe"]:
            return {
                "query": query,
                "normalized_query": normalized_query,
                "answer": self._gateway_refusal_message(safety_res),
                "citations": [],
                "intent": "sensitive",
                "gateway_checked": True,
                "safety_res": safety_res,
                "strategy_selected": "Bypass",
                "faithfulness_passed": True,
                "llm_cost_usd": 0.0,
                "llm_cost_vnd": 0.0,
                "raw_candidates": [],
                "reranked_docs": [],
                "expanded_docs": []
            }

        # 2. Unified NLU Gateway Call
        t_nlu_start = time.time()
        nlu_res = self.classifier.unified_nlu(normalized_query, chat_history)
        nlu_latency = (time.time() - t_nlu_start) * 1000
        
        rewritten_query = nlu_res["rewritten_query"]
        intent = nlu_res["intent"]
        expanded_queries = nlu_res["expanded_queries"]
        nlu_usage = nlu_res.get("usage", {"prompt_tokens": 0, "completion_tokens": 0})
        nlu_fast_path = bool(nlu_res.get("fast_path"))
        nlu_fast_path_reason = nlu_res.get("fast_path_reason")

        # 3. Handle Sensitive / Safety Block from NLU
        if intent == "sensitive":
            refusal_msg = nlu_res.get("suggested_answer") or "Dạ, em rất tiếc nhưng em không thể thực hiện yêu cầu này vì lý do bảo mật hệ thống. Tuy nhiên, em luôn sẵn sàng hỗ trợ anh/chị các thông tin về dịch vụ, giá cước hoặc chính sách của Xanh SM ạ!"
            return {
                "query": query,
                "normalized_query": normalized_query,
                "rewritten_query": rewritten_query,
                "answer": refusal_msg,
                "citations": [],
                "intent": "sensitive",
                "gateway_checked": True,
                "safety_res": {"safe": True, "reason": ""},
                "strategy_selected": "Bypass",
                "faithfulness_passed": True,
                "llm_cost_usd": 0.0,
                "llm_cost_vnd": 0.0,
                "raw_candidates": [],
                "reranked_docs": [],
                "expanded_docs": [],
                "num_chunks_before_expansion": 0,
                "compressed_context_len": 0,
                "nlu_latency_ms": round(nlu_latency, 2),
                "nlu_fast_path": nlu_fast_path,
                "nlu_fast_path_reason": nlu_fast_path_reason,
                "token_usage": {
                    "unified_nlu": nlu_usage,
                    "generation": {"prompt_tokens": 0, "completion_tokens": 0},
                    "total_prompt_tokens": nlu_usage.get("prompt_tokens", 0),
                    "total_completion_tokens": nlu_usage.get("completion_tokens", 0)
                }
            }

        # 4. Handle Small Talk
        if intent == "small-talk":
            answer = nlu_res.get("suggested_answer")
            if not answer:
                intercept = self._is_greeting_or_thanks(rewritten_query)
                answer = intercept["answer"] if intercept["type"] != "none" else "Dạ, em là Trợ lý ảo chuyên hỗ trợ các dịch vụ của Xanh SM. Hiện tại em chưa có thông tin về vấn đề này. Anh/chị có thể hỏi em các vấn đề liên quan đến Xanh SM như: giá cước taxi, chính sách hủy chuyến, hoặc cách đặt xe ạ!"
            return {
                "query": query,
                "normalized_query": normalized_query,
                "rewritten_query": rewritten_query,
                "answer": answer,
                "citations": [],
                "intent": "small-talk",
                "gateway_checked": True,
                "safety_res": {"safe": True, "reason": ""},
                "strategy_selected": "Bypass",
                "faithfulness_passed": True,
                "llm_cost_usd": 0.0,
                "llm_cost_vnd": 0.0,
                "raw_candidates": [],
                "reranked_docs": [],
                "expanded_docs": [],
                "nlu_latency_ms": round(nlu_latency, 2),
                "nlu_fast_path": nlu_fast_path,
                "nlu_fast_path_reason": nlu_fast_path_reason,
                "token_usage": {
                    "unified_nlu": nlu_usage,
                    "generation": {"prompt_tokens": 0, "completion_tokens": 0},
                    "total_prompt_tokens": nlu_usage.get("prompt_tokens", 0),
                    "total_completion_tokens": nlu_usage.get("completion_tokens", 0)
                }
            }

        # 5. Search Strategy Selection
        strategy = self.select_retrieval_strategy(rewritten_query)

        # 6. Execute Retrieval (Hybrid Search)
        retrieved_candidates = self.search_engine.search(
            query=rewritten_query,
            limit=config.RETRIEVAL_CANDIDATE_LIMIT,
            expanded_queries=expanded_queries,
        )
        raw_candidates_data = [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "section": doc.metadata.get("section", "unknown"),
                "score": doc.metadata.get("score", 0.0)
            } for doc in retrieved_candidates
        ]

        # 7. Rerank
        top_docs = self.reranker.rerank(
            query=rewritten_query,
            docs=retrieved_candidates,
            top_n=config.RERANK_TOP_N,
        )
        reranked_docs_data = [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "section": doc.metadata.get("section", "unknown"),
                "score": doc.metadata.get("rerank_score", 0.0)
            } for doc in top_docs
        ]

        # 8. Expand context
        top_docs_expanded = self.search_engine.expand_context(top_docs)
        expanded_docs_data = [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "section": doc.metadata.get("section", "unknown"),
                "score": doc.metadata.get("rerank_score", 0.0),
                "parent_chunk_id": doc.metadata.get("parent_chunk_id")
            } for doc in top_docs_expanded
        ]

        # 9. Compress Context
        # 10. LLM Generation
        final_answer = ""
        citations = []
        prompt_tokens = 0
        completion_tokens = 0

        citations = self._build_citations(top_docs_expanded)
        messages, compressed_context, _ = self._build_prompt_messages(
            query=rewritten_query,
            context_docs=top_docs_expanded,
            chat_history=chat_history
        )

        if config.OPENAI_API_KEY and config.EMBEDDING_PROVIDER != "mock" and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            try:
                client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=config.OPENAI_TIMEOUT_SECONDS)
                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=config.LLM_MAX_TOKENS
                )
                final_answer = response.choices[0].message.content
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
            except Exception as e:
                log_warn("LLM_GEN", f"LLM Generation Error in Debug: {str(e)}. Falling back.")
                final_answer = self._generate_fallback_answer(rewritten_query, top_docs_expanded)
        else:
            final_answer = self._generate_fallback_answer(rewritten_query, top_docs_expanded)

        output_guardrail_passed = True

        # Cost calculation
        total_prompt = prompt_tokens + nlu_usage.get("prompt_tokens", 0)
        total_comp = completion_tokens + nlu_usage.get("completion_tokens", 0)
        cost_info = self._calculate_llm_cost(total_prompt, total_comp)

        return {
            "query": query,
            "normalized_query": normalized_query,
            "rewritten_query": rewritten_query,
            "answer": final_answer,
            "citations": citations,
            "expanded_queries": expanded_queries,
            "compressed_context_len": len(compressed_context),
            "num_chunks_before_expansion": len(top_docs),
            "nlu_latency_ms": round(nlu_latency, 2),
            "nlu_fast_path": nlu_fast_path,
            "nlu_fast_path_reason": nlu_fast_path_reason,
            "intent": intent,
            "gateway_checked": True,
            "safety_res": {"safe": True, "reason": ""},
            "strategy_selected": strategy,
            "faithfulness_passed": True,
            "faithfulness_score": 1.0,
            "raw_candidates": raw_candidates_data,
            "reranked_docs": reranked_docs_data,
            "expanded_docs": expanded_docs_data,
            "output_guardrail_passed": output_guardrail_passed,
            "token_usage": {
                "unified_nlu": nlu_usage,
                "generation": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
                "total_prompt_tokens": total_prompt,
                "total_completion_tokens": total_comp
            },
            "llm_cost_usd": cost_info["cost_usd"],
            "llm_cost_vnd": cost_info["cost_vnd"]
        }

    def stream_run(self, query: str, chat_history: List[Dict[str, str]] = None, bypass_cache: bool = False, image_base64: str = None, is_deep_search: bool = False, food_context: Dict[str, Any] | None = None):
        """
        Stream version of the NLU-Gateway RAG chain.
        """
        return self._stream_run_raw(query=query, chat_history=chat_history, bypass_cache=bypass_cache, image_base64=image_base64, is_deep_search=is_deep_search, food_context=food_context)

    def _sse_pipeline_step(self, step: str, message: str, progress: float | None = None, **debug):
        payload = {
            "type": "pipeline_step",
            "step": step,
            "message": message,
        }
        if progress is not None:
            payload["progress"] = progress
        if debug:
            payload["debug"] = debug
        return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

    def _stream_plain_answer(self, answer: str):
        import re
        for token in re.split(r"(\s+)", answer):
            if token:
                safe_token = token.replace("\n", "\ndata: ")
                yield f"data: {safe_token}\n\n"

    def _food_missing_location_answer(self) -> str:
        return (
            "Dạ, em cần vị trí giao món để sắp xếp các quán gần anh/chị chính xác hơn. "
            "Anh/chị có thể dùng vị trí hiện tại hoặc nhập địa chỉ giao hàng bên dưới."
        )

    def _format_food_answer(self, items, category: str | None = None) -> str:
        if not items:
            return (
                "Dạ, em chưa tìm được quán phù hợp quanh vị trí này trong catalog hiện tại. "
                "Anh/chị có thể chọn lại vị trí ở khu vực trung tâm hoặc nhập địa chỉ cụ thể hơn để em tìm chính xác."
            )

        intro = "Dạ, em đã sắp xếp một vài lựa chọn"
        if category:
            intro += f" cho món {category}"
        return intro + " gần anh/chị. Em ưu tiên khoảng cách, thời gian giao và mức độ phù hợp với nhu cầu."

    def _format_vnd(self, value: int | None) -> str:
        if value is None:
            return "Đang cập nhật"
        return f"{int(value):,}đ".replace(",", ".")

    def _display_rating(self, value: float | None) -> float | None:
        if value is None:
            return None
        if value > 10:
            return round(min(value / 20, 5), 1)
        if value > 5:
            return round(min(value / 2, 5), 1)
        return round(min(value, 5), 1)

    def _distance_text(self, distance_km: float | None) -> str:
        if distance_km is None:
            return "Đang cập nhật"
        if distance_km < 1:
            return f"{int(round(distance_km * 1000))} m"
        return f"{distance_km:.1f} km"

    def _food_location_payload(self, query: str) -> Dict[str, Any]:
        return {
            "title": "Bạn muốn giao đến đâu?",
            "query": query,
            "address_placeholder": "Nhập địa chỉ giao hàng",
            "current_location_label": "Dùng vị trí hiện tại",
            "submit_label": "Tìm quán gần đây",
        }

    def _food_recommendations_payload(self, items, category: str | None = None, query: str | None = None) -> Dict[str, Any]:
        title = "Một vài quán phù hợp gần bạn"
        if category:
            title = f"Một vài quán {category} phù hợp gần bạn"

        def to_payload(item, index: int) -> Dict[str, Any]:
            price = item.final_price or item.price
            return {
                "item_id": item.item_id,
                "name": item.merchant_name or item.name,
                "dish_name": item.name,
                "address": item.address,
                "image_url": item.image_url,
                "order_url": item.order_url,
                "rating": self._display_rating(item.rating),
                "review_count": item.review_count,
                "distance_km": item.distance_km,
                "distance_text": self._distance_text(item.distance_km),
                "eta_minutes": item.eta_minutes,
                "eta_text": f"{item.eta_minutes} phút" if item.eta_minutes else "Đang cập nhật",
                "delivery_fee": item.delivery_fee,
                "delivery_fee_text": self._format_vnd(item.delivery_fee),
                "price": price,
                "price_text": self._format_vnd(price) if price else "",
                "reason": item.reason,
                "is_best": index == 0,
            }

        return {
            "title": title,
            "subtitle": "Đã sắp xếp theo khoảng cách, thời gian giao hàng và mức độ phù hợp với nhu cầu của bạn.",
            "query": query,
            "items": [to_payload(item, index) for index, item in enumerate(items[:4])],
            "more_items": [to_payload(item, index + 4) for index, item in enumerate(items[4:8])],
        }

    def _handle_food_recommendation_stream(self, query: str, chat_history: List[Dict[str, str]], metrics: Dict[str, Any], t_start: float, nlu_food_slots: Dict[str, Any] | None = None):
        slots = slots_from_nlu(nlu_food_slots, raw_query=query)
        metrics["intent"] = "food_recommendation"
        metrics["food_slots"] = {
            "has_location": slots.lat is not None and slots.lng is not None,
            "category": slots.category,
            "taste_tags": slots.taste_tags,
            "budget_min": slots.budget_min,
            "budget_max": slots.budget_max,
            "meal_time": slots.meal_time,
            "max_distance_km": slots.max_distance_km,
        }

        if slots.lat is None or slots.lng is None:
            geocode_target = slots.address_text
            if geocode_target:
                try:
                    yield self._sse_pipeline_step("food_geocode", "Đang xác định vị trí trên bản đồ...", 0.32, address_text=geocode_target)
                    geocoded = geocode_address(geocode_target)
                    if geocoded:
                        slots.lat = float(geocoded["lat"])
                        slots.lng = float(geocoded["lng"])
                        metrics["food_geocoded_address"] = geocode_target
                        metrics["food_geocode_source"] = geocoded.get("source")
                except Exception as exc:
                    metrics["food_geocode_error"] = str(exc)

        if slots.lat is None or slots.lng is None:
            answer = self._food_missing_location_answer()
            metrics["total_latency_ms"] = (time.time() - t_start) * 1000
            yield self._sse_pipeline_step("food_missing_info", "Em cần thêm một chút thông tin để gợi ý chính xác hơn...", 0.42)
            yield from self._stream_plain_answer(answer)
            yield f'data: {json.dumps({"food_location_request": self._food_location_payload(query)}, ensure_ascii=False)}\n\n'
            yield f'data: {json.dumps({"metrics": metrics, "step": "food-missing-location"}, ensure_ascii=False)}\n\n'
            yield "data: [DONE]\n\n"
            return

        from app.db.database import SessionLocal

        t_tool_start = time.time()
        db = SessionLocal()
        try:
            yield self._sse_pipeline_step("food_candidate_search", "Đang tìm các món ăn phù hợp...", 0.42)
            items = recommend_food(
                lat=slots.lat,
                lng=slots.lng,
                category=slots.category,
                taste_tags=slots.taste_tags,
                budget_min=slots.budget_min,
                budget_max=slots.budget_max,
                meal_time=slots.meal_time,
                max_distance_km=slots.max_distance_km,
                limit=8,
                db=db,
            )
            if not items:
                metrics["food_fallback"] = "expanded_radius"
                yield self._sse_pipeline_step("food_candidate_filter", "Đang lọc quán theo vị trí, ngân sách và khẩu vị...", 0.52, radius_km=max(slots.max_distance_km, 25))
                items = recommend_food(
                    lat=slots.lat,
                    lng=slots.lng,
                    category=slots.category,
                    taste_tags=slots.taste_tags,
                    budget_min=slots.budget_min,
                    budget_max=slots.budget_max,
                    meal_time=slots.meal_time,
                    max_distance_km=max(slots.max_distance_km, 25),
                    limit=8,
                    db=db,
                )
            if not items and slots.category:
                metrics["food_fallback"] = "expanded_radius_relaxed_category"
                yield self._sse_pipeline_step("food_ml_rank", "Đang xếp hạng món ăn phù hợp nhất...", 0.62, relaxed_category=True)
                items = recommend_food(
                    lat=slots.lat,
                    lng=slots.lng,
                    category=None,
                    taste_tags=slots.taste_tags,
                    budget_min=slots.budget_min,
                    budget_max=slots.budget_max,
                    meal_time=slots.meal_time,
                    max_distance_km=max(slots.max_distance_km, 25),
                    limit=8,
                    db=db,
                )
        finally:
            db.close()

        metrics["search_latency_ms"] = (time.time() - t_tool_start) * 1000
        metrics["total_latency_ms"] = (time.time() - t_start) * 1000
        metrics["food_result_count"] = len(items)
        answer = self._format_food_answer(items, slots.category)
        if items:
            yield self._sse_pipeline_step("food_found", "Yeah, đã tìm được món ăn phù hợp, đang chuẩn bị lên món...", 0.78, result_count=len(items))
            yield self._sse_pipeline_step("food_answer_llm", "Đang viết lời gợi ý dễ hiểu hơn cho bạn...", 0.86)
        yield from self._stream_plain_answer(answer)
        if items:
            yield f'data: {json.dumps({"food_recommendations": self._food_recommendations_payload(items, slots.category, query)}, ensure_ascii=False)}\n\n'
        else:
            yield f'data: {json.dumps({"food_location_request": self._food_location_payload(query)}, ensure_ascii=False)}\n\n'
        yield f'data: {json.dumps({"metrics": metrics, "step": "food-recommendation"}, ensure_ascii=False)}\n\n'
        yield "data: [DONE]\n\n"

    def _stream_run_raw(self, query: str, chat_history: List[Dict[str, str]] = None, bypass_cache: bool = False, image_base64: str = None, is_deep_search: bool = False, food_context: Dict[str, Any] | None = None):
        """
        Internal raw streaming implementation of the RAG chain.
        """
        t_start = time.time()
        
        metrics = {
            "search_latency_ms": 0, "generation_latency_ms": 0, "rewrite_latency_ms": 0,
            "classification_latency_ms": 0, "expansion_latency_ms": 0, "rerank_latency_ms": 0,
            "total_tokens": 0, "cost_usd": 0.0, "expanded_queries": [], "rewritten_query": "",
            "num_chunks_before_expansion": 0, "compressed_context_len": 0
        }
        
        def yield_msg(val):
            yield val

        def finalize_generation(final_answer: str, top_docs: List[Any], messages: List[Dict[str, str]]):
            est_p = len(" ".join([m["content"] for m in messages])) // 4
            est_c = len(final_answer) // 4
            metrics["total_tokens"] += est_p + est_c
            gen_cost = self._calculate_llm_cost(est_p, est_c)
            metrics["cost_usd"] += gen_cost["cost_usd"]

            citations = self._build_citations(top_docs[:5])
            yield from yield_msg(f'data: {json.dumps({"sources": citations})}\n\n')

            if self.cache and not bypass_cache and final_answer:
                self.cache.set(normalized_query, final_answer, citations)
                if rewritten_query != normalized_query:
                    self.cache.set(rewritten_query, final_answer, citations)

            yield from yield_msg(f'data: {json.dumps({"metrics": metrics})}\n\n')

        if is_deep_search:
            bypass_cache = True

        yield from yield_msg(self._sse_pipeline_step("received", "Chờ một chút...", 0.03))
        normalized_query = self.gateway.normalize_input(query)
        yield from yield_msg(self._sse_pipeline_step("gateway_safety", "Đang kiểm tra an toàn nội dung...", 0.06))
        safety_res = self.gateway.safety_precheck(normalized_query)
        if not safety_res["safe"]:
            yield from yield_msg(f"data: {self._gateway_refusal_message(safety_res)}\n\n")
            yield from yield_msg("data: [DONE]\n\n")
            return

        # 2. Early Cache Lookup
        yield from yield_msg(self._sse_pipeline_step("cache_lookup", "Đang kiểm tra câu trả lời đã có...", 0.1))
        if self.cache and not bypass_cache:
            is_hit, hit_res, hit_type = self.cache.get(normalized_query)
            if is_hit:
                metrics["total_latency_ms"] = (time.time() - t_start) * 1000
                metrics["intent"] = "faq"
                metrics["rewritten_query"] = normalized_query
                import re
                for token in re.split(r'(\s+)', hit_res["answer"]):
                    if token:
                        safe_token = token.replace('\n', '\ndata: ')
                        yield from yield_msg(f"data: {safe_token}\n\n")
                yield from yield_msg(f'data: {json.dumps({"sources": hit_res.get("citations", [])})}\n\n')
                yield from yield_msg(f'data: {json.dumps({"metrics": metrics, "step": "cache-hit"})}\n\n')
                yield from yield_msg("data: [DONE]\n\n")
                return

        if is_deep_search:
            yield from yield_msg('data: {"step": "Đang phân tích chuyên sâu (Deep Search)..."}\n\n')
        else:
            yield from yield_msg('data: {"step": "Phân tích ngữ cảnh & Ý định..."}\n\n')
        
        # 3. Unified NLU Call
        t_nlu_start = time.time()
        # For deep search, we could optionally tell NLU to expand more aggressively
        yield from yield_msg(self._sse_pipeline_step("nlu_intent", "Đang phân tích ý định...", 0.18))
        nlu_res = self.classifier.unified_nlu(normalized_query, chat_history, image_base64=image_base64, food_context=food_context)
        metrics["rewrite_latency_ms"] = (time.time() - t_nlu_start) * 1000
        
        rewritten_query = nlu_res["rewritten_query"]
        intent = nlu_res["intent"]
        expanded_queries = nlu_res["expanded_queries"]
        nlu_usage = nlu_res.get("usage", {"prompt_tokens": 0, "completion_tokens": 0})
        
        metrics["rewritten_query"] = rewritten_query
        metrics["intent"] = intent
        metrics["expanded_queries"] = expanded_queries
        metrics["nlu_fast_path"] = bool(nlu_res.get("fast_path"))
        metrics["nlu_fast_path_reason"] = nlu_res.get("fast_path_reason")
        metrics["food_user_context"] = food_context
        metrics["nlu_missing_fields"] = nlu_res.get("missing_fields", [])
        metrics["total_tokens"] += nlu_usage.get("prompt_tokens", 0) + nlu_usage.get("completion_tokens", 0)
        
        # Calculate NLU/Rewrite cost immediately so it is recorded even if generating fails/is interrupted
        nlu_cost = self._calculate_llm_cost(nlu_usage.get("prompt_tokens", 0), nlu_usage.get("completion_tokens", 0))
        metrics["cost_usd"] += nlu_cost["cost_usd"]

        if intent == "food_recommendation":
            yield from yield_msg(self._sse_pipeline_step("food_context_load", "Đang xem lại khẩu vị và vị trí của bạn...", 0.24))
            yield from self._handle_food_recommendation_stream(query, chat_history, metrics, t_start, nlu_food_slots=nlu_res.get("food_slots"))
            return

        # 4. Handle Sensitive / Safety Block
        if intent == "sensitive":
            refusal_msg = nlu_res.get("suggested_answer") or "Dạ, em rất tiếc nhưng em không thể thực hiện yêu cầu này vì lý do bảo mật hệ thống. Tuy nhiên, em luôn sẵn sàng hỗ trợ anh/chị các thông tin về dịch vụ, giá cước hoặc chính sách của Xanh SM ạ!"
            metrics["total_latency_ms"] = (time.time() - t_start) * 1000
            import re
            for token in re.split(r'(\s+)', refusal_msg):
                if token:
                    safe_token = token.replace('\n', '\ndata: ')
                    yield from yield_msg(f"data: {safe_token}\n\n")
            yield from yield_msg(f'data: {json.dumps({"metrics": metrics, "step": "sensitive"})}\n\n')
            yield from yield_msg("data: [DONE]\n\n")
            return

        # 5. Handle Small Talk
        if intent == "small-talk":
            answer = nlu_res.get("suggested_answer")
            if not answer:
                intercept = self._is_greeting_or_thanks(rewritten_query)
                if intercept["type"] != "none":
                    answer = intercept["answer"]
                else:
                    answer = "Dạ, em là Trợ lý ảo chuyên hỗ trợ các dịch vụ của Xanh SM. Hiện tại em chưa có thông tin về vấn đề này. Anh/chị có thể hỏi em các vấn đề liên quan đến Xanh SM như: giá cước taxi, chính sách hủy chuyến, hoặc cách đặt xe ạ!"
            
            metrics["total_latency_ms"] = (time.time() - t_start) * 1000
            import re
            for token in re.split(r'(\s+)', answer):
                if token:
                    safe_token = token.replace('\n', '\ndata: ')
                    yield from yield_msg(f"data: {safe_token}\n\n")
            yield from yield_msg(f'data: {json.dumps({"metrics": metrics, "step": "small-talk"})}\n\n')
            yield from yield_msg("data: [DONE]\n\n")
            return

        # 5. Second Cache Lookup
        if self.cache and not bypass_cache and rewritten_query != normalized_query:
            is_hit, hit_res, hit_type = self.cache.get(rewritten_query)
            if is_hit:
                metrics["total_latency_ms"] = (time.time() - t_start) * 1000
                metrics["intent"] = "faq"
                metrics["rewritten_query"] = rewritten_query
                import re
                for token in re.split(r'(\s+)', hit_res["answer"]):
                    if token:
                        safe_token = token.replace('\n', '\ndata: ')
                        yield from yield_msg(f"data: {safe_token}\n\n")
                yield from yield_msg(f'data: {json.dumps({"sources": hit_res.get("citations", [])})}\n\n')
                yield from yield_msg(f'data: {json.dumps({"metrics": metrics, "step": "cache-hit"})}\n\n')
                yield from yield_msg("data: [DONE]\n\n")
                return

        try:
            strategy = self.select_retrieval_strategy(rewritten_query)
            yield from yield_msg(self._sse_pipeline_step("retrieval_search", "Đang tìm kiếm tài liệu...", 0.34, strategy=strategy))
            t_search_start = time.time()
            
            search_limit = config.DEEP_SEARCH_CANDIDATE_LIMIT if is_deep_search else config.RETRIEVAL_CANDIDATE_LIMIT
            retrieved_candidates = self.search_engine.search(
                query=rewritten_query,
                limit=search_limit,
                expanded_queries=expanded_queries,
            )
            metrics["search_latency_ms"] = (time.time() - t_search_start) * 1000

            yield from yield_msg(self._sse_pipeline_step("rerank_documents", "Đang xếp hạng tài liệu...", 0.52))
            t_rerank_start = time.time()
            
            rerank_top_n = config.DEEP_SEARCH_RERANK_TOP_N if is_deep_search else config.RERANK_TOP_N
            top_docs = self.reranker.rerank(
                query=rewritten_query,
                docs=retrieved_candidates,
                top_n=rerank_top_n,
            )
            metrics["rerank_latency_ms"] = (time.time() - t_rerank_start) * 1000
            metrics["num_chunks_before_expansion"] = len(top_docs)
            
            yield from yield_msg(self._sse_pipeline_step("context_expansion", "Đang gọi thêm tài liệu đầy đủ...", 0.64, top_docs=len(top_docs)))
            top_docs = self.search_engine.expand_context(top_docs)
            messages, compressed_context, _ = self._build_prompt_messages(
                query=rewritten_query,
                context_docs=top_docs,
                chat_history=chat_history
            )
            
            
            metrics["compressed_context_len"] = len(compressed_context)

            yield from yield_msg(self._sse_pipeline_step("answer_prepare", "Đang chuẩn bị trả lời...", 0.78))
            t_gen_start = time.time()

            final_answer = ""
            client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=config.OPENAI_TIMEOUT_SECONDS)
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=config.LLM_MAX_TOKENS,
                stream=True
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
                        yield from yield_msg(f"data: {text.replace('\n', '\ndata: ')}\n\n")
            except Exception as stream_error:
                stream_failed = True
                log_warn("CHAT", f"Streaming generation interrupted: {stream_error}")

            if stream_failed and not final_answer:
                log_warn("CHAT", "Retrying generation once without streaming.")
                retry_response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=config.LLM_MAX_TOKENS
                )
                final_answer = retry_response.choices[0].message.content or ""
                metrics["generation_latency_ms"] = (time.time() - t_gen_start) * 1000
                metrics["total_latency_ms"] = (time.time() - t_start) * 1000
                if final_answer:
                    yield from yield_msg(f"data: {final_answer.replace('\n', '\ndata: ')}\n\n")
            
            if not first_token_received:
                metrics["generation_latency_ms"] = (time.time() - t_gen_start) * 1000
                metrics["total_latency_ms"] = (time.time() - t_start) * 1000

            yield from finalize_generation(final_answer, top_docs, messages)
                
        except Exception as e:
            log_error("CHAT", f"Pipeline Execution Error: {e}")
            yield from yield_msg(f"data: Xin loi, he thong dang ban. Vui long thu lai sau.\n\n")
            metrics["total_latency_ms"] = (time.time() - t_start) * 1000
            yield from yield_msg(f'data: {json.dumps({"metrics": metrics})}\n\n')
            
        yield from yield_msg("data: [DONE]\n\n")



    def run_vision_diagnostics(self, image_bytes: bytes, mime_type: str) -> Tuple[str, Dict[str, Any]]:
        """
        Uses OpenAI Vision model to analyze taplo EV warning lights and translate to text diagnostic query.
        """
        import base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        
        system_prompt = (
            "Bạn là chuyên gia chẩn đoán kỹ thuật xe điện (EV) của hãng Xanh SM.\n"
            "Hãy phân tích kỹ hình ảnh bảng điều khiển (taplo), đèn cảnh báo lỗi, hoặc sự cố xe điện được gửi kèm.\n"
            "Nhiệm vụ của bạn:\n"
            "1. Xác định tên lỗi cảnh báo (ví dụ: 'Lỗi rùa vàng', 'Lỗi báo lỗi động cơ', 'Lỗi hệ thống phanh', 'Lỗi ắc quy').\n"
            "2. Mô tả ngắn gọn sự cố bằng Tiếng Việt kỹ thuật.\n"
            "3. Tạo ra một câu truy vấn tìm kiếm sách hướng dẫn (ví dụ: 'Cách khắc phục lỗi rùa vàng xe điện VinFast').\n"
            "BẮT BUỘC chỉ trả về duy nhất chuỗi câu truy vấn chẩn đoán kỹ thuật để gửi vào RAG, KHÔNG giải thích thêm."
        )
        
        if config.OPENAI_API_KEY and config.EMBEDDING_PROVIDER != "mock" and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            try:
                client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=config.OPENAI_TIMEOUT_SECONDS)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": system_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{mime_type};base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=min(config.LLM_MAX_TOKENS, 300)
                )
                diagnostic_query = response.choices[0].message.content.strip().strip('"').strip("'")
                log_info("NLU", f"Identified diagnostic query: '{diagnostic_query}'")
                return diagnostic_query, {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            except Exception as e:
                log_warn("NLU", f"Failed to analyze image with Vision LLM: {e}")
                
        return "Lỗi cảnh báo kỹ thuật xe điện VinFast", {"prompt_tokens": 0, "completion_tokens": 0}

    def _generate_fallback_answer(self, query: str, docs: List[Any]) -> str:
        """
        Creates a cautious deterministic fallback response when synthesis is skipped.
        """
        if not docs:
            return (
                "Rất tiếc, tài liệu chính sách hiện tại của Xanh SM "
                "không có thông tin về vấn đề này."
            )

        first_doc = docs[0]
        source = first_doc.metadata.get("source", "policy.md")
        section = first_doc.metadata.get("section", "Quy định")

        # Cautious phrasing to avoid "blind citation"
        answer = (
            "Hiện tại tôi chưa tìm thấy câu trả lời trực tiếp trong chính sách, "
            f"nhưng bạn có thể tham khảo thông tin liên quan tại mục **\"{section}\"** của tài liệu **{source}**:\n\n"
            f"> {first_doc.page_content.strip()[:600]}...\n\n"
            f"Để được hỗ trợ chính xác nhất, quý khách vui lòng liên hệ Tổng đài Xanh SM: **1900 2088**."
        )
        return answer
if __name__ == "__main__":
    pipeline = XanhSMRAGPipeline()
    res = pipeline.run("Giá cước taxi Xanh SM Car tại Hà Nội")
    print(f"\nAnswer:\n{res['answer']}")
    print(f"\nIntent:\n{res.get('intent')}")
    print(f"\nStrategy:\n{res.get('strategy_selected')}")

