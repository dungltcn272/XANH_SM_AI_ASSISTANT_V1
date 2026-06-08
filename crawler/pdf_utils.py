import hashlib
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests


def download_pdf(url: str, timeout: int = 45) -> tuple[bytes, str]:
    response = requests.get(url, timeout=timeout, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    content = response.content
    if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
        raise ValueError(f"URL did not return a PDF content-type: {content_type}")
    if len(content) < 1024:
        raise ValueError(f"PDF response too small: {len(content)} bytes")
    return content, content_type


def extract_pdf_markdown(url: str) -> dict:
    content, content_type = download_pdf(url)
    suffix = Path(urlparse(url).path).suffix or ".pdf"
    raw_md = ""
    page_count = 0

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        try:
            import pymupdf4llm

            raw_md = pymupdf4llm.to_markdown(str(tmp_path))
        except Exception:
            import fitz

            parts = []
            with fitz.open(str(tmp_path)) as doc:
                page_count = doc.page_count
                for idx, page in enumerate(doc, 1):
                    text = page.get_text("text")
                    if text.strip():
                        parts.append(f"## Trang {idx}\n\n{text.strip()}")
            raw_md = "\n\n".join(parts)

        if page_count == 0:
            import fitz

            with fitz.open(str(tmp_path)) as doc:
                page_count = doc.page_count

        parsed = urlparse(url)
        title = Path(parsed.path).name.replace(".pdf", "").replace("_", " ").strip() or "Policy Document"
        markdown = raw_md.strip()
        if not markdown.startswith("#"):
            markdown = f"# {title}\n\n{markdown}"

        return {
            "url": url,
            "title": title,
            "markdown": markdown,
            "audit": {
                "bytes": len(content),
                "content_type": content_type,
                "page_count": page_count,
                "raw_md_len": len(raw_md),
                "clean_md_len": len(markdown),
                "table_count": markdown.count("\n|"),
                "sha256": hashlib.sha256(content).hexdigest(),
            },
        }
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
