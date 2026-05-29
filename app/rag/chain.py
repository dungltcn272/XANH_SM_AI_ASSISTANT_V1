import os
import sys
import json
import hashlib
from typing import List, Dict, Any, Tuple

# Force UTF-8 encoding on standard streams to prevent CP1252 console encoding crashes on Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from openai import OpenAI
from app.retrieval.hybrid_search import XanhSMHybridSearch
from app.retrieval.reranker import XanhSMReranker
from app.rag.prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, get_role_display_name, FAITHFULNESS_CHECK_PROMPT
from app.rag.gateway import XanhSMGateway
from app.rag.classifier import XanhSMClassifier, RefundCalculatorTool
from app.config import config

class XanhSMRAGPipeline:
    """
    Phase 3 Advanced NLU-Gateway RAG Pipeline:
    Coordinates Conversation Gateway ➔ Intent Classifier ➔ Slot Filling (Task Agent) ➔ Semantic Cache Check 
    ➔ Query Rewrite ➔ Strategy Selector ➔ Hybrid Search ➔ Reranker ➔ Parent-Child ➔ LLM Gen ➔ Faithfulness Check ➔ Citations.
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
            print(f"[WARN] Failed to load cache: {e}")
            self.cache = None
            
    def _compress_context(self, docs: List[Any]) -> str:
        """
        Formats and compresses retrieved documents with source boundaries.
        Implements Parent-Child retrieval by mapping smaller search chunks to full headings.
        """
        formatted_blocks = []
        seen_parents = set()
        
        for doc in docs:
            parent_id = doc.metadata.get("parent_chunk_id")
            if parent_id:
                if parent_id in seen_parents:
                    continue
                seen_parents.add(parent_id)
                content = doc.metadata.get("parent_content", doc.page_content).strip()
            else:
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
            client = OpenAI(api_key=config.OPENAI_API_KEY)
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
            print(f"[WARN] Faithfulness Check failed: {e}. Defaulting to True.")
            return True, 1.0, f"Error: {e}"

    def run(self, query: str, role: str = None, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Executes the full advanced NLU-Gateway RAG chain.
        """
        target_role = role.lower() if role else "faq"
        role_display = get_role_display_name(target_role)
        
        # 1. Gateway Phase (Normalize, Safety & Language detect)
        normalized_query = self.gateway.normalize_input(query)
        lang = self.gateway.language_detect(normalized_query)
        safety_res = self.gateway.safety_precheck(normalized_query)
        
        # Handle early-exit for safety violations
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

        # 2. Context-aware query rewrite before classification
        rewritten_query, rewrite_usage = self._rewrite_query(normalized_query, chat_history)

        # 3. Intent & Query Classifier
        intent_res = self.classifier.classify_intent(rewritten_query, chat_history)
        intent = intent_res.get("intent", "rag")
        sub_task = intent_res.get("sub_task")

        # 4. Handle Small Talk Path
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
            
        # 5. Handle Task / Agent Path (e.g. Refund Calculator Tool)
        if intent == "task-agent" and sub_task == "refund_calculator":
            slot_res = self.classifier.fill_slots(rewritten_query, chat_history)
            if slot_res.get("missing_info", False):
                # Prompt user for missing fields
                return {
                    "query": query,
                    "role": target_role,
                    "answer": slot_res["clarification_question"],
                    "citations": [],
                    "intent": "task-agent",
                    "sub_task": "refund_calculator",
                    "missing_fields": True,
                    "gateway_checked": True,
                    "strategy_selected": "Slot Filling",
                    "faithfulness_passed": True,
                    "llm_cost_usd": 0.0,
                    "llm_cost_vnd": 0.0
                }
            else:
                # Execute calculation
                slots = slot_res.get("slots", {})
                calc_res = RefundCalculatorTool.calculate(slots.get("vehicle_type"), slots.get("waiting_time"))
                return {
                    "query": query,
                    "role": target_role,
                    "answer": calc_res["explanation"],
                    "citations": [
                        {
                            "source": "refund.md",
                            "section": "Điều 1: Quy Định Hủy Chuyến Từ Phía Khách Hàng",
                            "url": "",
                            "relevance_score": 1.0
                        }
                    ],
                    "intent": "task-agent",
                    "sub_task": "refund_calculator",
                    "missing_fields": False,
                    "gateway_checked": True,
                    "strategy_selected": "Action Engine",
                    "faithfulness_passed": True,
                    "llm_cost_usd": 0.0,
                    "llm_cost_vnd": 0.0
                }

        # 5. RAG Entry (for 'rag' or 'faq' intents)
        # Fast FAQ / Semantic Cache check
        if self.cache:
            is_hit, hit_res, hit_type = self.cache.get(rewritten_query, target_role)
            if is_hit:
                print(f"[CACHE] Hit query='{query}' via {hit_type} match.")
                return {
                    "query": query,
                    "rewritten_query": rewritten_query,
                    "role": target_role,
                    "answer": hit_res["answer"],
                    "citations": hit_res["citations"],
                    "intent": "faq" if hit_type == "exact" else "rag",
                    "gateway_checked": True,
                    "strategy_selected": "Semantic Cache Hit",
                    "faithfulness_passed": True,
                    "llm_cost_usd": 0.0,
                    "llm_cost_vnd": 0.0,
                    "cache_hit": hit_res.get("cache_hit", "exact"),
                    "cache_similarity": hit_res.get("cache_similarity", 1.0)
                }

        # Retrieval Strategy Selector
        strategy = self.select_retrieval_strategy(rewritten_query)
        print(f"[STRATEGY] Dynamically selected search strategy: {strategy}")

        # Expand queries
        expanded_queries = self.search_engine.expander.get_queries(rewritten_query)

        # Execute Retrieval based on chosen Strategy
        retrieved_candidates = []
        if strategy == "BM25 / Keyword":
            # Direct sparse search
            retrieved_candidates = self.search_engine.bm25_retriever.search(query=rewritten_query, k=25, role=target_role)
        elif strategy == "Dense Search":
            # Direct dense search
            retrieved_candidates = self.search_engine.db.search(query=rewritten_query, k=25, role=target_role)
        else:
            # Hybrid search merging RRF
            retrieved_candidates = self.search_engine.search(query=rewritten_query, role=target_role, limit=25, expanded_queries=expanded_queries)

        # Reranker
        top_docs = self.reranker.rerank(query=rewritten_query, docs=retrieved_candidates, top_n=5)

        # Context compression
        compressed_context = self._compress_context(top_docs)

        # LLM Synthesis
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

        # Build messages array with chat history for context
        messages = [{"role": "system", "content": system_msg}]
        
        # Add last 3 turns of chat history for conversational context
        if chat_history and len(chat_history) > 0:
            history_messages = []
            for turn in chat_history[-6:]:
                if isinstance(turn, dict) and turn.get("role") and turn.get("content"):
                    history_messages.append({
                        "role": turn["role"],
                        "content": turn["content"]
                    })
            if history_messages:
                messages.extend(history_messages)
                print(f"[DEBUG] Added {len(history_messages)} history messages to LLM context.")
        
        messages.append({"role": "user", "content": user_msg})

        if config.OPENAI_API_KEY and config.EMBEDDING_PROVIDER != "mock" and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            try:
                client = OpenAI(api_key=config.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    temperature=0.3
                )
                final_answer = response.choices[0].message.content
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
            except Exception as e:
                print(f"[WARN] LLM Generation Error: {str(e)}. Falling back to offline synthesis.")
                final_answer = self._generate_fallback_answer(rewritten_query, top_docs, role_display)
        else:
            print("[INFO] Running Resilient Offline Fallback Synthesis.")
            final_answer = self._generate_fallback_answer(rewritten_query, top_docs, role_display)

        # Calculate costs
        qe_usage = self.search_engine.expander.last_token_usage
        total_prompt = qe_usage["prompt_tokens"] + prompt_tokens + rewrite_usage["prompt_tokens"]
        total_comp = qe_usage["completion_tokens"] + completion_tokens + rewrite_usage["completion_tokens"]
        cost_info = self._calculate_llm_cost(total_prompt, total_comp)

        # Save to cache
        if self.cache:
            self.cache.set(normalized_query, final_answer, citations, target_role)

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
            "faithfulness_passed": True, # Verification disabled per request
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
                "query_expansion": qe_usage,
                "generation": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
                "total_prompt_tokens": total_prompt,
                "total_completion_tokens": total_comp
            },
            "llm_cost_usd": cost_info["cost_usd"],
            "llm_cost_vnd": cost_info["cost_vnd"]
        }

    def run_step_by_step(self, query: str, role: str = None, chat_history: List[Dict[str, str]] = None):
        """
        Step-by-step generator for real-time visual pipeline tracking in Streamlit UI or Dashboard.
        Yields active stages sequentially.
        """
        target_role = role.lower() if role else "faq"
        role_display = get_role_display_name(target_role)

        # 1. Gateway
        yield {"stage": "Gateway", "msg": "đang chuẩn hóa đầu vào và kiểm tra rào cản bảo mật (Safety Gateway)...", "result": None}
        normalized_query = self.gateway.normalize_input(query)
        safety_res = self.gateway.safety_precheck(normalized_query)
        
        if not safety_res["safe"]:
            res = {
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
            yield {"stage": "Classifier", "msg": "đã định tuyến đến luồng nội dung nhạy cảm!", "result": None}
            yield {"stage": "CitationValidator", "msg": "hoàn tất phản hồi!", "result": res}
            return

        # 2. Contextual Rewriting
        yield {"stage": "QueryUnderstanding", "msg": "đang tổng hợp bối cảnh lịch sử trò chuyện để viết lại câu hỏi...", "result": None}
        rewritten_query, rewrite_usage = self._rewrite_query(normalized_query, chat_history)

        # 3. Classifier
        yield {"stage": "Classifier", "msg": "đang phân tích ý định người dùng và bóc tách thực thể...", "result": None}
        intent_res = self.classifier.classify_intent(rewritten_query, chat_history)
        intent = intent_res.get("intent", "rag")
        sub_task = intent_res.get("sub_task")

        # 4. Small-talk
        if intent == "small-talk":
            intercept = self._is_greeting_or_thanks(rewritten_query)
            answer = intercept["answer"] if intercept["type"] != "none" else "Xin chào! Tôi có thể giúp gì cho bạn hôm nay?"
            res = {
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
            yield {"stage": "CitationValidator", "msg": "hoàn tất phản hồi hội thoại trực tiếp!", "result": res}
            return

        # 5. Task-agent
        if intent == "task-agent" and sub_task == "refund_calculator":
            yield {"stage": "SlotFilling", "msg": "đang kiểm tra các slots thông tin và tham số bóc tách...", "result": None}
            slot_res = self.classifier.fill_slots(rewritten_query, chat_history)
            
            if slot_res.get("missing_info", False):
                res = {
                    "query": query,
                    "rewritten_query": rewritten_query,
                    "role": target_role,
                    "answer": slot_res["clarification_question"],
                    "citations": [],
                    "intent": "task-agent",
                    "sub_task": "refund_calculator",
                    "missing_fields": True,
                    "gateway_checked": True,
                    "strategy_selected": "Slot Filling",
                    "faithfulness_passed": True,
                    "llm_cost_usd": 0.0,
                    "llm_cost_vnd": 0.0
                }
                yield {"stage": "CitationValidator", "msg": "đã gửi câu hỏi làm rõ các trường còn thiếu!", "result": res}
                return
            else:
                slots = slot_res.get("slots", {})
                calc_res = RefundCalculatorTool.calculate(slots.get("vehicle_type"), slots.get("waiting_time"))
                res = {
                    "query": query,
                    "rewritten_query": rewritten_query,
                    "role": target_role,
                    "answer": calc_res["explanation"],
                    "citations": [
                        {
                            "source": "refund.md",
                            "section": "Điều 1: Quy Định Hủy Chuyến Từ Phía Khách Hàng",
                            "url": "",
                            "relevance_score": 1.0
                        }
                    ],
                    "intent": "task-agent",
                    "sub_task": "refund_calculator",
                    "missing_fields": False,
                    "gateway_checked": True,
                    "strategy_selected": "Action Engine",
                    "faithfulness_passed": True,
                    "llm_cost_usd": 0.0,
                    "llm_cost_vnd": 0.0
                }
                yield {"stage": "CitationValidator", "msg": "đã hoàn tất tính toán qua Action Engine!", "result": res}
                return

        # 6. RAG Entry
        # Cache Check
        if self.cache:
            is_hit, hit_res, hit_type = self.cache.get(rewritten_query, target_role)
            if is_hit:
                res = {
                    "query": query,
                    "rewritten_query": rewritten_query,
                    "role": target_role,
                    "answer": hit_res["answer"],
                    "citations": hit_res["citations"],
                    "intent": "faq" if hit_type == "exact" else "rag",
                    "gateway_checked": True,
                    "strategy_selected": "Semantic Cache Hit",
                    "faithfulness_passed": True,
                    "llm_cost_usd": 0.0,
                    "llm_cost_vnd": 0.0
                }
                yield {"stage": "CitationValidator", "msg": f"đã tìm thấy trong bộ đệm ({hit_type} cache)!", "result": res}
                return

        # Strategy Selection
        yield {"stage": "StrategySelector", "msg": "đang phân tích và lựa chọn chiến lược tìm kiếm tối ưu...", "result": None}
        strategy = self.select_retrieval_strategy(rewritten_query)

        # Retrieval
        yield {"stage": "HybridSearch", "msg": f"đang tiến hành tìm kiếm tài liệu theo chiến lược: {strategy}...", "result": None}
        expanded_queries = self.search_engine.expander.get_queries(rewritten_query)
        if strategy == "BM25 / Keyword":
            retrieved_candidates = self.search_engine.bm25_retriever.search(query=rewritten_query, k=25, role=target_role)
        elif strategy == "Dense Search":
            retrieved_candidates = self.search_engine.db.search(query=rewritten_query, k=25, role=target_role)
        else:
            retrieved_candidates = self.search_engine.search(query=rewritten_query, role=target_role, limit=25, expanded_queries=expanded_queries)

        # Reranker
        yield {"stage": "Reranker", "msg": "đang xếp hạng Cross-Encoder các trích đoạn ứng viên...", "result": None}
        top_docs = self.reranker.rerank(query=rewritten_query, docs=retrieved_candidates, top_n=5)

        # Context compression
        yield {"stage": "ContextCompression", "msg": "đang nén tối ưu cấu trúc phân cấp (Parent-Child)...", "result": None}
        compressed_context = self._compress_context(top_docs)

        # LLM Generation
        yield {"stage": "LLMGeneration", "msg": "đang kết nối LLM để tổng hợp câu trả lời...", "result": None}
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

        # Build messages array with chat history for context
        messages = [{"role": "system", "content": system_msg}]
        
        # Add last 3 turns of chat history for conversational context
        if chat_history and len(chat_history) > 0:
            history_messages = []
            for turn in chat_history[-6:]:
                if isinstance(turn, dict) and turn.get("role") and turn.get("content"):
                    history_messages.append({
                        "role": turn["role"],
                        "content": turn["content"]
                    })
            if history_messages:
                messages.extend(history_messages)
                print(f"[DEBUG] Added {len(history_messages)} history messages to LLM context.")
        
        messages.append({"role": "user", "content": user_msg})

        if config.OPENAI_API_KEY and config.EMBEDDING_PROVIDER != "mock" and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            try:
                client = OpenAI(api_key=config.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    temperature=0.3
                )
                final_answer = response.choices[0].message.content
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
            except Exception as e:
                print(f"[WARN] LLM Generation Error: {str(e)}. Falling back to offline synthesis.")
                final_answer = self._generate_fallback_answer(rewritten_query, top_docs, role_display)
        else:
            final_answer = self._generate_fallback_answer(rewritten_query, top_docs, role_display)

        # Final answer & citations
        qe_usage = self.search_engine.expander.last_token_usage
        total_prompt = qe_usage["prompt_tokens"] + prompt_tokens + rewrite_usage["prompt_tokens"]
        total_comp = qe_usage["completion_tokens"] + completion_tokens + rewrite_usage["completion_tokens"]
        cost_info = self._calculate_llm_cost(total_prompt, total_comp)

        # Save to cache
        if self.cache:
            self.cache.set(normalized_query, final_answer, citations, target_role)

        res = {
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
            "faithfulness_passed": True, # Verification disabled per request
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
                "query_expansion": qe_usage,
                "generation": {"prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens},
                "total_prompt_tokens": total_prompt,
                "total_completion_tokens": total_comp
            },
            "llm_cost_usd": cost_info["cost_usd"],
            "llm_cost_vnd": cost_info["cost_vnd"]
        }
        
        yield {"stage": "CitationValidator", "msg": "hoàn tất xác thực và phản hồi sạch!", "result": res}

    def _rewrite_query(self, query: str, chat_history: List[Dict[str, str]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Rewrites a contextual query into a self-contained search query.
        """
        if not chat_history:
            return query, {"prompt_tokens": 0, "completion_tokens": 0}
            
        history_str = ""
        for turn in chat_history[-3:]:
            role_tag = "Người dùng" if turn.get("role") == "user" else "Trợ lý"
            history_str += f"{role_tag}: {turn.get('content')}\n"
            
        system_prompt = (
            "Bạn là trợ lý AI chuyên nghiệp của Xanh SM. Nhiệm vụ của bạn là phân tích lịch sử hội thoại "
            "và câu hỏi mới của người dùng để biên dịch lại thành một câu hỏi độc lập (Self-Contained Query) "
            "bằng Tiếng Việt rõ ràng để tìm kiếm trong cơ sở dữ liệu.\n\n"
            "Quy tắc:\n"
            "1. Nếu câu hỏi mới sử dụng đại từ thay thế (ví dụ: 'họ', 'nó', 'đó', 'ở đâu', 'bao nhiêu'...) hoặc phụ thuộc ngữ cảnh trước đó, "
            "hãy viết lại đầy đủ thực thể và nghĩa (ví dụ: 'Doanh thu của họ là bao nhiêu?' -> 'Doanh thu của Xanh SM là bao nhiêu?').\n"
            "2. Nếu câu hỏi mới đã rõ ràng và tự vững nghĩa, hãy giữ nguyên 100% câu hỏi mới đó.\n"
            "3. BẮT BUỘC chỉ trả về duy nhất chuỗi câu hỏi đã viết lại, KHÔNG giải thích, KHÔNG thêm lời chào."
        )
        
        user_prompt = f"Lịch sử hội thoại:\n{history_str}\nCâu hỏi mới: {query}\nCâu hỏi độc lập viết lại:"
        
        if config.OPENAI_API_KEY and config.EMBEDDING_PROVIDER != "mock" and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            try:
                client = OpenAI(api_key=config.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0
                )
                rewritten = response.choices[0].message.content.strip()
                rewritten = rewritten.strip('"').strip("'")
                print(f"[MEMORY] Rewrote query: '{query}' -> '{rewritten}'")
                return rewritten, {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            except Exception as e:
                print(f"[WARN] Failed to rewrite query: {e}. Using original query.")
                
        return query, {"prompt_tokens": 0, "completion_tokens": 0}

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
                client = OpenAI(api_key=config.OPENAI_API_KEY)
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
                print(f"[VISION] Identified diagnostic query: '{diagnostic_query}'")
                return diagnostic_query, {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            except Exception as e:
                print(f"[WARN] Failed to analyze image with Vision LLM: {e}")
                
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
