import os
import json
from typing import List
from openai import OpenAI
from app.core.config import settings as config
from app.core.logger import log_warn
from app.rag.search.domain_vocabulary import enrich_queries

class XanhSMQueryExpansion:
    """
    Advanced query expansion module.
    Uses pure rule-based dictionary lookups for legal, policy, and service Vietnamese synonyms.
    LLM calls have been completely removed for maximum speed (~0ms).
    """
    
    def __init__(self):
        # Premium Vietnamese Legal/Operations Synonyms & Xanh SM Specific Terms
        self.synonym_dict = {
            # Dịch vụ CSKH
            "tong dai": ["hotline", "so dien thoai ho tro", "cham soc khach hang", "cskh", "1900 2088"],
            "hotline": ["tong dai", "so dien thoai ho tro", "cham soc khach hang", "cskh", "1900 2088"],
            "quen do": ["hanh ly that lac", "mat do", "quen hanh ly", "tra do", "tim do", "tim dien thoai"],
            
            # Tiền nong, cước phí
            "huy chuyen": ["huy xe", "huy cuoc", "phi phat huy", "khong di xe", "hoan tien huy"],
            "huy cuoc": ["huy chuyen", "huy xe", "phi phat huy", "khong di xe"],
            "hoa hong": ["chiet khau", "phi dich vu he thong", "phan chia doanh thu", "ty le an chia", "tien an chia"],
            "chiet khau": ["hoa hong", "phi dich vu he thong", "phan chia doanh thu", "ty le an chia"],
            "rut tien": ["doi soat", "chu ky thanh toan", "vi tai khoan", "chuyen tien", "chuyen khoan", "thanh toan"],
            "cuoc": ["gia tien", "phi dich vu", "bang gia", "gia cuoc", "tien xe"],
            "gia": ["cuoc", "phi", "chi phi", "bang gia", "gia ca"],
            
            # Xử lý sự cố, khiếu nại
            "phat": ["ky luat", "vi pham", "khoa tai khoan", "tam ngung", "che tai", "tru tien"],
            "khoa": ["tam ngung", "phat", "ky luat", "vi pham", "vo hieu hoa"],
            "tai nan": ["va cham", "su co", "bao hiem", "boi thuong", "den bu", "gap loi"],
            "den bu": ["boi thuong", "bao hiem", "hoan tien", "tai nan", "va cham"],
            "den hang": ["boi thuong", "bao hiem", "lam hong do", "hu hong", "that lac"],
            
            # Tên dịch vụ Xanh SM
            "bike": ["xe may", "xe 2 banh", "xe hai banh", "xanh sm bike", "xe may dien"],
            "taxi": ["o to", "xe 4 banh", "xe 4 cho", "xe 5 cho", "xanh sm taxi", "xe hoi"],
            "luxury": ["xe sang", "vf8", "xe vip", "xe cao cap"],
            "giao hang": ["express", "ship", "shipper", "giao do", "chuyen phat", "giao do an"],
            "express": ["giao hang", "ship", "shipper"],
            "tinh": ["duong dai", "di xa", "xe di tinh", "thue xe di tinh", "lien tinh"],
            "thue xe": ["tu lai", "thue mien phi", "thue o to", "thue xe the"],
            
            # Từ đồng nghĩa đời thường
            "app": ["ung dung", "phan mem", "chuong trinh"],
            "tx": ["tai xe", "bac tai", "nguoi lai xe", "doi tac", "lai xe"],
            "doi tac": ["tai xe", "bac tai", "tx"],
            "kh": ["khach", "nguoi dung", "nguoi di xe", "khach hang"],
            "sdt": ["so dien thoai", "hotline", "sdt", "sđt", "phone"],
            "dang ky": ["dk", "tao tai khoan", "mo tai khoan", "dang ki"],
            "tuyen": ["dang ky chay", "lam tai xe", "chay xe", "hop tac"],
            
            # Xe điện
            "pin": ["sac", "tram sac", "doi pin", "thue pin", "het pin", "pin xe"],
            "tram sac": ["cay sac", "cho sac", "tram vgreen", "v-green"],
        }

    def _strip_accents(self, text: str) -> str:
        import unicodedata
        normalized = unicodedata.normalize("NFD", text or "")
        return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower()

    def expand_query_rule_based(self, query: str) -> List[str]:
        expanded = [query]
        query_lower = self._strip_accents(query)
        
        for key, synonyms in self.synonym_dict.items():
            key_lower = self._strip_accents(key)
            # Khớp từ một cách tương đối
            if key_lower in query_lower:
                for syn in synonyms:
                    if syn not in expanded:
                        expanded.append(syn)
        return enrich_queries(query, expanded, max_queries=8)

    def get_queries(self, query: str) -> List[str]:
        """
        Main entry point for expansion. Now purely rule-based.
        """
        return self.expand_query_rule_based(query)

    def get_understanding(self, query: str):
        return None
