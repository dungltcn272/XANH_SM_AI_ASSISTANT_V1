"""
Orchestration - Điều phối toàn bộ crawler
Phase 1: URL Discovery
Phase 2: URL Filtering (integrated in Phase 1)
Phase 3: Content Crawling
Phase 4: HTML → Markdown
Phase 5: Classification
Phase 6: Save File
"""

import json
import logging
from pathlib import Path
from typing import List, Dict
from datetime import datetime
import urllib.parse

# Import modules
from discovery import URLDiscovery
from crawler import PageCrawler
from markdown_converter import MarkdownConverter
from classifier import Classifier
from storage import Storage
from pdf_generator import PDFGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GreenSMCrawler:
    """Main crawler orchestrator"""
    
    def __init__(self, 
                 base_url: str = "https://www.greensm.com/vn-vi",
                 use_playwright: bool = False,
                 max_urls: int = 500):
        self.base_url = base_url
        self.max_urls = max_urls
        
        self.discovery = URLDiscovery(base_url)
        self.crawler = PageCrawler(use_playwright=use_playwright)
        self.converter = MarkdownConverter()
        self.classifier = Classifier()
        self.storage = Storage()
        self.pdf_generator = PDFGenerator()
    
    def run(self, resume_from: int = 0):
        """Chạy toàn bộ crawler"""
        logger.info("=" * 70)
        logger.info("🚀 GREEN SM CRAWLER START")
        logger.info("=" * 70)
        
        # Phase 1 & 2: Read URLs and Categories from urls.txt
        logger.info("\n📍 PHASE 1 & 2: Read URLs from urls.txt")
        urls_to_crawl = []
        url_categories = {}
        url_is_pdf = {}
        current_category = "user"
        
        urls_file = Path(__file__).parent / "urls.json"
        if urls_file.exists():
            with open(urls_file, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                    for cat, urls_list in data.items():
                        for url_str in urls_list:
                            is_pdf = "(pdf)" in url_str.lower()
                            clean_url = url_str.split(" ")[0].strip()
                            urls_to_crawl.append(clean_url)
                            url_categories[clean_url] = cat.lower()
                            url_is_pdf[clean_url] = is_pdf
                except Exception as e:
                    logger.error(f"❌ Lỗi khi đọc urls.json: {e}")
                    return
        else:
            logger.error("❌ urls.json not found!")
            return
            
        urls = urls_to_crawl[:self.max_urls]
        
        if not urls:
            logger.error("❌ No URLs found in urls.txt!")
            return
        
        logger.info(f"✅ Loaded {len(urls)} URLs from urls.txt")
        
        # Resume từ URL cụ thể nếu cần
        if resume_from > 0:
            urls = urls[resume_from:]
            logger.info(f"⏭️  Resuming from URL #{resume_from} ({len(urls)} remaining)")
        
        # Phase 3: Content Crawling
        logger.info("\n📍 PHASE 3: Content Crawling")
        root_dir = Path(__file__).parent.parent
        raw_dir = root_dir / "data" / "raw"
        crawl_results = self.crawler.crawl_batch(urls, output_dir=str(raw_dir))
        
        if not crawl_results["success"]:
            logger.error("❌ No pages crawled successfully!")
            return
        
        # Phase 4, 5, 6: Extraction + Classification + Storage
        logger.info("\n📍 PHASE 4, 5, 6: Extraction → Classification → Storage")
        
        documents = []
        for i, page_data in enumerate(crawl_results["success"], 1):
            try:
                # Extract markdown from HTML
                markdown_content = self.converter.html_to_markdown(
                    page_data["html"],
                    page_data["title"],
                    page_data["url"]
                )
                
                # Sử dụng category được map từ urls.txt
                category = url_categories.get(page_data["url"], "user")
                
                # Đặt tên file logic
                path = urllib.parse.urlparse(page_data["url"]).path
                slug = path.strip("/").replace("/", "_")
                if not slug:
                    slug = "home"
                    
                is_pdf = url_is_pdf.get(page_data["url"], False)
                
                if is_pdf:
                    pdf_path = f"data/{category}/{slug}.pdf"
                    logger.info(f"[{i}] Generaring PDF for {page_data['url']} -> {pdf_path}")
                    self.pdf_generator.extract_images_and_save_pdf(
                        html=page_data["html"],
                        base_url=page_data["url"],
                        output_path=pdf_path
                    )
                
                doc = {
                    "url": page_data["url"],
                    "title": page_data["title"],
                    "content": markdown_content,
                    "category": category,
                    "crawl_date": datetime.now().strftime("%Y-%m-%d"),
                    "slug": slug
                }
                
                documents.append(doc)
                logger.debug(f"[{i}] {category}: {page_data['title'][:50]}")
                
            except Exception as e:
                logger.error(f"[{i}] Error processing {page_data['url']}: {e}")
                continue
        
        # Save to files
        logger.info(f"\n💾 Saving {len(documents)} documents...")
        results = self.storage.save_batch(documents)
        
        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("✨ SUMMARY")
        logger.info("=" * 70)
        logger.info(f"URLs discovered: {len(urls)}")
        logger.info(f"Pages crawled: {len(crawl_results['success'])}")
        logger.info(f"Pages failed: {len(crawl_results['failed'])}")
        logger.info(f"Documents saved: {len(results['saved'])}")
        logger.info(f"Documents failed: {len(results['failed'])}")
        logger.info(f"\nBy category:")
        for category, count in sorted(results["by_category"].items()):
            logger.info(f"  - {category}: {count}")
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ CRAWLER COMPLETE")
        logger.info("=" * 70)
        
        # Save metadata
        self._save_metadata({
            "urls_discovered": len(urls),
            "pages_crawled": len(crawl_results["success"]),
            "pages_failed": len(crawl_results["failed"]),
            "documents_saved": len(results["saved"]),
            "by_category": results["by_category"],
            "timestamp": datetime.now().isoformat()
        })
    
    def _save_metadata(self, metadata: Dict):
        """Lưu metadata"""
        metadata_file = Path("data/metadata.json")
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        logger.info(f"📊 Metadata saved to {metadata_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Green SM Website Crawler")
    parser.add_argument("--max-urls", type=int, default=100, 
                       help="Maximum URLs to crawl (default: 100)")
    parser.add_argument("--use-playwright", action="store_true",
                       help="Use Playwright for JavaScript rendering")
    parser.add_argument("--resume", type=int, default=0,
                       help="Resume from URL index (default: 0)")
    
    args = parser.parse_args()
    
    crawler = GreenSMCrawler(
        use_playwright=args.use_playwright,
        max_urls=args.max_urls
    )
    
    crawler.run(resume_from=args.resume)
