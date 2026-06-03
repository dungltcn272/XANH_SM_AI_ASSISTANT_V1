import os
import sys
import uuid
from typing import List

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from langchain_core.documents import Document

from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import DocumentChunk
from app.ingestion.chunking import HeadingAwareSplitter
from app.ingestion.embedding import get_embedding_model
from app.vectordb.qdrant_client import vectordb
from app.core.logger import log_info, log_warn, log_error

COLLECTION_NAME = "greensm_knowledge"

def setup_qdrant(client: QdrantClient, vector_size: int = 1536):
    """Đảm bảo Collection Qdrant đã tồn tại với Named Vectors cho Hybrid Search"""
    try:
        client.get_collection(collection_name=COLLECTION_NAME)
        log_info("INGESTION", f"Collection '{COLLECTION_NAME}' already exists. Recreating for Hybrid Search...")
        client.delete_collection(collection_name=COLLECTION_NAME)
    except Exception:
        pass
        
    log_info("INGESTION", f"Creating collection '{COLLECTION_NAME}' for Hybrid Search...")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            "dense": qdrant_models.VectorParams(
                size=vector_size,
                distance=qdrant_models.Distance.COSINE
            )
        },
        sparse_vectors_config={
            "sparse": qdrant_models.SparseVectorParams(
                index=qdrant_models.SparseIndexParams(
                    on_disk=False
                )
            )
        }
    )
    
    # Tạo Payload Index để filter scroll/search theo metadata.url và metadata.chunk_index
    # Bắt buộc phải có index mới có thể dùng Filter trong scroll()
    log_info("INGESTION", "Creating payload indexes for 'metadata.url' and 'metadata.chunk_index'...")
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="metadata.url",
            field_schema=qdrant_models.PayloadSchemaType.KEYWORD
        )
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="metadata.chunk_index",
            field_schema=qdrant_models.PayloadSchemaType.INTEGER
        )
        log_info("INGESTION", "Payload indexes created successfully.")
    except Exception as e:
        log_warn("INGESTION", f"Could not create payload indexes: {e}")

def ingest_data(data_dir: str):
    db = SessionLocal()
    qdrant = vectordb.qdrant
    embedder = get_embedding_model()
    sparse_model = vectordb.sparse_embedder
    
    setup_qdrant(qdrant)
    
    splitter = HeadingAwareSplitter(chunk_size=400, chunk_overlap=50)
    log_info("INGESTION", "Bắt đầu duyệt và chunk file...")
    chunks: List[Document] = splitter.split_directory(data_dir)
    
    if not chunks:
        log_warn("INGESTION", "Không có chunks nào được tạo ra.")
        return

    log_info("INGESTION", f"Đã tạo tổng cộng {len(chunks)} chunks. Bắt đầu embedding (Dense + Sparse)...")
    
    source_map = {}
    for chunk in chunks:
        url = chunk.metadata.get("url", chunk.metadata.get("source", "unknown"))
        if url not in source_map:
            source_map[url] = []
        source_map[url].append(chunk)

    for url, file_chunks in source_map.items():
        log_info("INGESTION", f"Đang nạp dữ liệu cho {url} ({len(file_chunks)} chunks)...")
        
        category = file_chunks[0].metadata.get("category", file_chunks[0].metadata.get("role", "unknown"))
        filename = file_chunks[0].metadata.get("source", "")
        
        # Xóa các chunk cũ trong DB nếu có
        db.query(DocumentChunk).filter(DocumentChunk.source == url).delete()
        db.commit()
        
        texts = [c.page_content for c in file_chunks]
        
        # Sinh Dense Vector (OpenAI)
        try:
            dense_embeddings = embedder.embed_documents(texts)
        except Exception as e:
            log_error("INGESTION", f"Failed to dense embed chunks for {url}: {e}")
            continue
            
        # Sinh Sparse Vector (FastEmbed / Splade)
        try:
            sparse_embeddings = list(sparse_model.embed(texts))
        except Exception as e:
            log_error("INGESTION", f"Failed to sparse embed chunks for {url}: {e}")
            continue
            
        points = []
        for i, (chunk, dense_vec, sparse_vec) in enumerate(zip(file_chunks, dense_embeddings, sparse_embeddings)):
            vector_id = str(uuid.uuid4())
            
            payload = {
                "page_content": chunk.page_content,
                "metadata": chunk.metadata
            }
            payload["metadata"]["chunk_index"] = i
            payload["metadata"]["url"] = url
            
            points.append(qdrant_models.PointStruct(
                id=vector_id,
                vector={
                    "dense": dense_vec,
                    "sparse": qdrant_models.SparseVector(
                        indices=sparse_vec.indices.tolist(),
                        values=sparse_vec.values.tolist()
                    )
                },
                payload=payload
            ))
            
            doc_chunk = DocumentChunk(
                source=url,
                section=chunk.metadata.get("section", ""),
                content=chunk.page_content
            )
            db.add(doc_chunk)
            
        qdrant.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        db.commit()
        log_info("INGESTION", f"Đã nạp thành công {url}.")

    db.close()
    log_info("INGESTION", "Quá trình Ingestion hoàn tất!")

if __name__ == "__main__":
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
    ingest_data(DATA_DIR)
