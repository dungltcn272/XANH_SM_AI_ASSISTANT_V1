import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from category_cleaners import DeterministicCleaner
from crawler import PageCrawler
from manifest import CrawlManifest
from overview_generator import generate_overview_catalogs
from pdf_utils import extract_pdf_markdown
from registry import get_enabled_sources
from storage import Storage


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class GreenSMCrawler:
    """Deterministic crawler orchestrator.

    Production crawling reads curated URLs from crawl_sources/urls.json only.
    It never discovers URLs automatically and never calls an LLM.
    """

    def __init__(
        self,
        max_urls: int = 0,
        source_profiles: list[str] | None = None,
        categories: list[str] | None = None,
    ):
        self.max_urls = max_urls
        self.source_profiles = source_profiles or ["main_site"]
        self.categories = categories
        self.crawler = PageCrawler()
        self.cleaner = DeterministicCleaner()
        self.storage = Storage()
        self.root_dir = Path(__file__).parent.parent

    def run(self, resume_from: int = 0) -> None:
        logger.info("=" * 70)
        logger.info("GREEN SM DETERMINISTIC CRAWLER START")
        logger.info("=" * 70)

        sources = get_enabled_sources(
            source_profiles=self.source_profiles,
            categories=self.categories,
            include_pdfs=True,
            limit=self.max_urls,
            auto_bootstrap=True,
        )
        if resume_from > 0:
            sources = sources[resume_from:]
            logger.info("Resuming from URL index %s (%s remaining)", resume_from, len(sources))

        if not sources:
            logger.error("No enabled URLs found in crawl_sources.")
            return

        source_meta = {source.url: source for source in sources}
        logger.info("Loaded %s URLs from crawl_sources", len(sources))
        logger.info("Source profiles: %s", ", ".join(self.source_profiles))
        if self.categories:
            logger.info("Categories: %s", ", ".join(self.categories))

        crawl_success, crawl_failed = self._crawl_sources(sources)
        if not crawl_success:
            logger.error("No documents crawled successfully.")
            return

        documents = []
        manifest = CrawlManifest("deterministic_crawl", sources=self.source_profiles)

        for page_data in crawl_success:
            source = source_meta.get(page_data["url"])
            try:
                doc = self._build_document(page_data, source)
                documents.append(doc)
                logger.debug("Prepared %s: %s", doc["category"], doc["title"][:80])
            except Exception as exc:
                logger.exception("Error processing %s: %s", page_data.get("url"), exc)
                manifest.add_error(
                    page_data.get("url", ""),
                    str(exc),
                    source_profile=getattr(source, "source_profile", ""),
                    category=getattr(source, "category", ""),
                )

        logger.info("Saving %s documents...", len(documents))
        results = self.storage.save_batch(documents)

        for item in results["saved"]:
            manifest.add_document(
                url=item["url"],
                output_path=item["path"],
                source_profile=item.get("source_profile", ""),
                source_type=item.get("source_type", ""),
                category=item.get("category", ""),
                document_type=item.get("document_type", ""),
                content=item.get("content", ""),
                warnings=item.get("warnings", []),
            )
        for item in results["failed"]:
            manifest.add_error(item.get("url", ""), item.get("error", ""))
        for failed_url in crawl_failed:
            source = source_meta.get(failed_url)
            manifest.add_error(
                failed_url,
                "crawl_failed",
                source_profile=getattr(source, "source_profile", ""),
                category=getattr(source, "category", ""),
            )

        manifest_path = manifest.save(root_dir=self.root_dir / "data")
        overview_paths = generate_overview_catalogs(self.root_dir / "data")
        self._save_metadata({
            "urls_from_registry": len(sources),
            "pages_crawled": len(crawl_success),
            "pages_failed": len(crawl_failed),
            "documents_saved": len(results["saved"]),
            "documents_failed": len(results["failed"]),
            "by_category": results["by_category"],
            "source_profiles": self.source_profiles,
            "categories": self.categories or [],
            "timestamp": datetime.now().isoformat(),
        })

        logger.info("Crawl manifest saved to %s", manifest_path)
        logger.info("Overview catalogs generated: %s files", len(overview_paths))
        logger.info("=" * 70)
        logger.info("CRAWLER COMPLETE")
        logger.info("Loaded: %s | Crawled: %s | Failed: %s | Saved: %s",
                    len(sources), len(crawl_success), len(crawl_failed), len(results["saved"]))
        logger.info("=" * 70)

    def _crawl_sources(self, sources) -> tuple[list[dict], list[str]]:
        success = []
        failed = []
        for index, source in enumerate(sources, 1):
            logger.info("[%s/%s] Crawling %s", index, len(sources), source.url)
            try:
                if source.source_type == "pdf":
                    pdf_doc = extract_pdf_markdown(source.url)
                    success.append({
                        "url": source.url,
                        "title": source.title or pdf_doc["title"],
                        "markdown": pdf_doc["markdown"],
                        "source_type": "pdf",
                        "pdf_audit": pdf_doc["audit"],
                    })
                    audit = pdf_doc["audit"]
                    logger.info(
                        "PDF extracted: pages=%s raw_chars=%s tables=%s",
                        audit.get("page_count"),
                        audit.get("raw_md_len"),
                        audit.get("table_count"),
                    )
                    continue

                page = self.crawler.crawl(source.url)
                if page:
                    success.append(page)
                else:
                    failed.append(source.url)
            except Exception as exc:
                logger.error("Crawl failed for %s: %s", source.url, exc)
                failed.append(source.url)
        return success, failed

    def _build_document(self, page_data: dict, source) -> dict:
        category = getattr(source, "category", "user") or "user"
        source_profile = getattr(source, "source_profile", "main_site") or "main_site"
        source_type = getattr(source, "source_type", page_data.get("source_type", "web")) or "web"
        document_type = getattr(source, "document_type", "service") or "service"

        if source_type == "pdf":
            title = page_data.get("title") or getattr(source, "title", "") or page_data["url"]
            markdown_content = page_data.get("markdown", "")
            document_type = "policy_pdf"
            category = "pdf"  # Force output to the pdf directory
        else:
            cleaned = self.cleaner.clean(
                page_data.get("html", ""),
                page_data.get("title", ""),
                page_data["url"],
                category=category,
                source_profile=source_profile,
                document_type=document_type,
            )
            title = cleaned.title
            markdown_content = cleaned.markdown
            document_type = cleaned.document_type or document_type

        return {
            "url": page_data["url"],
            "title": title,
            "content": markdown_content,
            "category": category,
            "crawl_date": datetime.now().strftime("%Y-%m-%d"),
            "slug": self.storage.url_to_filename(page_data["url"]),
            "source_profile": source_profile,
            "source_type": source_type,
            "document_type": document_type,
        }

    def _save_metadata(self, metadata: Dict) -> None:
        metadata_file = self.root_dir / "data" / "metadata.json"
        metadata_file.parent.mkdir(parents=True, exist_ok=True)
        metadata_file.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
        logger.info("Metadata saved to %s", metadata_file)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Green SM deterministic Markdown crawler")
    parser.add_argument("--max-urls", type=int, default=0, help="Maximum URLs to crawl; 0 means all enabled URLs")
    parser.add_argument("--resume", type=int, default=0, help="Resume from URL index")
    parser.add_argument("--sources", type=str, default="main_site",
                        help="Comma-separated source profiles, e.g. main_site,platform,platform_pdf")
    parser.add_argument("--categories", type=str, default="",
                        help="Comma-separated categories; empty means all categories in selected sources")
    args = parser.parse_args()

    source_profiles = [item.strip() for item in args.sources.split(",") if item.strip()]
    categories = [item.strip() for item in args.categories.split(",") if item.strip()] or None
    GreenSMCrawler(
        max_urls=args.max_urls,
        source_profiles=source_profiles,
        categories=categories,
    ).run(resume_from=args.resume)
