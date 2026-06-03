"""
Phase 6: Save File
Lưu Markdown với metadata YAML frontmatter
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Storage:
    """Lưu Markdown file"""
    
    def __init__(self, output_dir: str = None):
        if output_dir is None:
            self.output_dir = Path(__file__).parent.parent / "data"
        else:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def url_to_filename(self, url: str) -> str:
        """Chuyển URL thành tên file"""
        # Lấy path từ URL
        # https://www.greensm.com/vn-vi/terms-policies/privacy-notice
        # → terms_policies_privacy_notice
        
        path = url.split("vn-vi/", 1)[-1]  # Lấy phần sau /vn-vi/
        path = path.rstrip("/")
        path = path.replace("/", "_")      # / → _
        path = path.replace("-", "_")      # - → _
        path = re.sub(r'[^\w_]', '', path)  # Loại bỏ ký tự đặc biệt
        path = re.sub(r'_+', '_', path)     # _ liên tiếp → _
        
        return path or "index"
    
    def save_markdown(self, 
                     url: str,
                     title: str,
                     content: str,
                     category: str,
                     crawl_date: str = None) -> Path:
        """Lưu Markdown file với metadata"""
        
        if not crawl_date:
            crawl_date = datetime.now().strftime("%Y-%m-%d")
        
        # Tạo frontmatter
        frontmatter = f"""---
url: {url}
category: {category}
crawl_date: {crawl_date}
title: {title}
---

"""
        
        # Combine frontmatter + content
        full_content = frontmatter + content
        
        # Tên file
        filename = self.url_to_filename(url) + ".md"
        
        # Make sure category directory exists
        category_dir = self.output_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = category_dir / filename
        
        # Lưu file
        filepath.write_text(full_content, encoding="utf-8")
        logger.info(f"✅ Saved: {filepath}")
        
        return filepath
    
    def save_batch(self, documents: list) -> Dict:
        """Lưu nhiều document"""
        results = {
            "saved": [],
            "failed": [],
            "by_category": {}
        }
        
        for doc in documents:
            try:
                filepath = self.save_markdown(
                    url=doc["url"],
                    title=doc.get("title", ""),
                    content=doc["content"],
                    category=doc["category"],
                    crawl_date=doc.get("crawl_date")
                )
                
                results["saved"].append(str(filepath))
                
                category = doc["category"]
                if category not in results["by_category"]:
                    results["by_category"][category] = 0
                results["by_category"][category] += 1
                
            except Exception as e:
                logger.error(f"❌ Failed to save {doc.get('url')}: {e}")
                results["failed"].append({
                    "url": doc.get("url"),
                    "error": str(e)
                })
        
        logger.info(f"\n✨ Saved {len(results['saved'])} files")
        logger.info(f"❌ Failed: {len(results['failed'])}")
        logger.info(f"\nBy category: {results['by_category']}")
        
        return results


if __name__ == "__main__":
    storage = Storage()
    
    test_doc = {
        "url": "https://www.greensm.com/vn-vi/terms-policies/privacy-notice",
        "title": "Chính sách bảo mật",
        "content": "# Chính sách bảo mật\n\nNội dung đây là nội dung chính sách...",
        "category": "policy"
    }
    
    filepath = storage.save_markdown(**test_doc)
    print(f"Saved to: {filepath}")
