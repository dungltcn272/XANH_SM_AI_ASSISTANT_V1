import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.database import SessionLocal
from app.db.models import CrawlSource


PLATFORM_HOST = "platform.greensm.com"
PLATFORM_STATIC_HINT = "/public/document/"


@dataclass
class CrawlSourceSeed:
    url: str
    title: str = ""
    source_profile: str = "main_site"
    source_type: str = "web"
    category: str = "user"
    document_type: str = "service"
    output_dir: str = "data/user"
    crawl_strategy: str = "default"
    enabled: bool = True
    priority: int = 100
    notes: str = ""


def clean_seed_url(value: str) -> tuple[str, bool]:
    raw = value.strip()
    is_pdf = "(pdf)" in raw.lower() or raw.lower().endswith(".pdf")
    cleaned = raw.replace("(pdf)", "").replace("(PDF)", "").strip()
    cleaned = cleaned.split()[0].strip() if " " in cleaned else cleaned
    return cleaned, is_pdf


def infer_document_type(url: str, category: str, source_type: str) -> str:
    lower = url.lower()
    path = re.sub(r"/+$", "", lower.split("?", 1)[0])
    if source_type == "pdf":
        return "policy_pdf"
    if "/news/all/page/" in lower or path.endswith("/news"):
        return "news_list"
    if "/news/" in lower:
        return "news"
    if "terms-policies" in lower or "privacy" in lower or "policy" in lower:
        return "policy"
    if category == "helps":
        return "faq"
    if category in {"driver", "merchant"}:
        return category
    if "price" in lower or "pricing" in lower or "gia" in lower:
        return "pricing"
    if PLATFORM_HOST in lower:
        if path in {f"https://{PLATFORM_HOST.lower()}/vn-vi", f"http://{PLATFORM_HOST.lower()}/vn-vi"}:
            return "platform_overview"
        vehicle_terms = [
            "order_type", "order-type", "model", "car", "bike", "vf", "limo", "herio",
            "minio", "ec-van", "ec_van", "evo", "feliz", "feliz2", "viper",
        ]
        return "vehicle" if any(k in lower for k in vehicle_terms) else "platform_page"
    return "service"


def infer_pdf_category(url: str) -> str:
    lower = url.lower()
    if "terms-policies" in lower or "privacy" in lower or "policy" in lower:
        return "term-policies"
    if PLATFORM_STATIC_HINT in lower or "car-trading.gsm-api.net" in lower or PLATFORM_HOST in lower:
        return "vehicle"
    return "pdf"


def infer_seed(url: str, category: str, title: str = "", priority: int = 100) -> CrawlSourceSeed:
    cleaned_url, marked_pdf = clean_seed_url(url)
    lower = cleaned_url.lower()
    source_type = "pdf" if marked_pdf or lower.endswith(".pdf") else "web"

    if source_type == "pdf":
        source_profile = "platform_pdf"
        if category in {"pdf", "platform-pdf"}:
            category = infer_pdf_category(cleaned_url)
    elif PLATFORM_HOST in lower:
        source_profile = "platform"
        if category == "platform":
            category = "vehicle"
    else:
        source_profile = "main_site"

    document_type = infer_document_type(cleaned_url, category, source_type)
    output_dir = f"data/{category}"
    crawl_strategy = "pdf_extract" if source_type == "pdf" else source_profile

    return CrawlSourceSeed(
        url=cleaned_url,
        title=title,
        source_profile=source_profile,
        source_type=source_type,
        category=category,
        document_type=document_type,
        output_dir=output_dir,
        crawl_strategy=crawl_strategy,
        priority=priority,
    )


def load_seed_file(path: Path | None = None) -> list[CrawlSourceSeed]:
    seed_path = path or Path(__file__).parent / "urls.json"
    data = json.loads(seed_path.read_text(encoding="utf-8"))
    seeds: list[CrawlSourceSeed] = []
    for category, urls in data.items():
        for idx, url in enumerate(urls):
            seeds.append(infer_seed(url, category=category, priority=100 + idx))
    return seeds


