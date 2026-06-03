"""
Phase 3: Content Crawling
- Dùng requests + BeautifulSoup cho HTML tĩnh
- Hoặc Playwright cho JavaScript rendering
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
    def __init__(self, use_playwright: bool = False):
        self.use_playwright = use_playwright
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.playwright = None
        self.browser = None

    def init_playwright(self):
        """Khởi tạo Playwright nếu cần"""
        if not self.use_playwright:
            return
        
        try:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright()
            self.browser = self.playwright.start()
            logger.info("✅ Playwright initialized")
        except ImportError:
            logger.warning("⚠️ Playwright not installed, falling back to requests")
            self.use_playwright = False

    def close_playwright(self):
        """Đóng Playwright"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def crawl_with_requests(self, url: str) -> Optional[Dict]:
        """Crawl bằng requests (nhanh, nhưng không render JS)"""
        try:
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            
            soup = BeautifulSoup(resp.content, "html.parser")
            
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

    def crawl_with_playwright(self, url: str) -> Optional[Dict]:
        """Crawl bằng Playwright (chậm, nhưng render JS)"""
        try:
            if not self.browser:
                self.init_playwright()
            
            page = self.browser.new_page()
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle")
            
            # Lấy title
            title = page.title()
            
            # Lấy HTML đã render
            html = page.content()
            
            page.close()
            
            return {
                "url": url,
                "title": title,
                "html": html,
                "status": 200,
                "crawl_method": "playwright",
                "crawl_timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"❌ Playwright crawl failed for {url}: {e}")
            return None

    def crawl(self, url: str) -> Optional[Dict]:
        """Crawl URL"""
        logger.info(f"🔗 Crawling: {url}")
        
        if self.use_playwright:
            return self.crawl_with_playwright(url)
        else:
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
    crawler = PageCrawler(use_playwright=False)
    
    # Test
    result = crawler.crawl("https://www.greensm.com/vn-vi")
    if result:
        print(f"Title: {result['title']}")
        print(f"HTML length: {len(result['html'])}")
