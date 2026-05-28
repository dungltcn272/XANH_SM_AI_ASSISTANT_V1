import os
import sys

# Force UTF-8 encoding on standard streams to prevent CP1252 console encoding crashes on Windows
try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

from typing import List, Dict, Any, Tuple
from openai import OpenAI
from app.retrieval.hybrid_search import XanhSMHybridSearch
from app.retrieval.reranker import XanhSMReranker
from app.rag.prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, get_role_display_name
from app.config import config

class XanhSMRAGPipeline:
    """
    Advanced RAG Pipeline coordinating:
    Role Routing ➔ Hybrid Search ➔ Reranking ➔ Context Compression ➔ LLM + Citations.
    Includes robust offline / invalid key checks to prevent process conflicts.
    """
    
    def __init__(self):
        self.search_engine = XanhSMHybridSearch()
        self.reranker = XanhSMReranker()
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
        Input: $0.15 per million tokens
        Output: $0.60 per million tokens
        Exchange rate: 1 USD = 25,400 VND
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
        Fuzzy, spell-tolerant and accent-insensitive detector for greetings, thanks, and short chit-chat.
        Bypasses the RAG/LLM flow for simple social queries.
        """
        import unicodedata
        import re

        # Clean string
        q_clean = query.strip().lower()
        q_clean = re.sub(r"[\?\!\.\,]", "", q_clean).strip()

        # Remove accents
        nfkd_form = unicodedata.normalize('NFKD', q_clean)
        q_no_accent = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

        greeting_phrases = {
            "hello", "hi", "halo", "hey", "hola", "hiii", "helloo", "heloo", "helooo",
            "xin chao", "xinchao", "chao ban", "chao", "chao ad", "ad oi", "chao em",
            "chao anh", "chao chi", "chao ban nhe", "chao ban", "chao buoi sang",
            "chao buoi trua", "chao buoi chieu", "chao buoi toi"
        }
        thanks_phrases = {
            "cam on", "camon", "cam on nhieu", "cam on ban", "cam on rat nhieu",
            "thank you", "thanks", "tks", "thks", "ty", "thank"
        }
        farewell_phrases = {
            "tam biet", "tam biet nhe", "goodbye", "bye", "see you", "hen gap lai"
        }

        tokens = q_no_accent.split()
        is_short = len(tokens) <= 6

        # Exact or short social pattern detection
        is_greet = any(q_no_accent == phrase or q_no_accent.startswith(phrase + " ") or phrase in q_no_accent for phrase in greeting_phrases) and is_short
        is_thank = any(phrase in q_no_accent for phrase in thanks_phrases) and is_short
        is_farewell = any(phrase in q_no_accent for phrase in farewell_phrases) and is_short

        # fallback for very short chats
        if not (is_greet or is_thank or is_farewell):
            if len(tokens) <= 4:
                if any(token in {"chao", "xin", "hello", "hi", "hey", "alo", "alo", "ok", "oke"} for token in tokens):
                    is_greet = True
                if any(token in {"camon", "thanks", "thank", "tks", "thks", "ty"} for token in tokens):
                    is_thank = True
                if any(token in {"bye", "tam", "goodbye"} for token in tokens):
                    is_farewell = True

        # Avoid false positives for actual questions that mention greeting words with additional intent
        if is_greet and len(tokens) > 5:
            is_greet = False
        if is_thank and len(tokens) > 5:
            is_thank = False
        if is_farewell and len(tokens) > 5:
            is_farewell = False

        if is_greet:
            return {
                "type": "greeting",
                "answer": "Xin chào! Tôi là Trợ lý AI CSKH của Xanh SM. Tôi có thể hỗ trợ gì cho quý khách về chính sách, hủy chuyến, phí dịch vụ hoặc quy định hôm nay?"
            }
        if is_thank:
            return {
                "type": "thanks",
                "answer": "Dạ, rất vui được hỗ trợ quý khách! Nếu còn thắc mắc nào khác, xin cứ tiếp tục hỏi nhé."
            }
        if is_farewell:
            return {
                "type": "farewell",
                "answer": "Cảm ơn quý khách đã sử dụng dịch vụ Xanh SM. Chúc quý khách một ngày tốt lành!"
            }

        return {"type": "none", "answer": ""}

    def run(self, query: str, role: str = None, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Executes the full advanced RAG chain.
        Supports caching, chat history query rewriting, and parent-child retrieval.
        """
        target_role = role.lower() if role else "faq"
        role_display = get_role_display_name(target_role)
        
        # Spell-tolerant interceptor
        intercept = self._is_greeting_or_thanks(query)
        if intercept["type"] != "none":
            cost_metrics = self._calculate_llm_cost(0, 0)
            return {
                "query": query,
                "role": target_role,
                "answer": intercept["answer"],
                "citations": [],
                "expanded_queries": [query],
                "compressed_context_len": 0,
                "top_docs": [],
                "token_usage": {
                    "query_expansion": {"prompt_tokens": 0, "completion_tokens": 0},
                    "generation": {"prompt_tokens": 0, "completion_tokens": 0},
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0
                },
                "llm_cost_usd": 0.0,
                "llm_cost_vnd": 0.0
            }

        # 1. Caching Layer Check
        if self.cache:
            is_hit, hit_res, hit_type = self.cache.get(query, target_role)
            if is_hit:
                cost_info = self._calculate_llm_cost(0, 0)
                print(f"[CACHE] Hit query='{query}' via {hit_type} match.")
                return {
                    "query": query,
                    "role": target_role,
                    "rewritten_query": query,
                    "answer": hit_res["answer"],
                    "citations": hit_res["citations"],
                    "expanded_queries": [query],
                    "compressed_context_len": 0,
                    "top_docs": [],
                    "token_usage": {
                        "query_expansion": {"prompt_tokens": 0, "completion_tokens": 0},
                        "generation": {"prompt_tokens": 0, "completion_tokens": 0},
                        "total_prompt_tokens": 0,
                        "total_completion_tokens": 0
                    },
                    "llm_cost_usd": 0.0,
                    "llm_cost_vnd": 0.0,
                    "cache_hit": hit_res.get("cache_hit", "exact"),
                    "cache_similarity": hit_res.get("cache_similarity", 1.0)
                }

        print(f"[*] Processing pipeline query='{query}' for role='{target_role}' ({role_display})")
        
        # 2. Conversational Memory Query Rewriting
        rewritten_query, rewrite_usage = self._rewrite_query(query, chat_history)
        
        # 3. Retrieve Candidate Documents (Dense + Sparse Hybrid RRF) using rewritten query
        expanded_queries = self.search_engine.expander.get_queries(rewritten_query)
        retrieved_candidates = self.search_engine.search(query=rewritten_query, role=target_role, limit=25, expanded_queries=expanded_queries)
        
        # 4. Rerank down to top 5
        top_docs = self.reranker.rerank(query=rewritten_query, docs=retrieved_candidates, top_n=5)
        
        # 5. Compress context blocks (Parent-Child De-duplicated context mapping)
        compressed_context = self._compress_context(top_docs)
        
        # 6. Synthesize final response using LLM
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
        
        # Bypass OpenAI API request if in offline mock mode to prevent Windows socket DLL conflicts
        if config.OPENAI_API_KEY and config.EMBEDDING_PROVIDER != "mock" and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            try:
                client = OpenAI(api_key=config.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg}
                    ],
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
            
        # 7. Calculate cumulative costs (including query rewrite)
        qe_usage = self.search_engine.expander.last_token_usage
        total_prompt = qe_usage["prompt_tokens"] + prompt_tokens + rewrite_usage["prompt_tokens"]
        total_comp = qe_usage["completion_tokens"] + completion_tokens + rewrite_usage["completion_tokens"]
        cost_info = self._calculate_llm_cost(total_prompt, total_comp)
        
        # Save to cache
        if self.cache:
            self.cache.set(query, final_answer, citations, target_role)
            
        return {
            "query": query,
            "rewritten_query": rewritten_query,
            "role": target_role,
            "answer": final_answer,
            "citations": citations,
            "expanded_queries": expanded_queries,
            "compressed_context_len": len(compressed_context),
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
        Step-by-step generator for real-time visual pipeline tracking in Streamlit UI.
        Yields the current active stage ID and its metadata to allow true real-time node lighting.
        """
        target_role = role.lower() if role else "faq"
        role_display = get_role_display_name(target_role)
        
        # Spell-tolerant interceptor
        intercept = self._is_greeting_or_thanks(query)
        if intercept["type"] != "none":
            res = {
                "query": query,
                "role": target_role,
                "answer": intercept["answer"],
                "citations": [],
                "expanded_queries": [query],
                "compressed_context_len": 0,
                "top_docs": [],
                "token_usage": {
                    "query_expansion": {"prompt_tokens": 0, "completion_tokens": 0},
                    "generation": {"prompt_tokens": 0, "completion_tokens": 0},
                    "total_prompt_tokens": 0,
                    "total_completion_tokens": 0
                },
                "llm_cost_usd": 0.0,
                "llm_cost_vnd": 0.0
            }
            yield {"stage": "Question", "msg": "đang nhận câu hỏi...", "result": None}
            yield {"stage": "QueryUnderstanding", "msg": "đang bỏ qua RAG cho lời chào xã giao...", "result": None}
            yield {"stage": "CitationValidator", "msg": "hoàn tất phản hồi!", "result": res}
            return

        # 1. Caching Check
        if self.cache:
            is_hit, hit_res, hit_type = self.cache.get(query, target_role)
            if is_hit:
                res = {
                    "query": query,
                    "rewritten_query": query,
                    "role": target_role,
                    "answer": hit_res["answer"],
                    "citations": hit_res["citations"],
                    "expanded_queries": [query],
                    "compressed_context_len": 0,
                    "top_docs": [],
                    "token_usage": {
                        "query_expansion": {"prompt_tokens": 0, "completion_tokens": 0},
                        "generation": {"prompt_tokens": 0, "completion_tokens": 0},
                        "total_prompt_tokens": 0,
                        "total_completion_tokens": 0
                    },
                    "llm_cost_usd": 0.0,
                    "llm_cost_vnd": 0.0,
                    "cache_hit": hit_res.get("cache_hit", "exact"),
                    "cache_similarity": hit_res.get("cache_similarity", 1.0)
                }
                yield {"stage": "Question", "msg": "đang nhận câu hỏi...", "result": None}
                yield {"stage": "CitationValidator", "msg": f"đã tìm thấy trong bộ đệm ({hit_type} cache)!", "result": res}
                return

        # Regular RAG Flow step by step
        yield {"stage": "Question", "msg": "đang nhận câu hỏi...", "result": None}
        
        # 2. Conversational Memory Query Rewriting
        rewritten_query, rewrite_usage = self._rewrite_query(query, chat_history)
        yield {"stage": "QueryUnderstanding", "msg": f"đang giải nghĩa lịch sử và mở rộng ý định... (Ý định viết lại: '{rewritten_query}')", "result": rewritten_query}
        
        # 3. Query Expansion
        expanded_queries = self.search_engine.expander.get_queries(rewritten_query)
        
        # 4. Hybrid Search
        retrieved_candidates = self.search_engine.search(query=rewritten_query, role=target_role, limit=25, expanded_queries=expanded_queries)
        yield {"stage": "HybridSearch", "msg": "đang tìm kiếm Hybrid (Dense + BM25)...", "result": len(retrieved_candidates)}
        
        # 5. Reranker
        top_docs = self.reranker.rerank(query=rewritten_query, docs=retrieved_candidates, top_n=5)
        yield {"stage": "Reranker", "msg": "đang xếp hạng Cross-Encoder...", "result": top_docs}
        
        # 6. Context Compression & Parent-Child mapping
        compressed_context = self._compress_context(top_docs)
        yield {"stage": "ContextCompression", "msg": "đang nén tối ưu ngữ cảnh phân cấp cha-con...", "result": len(compressed_context)}
        
        # 7. LLM Generation
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
        
        if config.OPENAI_API_KEY and config.EMBEDDING_PROVIDER != "mock" and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            try:
                client = OpenAI(api_key=config.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=[
                        {"role": "system", "content": system_msg},
                        {"role": "user", "content": user_msg}
                    ],
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
            
        # Cumulative cost calculations
        qe_usage = self.search_engine.expander.last_token_usage
        total_prompt = qe_usage["prompt_tokens"] + prompt_tokens + rewrite_usage["prompt_tokens"]
        total_comp = qe_usage["completion_tokens"] + completion_tokens + rewrite_usage["completion_tokens"]
        cost_info = self._calculate_llm_cost(total_prompt, total_comp)
        
        # Save to cache
        if self.cache:
            self.cache.set(query, final_answer, citations, target_role)
            
        res = {
            "query": query,
            "rewritten_query": rewritten_query,
            "role": target_role,
            "answer": final_answer,
            "citations": citations,
            "expanded_queries": expanded_queries,
            "compressed_context_len": len(compressed_context),
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
        
        yield {"stage": "CitationValidator", "msg": "hoàn tất xác thực nguồn trích dẫn!", "result": res}

    def _rewrite_query(self, query: str, chat_history: List[Dict[str, str]] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Rewrites a contextual query into a self-contained search query based on chat history.
        Returns (rewritten_query, token_usage).
        """
        if not chat_history:
            return query, {"prompt_tokens": 0, "completion_tokens": 0}
            
        # Format history
        history_str = ""
        for turn in chat_history[-3:]:  # limit to last 3 turns
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
        Returns (extracted_description, token_usage).
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
        Creates a high-quality deterministic fallback response displaying
        exact legal sections and citations if the LLM key is absent.
        """
        if not docs:
            return (
                f"Chào {role_display}, rất tiếc là hệ thống hiện không tìm thấy tài liệu chính sách nào "
                f"liên quan đến câu hỏi '{query}' của bạn."
            )
            
        first_doc = docs[0]
        source = first_doc.metadata.get("source", "policy.md")
        section = first_doc.metadata.get("section", "Introduction")
        
        answer = (
            f"Hệ thống RAG Xanh SM (Chế độ Ngoại tuyến) xin phản hồi đến {role_display}:\n\n"
            f"Dựa trên tài liệu chính sách chính thức mục **\"{section}\"**:\n\n"
            f"> {first_doc.page_content.strip()}\n\n"
            f"Để được giải đáp chi tiết hơn hoặc xử lý khiếu nại, quý khách vui lòng liên hệ Tổng đài Xanh SM: **1900 2088**."
        )
        return answer

if __name__ == "__main__":
    pipeline = XanhSMRAGPipeline()
    res = pipeline.run("Phí hủy chuyến xe là bao nhiêu?", role="customer")
    print(f"\nAnswer:\n{res['answer']}")
    print(f"\nCitations:\n{res['citations']}")
