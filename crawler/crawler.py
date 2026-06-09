"""
Phase 3: Content Crawling
- Dùng requests + BeautifulSoup cho HTML tĩnh từ URL registry
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Optional
from datetime import datetime
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PageCrawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def crawl_with_requests(self, url: str) -> Optional[Dict]:
        """Crawl bằng requests (nhanh, nhưng không render JS)"""
        try:
            resp = self.session.get(url, timeout=15)
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
        return self.crawl_with_requests(url)

    def crawl_batch(self, urls: list, output_dir: str = "data/raw") -> Dict[str, list]:
        """Crawl nhiều URL"""
        logger.info("=" * 50)
        logger.info("PHASE 3: CONTENT CRAWLING")
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
    
    # Test
    result = crawler.crawl("https://www.greensm.com/vn-vi")
    if result:
        print(f"Title: {result['title']}")
        print(f"HTML length: {len(result['html'])}")
