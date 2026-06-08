import json
import re
from pathlib import Path


OVERVIEW_DIR = "overview"


def parse_frontmatter(content: str) -> tuple[dict, str]:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return {}, content
    meta = {}
    for line in match.group(1).splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip()] = value.strip().strip("\"'")
    return meta, content[match.end():]


def first_heading(body: str) -> str:
    match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    return match.group(1).strip() if match else ""


def first_paragraph(body: str) -> str:
    for block in re.split(r"\n\s*\n", body):
        text = block.strip()
        if text and not text.startswith("#") and not text.startswith("!") and "|" not in text:
            return re.sub(r"\s+", " ", text)[:280]
    return ""


def load_markdown_docs(data_root: Path) -> list[dict]:
    docs = []
    for path in sorted(data_root.rglob("*.md")):
        rel = path.relative_to(data_root)
        if rel.parts and rel.parts[0] in {"raw", "raw_converted", OVERVIEW_DIR, "manifests"}:
            continue
        content = path.read_text(encoding="utf-8", errors="replace")
        meta, body = parse_frontmatter(content)
        category = meta.get("category") or rel.parts[0]
        title = meta.get("title") or first_heading(body) or path.stem.replace("_", " ").title()
        docs.append({
            "path": str(path),
            "relative_path": str(rel).replace("\\", "/"),
            "url": meta.get("url", ""),
            "category": category,
            "document_type": meta.get("document_type") or meta.get("agent_category", "").lower() or infer_document_type(path, body, category),
            "title": title,
            "summary": meta.get("summary") or first_paragraph(body),
            "body": body,
        })
    return docs


def infer_document_type(path: Path, body: str, category: str) -> str:
    lower = f"{path.name} {body[:1000]}".lower()
    if category == "green-care" or any(k in lower for k in ["bảo hiểm", "bồi thường", "bồi hoàn"]):
        return "policy"
    if category == "helps" or "câu hỏi thường gặp" in lower:
        return "faq"
    if "giá" in lower or "phí" in lower or "cước" in lower:
        return "pricing"
    if "news" in lower or "/news/" in lower:
        return "news"
    if category in {"vehicle", "platform"}:
        return "vehicle"
    return "service"


def write_catalog(path: Path, title: str, rows: list[dict], description: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        f"url: file://{path.name}",
        "category: overview",
        "document_type: overview",
        f"title: {title}",
        "---",
        "",
        f"# {title}",
        "",
        description,
        "",
        "| Danh mục | Tên tài liệu | Loại | Tóm tắt | Nguồn |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        summary = (row.get("summary") or "").replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| {row.get('category', '')} | {row.get('title', '')} | {row.get('document_type', '')} | "
            f"{summary[:220]} | {row.get('url') or row.get('relative_path', '')} |"
        )
    path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")
    return path


def generate_service_catalog(data_root: Path, docs: list[dict]) -> Path:
    service_categories = {"user", "merchant", "driver", "green-care", "helps", "term-policies", "vehicle", "platform"}
    rows = [d for d in docs if d["category"] in service_categories]
    return write_catalog(
        data_root / OVERVIEW_DIR / "service_catalog.md",
        "Tổng quan danh mục dịch vụ và tài liệu Green SM",
        rows,
        "Tài liệu tổng hợp deterministic từ các file Markdown đã crawl để trả lời các câu hỏi tổng quát như Green SM gồm những danh mục nào.",
    )


def generate_pricing_catalog(data_root: Path, docs: list[dict]) -> Path:
    rows = [d for d in docs if d["document_type"] == "pricing" or re.search(r"(giá|phí|cước|bảng giá)", d["body"], re.IGNORECASE)]
    return write_catalog(data_root / OVERVIEW_DIR / "pricing_catalog.md", "Tổng quan giá cước và phụ phí Green SM", rows, "Các tài liệu có nội dung liên quan giá, phí, phụ phí hoặc bảng giá.")


def generate_platform_vehicle_catalog(data_root: Path, docs: list[dict]) -> Path:
    rows = [
        d for d in docs
        if d["category"] in {"vehicle", "platform"}
        and d["document_type"] in {"platform_overview", "vehicle", "pricing", "policy_pdf", "policy_page", "policy"}
    ]
    return write_catalog(data_root / OVERVIEW_DIR / "platform_vehicle_catalog.md", "Tổng quan Green SM Platform", rows, "Tổng hợp trang xe, chính sách và PDF liên quan Green SM Platform.")


def generate_policy_catalog(data_root: Path, docs: list[dict]) -> Path:
    rows = [d for d in docs if "policy" in d["document_type"] or d["category"] in {"green-care", "term-policies"}]
    return write_catalog(data_root / OVERVIEW_DIR / "policy_catalog.md", "Tổng quan chính sách Green SM", rows, "Tổng hợp các tài liệu chính sách, điều khoản, bảo hiểm và quy định.")


def generate_news_catalog(data_root: Path, docs: list[dict]) -> Path:
    rows = [d for d in docs if d["document_type"] == "news" or "/news/" in d.get("url", "")]
    return write_catalog(data_root / OVERVIEW_DIR / "news_catalog.md", "Tổng quan tin tức Green SM", rows, "Tổng hợp các bài tin tức/detail news đã có trong registry và dữ liệu đã crawl.")


def generate_overview_catalogs(data_root: str | Path = "data") -> list[Path]:
    root = Path(data_root)
    docs = load_markdown_docs(root)
    generated = [
        generate_service_catalog(root, docs),
        generate_pricing_catalog(root, docs),
        generate_platform_vehicle_catalog(root, docs),
        generate_policy_catalog(root, docs),
        generate_news_catalog(root, docs),
    ]
    summary_path = root / OVERVIEW_DIR / "overview_manifest.json"
    summary_path.write_text(json.dumps({
        "documents_seen": len(docs),
        "generated": [str(p) for p in generated],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return generated


if __name__ == "__main__":
    for generated_path in generate_overview_catalogs():
        print(generated_path)
