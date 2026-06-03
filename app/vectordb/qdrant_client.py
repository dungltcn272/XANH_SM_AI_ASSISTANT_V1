from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from langchain_core.documents import Document
from fastembed import SparseTextEmbedding
from app.core.config import settings
from app.ingestion.embedding import get_embedding_model

COLLECTION_NAME = "greensm_knowledge"

class VectorDBClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorDBClient, cls).__new__(cls)
            cls._instance.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY if settings.QDRANT_API_KEY else None
            )
            cls._instance.dense_model = get_embedding_model()
            cls._instance.sparse_model = SparseTextEmbedding(model_name="Qdrant/bm25")
        return cls._instance

    @property
    def qdrant(self) -> QdrantClient:
        return self.client
        
    @property
    def sparse_embedder(self):
        return self.sparse_model

    @property
    def dense_embedder(self):
        return self.dense_model

    def hybrid_search(self, query: str, limit: int = 25, role: str = None) -> list[Document]:
        """Thực hiện Hybrid Search bằng tính năng RRF tích hợp sẵn của Qdrant"""
        # Sinh Dense Vector
        dense_vector = self.dense_embedder.embed_query(query)
        
        # Sinh Sparse Vector
        sparse_gen = list(self.sparse_embedder.embed([query]))[0]
        sparse_vector = qdrant_models.SparseVector(
            indices=sparse_gen.indices.tolist(),
            values=sparse_gen.values.tolist()
        )
        
        # Bỏ filter theo role để tăng recall trên mọi tập dữ liệu
        query_filter = None

        # Sử dụng Qdrant Query API mới cho Hybrid Search tích hợp
        results = self.client.query_points(
            collection_name=COLLECTION_NAME,
            prefetch=[
                qdrant_models.Prefetch(
                    query=dense_vector,
                    using="dense",
                    limit=limit
                ),
                qdrant_models.Prefetch(
                    query=sparse_vector,
                    using="sparse",
                    limit=limit
                )
            ],
            query=qdrant_models.FusionQuery(fusion=qdrant_models.Fusion.RRF),
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        )
        
        docs = []
        for hit in results.points:
            payload = hit.payload or {}
            meta = payload.get("metadata", {}).copy()
            meta["score"] = hit.score if hit.score is not None else 0.0
            docs.append(Document(
                page_content=payload.get("page_content", ""),
                metadata=meta
            ))
            
        return docs

vectordb = VectorDBClient()
