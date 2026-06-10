"""
Phase 3: Content Crawling
- Dùng requests + BeautifulSoup cho HTML tĩnh từ URL registry
- Tích hợp cơ chế Retry và Stealth headers để xử lý link không ổn định
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import logging
import time
import random
from typing import Dict, Optional
from datetime import datetime
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PageCrawler:
    def __init__(self):
        self.session = requests.Session()
        
        # Chiến thuật Retry: Thử lại tối đa 3 lần nếu gặp lỗi server hoặc mạng
        # Backoff factor giúp giãn cách thời gian giữa các lần thử (2s, 4s, 8s...)
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Headers giả lập trình duyệt thật để vượt qua các bộ lọc cơ bản
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Cache-Control": "max-age=0",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        })

    def crawl_with_requests(self, url: str) -> Optional[Dict]:
        """Crawl bằng requests với cơ chế Retry và Stealth headers"""
        try:
            # Thêm Referer ngẫu nhiên để trông giống người dùng từ Google tới
            self.session.headers.update({"Referer": "https://www.google.com/"})
            
            # Tăng timeout lên 30s
            resp = self.session.get(url, timeout=30, allow_redirects=True)
            
            # Xử lý các mã lỗi HTTP cụ thể
            if resp.status_code == 404:
                logger.warning(f"⚠️ URL not found (404): {url}. Skipping...")
                return None
            
            resp.raise_for_status()
            resp.encoding = resp.encoding or "utf-8"
            if resp.encoding.lower() in {"iso-8859-1", "latin-1"}:
                resp.encoding = "utf-8"
            
            soup = BeautifulSoup(resp.text, "html.parser")
            
            # Lấy title
            title = soup.find("title")
            title_text = title.string if title else ""
            
            # Hoặc lấy từ meta
            og_title = soup.find("meta", property="og:title")
            if og_title:
                title_text = og_title.get("content", title_text)
            
            return {
                "url": url,
                "title": title_text,
                "html": str(soup),
                "status": 200,
                "crawl_method": "requests",
                "crawl_timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Requests crawl failed for {url}: {e}")
            return None

    def crawl(self, url: str) -> Optional[Dict]:
        """Crawl URL"""
        logger.info(f"🔗 Crawling: {url}")
        # Thêm một khoảng nghỉ nhỏ ngẫu nhiên (0.5s - 1.5s) để tránh bị nhận diện bot
        time.sleep(random.uniform(0.5, 1.5))
        return self.crawl_with_requests(url)

    def crawl_batch(self, urls: list, output_dir: str = "data/raw") -> Dict[str, list]:
        """Crawl nhiều URL"""
        logger.info("=" * 50)
        logger.info("PHASE 3: CONTENT CRAWLING (Robust Mode)")
        logger.info("=" * 50)
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        success = []
        failed = []
        
        for i, url in enumerate(urls, 1):
            logger.info(f"\n[{i}/{len(urls)}] Crawling...")
            
            result = self.crawl(url)
            
            if result:
                success.append(result)
                
                # Lưu HTML thô
                html_file = Path(output_dir) / f"{i:04d}.json"
                with open(html_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                logger.info(f"✅ Saved to {html_file}")
            else:
                failed.append(url)
        
        logger.info(f"\n✨ Crawled: {len(success)}/{len(urls)}")
        logger.info(f"❌ Failed: {len(failed)}")
        
        return {
            "success": success,
            "failed": failed,
            "total": len(urls)
        }


if __name__ == "__main__":
    crawler = PageCrawler()
    
    # Test link khó
    result = crawler.crawl("https://www.greensm.com/vn-vi/news/bac-tai-xanh-taxi-cap-nhat-dieu-kien-chinh-sach-dam-bao-thu-nhap-moi")
    if result:
        print(f"✅ Success! Title: {result['title']}")
    else:
        print("❌ Still failed.")
