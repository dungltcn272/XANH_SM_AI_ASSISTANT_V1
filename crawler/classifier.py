"""
Phase 5: Classification
Rule-based classification dựa vào URL
"""

import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Classifier:
    """Phân loại tài liệu dựa vào URL"""
    
    def __init__(self):
        self.rules = {
            "policy": [
                "terms-policies", "policy", "terms", "conditions", "terms-and-conditions", "dieu-khoan", "chinh-sach"
            ],
            "driver": [
                "tai-xe", "driver", "tai-xet", "taixe", "for-driver"
            ],
            "merchant": [
                "merchant", "partner", "business", "doanh-nghiep"
            ],
            "greencare": [
                "green-care", "bao-hiem", "insurance"
            ],
            "support": [
                "support", "help", "faq", "ho-tro", "tro-giup", "question", "answer", "helps"
            ],
            "user": [
                "green-sm", "car", "bike", "premium", "limo", "airport", "tour", "express", "van", "gift-card", "lien-tinh", "service", "product", "dich-vu", "san-pham", "khach-hang", "user"
            ]
        }
    
    def classify(self, url: str, title: str = "") -> str:
        """Phân loại URL"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        # Kiểm tra rule
        for category, keywords in self.rules.items():
            for keyword in keywords:
                if keyword in url_lower or keyword in title_lower:
                    logger.debug(f"Classified as '{category}' (keyword: {keyword})")
                    return category
        
        # Default fallback to user since most uncategorized are user vehicle pages
        return "user"


if __name__ == "__main__":
    clf = Classifier()
    
    tests = [
        ("https://www.greensm.com/vn-vi/terms-policies/general", "Điều khoản chung"),
        ("https://www.greensm.com/vn-vi/tai-xe", "Tài xế"),
        ("https://www.greensm.com/vn-vi/merchant", "Merchant"),
        ("https://www.greensm.com/vn-vi/support", "Hỗ trợ"),
        ("https://www.greensm.com/vn-vi/green-sm-car", "Green SM Car"),
        ("https://www.greensm.com/vn-vi/about", "Về chúng tôi"),
    ]
    
    for url, title in tests:
        category = clf.classify(url, title)
        print(f"{url} → {category}")
