import hashlib
import json
from datetime import datetime
from pathlib import Path


class CrawlManifest:
    def __init__(self, run_label: str, sources: list[str] | None = None):
        self.started_at = datetime.now().isoformat()
        self.run_label = run_label
        self.sources = sources or []
        self.documents: list[dict] = []
        self.errors: list[dict] = []

    def add_document(
        self,
        url: str,
        output_path: str,
        source_profile: str = "",
        source_type: str = "web",
        category: str = "",
        document_type: str = "",
        content: str = "",
        warnings: list[str] | None = None,
        status: str = "saved",
    ):
        self.documents.append({
            "url": url,
            "source_profile": source_profile,
            "source_type": source_type,
            "category": category,
            "document_type": document_type,
            "output_path": output_path,
            "content_hash": hashlib.sha256((content or "").encode("utf-8")).hexdigest() if content else "",
            "warnings": warnings or [],
            "status": status,
        })

    def add_error(self, url: str, error: str, source_profile: str = "", category: str = ""):
        self.errors.append({
            "url": url,
            "source_profile": source_profile,
            "category": category,
            "error": error,
        })

    def save(self, root_dir: str | Path = "data") -> Path:
        finished_at = datetime.now().isoformat()
        manifest = {
            "crawl_run_id": f"{self.run_label}_{finished_at.replace(':', '').replace('-', '').replace('.', '')}",
            "run_label": self.run_label,
            "started_at": self.started_at,
            "finished_at": finished_at,
            "sources": self.sources,
            "documents": self.documents,
            "errors": self.errors,
            "summary": {
                "documents_saved": len(self.documents),
                "errors": len(self.errors),
            },
        }
        manifest_dir = Path(root_dir) / "manifests"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        path = manifest_dir / f"{manifest['crawl_run_id']}.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return path
