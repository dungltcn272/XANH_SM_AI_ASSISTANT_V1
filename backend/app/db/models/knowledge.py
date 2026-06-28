from __future__ import annotations

from .common import *

class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id = Column(String, primary_key=True, default=lambda: generate_id("ksrc"))
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    uri = Column(Text, nullable=False)
    category = Column(String, nullable=False, index=True)
    access_scope = Column(String, nullable=False, index=True)
    crawl_strategy = Column(String, nullable=True)
    enabled = Column(Boolean, default=True)
    last_status = Column(String, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time)

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: generate_id("doc"))
    source_id = Column(String, ForeignKey("knowledge_sources.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    document_type = Column(String, nullable=False, index=True)
    language = Column(String, default="vi", nullable=False)
    content_hash = Column(String, unique=True, nullable=False, index=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
    updated_at = Column(DateTime(timezone=True), default=get_vn_time, onupdate=get_vn_time)

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=lambda: generate_id("chunk"))
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    section_title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    metadata_json = Column(Text, nullable=True)
    vector_collection = Column(String, nullable=True, index=True)
    vector_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)

    @property
    def source(self) -> str | None:
        return self.document_id

    @property
    def section(self) -> str | None:
        return self.section_title

class RetrievalEvent(Base):
    __tablename__ = "retrieval_events"

    id = Column(String, primary_key=True, default=lambda: generate_id("ret"))
    run_id = Column(String, ForeignKey("assistant_runs.id"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    retriever_name = Column(String, nullable=False)
    top_k = Column(Integer, nullable=False)
    results_json = Column(Text, nullable=True)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=get_vn_time)
