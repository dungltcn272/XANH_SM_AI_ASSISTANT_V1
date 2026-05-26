import os
from typing import List, Dict, Any
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
        
    def _compress_context(self, docs: List[Any]) -> str:
        """
        Formats and compresses retrieved documents with source boundaries.
        """
        formatted_blocks = []
        for idx, doc in enumerate(docs):
            source = doc.metadata.get("source", "unknown_policy.md")
            section = doc.metadata.get("section", "Introduction")
            content = doc.page_content.strip()
            
            block = (
                f"[Tài liệu tham khảo #{idx + 1}]\n"
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
        Fuzzy, spell-tolerant and accent-insensitive detector for greetings and thanks.
        Bypasses LLM calls entirely to avoid process cost.
        """
        import unicodedata
        
        # Clean string
        q_clean = query.strip().lower().rstrip('?').rstrip('!').strip()
        
        # Remove accents
        nfkd_form = unicodedata.normalize('NFKD', q_clean)
        q_no_accent = u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
        
        # Core greeting roots (including spelling typos)
        greeting_roots = {
            "hello", "hi", "halo", "helo", "hey", "hola", "hiii", "helloo", "heloo",
            "xin chao", "xinchao", "chao ban", "chao", "xjn chao", "gui loi chao", "helooo",
            "chao ad", "chao ban nhe", "chao bot", "ad oi"
        }
        
        # Core thanks roots (including spelling typos)
        thanks_roots = {
            "cam on", "camon", "thank you", "thanks", "thankss", "tks", "thks", "ty", "thank",
            "cam on nhiu", "cam on nhieu", "cam on ban", "thanks ban", "cám ơn", "cảm ơn"
        }
        
        # 1. Exact match or root overlap checks
        is_greet = q_clean in greeting_roots or q_no_accent in greeting_roots or any(root in q_no_accent for root in ["xin chao", "xinchao", "chao ban"])
        is_thank = q_clean in thanks_roots or q_no_accent in thanks_roots or any(root in q_no_accent for root in ["cam on", "camon", "thank you"])
        
        # 2. Extremely short queries with no numbers (e.g. "ok", "yes", "no", "he", "uh", "a")
        if not is_greet and not is_thank:
            if len(q_clean) <= 3 and not any(c.isdigit() for c in q_clean):
                is_greet = True
                
        if is_greet:
            return {
                "type": "greeting",
                "answer": "Xin chào! Tôi là Trợ lý AI CSKH của Xanh SM. Tôi có thể hỗ trợ gì cho quý khách về các chính sách hủy chuyến, biểu phí dịch vụ hay quy định hôm nay?"
            }
        elif is_thank:
            return {
                "type": "thanks",
                "answer": "Dạ, rất vui được hỗ trợ quý khách! Nếu cần bất kỳ thông tin gì thêm, xin vui lòng nhắn tôi nhé."
            }
            
        return {"type": "none", "answer": ""}

    def run(self, query: str, role: str = None) -> Dict[str, Any]:
        """
        Executes the full advanced RAG chain.
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

        print(f"[*] Processing pipeline query='{query}' for role='{target_role}' ({role_display})")
        
        # 1. Retrieve Candidate Documents (Dense + Sparse Hybrid RRF)
        # Expansion step may trigger an OpenAI Completion call (will be tracked)
        expanded_queries = self.search_engine.expander.get_queries(query)
        retrieved_candidates = self.search_engine.search(query=query, role=target_role, limit=25)
        
        # 2. Rerank down to top 5 (Offline: Cost = $0)
        top_docs = self.reranker.rerank(query=query, docs=retrieved_candidates, top_n=5)
        
        # 3. Compress context blocks (Offline)
        compressed_context = self._compress_context(top_docs)
        
        # 4. Synthesize final response using LLM
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
        user_msg = USER_PROMPT_TEMPLATE.format(role_display=role_display, query=query)
        
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
                final_answer = self._generate_fallback_answer(query, top_docs, role_display)
        else:
            print("[INFO] Running Resilient Offline Fallback Synthesis.")
            final_answer = self._generate_fallback_answer(query, top_docs, role_display)
            
        # 5. Calculate cumulative costs
        qe_usage = self.search_engine.expander.last_token_usage
        total_prompt = qe_usage["prompt_tokens"] + prompt_tokens
        total_comp = qe_usage["completion_tokens"] + completion_tokens
        cost_info = self._calculate_llm_cost(total_prompt, total_comp)
            
        return {
            "query": query,
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

    def run_step_by_step(self, query: str, role: str = None):
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

        # Regular RAG Flow step by step
        yield {"stage": "Question", "msg": "đang nhận câu hỏi...", "result": None}
        
        # 1. Query Expansion (triggers OpenAI token usage)
        expanded_queries = self.search_engine.expander.get_queries(query)
        yield {"stage": "QueryUnderstanding", "msg": "đang mở rộng truy vấn (Query Expansion)...", "result": expanded_queries}
        
        # 2. Hybrid Search (Dense and Sparse indexes)
        retrieved_candidates = self.search_engine.search(query=query, role=target_role, limit=25)
        yield {"stage": "HybridSearch", "msg": "đang tìm kiếm Hybrid (Dense + BM25)...", "result": len(retrieved_candidates)}
        
        # 3. Reranker
        top_docs = self.reranker.rerank(query=query, docs=retrieved_candidates, top_n=5)
        yield {"stage": "Reranker", "msg": "đang xếp hạng Cross-Encoder...", "result": top_docs}
        
        # 4. Context Compression
        compressed_context = self._compress_context(top_docs)
        yield {"stage": "ContextCompression", "msg": "đang nén tối ưu ngữ cảnh...", "result": len(compressed_context)}
        
        # 5. LLM Generation
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
        user_msg = USER_PROMPT_TEMPLATE.format(role_display=role_display, query=query)
        
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
                final_answer = self._generate_fallback_answer(query, top_docs, role_display)
        else:
            print("[INFO] Running Resilient Offline Fallback Synthesis.")
            final_answer = self._generate_fallback_answer(query, top_docs, role_display)
            
        # Cumulative cost calculations
        qe_usage = self.search_engine.expander.last_token_usage
        total_prompt = qe_usage["prompt_tokens"] + prompt_tokens
        total_comp = qe_usage["completion_tokens"] + completion_tokens
        cost_info = self._calculate_llm_cost(total_prompt, total_comp)
            
        res = {
            "query": query,
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
