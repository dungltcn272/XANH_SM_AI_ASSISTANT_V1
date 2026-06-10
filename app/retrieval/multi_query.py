import os
import json
from typing import List
from openai import OpenAI
from app.core.config import settings as config
from app.core.logger import log_warn

class XanhSMQueryExpansion:
    """
    Advanced query expansion module.
    Uses rule-based dictionary lookups for legal & policy Vietnamese synonyms,
    and handles LLM-based Query Expansion if OpenAI API keys are configured.
    Includes robust offline check to prevent HTTPS DLL conflicts on Windows hosts.
    """
    
    def __init__(self):
        self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        # Premium Vietnamese Legal/Operations Synonyms
        self.synonym_dict = {
            "tongs dai": ["hotline", "so dien thoai ho tro", "cham soc khach hang", "cskh", "1900 2088"],
            "hotline": ["tong dai", "so dien thoai ho tro", "cham soc khach hang", "cskh", "1900 2088"],
            "huy chuyen": ["huy xe", "huy cuoc", "phi phat huy", "khong di xe", "hoan tien huy"],
            "huy cuoc": ["huy chuyen", "huy xe", "phi phat huy", "khong di xe"],
            "hoa hong": ["chiet khau", "phi dich vu he thong", "phan chia doanh thu", "ty le an chia"],
            "chiet khau": ["hoa hong", "phi dich vu he thong", "phan chia doanh thu", "ty le an chia"],
            "phat": ["ky luat", "vi pham", "khoa tai khoan", "tam ngung", "che tai"],
            "quen do": ["hanh ly that lac", "mat do", "quen hanh ly", "tra do"],
            "rut tien": ["doi soat", "chu ky thanh toan", "vi tai khoan", "chuyen tien"]
        }

    def expand_query_rule_based(self, query: str) -> List[str]:
        expanded = [query]
        query_lower = query.lower()
        
        for key, synonyms in self.synonym_dict.items():
            if key in query_lower:
                for syn in synonyms:
                    if syn not in expanded:
                        expanded.append(syn)
        return expanded

    def expand_query_llm(self, query: str) -> List[str]:
        """
        Uses LLM to generate 3 alternative queries in Vietnamese.
        Completely bypasses HTTPS request if the API key is not valid or in mock fallback.
        """
        self.last_token_usage = {"prompt_tokens": 0, "completion_tokens": 0}
        # If in fallback mock mode, bypass HTTPS call to avoid process-level DLL conflicts with local native models
        if config.EMBEDDING_PROVIDER == "mock" or not config.OPENAI_API_KEY or "YOUR_OPENAI_API_KEY" in config.OPENAI_API_KEY:
            return self.expand_query_rule_based(query)
            
        try:
            client = OpenAI(api_key=config.OPENAI_API_KEY, timeout=config.OPENAI_TIMEOUT_SECONDS)
            prompt = (
                f"Ban la chuyen gia hieu y dinh nguoi dung (Query Understanding). "
                f"Hay sinh ra 1 cau hoi dong nghia hoac co muc dich tim kiem tuong tu cau hoi duoi duoi bang tieng Viet.\n"
                f"Cau hoi goc: '{query}'\n\n"
                f"Tra ve ket qua duoi dang danh sach JSON cac chuoi: [\"cau 1\"]"
            )
            
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=120,
                response_format={"type": "json_object"}
            )
            
            self.last_token_usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            }
            
            data = json.loads(response.choices[0].message.content)
            for val in data.values():
                if isinstance(val, list):
                    # Limit to 1 extra query to avoid search noise
                    return [query] + val[:1]
            return self.expand_query_rule_based(query)
        except Exception as e:
            log_warn("RETRIEVAL", f"LLM Query Expansion failed: {str(e)}. Falling back to rule-based.")
            return self.expand_query_rule_based(query)

    def get_queries(self, query: str) -> List[str]:
        queries = self.expand_query_llm(query)
        return list(dict.fromkeys(queries))

    def get_understanding(self, query: str):
        return None
