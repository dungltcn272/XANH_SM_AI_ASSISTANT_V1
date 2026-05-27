import os
import sys
import argparse
import time
import requests
from pathlib import Path
from urllib.parse import urlparse, urljoin
from collections import deque
from bs4 import BeautifulSoup

# Allow running this file directly: `python app/crawler/crawl.py`
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.crawler.parser import html_to_markdown
from app.config import config

class GreenSMCrawler:
    """
    State-of-the-art BFS Web Crawler targeting Greensm.com.
    Traverses internal links, extracts policies, terms, and FAQs, 
    and saves them in a classified folder structure.
    """
    
    def __init__(self, start_url: str, max_depth: int = 3, max_pages: int = 50, progress_callback = None):
        self.start_url = start_url
        self.domain = urlparse(start_url).netloc
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited = set()
        self.progress_callback = progress_callback
        
    def is_internal_link(self, url: str) -> bool:
        netloc = urlparse(url).netloc
        return netloc == self.domain or netloc == ""

    def categorize_content(self, url: str, content: str) -> str:
        """
        Classifies page into: customer, driver, merchant, or faq based on URL & content.
        Uses high-threshold body content matching to avoid global footer matches.
        """
        url_lower = url.lower()
        content_lower = content.lower()
        
        # 1. Reliable URL keyword patterns first
        if "driver" in url_lower or "tai-xe" in url_lower:
            return "driver"
        elif "merchant" in url_lower or "doi-tac-cua-hang" in url_lower:
            return "merchant"
        elif "refund" in url_lower or "hoan-tien" in url_lower:
            return "customer"
        elif "terms" in url_lower or "policy" in url_lower or "dieu-khoan" in url_lower:
            return "customer"
            
        # 2. Specific main body text matches (avoiding general footer elements like "Đăng ký tài xế")
        if "chính sách tài xế" in content_lower or "chiết khấu của tài xế" in content_lower or "tác phong tài xế" in content_lower:
            return "driver"
        elif "chiết khấu hoa hồng cửa hàng" in content_lower or "quy trình đối soát cửa hàng" in content_lower:
            return "merchant"
        elif "chính sách bồi thường" in content_lower or "chính sách hoàn tiền" in content_lower or "phí hủy chuyến sau" in content_lower:
            return "customer"
            
        return "faq"

    def get_filename_from_url(self, url: str) -> str:
        path = urlparse(url).path
        if not path or path == "/":
            return "index.md"
        
        filename = path.strip("/").replace("/", "_").replace("-", "_")
        if not filename.endswith(".md"):
            filename += ".md"
        return filename

    def crawl(self):
        msg_start = f"Starting BFS crawl on {self.start_url} (Max Depth: {self.max_depth}, Max Pages: {self.max_pages})"
        print(f"[INFO] {msg_start}")
        if self.progress_callback:
            self.progress_callback("START", msg_start)
            
        queue = deque([(self.start_url, 0)])
        self.visited.add(self.start_url)
        pages_crawled = 0
        
        while queue and pages_crawled < self.max_pages:
            url, depth = queue.popleft()
            
            if depth > self.max_depth:
                continue
                
            msg_crawl = f"Crawling ({pages_crawled + 1}/{self.max_pages}): {url} (Depth: {depth})"
            print(f"[INFO] {msg_crawl}")
            if self.progress_callback:
                self.progress_callback("CRAWLING", msg_crawl)
            
            try:
                time.sleep(0.5)
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7"
                }
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code != 200:
                    print(f"[WARN] Failed to fetch {url}: Status code {response.status_code}")
                    continue
                    
                html_content = response.text
                markdown_content = html_to_markdown(html_content)
                
                if not markdown_content.strip():
                    print(f"[WARN] Empty markdown generated for {url}, skipping save.")
                    continue
                
                category = self.categorize_content(url, markdown_content)
                save_dir = os.path.join(config.DATA_DIR, category)
                os.makedirs(save_dir, exist_ok=True)
                
                filename = self.get_filename_from_url(url)
                filepath = os.path.join(save_dir, filename)
                
                metadata_header = f"---\nurl: {url}\ncategory: {category}\ncrawled_at: {time.strftime('%Y-%m-%d')}\n---\n\n"
                final_content = metadata_header + markdown_content
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(final_content)
                    
                msg_save = f"Saved to {filepath}"
                print(f"[SUCCESS] {msg_save}")
                if self.progress_callback:
                    self.progress_callback("SAVED", f"Saved {category}/{filename} ({url})")
                pages_crawled += 1
                
                if depth < self.max_depth:
                    soup = BeautifulSoup(html_content, "html.parser")
                    for a_tag in soup.find_all("a", href=True):
                        href = a_tag["href"]
                        full_url = urljoin(url, href)
                        
                        parsed_url = urlparse(full_url)
                        clean_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
                        
                        if self.is_internal_link(clean_url) and clean_url not in self.visited:
                            self.visited.add(clean_url)
                            queue.append((clean_url, depth + 1))
                            
            except Exception as e:
                msg_error = f"Error crawling {url}: {e}"
                print(f"[ERROR] {msg_error}")
                if self.progress_callback:
                    self.progress_callback("ERROR", msg_error)
 
        msg_complete = f"Crawling complete! Total pages successfully crawled: {pages_crawled}"
        print(f"[INFO] {msg_complete}")
        if self.progress_callback:
            self.progress_callback("COMPLETE", msg_complete)


def main():
    parser = argparse.ArgumentParser(description="Crawl Xanh SM pages into categorized markdown files.")
    parser.add_argument(
        "start_url",
        nargs="?",
        default=os.getenv("CRAWL_START_URL", "https://www.xanhsm.com/"),
        help="Starting URL for the crawl.",
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=config.MAX_CRAWL_DEPTH,
        help="Maximum crawl depth.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=config.MAX_CRAWL_PAGES,
        help="Maximum number of pages to crawl.",
    )
    args = parser.parse_args()

    crawler = GreenSMCrawler(
        start_url=args.start_url,
        max_depth=args.max_depth,
        max_pages=args.max_pages,
    )
    crawler.crawl()


if __name__ == "__main__":
    main()
