from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk, KnowledgeSource
from app.domains.rag.chunking.chunker import Chunk, chunk_markdown
from app.vectorstore.collections import KNOWLEDGE_COLLECTION
from app.vectorstore.vector_repository import upsert_texts


def _sha256(text: str | bytes) -> str:
    payload = text if isinstance(text, bytes) else text.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _html_to_markdown(html: str, *, url: str = "", title: str = "") -> str:
    try:
        from crawler.markdown_converter import MarkdownConverter

        return MarkdownConverter().html_to_markdown(html, title=title, url=url)
    except Exception:
        import markdownify

        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        return markdownify.markdownify(str(soup), heading_style="ATX").strip()


def load_url(url: str) -> dict:
    response = requests.get(url, timeout=45, headers={"User-Agent": "xanhsm-rag-ingestion/1.0"})
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "pdf" in content_type.lower() or url.lower().endswith(".pdf"):
        return load_pdf_bytes(response.content, uri=url)
    response.encoding = response.encoding or "utf-8"
    html = response.text
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.find("title").get_text(" ", strip=True) if soup.find("title") else url).strip()
    return {"title": title, "markdown": _html_to_markdown(html, url=url, title=title), "source_type": "web", "uri": url}


def load_pdf_bytes(content: bytes, *, uri: str) -> dict:
    suffix = Path(urlparse(uri).path).suffix or ".pdf"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(content)
        temp_path = Path(temp.name)
    try:
        try:
            import pymupdf4llm

            markdown = pymupdf4llm.to_markdown(str(temp_path))
        except Exception:
            import fitz

            parts = []
            with fitz.open(str(temp_path)) as doc:
                for index, page in enumerate(doc, 1):
                    text = page.get_text("text").strip()
                    if text:
                        parts.append(f"## Trang {index}\n\n{text}")
            markdown = "\n\n".join(parts)
    finally:
        temp_path.unlink(missing_ok=True)
    title = Path(urlparse(uri).path).name.replace(".pdf", "").replace("_", " ") or "PDF Document"
    if not markdown.lstrip().startswith("#"):
        markdown = f"# {title}\n\n{markdown}"
    return {"title": title, "markdown": markdown, "source_type": "pdf", "uri": uri}


def load_markdown_file(path: str | Path) -> dict:
    file_path = Path(path)
    markdown = file_path.read_text(encoding="utf-8")
    title = file_path.stem.replace("_", " ").replace("-", " ").title()
    return {"title": title, "markdown": markdown, "source_type": "file", "uri": str(file_path)}


def _get_or_create_source(db: Session, *, uri: str, title: str, source_type: str, category: str, access_scope: str) -> KnowledgeSource:
    row = db.query(KnowledgeSource).filter(KnowledgeSource.uri == uri).first()
    if row:
        row.name = title
        row.source_type = source_type
        row.category = category
        row.access_scope = access_scope
        row.last_status = "loaded"
        db.commit()
        return row
    row = KnowledgeSource(name=title, source_type=source_type, uri=uri, category=category, access_scope=access_scope, crawl_strategy="modular_ingestion", last_status="loaded")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _save_document(db: Session, *, source: KnowledgeSource, title: str, markdown: str, document_type: str, metadata: dict) -> Document:
    content_hash = _sha256(markdown)
    row = db.query(Document).filter(Document.content_hash == content_hash).first()
    if row:
        return row
    row = Document(
        source_id=source.id,
        title=title,
        document_type=document_type,
        content_hash=content_hash,
        metadata_json=json.dumps(metadata, ensure_ascii=False, default=str),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _save_chunks(db: Session, *, document: Document, chunks: list[Chunk]) -> list[DocumentChunk]:
    db.query(DocumentChunk).filter(DocumentChunk.document_id == document.id).delete()
    rows = []
    for chunk in chunks:
        metadata = {
            **chunk.metadata,
            "chunk_id": chunk.chunk_id,
            "parent_chunk_id": chunk.parent_chunk_id,
            "chunk_type": chunk.chunk_type,
            "chunk_index": chunk.chunk_index,
            "section": chunk.section,
            "document_id": document.id,
        }
        row = DocumentChunk(
            id=chunk.chunk_id,
            document_id=document.id,
            chunk_index=chunk.chunk_index,
            section_title=chunk.section,
            content=chunk.content,
            token_count=max(1, len(chunk.content) // 4),
            metadata_json=json.dumps(metadata, ensure_ascii=False, default=str),
            vector_collection=KNOWLEDGE_COLLECTION,
            vector_id=chunk.chunk_id,
        )
        db.add(row)
        rows.append(row)
    db.commit()
    return rows


def ingest_markdown(
    db: Session,
    *,
    title: str,
    markdown: str,
    uri: str,
    source_type: str = "manual",
    category: str = "public",
    access_scope: str = "public",
    document_type: str = "policy",
    upsert_vectors: bool = True,
) -> dict:
    source = _get_or_create_source(db, uri=uri, title=title, source_type=source_type, category=category, access_scope=access_scope)
    document = _save_document(db, source=source, title=title, markdown=markdown, document_type=document_type, metadata={"uri": uri, "category": category})
    chunks = chunk_markdown(markdown, source_key=uri)
    rows = _save_chunks(db, document=document, chunks=chunks)
    vector_ids: list[str] = []
    if upsert_vectors:
        vector_ids = upsert_texts(
            [{"id": row.id, "text": row.content, "metadata": json.loads(row.metadata_json or "{}")} for row in rows],
            collection=KNOWLEDGE_COLLECTION,
        )
    return {"source_id": source.id, "document_id": document.id, "chunks": len(rows), "vectors": len(vector_ids)}


def ingest_uri(db: Session, uri: str, **kwargs) -> dict:
    loaded = load_url(uri) if uri.startswith(("http://", "https://")) else load_markdown_file(uri)
    title = kwargs.pop("title", None) or loaded["title"]
    return ingest_markdown(db, title=title, markdown=loaded["markdown"], uri=loaded["uri"], source_type=loaded["source_type"], **kwargs)
