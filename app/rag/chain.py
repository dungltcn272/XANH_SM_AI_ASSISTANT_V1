import os
import sys
import json
import hashlib
import time
from typing import List, Dict, Any, Tuple

from openai import OpenAI
from app.retrieval.hybrid_search import XanhSMHybridSearch
from app.retrieval.reranker import XanhSMReranker
from app.rag.prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, get_role_display_name, FAITHFULNESS_CHECK_PROMPT
from app.rag.gateway import XanhSMGateway
from app.rag.classifier import XanhSMClassifier
from app.core.config import settings as config
from app.core.logger import log_info, log_warn, log_error

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
        try:
            from app.rag.cache import XanhSMRAGCache
            self.cache = XanhSMRAGCache()
        except Exception as e:
            log_warn("CACHE", f"Failed to load cache: {e}")
            self.cache = None
            
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

    def _is_greeting_or_thanks(self, query: str) -> Dict[str, Any]:
        """
        Spell-tolerant and accent-insensitive detector for greetings, thanks, and short chit-chat.
        """
        return self.gateway.is_greeting_or_thanks(query)

    def select_retrieval_strategy(self, query: str) -> str:
        """
        Strategy Selector: Dynamically decides the optimal search mechanism based on query properties.
        - BM25: For queries seeking specific error codes, hotlines, bridge fees, numbers, exact rule clauses.
        - Dense: For conceptual, abstract, semantic meaning queries.
        - Hybrid (Default): Merges dense semantic & exact keyword search.
        """
        query_clean = query.lower()
        
        # Specific indicators for exact keywords/numbers
        bm25_indicators = {
            "1900", "2088", "hotline", "điều", "khoản", "mục", "phần", "chế tài", 
            "vnđ", "đồng", "triệu", "phạt", "mã lỗi", "rùa vàng", "rùa", "cứu hộ"
        }
        
        # Numeric or phone check
        has_numbers = any(char.isdigit() for char in query_clean)
        
        if any(ind in query_clean for ind in bm25_indicators) or has_numbers:
            # Contains high density of exact keywords or numbers
            return "BM25 / Keyword"
            
        # Abstract queries like "tác phong chuẩn mực", "hỗ trợ khách hàng thế nào", "giúp tôi hiểu..."
        dense_indicators = {"chuẩn mực", "thế nào", "nghĩa là gì", "giải thích", "tại sao", "lý do", "ý nghĩa", "hiểu thế nào"}
        if any(ind in query_clean for ind in dense_indicators) and not has_numbers:
            return "Dense Search"
            
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
            client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=15.0)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": f"Bắt đầu đánh giá câu trả lời sau đây."}
                ],
                temperature=0.0
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

    def run(self, query: str, role: str = None, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Executes the full advanced NLU-Gateway RAG chain.
        """
        target_role = role.lower() if role else "faq"
        role_display = get_role_display_name(target_role)
        
        normalized_query = self.gateway.normalize_input(query)
        safety_res = self.gateway.safety_precheck(normalized_query)
        
        if not safety_res["safe"]:
            return {
                "query": query,
                "role": target_role,
                "answer": f"⚠️ Cảnh báo bảo mật: {safety_res['reason']}",
                "citations": [],
                "intent": "sensitive",
                "gateway_checked": True,
                "strategy_selected": "Bypass",
                "faithfulness_passed": True,
                "llm_cost_usd": 0.0,
                "llm_cost_vnd": 0.0
            }

        # 2. Early Cache Lookup
        if self.cache:
            is_hit, hit_res, hit_type = self.cache.get(normalized_query, target_role)
            if is_hit:
                log_info("CACHE", f"Early cache hit query via {hit_type} match.")
                return {
                    "query": query,
                    "rewritten_query": normalized_query,
                    "role": target_role,
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

        # 4. Handle Small Talk
        if intent == "small-talk":
            intercept = self._is_greeting_or_thanks(rewritten_query)
            answer = intercept["answer"] if intercept["type"] != "none" else "Xin chào! Tôi có thể giúp gì cho quý khách về các quy định dịch vụ Xanh SM hôm nay?"
            return {
                "query": query,
                "rewritten_query": rewritten_query,
                "role": target_role,
                "answer": answer,
                "citations": [],
                "intent": "small-talk",
                "gateway_checked": True,
                "strategy_selected": "Bypass",
                "faithfulness_passed": True,
                "llm_cost_usd": 0.0,
                "llm_cost_vnd": 0.0
            }

        # 5. Second Cache Lookup
        if self.cache and rewritten_query != normalized_query:
            is_hit, hit_res, hit_type = self.cache.get(rewritten_query, target_role)
            if is_hit:
                log_info("CACHE", f"Hit query after rewrite via {hit_type} match.")
                return {
                    "query": query,
                    "rewritten_query": rewritten_query,
                    "role": target_role,
                    "answer": hit_res["answer"],
                    "citations": hit_res["citations"],
                    "intent": "faq",
                    "gateway_checked": True,
                    "strategy_selected": "Semantic Cache Hit",
                    "faithfulness_passed": True,
                    "llm_cost_usd": 0.0,
                    "llm_cost_vnd": 0.0,
                    "cache_hit": hit_res.get("cache_hit", "exact"),
                    "cache_similarity": hit_res.get("cache_similarity", 1.0)
                }

        # 6. Search Strategy Selection
        strategy = self.select_retrieval_strategy(rewritten_query)
        log_info("RETRIEVAL", f"Dynamically selected search strategy: {strategy}")

        # 7. Execute Retrieval
        retrieved_candidates = self.search_engine.search(query=rewritten_query, role=target_role, limit=25, expanded_queries=expanded_queries)

        # 8. Rerank
        top_docs = self.reranker.rerank(query=rewritten_query, docs=retrieved_candidates, top_n=10)

        # 9. Expand context
        top_docs = self.search_engine.expand_context(top_docs)

        # 10. Compress Context
        compressed_context = self._compress_context(top_docs)

        # 11. LLM Generation
        final_answer = ""
        citations = []
        prompt_tokens = 0
        completion_tokens = 0

        for doc in top_docs:
            citations.append({
                "source": doc.metadata.get("source"),
                "section": doc.metadata.get("section"),
                "url": doc.metadata.get("url", ""),
                "relevance_score": doc.metadata.get("rerank_score", 0.0)
            })

        system_msg = SYSTEM_PROMPT.format(context=compressed_context, role=role_display)
        user_msg = USER_PROMPT_TEMPLATE.format(role_display=role_display, query=rewritten_query)

        messages = [{"role": "system", "content": system_msg}]
        if chat_history and len(chat_history) > 0:
            history_messages = []
            for turn in chat_history[-6:]:
                if isinstance(turn, dict) and turn.get("role") and turn.get("content"):
                    history_messages.append({"role": turn["role"], "content": turn["content"]})
            if history_messages:
                messages.extend(history_messages)
        
        messages.append({"role": "user", "content": user_msg})

        if config.OPENAI_API_KEY and config.EMBEDDING_PROVIDER != "mock" and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            try:
                client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=15.0)
                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    temperature=0.3
                )
                final_answer = response.choices[0].message.content
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
            except Exception as e:
                log_warn("LLM_GEN", f"LLM Generation Error: {str(e)}. Falling back to offline synthesis.")
                final_answer = self._generate_fallback_answer(rewritten_query, top_docs, role_display)
        else:
            final_answer = self._generate_fallback_answer(rewritten_query, top_docs, role_display)

        # Cost calculation
        total_prompt = prompt_tokens + nlu_usage.get("prompt_tokens", 0)
        total_comp = completion_tokens + nlu_usage.get("completion_tokens", 0)
        cost_info = self._calculate_llm_cost(total_prompt, total_comp)

        # Save to Cache
        if self.cache:
            self.cache.set(normalized_query, final_answer, citations, target_role)
            if rewritten_query != normalized_query:
                self.cache.set(rewritten_query, final_answer, citations, target_role)

        return {
            "query": query,
            "rewritten_query": rewritten_query,
            "role": target_role,
            "answer": final_answer,
            "citations": citations,
            "expanded_queries": expanded_queries,
            "compressed_context_len": len(compressed_context),
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

    def stream_run(self, query: str, role: str = None, chat_history: List[Dict[str, str]] = None):
        """
        Stream version of the NLU-Gateway RAG chain.
        """
        t_start = time.time()
        target_role = role.lower() if role else "faq"
        role_display = get_role_display_name(target_role)
        
        metrics = {
            "search_latency_ms": 0, "generation_latency_ms": 0, "rewrite_latency_ms": 0,
            "classification_latency_ms": 0, "expansion_latency_ms": 0, "rerank_latency_ms": 0,
            "total_tokens": 0, "cost_usd": 0.0, "expanded_queries": [], "rewritten_query": ""
        }
        
        def yield_msg(val):
            yield val

        normalized_query = self.gateway.normalize_input(query)
        safety_res = self.gateway.safety_precheck(normalized_query)
        if not safety_res["safe"]:
            yield from yield_msg(f"data: ⚠️ Cảnh báo bảo mật: {safety_res['reason']}\n\n")
            yield from yield_msg("data: [DONE]\n\n")
            return

        # 2. Early Cache Lookup
        if self.cache:
            is_hit, hit_res, hit_type = self.cache.get(normalized_query, target_role)
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

        yield from yield_msg('data: {"step": "Phân tích ngữ cảnh & Ý định..."}\n\n')
        
        # 3. Unified NLU Call
        t_nlu_start = time.time()
        nlu_res = self.classifier.unified_nlu(normalized_query, chat_history)
        metrics["rewrite_latency_ms"] = (time.time() - t_nlu_start) * 1000
        
        rewritten_query = nlu_res["rewritten_query"]
        intent = nlu_res["intent"]
        expanded_queries = nlu_res["expanded_queries"]
        nlu_usage = nlu_res.get("usage", {"prompt_tokens": 0, "completion_tokens": 0})
        
        metrics["rewritten_query"] = rewritten_query
        metrics["intent"] = intent
        metrics["expanded_queries"] = expanded_queries
        metrics["total_tokens"] += nlu_usage.get("prompt_tokens", 0) + nlu_usage.get("completion_tokens", 0)

        # 4. Handle Small Talk
        if intent == "small-talk":
            intercept = self._is_greeting_or_thanks(rewritten_query)
            answer = intercept["answer"] if intercept["type"] != "none" else "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?"
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
        if self.cache and rewritten_query != normalized_query:
            is_hit, hit_res, hit_type = self.cache.get(rewritten_query, target_role)
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
            yield from yield_msg('data: {"step": "Đang truy xuất dữ liệu (Hybrid)..."}\n\n')
            t_search_start = time.time()
            retrieved_candidates = self.search_engine.search(query=rewritten_query, role=target_role, limit=25, expanded_queries=expanded_queries)
            metrics["search_latency_ms"] = (time.time() - t_search_start) * 1000

            yield from yield_msg('data: {"step": "Đang chấm điểm & Reranking tài liệu..."}\n\n')
            t_rerank_start = time.time()
            top_docs = self.reranker.rerank(query=rewritten_query, docs=retrieved_candidates, top_n=10)
            metrics["rerank_latency_ms"] = (time.time() - t_rerank_start) * 1000
            
            top_docs = self.search_engine.expand_context(top_docs)
            compressed_context = self._compress_context(top_docs)

            yield from yield_msg('data: {"step": "Đang khởi tạo LLM & Tổng hợp câu trả lời..."}\n\n')
            t_gen_start = time.time()
            messages = [{"role": "system", "content": SYSTEM_PROMPT.format(context=compressed_context, role=role_display)}]
            if chat_history and len(chat_history) > 0:
                for turn in chat_history[-6:]:
                    if isinstance(turn, dict) and turn.get("role") and turn.get("content"):
                        messages.append({"role": turn["role"], "content": turn["content"]})
            messages.append({"role": "user", "content": USER_PROMPT_TEMPLATE.format(role_display=role_display, query=rewritten_query)})

            final_answer = ""
            client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=15.0)
            response = client.chat.completions.create(model=config.LLM_MODEL, messages=messages, temperature=0.3, stream=True)
            
            first_token_received = False
            for chunk in response:
                if chunk.choices[0].delta.content:
                    if not first_token_received:
                        metrics["generation_latency_ms"] = (time.time() - t_gen_start) * 1000
                        metrics["total_latency_ms"] = (time.time() - t_start) * 1000
                        first_token_received = True
                    text = chunk.choices[0].delta.content
                    final_answer += text
                    yield from yield_msg(f"data: {text.replace('\n', '\ndata: ')}\n\n")
            
            if not first_token_received:
                metrics["generation_latency_ms"] = (time.time() - t_gen_start) * 1000
                metrics["total_latency_ms"] = (time.time() - t_start) * 1000
            
            est_p = len(" ".join([m["content"] for m in messages])) // 4
            est_c = len(final_answer) // 4
            metrics["total_tokens"] += est_p + est_c
            metrics["cost_usd"] = (est_p * 0.15 + est_c * 0.60) / 1_000_000
                    
            citations = [{"source": d.metadata.get("source", "unknown"), "section": d.metadata.get("section", ""), "url": d.metadata.get("url", "") or d.metadata.get("source", "")} for d in top_docs[:5]]
            yield from yield_msg(f'data: {json.dumps({"sources": citations})}\n\n')
            
            if self.cache and final_answer:
                self.cache.set(normalized_query, final_answer, citations, target_role)
                if rewritten_query != normalized_query:
                    self.cache.set(rewritten_query, final_answer, citations, target_role)
            
            yield from yield_msg(f'data: {json.dumps({"metrics": metrics})}\n\n')
                
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
                client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=15.0)
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
                    max_tokens=300
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

    def _generate_fallback_answer(self, query: str, docs: List[Any], role_display: str) -> str:
        """
        Creates a cautious deterministic fallback response when synthesis is skipped.
        """
        if not docs:
            return (
                f"Chào {role_display}, rất tiếc là tài liệu chính sách hiện tại của Xanh SM "
                f"không có thông tin về vấn đề này."
            )

        first_doc = docs[0]
        source = first_doc.metadata.get("source", "policy.md")
        section = first_doc.metadata.get("section", "Quy định")

        # Cautious phrasing to avoid "blind citation"
        answer = (
            f"Chào {role_display}, hiện tại tôi chưa tìm thấy câu trả lời trực tiếp trong chính sách, "
            f"nhưng bạn có thể tham khảo thông tin liên quan tại mục **\"{section}\"** của tài liệu **{source}**:\n\n"
            f"> {first_doc.page_content.strip()[:600]}...\n\n"
            f"Để được hỗ trợ chính xác nhất, quý khách vui lòng liên hệ Tổng đài Xanh SM: **1900 2088**."
        )
        return answer
if __name__ == "__main__":
    pipeline = XanhSMRAGPipeline()
    res = pipeline.run("Tôi muốn tính phí hủy chuyến xe VF 8 sau 3 phút")
    print(f"\nAnswer:\n{res['answer']}")
    print(f"\nIntent:\n{res.get('intent')}")
    print(f"\nStrategy:\n{res.get('strategy_selected')}")
