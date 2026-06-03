from typing import List, Dict, Any
from langchain_core.documents import Document
from app.vectordb.qdrant_client import vectordb
from app.retrieval.multi_query import XanhSMQueryExpansion
from app.core.config import safe_print

class XanhSMHybridSearch:
    """
    Hybrid Search pipeline tối ưu (Phase 4):
    Sử dụng trực tiếp Qdrant Hybrid Search (Dense + Sparse/BM25) tích hợp sẵn RRF Fusion.
    """
    
    def __init__(self):
        self.db = vectordb
        self.expander = XanhSMQueryExpansion()

    def expand_context(self, base_docs: List[Document]) -> List[Document]:
        """
        Chiến thuật 'Adjacent Context Expansion' (Sliding Window Context).
        Với mỗi document được tìm thấy (chunk N), lấy thêm chunk N-1 và N+1 
        để bảo đảm ngữ cảnh đầy đủ mà không làm phình to prompt như Parent-Child.
        
        LƯU Ý: Payload Qdrant lưu theo cấu trúc {"page_content":..., "metadata":{...}}
        nên filter phải dùng dot notation: "metadata.url" và "metadata.chunk_index".
        """
        from qdrant_client.http import models as qdrant_models
        from app.vectordb.qdrant_client import COLLECTION_NAME
        
        expanded_docs = []
        for doc in base_docs:
            chunk_index = doc.metadata.get("chunk_index")
            url = doc.metadata.get("url")
            
            if chunk_index is None or url is None:
                # Không có đủ metadata để expand → giữ nguyên
                expanded_docs.append(doc)
                continue
                
            # Tạo filter để tìm các chunk lân cận cùng url
            target_indices = [chunk_index - 1, chunk_index, chunk_index + 1]
            target_indices = [i for i in target_indices if i >= 0]
            
            # Sử dụng dot notation vì url và chunk_index nằm BÊN TRONG "metadata"
            q_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="metadata.url",
                        match=qdrant_models.MatchValue(value=url)
                    ),
                    qdrant_models.FieldCondition(
                        key="metadata.chunk_index",
                        match=qdrant_models.MatchAny(any=target_indices)
                    )
                ]
            )
            
            # Lấy các chunk lân cận
            try:
                safe_print(f"[DEBUG] Calling qdrant.scroll for url={url}, chunk={chunk_index}...")
                results = self.db.qdrant.scroll(
                    collection_name=COLLECTION_NAME,
                    scroll_filter=q_filter,
                    limit=3,
                    with_payload=True,
                    with_vectors=False
                )[0]
                safe_print(f"[DEBUG] Scroll returned {len(results)} records successfully.")
                
                if not results:
                    # scroll không tìm thấy gì (có thể index chưa được tạo) → fallback
                    safe_print(f"[WARN] expand_context: No adjacent chunks found for {url}[{chunk_index}]. Using original doc.")
                    expanded_docs.append(doc)
                    continue
                
                # Sắp xếp theo chunk_index
                results.sort(key=lambda x: x.payload.get("metadata", {}).get("chunk_index", 0))
                
                merged_content = "\n\n... ".join([r.payload.get("page_content", "") for r in results if r.payload.get("page_content")])
                
                if not merged_content:
                    expanded_docs.append(doc)
                    continue
                
                # Tạo Document mới với nội dung đã ghép nối
                merged_doc = Document(
                    page_content=merged_content,
                    metadata=doc.metadata
                )
                expanded_docs.append(merged_doc)
                safe_print(f"[INFO] Expanded context for {url} (Chunks: {[r.payload.get('metadata', {}).get('chunk_index') for r in results]})")
            except Exception as e:
                safe_print(f"[ERROR] Failed to expand context for {url}: {e}")
                expanded_docs.append(doc)
                
        return expanded_docs

    def search(self, query: str, role: str = None, limit: int = 25, expanded_queries: List[str] = None) -> List[Document]:
        """
        Chạy Multi-Query Expansion, sau đó gọi trực tiếp Hybrid Search của Qdrant 
        cho từng query và gom kết quả. Tiếp theo mở rộng ngữ cảnh (Adjacent Context).
        """
        if expanded_queries is None:
            expanded_queries = self.expander.get_queries(query)
        safe_print(f"[INFO] Expanded queries for search: {expanded_queries}")
        
        # Dùng set để deduplicate theo chunk_id
        all_docs_map = {}
        
        for q in expanded_queries:
            # db.hybrid_search gọi thẳng API Qdrant (Prefetch Dense + Sparse -> RRF)
            fused_docs = self.db.hybrid_search(query=q, limit=limit, role=role)
            for doc in fused_docs:
                doc_id = doc.metadata.get("chunk_id", doc.page_content[:50])
                if doc_id not in all_docs_map:
                    all_docs_map[doc_id] = doc
                    
        unique_docs = list(all_docs_map.values())
        
        safe_print(f"[SUCCESS] Native Qdrant Hybrid Search returned {len(unique_docs)} unique documents.")
        
        return unique_docs[:limit]
