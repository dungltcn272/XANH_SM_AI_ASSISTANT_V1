from typing import List, Dict, Any
from sqlalchemy import case, or_
from langchain_core.documents import Document
from app.db.database import SessionLocal
from app.db.models import DocumentChunk
from app.vectordb.qdrant_client import vectordb
from app.rag.multi_query import XanhSMQueryExpansion
from app.core.config import settings as config
from app.core.logger import log_info, log_warn, log_error

class XanhSMHybridSearch:
    """
    Hybrid Search pipeline tối ưu (Phase 4):
    Sử dụng trực tiếp Qdrant Hybrid Search (Dense + Sparse/BM25) tích hợp sẵn RRF Fusion.
    """
    
    def __init__(self):
        self.db = vectordb
        self.expander = XanhSMQueryExpansion()

    def _is_overview_query(self, query: str) -> bool:
        q = (query or "").lower()
        return any(term in q for term in [
            "green sm gồm",
            "xanh sm gồm",
            "danh mục",
            "cung cấp những dịch vụ",
            "các dịch vụ",
            "tổng quan",
            "bao gồm những gì",
        ])

    def _keyword_search_document_chunks(self, queries: List[str], limit: int = 10) -> List[Document]:
        """
        Adds exact keyword recall from SQL document_chunks. Qdrant remains the
        primary retriever; this catches literal phrases, codes, hotline numbers,
        and text snippets that should be prioritized in content-like fields.
        """
        db = SessionLocal()
        docs_map = {}

        try:
            for q in queries:
                clean_q = (q or "").strip()
                if not clean_q:
                    continue

                pattern = f"%{clean_q}%"
                content_match = DocumentChunk.content.ilike(pattern)
                section_match = DocumentChunk.section.ilike(pattern)
                source_match = DocumentChunk.source.ilike(pattern)
                keyword_score = (
                    case((content_match, 100), else_=0)
                    + case((section_match, 40), else_=0)
                    + case((source_match, 30), else_=0)
                )

                rows = (
                    db.query(DocumentChunk, keyword_score.label("keyword_score"))
                    .filter(or_(content_match, section_match, source_match))
                    .order_by(keyword_score.desc(), DocumentChunk.created_at.desc())
                    .limit(limit)
                    .all()
                )

                for chunk, score in rows:
                    if chunk.id in docs_map:
                        continue

                    docs_map[chunk.id] = Document(
                        page_content=chunk.content,
                        metadata={
                            "chunk_id": chunk.id,
                            "source": chunk.source,
                            "url": chunk.source,
                            "section": chunk.section or "Introduction",
                            "score": float(score or 0) / 100,
                            "keyword_score": int(score or 0),
                            "retrieval_source": "sql_keyword",
                        }
                    )

            docs = list(docs_map.values())
            if docs:
                log_info("RETRIEVAL", f"SQL keyword search added {len(docs)} candidate documents.")
            return docs[:limit]
        except Exception as e:
            log_warn("RETRIEVAL", f"SQL keyword search skipped: {e}")
            return []
        finally:
            db.close()

    def _apply_domain_boosts(self, docs: List[Document], query: str) -> List[Document]:
        return sorted(docs, key=lambda d: d.metadata.get("score", 0.0), reverse=True)

    def expand_context(self, base_docs: List[Document]) -> List[Document]:
        """
        Chiến thuật Parent-Child Retrieval tùy biến động theo điểm số Rerank:
        1. Ngưỡng mở rộng: Rerank Score >= 0.7.
        2. Nếu chunk đạt điểm >= 0.7, tiến hành truy vấn Qdrant lấy toàn bộ các chunk lân cận
           có chung parent_chunk_id (giới hạn tối đa 10 chunks) để tái cấu trúc trọn vẹn mục lớn.
        3. Ghép các chunk con liên tiếp bằng '\n\n', loại bỏ tiêu đề lặp lại ở các chunk con thứ cấp (idx > 0).
        4. Nếu chunk có điểm < 0.7, giữ nguyên để tránh phình to prompt.
        5. Đảm bảo loại bỏ trùng lặp nếu chunk thô đã nằm trong một mục lớn đã được mở rộng.
        """
        from qdrant_client.http import models as qdrant_models
        from app.vectordb.qdrant_client import COLLECTION_NAME

        EXPANSION_THRESHOLD = config.CONTEXT_EXPANSION_THRESHOLD
        MAX_CHUNKS_PER_SECTION = config.MAX_CHUNKS_PER_SECTION

        # Phân loại tài liệu
        docs_to_expand = []
        docs_to_keep = []
        table_row_docs = []

        for doc in base_docs:
            meta = doc.metadata or {}
            chunk_type = meta.get("chunk_type")
            derived_from = meta.get("derived_from")
            parent_id = meta.get("parent_chunk_id")
            score = doc.metadata.get("rerank_score", 0.0)

            if chunk_type == "table_row_index" and derived_from:
                table_row_docs.append(doc)
                continue

            if parent_id and score >= EXPANSION_THRESHOLD:
                docs_to_expand.append(doc)
            else:
                docs_to_keep.append(doc)

        expanded_docs = []
        covered_chunk_ids = set()

        # Mở rộng các hit bảng dạng row-index về lại full HTML table gốc
        for doc in table_row_docs:
            meta = doc.metadata or {}
            derived_from = meta.get("derived_from")
            if not derived_from:
                docs_to_keep.append(doc)
                continue

            try:
                log_info("RETRIEVAL", f"Table row hit: scrolling full table for derived_from={derived_from}")
                q_filter = qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="metadata.chunk_id",
                            match=qdrant_models.MatchValue(value=derived_from)
                        )
                    ]
                )
                results = self.db.qdrant.scroll(
                    collection_name=COLLECTION_NAME,
                    scroll_filter=q_filter,
                    limit=1,
                    with_payload=True,
                    with_vectors=False
                )[0]
            except Exception as e:
                log_error("RETRIEVAL", f"Failed to expand table row chunk {derived_from}: {e}")
                docs_to_keep.append(doc)
                continue

            if not results:
                docs_to_keep.append(doc)
                continue

            payload = results[0].payload or {}
            payload_meta = payload.get("metadata", {})
            full_content = payload.get("page_content", "").strip()
            full_chunk_id = payload_meta.get("chunk_id", derived_from)
            if full_chunk_id:
                covered_chunk_ids.add(full_chunk_id)

            if not full_content:
                docs_to_keep.append(doc)
                continue

            expanded_meta = payload_meta.copy()
            expanded_meta["retrieval_source"] = "table_full_expansion"
            expanded_meta["expanded_from"] = meta.get("chunk_id")
            expanded_meta["expanded_from_chunk_type"] = "table_row_index"
            if doc.metadata.get("rerank_score") is not None:
                expanded_meta["rerank_score"] = doc.metadata.get("rerank_score")

            row_chunk_id = meta.get("chunk_id")
            if row_chunk_id:
                covered_chunk_ids.add(row_chunk_id)

            expanded_docs.append(Document(
                page_content=full_content,
                metadata=expanded_meta
            ))
            log_info("RETRIEVAL", f"Expanded table row hit to full table chunk {full_chunk_id}")

        # Nhóm docs_to_expand theo parent_chunk_id
        parent_groups = {}
        for doc in docs_to_expand:
            pid = doc.metadata.get("parent_chunk_id")
            if pid not in parent_groups:
                parent_groups[pid] = []
            parent_groups[pid].append(doc)

        # Xử lý các nhóm cần mở rộng Parent-Child
        for pid, group_docs in parent_groups.items():
            # Chọn base doc tốt nhất để lấy metadata
            best_doc = max(group_docs, key=lambda x: x.metadata.get("rerank_score", 0.0))
            section_name = best_doc.metadata.get("section", "")
            url = best_doc.metadata.get("url", "")

            try:
                log_info("RETRIEVAL", f"Parent-Child: Scrolling chunks for parent={pid} (section={section_name})")
                q_filter = qdrant_models.Filter(
                    must=[
                        qdrant_models.FieldCondition(
                            key="metadata.parent_chunk_id",
                            match=qdrant_models.MatchValue(value=pid)
                        )
                    ]
                )
                results = self.db.qdrant.scroll(
                    collection_name=COLLECTION_NAME,
                    scroll_filter=q_filter,
                    limit=MAX_CHUNKS_PER_SECTION,
                    with_payload=True,
                    with_vectors=False
                )[0]
                log_info("RETRIEVAL", f"Scroll returned {len(results)} chunks for parent={pid}.")
            except Exception as e:
                log_error("RETRIEVAL", f"Failed to scroll parent chunks for {pid}: {e}")
                # Fallback: dùng lại các tài liệu gốc trong nhóm này
                for d in group_docs:
                    c_id = d.metadata.get("chunk_id")
                    if c_id:
                        covered_chunk_ids.add(c_id)
                expanded_docs.extend(group_docs)
                continue

            if not results:
                # Fallback nếu rỗng
                for d in group_docs:
                    c_id = d.metadata.get("chunk_id")
                    if c_id:
                        covered_chunk_ids.add(c_id)
                expanded_docs.extend(group_docs)
                continue

            # Sắp xếp các chunk con theo thứ tự index tăng dần
            results.sort(key=lambda x: x.payload.get("metadata", {}).get("chunk_index", 0))

            block_contents = []
            for i, r in enumerate(results):
                content = r.payload.get("page_content", "").strip()
                c_id = r.payload.get("metadata", {}).get("chunk_id")
                if c_id:
                    covered_chunk_ids.add(c_id)

                if not content:
                    continue

                # Loại bỏ tiêu đề lặp lại ở các chunk thứ cấp (idx > 0)
                c_idx = r.payload.get("metadata", {}).get("chunk_index", 0)
                if c_idx > 0 and section_name and section_name != "Introduction":
                    prefix = f"### {section_name}"
                    if content.startswith(prefix):
                        content = content[len(prefix):].strip()

                block_contents.append(content)

            merged_content = "\n\n".join(block_contents)
            
            merged_doc = Document(
                page_content=merged_content,
                metadata=best_doc.metadata.copy()
            )
            expanded_docs.append(merged_doc)
            log_info("RETRIEVAL", f"Expanded parent section for {url} (parent={pid})")

        # Xử lý các tài liệu giữ nguyên (không mở rộng)
        for doc in docs_to_keep:
            c_id = doc.metadata.get("chunk_id")
            # Chỉ thêm nếu chunk này chưa được gộp trong bất kỳ khối parent-child nào ở trên
            if not c_id or c_id not in covered_chunk_ids:
                expanded_docs.append(doc)
                if c_id:
                    covered_chunk_ids.add(c_id)

        # Sắp xếp lại theo điểm số rerank giảm dần để bảo toàn độ liên quan chính xác
        expanded_docs.sort(key=lambda x: x.metadata.get("rerank_score", 0.0), reverse=True)

        return expanded_docs


    def search(self, query: str, limit: int = 25, expanded_queries: List[str] = None) -> List[Document]:
        """
        Chạy Multi-Query Expansion, sau đó gọi trực tiếp Hybrid Search của Qdrant 
        cho từng query và gom kết quả. Tiếp theo mở rộng ngữ cảnh (Adjacent Context).
        """
        if expanded_queries is None:
            expanded_queries = self.expander.get_queries(query)
        if query not in expanded_queries:
            expanded_queries = [query] + expanded_queries
        if self._is_overview_query(query):
            expanded_queries.extend([
                "Tổng quan danh mục dịch vụ và tài liệu Green SM",
                "service_catalog overview Green SM",
                "Green SM gồm những danh mục dịch vụ nào",
            ])
            expanded_queries = list(dict.fromkeys(expanded_queries))
        log_info("RETRIEVAL", f"Expanded queries for search: {expanded_queries}")
        
        # Dùng set để deduplicate theo chunk_id
        all_docs_map = {}
        
        for q in expanded_queries:
            # db.hybrid_search gọi thẳng API Qdrant (Prefetch Dense + Sparse -> RRF)
            fused_docs = self.db.hybrid_search(query=q, limit=limit)
            for doc in fused_docs:
                doc_id = doc.metadata.get("chunk_id", doc.page_content[:50])
                if doc_id not in all_docs_map:
                    all_docs_map[doc_id] = doc

        # keyword_docs = self._keyword_search_document_chunks(expanded_queries, limit=min(10, limit))
        # for doc in keyword_docs:
        #     doc_id = doc.metadata.get("chunk_id", doc.page_content[:50])
        #     if doc_id not in all_docs_map:
        #         all_docs_map[doc_id] = doc
                    
        unique_docs = self._apply_domain_boosts(list(all_docs_map.values()), " ".join(expanded_queries))
        
        log_info("RETRIEVAL", f"Native Qdrant Hybrid Search returned {len(unique_docs)} unique documents.")
        
        return unique_docs[:limit]
