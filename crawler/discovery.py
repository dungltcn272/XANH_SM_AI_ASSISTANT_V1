"""
Phase 1 & 2: URL Discovery + Filtering
- Đọc robots.txt
- Tìm sitemap.xml
- BFS crawl nếu cần
- Lọc + chuẩn hóa URL
"""

import requests
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse, parse_qs, urlunparse
from collections import deque
import logging
from typing import Set, List
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.greensm.com/vn-vi"


class URLDiscovery:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.urls_found = set()
        self.urls_visited = set()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def normalize_url(self, url: str) -> str:
        """Chuẩn hóa URL: loại bỏ fragment, query params rác"""
        parsed = urlparse(url)
        
        # Loại bỏ fragment (#)
        parsed = parsed._replace(fragment="")
        
        # Loại bỏ query params rác
        if parsed.query:
            params = parse_qs(parsed.query)
            # Giữ lại params hữu ích, loại bỏ utm_*, fbclid, v.v.
            clean_params = {}
            for key, value in params.items():
                if key.startswith("utm_") or key in ["fbclid"]:
                    continue
                clean_params[key] = value[0] if value else ""
            
            if clean_params:
                query_string = "&".join(f"{k}={v}" for k, v in clean_params.items())
                parsed = parsed._replace(query=query_string)
            else:
                parsed = parsed._replace(query="")
        
        url = urlunparse(parsed)
        
        # Loại bỏ trailing slash (nhưng giữ base)
        if url != self.base_url and url.endswith("/"):
            url = url.rstrip("/")
        
        return url

    def is_valid_url(self, url: str) -> bool:
        """Kiểm tra URL có hợp lệ không"""
        parsed = urlparse(url)
        
        # Phải cùng domain
        if parsed.netloc != self.domain:
            return False
        
        # Phải là /vn-vi/
        if "/vn-vi/" not in url:
            return False
        
        # Loại bỏ URL với anchor hoặc social
        if any(x in url for x in ["#", "facebook.com", "linkedin.com", "youtube.com"]):
            return False
        
        return True

    def fetch_sitemap(self) -> List[str]:
        """Lấy URL từ sitemap.xml"""
        logger.info("🔍 Tìm sitemap.xml...")
        try:
            sitemap_url = f"{self.base_url.rsplit('/', 1)[0]}/sitemap.xml"
            resp = self.session.get(sitemap_url, timeout=10)
            
            if resp.status_code != 200:
                logger.warning(f"⚠️ sitemap.xml không tìm thấy")
                return []
            
            root = ET.fromstring(resp.content)
            urls = []
            
            # Parse sitemap namespace
            namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            for url_elem in root.findall('.//ns:loc', namespaces):
                url = url_elem.text
                if url and self.is_valid_url(url):
                    urls.append(self.normalize_url(url))
            
            logger.info(f"✅ Tìm được {len(urls)} URLs từ sitemap")
            return urls
            
        except Exception as e:
            logger.error(f"❌ Lỗi khi đọc sitemap: {e}")
            return []

    def bfs_crawl(self, max_urls: int = 500, start_url: str = None) -> List[str]:
        """BFS crawl từ base_url nếu không có sitemap"""
        if start_url is None:
            start_url = self.base_url
        
        logger.info(f"🔄 BFS crawl từ {start_url}...")
        
        queue = deque([start_url])
        urls_found = set()
        urls_visited = set()
        urls_found.add(start_url)
        urls_visited.add(start_url)
        
        while queue and len(urls_found) < max_urls:
            current_url = queue.popleft()
            
            try:
                resp = self.session.get(current_url, timeout=10)
                if resp.status_code != 200:
                    continue
                
                soup = BeautifulSoup(resp.content, "html.parser")
                
                for link in soup.find_all("a", href=True):
                    url = urljoin(current_url, link["href"])
                    url = self.normalize_url(url)
                    
                    if url not in urls_visited and self.is_valid_url(url):
                        urls_visited.add(url)
                        urls_found.add(url)
                        queue.append(url)
                        logger.debug(f"  Found: {url}")
                
                logger.info(f"📊 {len(urls_found)} URLs discovered")
                
            except Exception as e:
                logger.error(f"❌ Lỗi crawl {current_url}: {e}")
                continue
        
        return sorted(list(urls_found))

    def discover(self, use_sitemap: bool = True, max_urls: int = 500) -> List[str]:
        """Tìm toàn bộ URLs"""
        logger.info("=" * 50)
        logger.info("PHASE 1: URL DISCOVERY")
        logger.info("=" * 50)
        
        urls = []
        
        # Ưu tiên sitemap
        if use_sitemap:
            urls = self.fetch_sitemap()
        
        # Nếu sitemap rỗng, dùng BFS
        if not urls:
            logger.info("📍 Crawl trang chủ...")
            urls = self.bfs_crawl(max_urls=max_urls // 2)
            
            # Cộng thêm trang policy
            logger.info("📍 Crawl trang policy...")
            policy_url = f"{self.base_url}/terms-policies"
            if policy_url not in urls:
                policy_urls = self.bfs_crawl(max_urls=max_urls // 2, start_url=policy_url)
                urls.extend(policy_urls)
        
        # Remove duplicates while preserving order
        urls_seen = set()
        unique_urls = []
        for url in urls:
            if url not in urls_seen:
                urls_seen.add(url)
                unique_urls.append(url)
        
        logger.info(f"\n✨ Tìm được tổng cộng {len(unique_urls)} URLs\n")
        return unique_urls[:max_urls]


if __name__ == "__main__":
    discovery = URLDiscovery()
    urls = discovery.discover()
    
    for url in urls[:10]:
        print(url)