def bootstrap_from_urls_json(db=None, only_if_empty: bool = True) -> dict:
    owns_session = db is None
    session = db or SessionLocal()
    try:
        existing_count = session.query(CrawlSource).count()
        if only_if_empty and existing_count > 0:
            return {
                "success": True,
                "skipped": True,
                "reason": "crawl_sources already has data",
                "existing_count": existing_count,
                "inserted": 0,
            }

        inserted = 0
        skipped_duplicates = 0
        existing_urls = {
            row[0] for row in session.query(CrawlSource.url).all()
        }
        for seed in load_seed_file():
            if seed.url in existing_urls:
                skipped_duplicates += 1
                continue
            session.add(CrawlSource(**seed.__dict__))
            existing_urls.add(seed.url)
            inserted += 1

        session.commit()
        return {
            "success": True,
            "skipped": False,
            "existing_count": existing_count,
            "inserted": inserted,
            "skipped_duplicates": skipped_duplicates,
        }
    finally:
        if owns_session:
            session.close()


def sync_from_urls_json(db=None) -> dict:
    """Upsert curated urls.json into crawl_sources without deleting admin rows."""
    owns_session = db is None
    session = db or SessionLocal()
    try:
        seeds = load_seed_file()
        existing_by_url = {
            row.url: row for row in session.query(CrawlSource).all()
        }

        inserted = 0
        updated = 0
        unchanged = 0
        seen_urls = set()
        sync_fields = [
            "source_profile",
            "source_type",
            "category",
            "document_type",
            "output_dir",
            "crawl_strategy",
            "priority",
        ]

        for seed in seeds:
            seen_urls.add(seed.url)
            row = existing_by_url.get(seed.url)
            if not row:
                session.add(CrawlSource(**seed.__dict__))
                inserted += 1
                continue

            changed = False
            for field in sync_fields:
                seed_value = getattr(seed, field)
                if getattr(row, field) != seed_value:
                    setattr(row, field, seed_value)
                    changed = True
            if seed.title and not row.title:
                row.title = seed.title
                changed = True

            if changed:
                updated += 1
            else:
                unchanged += 1

        stale_count = len(set(existing_by_url.keys()) - seen_urls)
        session.commit()
        return {
            "success": True,
            "inserted": inserted,
            "updated": updated,
            "unchanged": unchanged,
            "stale_not_in_urls_json": stale_count,
            "total_urls_json": len(seeds),
        }
    finally:
        if owns_session:
            session.close()


def get_enabled_sources(
    source_profiles: Iterable[str] | None = None,
    categories: Iterable[str] | None = None,
    include_pdfs: bool = True,
    limit: int | None = None,
    auto_bootstrap: bool = True,
) -> list[CrawlSource]:
    session = SessionLocal()
    try:
        if auto_bootstrap and session.query(CrawlSource).count() == 0:
            bootstrap_from_urls_json(session, only_if_empty=True)

        query = session.query(CrawlSource).filter(CrawlSource.enabled == True)
        if source_profiles:
            query = query.filter(CrawlSource.source_profile.in_(list(source_profiles)))
        if categories:
            query = query.filter(CrawlSource.category.in_(list(categories)))
        if not include_pdfs:
            query = query.filter(CrawlSource.source_type != "pdf")
        query = query.order_by(CrawlSource.priority.asc(), CrawlSource.created_at.asc())
        if limit and limit > 0:
            query = query.limit(limit)
        rows = query.all()
        for row in rows:
            session.expunge(row)
        return rows
    finally:
        session.close()


def slugify_url(url: str) -> str:
    from urllib.parse import urlparse, parse_qs

    parsed = urlparse(url)
    path = parsed.path.strip("/")
    path = path.replace("vn-vi/", "").replace("VN-vi/", "")
    if not path:
        path = "home"
    if parsed.query:
        query_parts = []
        for key, values in sorted(parse_qs(parsed.query).items()):
            for value in values:
                query_parts.append(f"{key}_{value}")
        path = f"{path}_{'_'.join(query_parts)}"
    name = re.sub(r"[^\w]+", "_", path.replace("-", "_"))
    name = re.sub(r"_+", "_", name).strip("_")
    return name or "home"
