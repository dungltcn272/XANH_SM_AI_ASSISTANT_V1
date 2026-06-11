import os
import sys
import uuid
import json
from typing import List

# Set TIKTOKEN_CACHE_DIR for offline mode
if "TIKTOKEN_CACHE_DIR" not in os.environ:
    os.environ["TIKTOKEN_CACHE_DIR"] = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
        "tiktoken_cache"
    )

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
from app.core.logger import log_info as original_log_info, log_warn as original_log_warn, log_error as original_log_error

def log_info(phase: str, msg: str):
    print(msg, flush=True)
    original_log_info(phase, msg)

def log_warn(phase: str, msg: str):
    print(f"WARNING: {msg}", flush=True)
    original_log_warn(phase, msg)

def log_error(phase: str, msg: str):
    print(f"ERROR: {msg}", flush=True)
    original_log_error(phase, msg)

COLLECTION_NAME = "greensm_knowledge"

def setup_qdrant(client: QdrantClient, vector_size: int = 1536, recreate: bool = True):
    """Đảm bảo Collection Qdrant đã tồn tại với Named Vectors cho Hybrid Search."""
    try:
        client.get_collection(collection_name=COLLECTION_NAME)
        if recreate:
            log_info("INGESTION", f"Collection '{COLLECTION_NAME}' already exists. Recreating for Hybrid Search...")
            client.delete_collection(collection_name=COLLECTION_NAME)
        else:
            log_info("INGESTION", f"Collection '{COLLECTION_NAME}' already exists. Keeping it.")
            return
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
    log_info("INGESTION", "Creating payload indexes for retrieval metadata...")
    try:
        payload_indexes = {
            "metadata.url": qdrant_models.PayloadSchemaType.KEYWORD,
            "metadata.chunk_id": qdrant_models.PayloadSchemaType.KEYWORD,
            "metadata.parent_chunk_id": qdrant_models.PayloadSchemaType.KEYWORD,
            "metadata.chunk_index": qdrant_models.PayloadSchemaType.INTEGER,
            "metadata.chunk_type": qdrant_models.PayloadSchemaType.KEYWORD,
            "metadata.category": qdrant_models.PayloadSchemaType.KEYWORD,
            "metadata.document_type": qdrant_models.PayloadSchemaType.KEYWORD,
            "metadata.source_type": qdrant_models.PayloadSchemaType.KEYWORD,
            "metadata.table_id": qdrant_models.PayloadSchemaType.KEYWORD,
            "metadata.derived_from": qdrant_models.PayloadSchemaType.KEYWORD,
            "metadata.row_start": qdrant_models.PayloadSchemaType.INTEGER,
            "metadata.row_end": qdrant_models.PayloadSchemaType.INTEGER,
        }
        for field_name, schema in payload_indexes.items():
            try:
                client.create_payload_index(
                    collection_name=COLLECTION_NAME,
                    field_name=field_name,
                    field_schema=schema,
                )
            except Exception:
                pass
        log_info("INGESTION", "Payload indexes created successfully.")
    except Exception as e:
        log_warn("INGESTION", f"Could not create payload indexes: {e}")

def delete_qdrant_vectors_for_url(client: QdrantClient, url: str):
    try:
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="metadata.url",
                        match=qdrant_models.MatchValue(value=url)
                    )
                ]
            )
        )
    except Exception as e:
        log_warn("INGESTION", f"Could not delete existing vectors for URL '{url}': {e}")


def ingest_data(data_dir: str, category_filter: str = None, reset_collection: bool = False) -> dict:
    db = SessionLocal()
    qdrant = vectordb.qdrant
    embedder = get_embedding_model()
    sparse_model = vectordb.sparse_embedder

    setup_qdrant(qdrant, recreate=reset_collection)

    chunk_size = int(os.getenv("CHUNK_SIZE", 400))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", 50))
    splitter = HeadingAwareSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    log_info("INGESTION", "Bắt đầu duyệt và chunk file...")
    chunks: List[Document] = splitter.split_directory(data_dir, category_filter=category_filter)
    
    if not chunks:
        log_warn("INGESTION", "Không có chunks nào được tạo ra.")
        db.close()
        return {
            "files_processed": 0,
            "chunks_created": 0,
            "chunks_inserted": 0,
            "qdrant_points_upserted": 0,
            "failed_files": [],
        }

    log_info("INGESTION", f"Đã tạo tổng cộng {len(chunks)} chunks. Bắt đầu embedding (Dense + Sparse)...")
    
    source_map = {}
    for chunk in chunks:
        url = chunk.metadata.get("url", chunk.metadata.get("source", "unknown"))
        if url not in source_map:
            source_map[url] = []
        source_map[url].append(chunk)

    summary = {
        "files_processed": 0,
        "chunks_created": len(chunks),
        "chunks_inserted": 0,
        "qdrant_points_upserted": 0,
        "failed_files": [],
    }

    for url, file_chunks in source_map.items():
        log_info("INGESTION", f"Đang nạp dữ liệu cho {url} ({len(file_chunks)} chunks)...")
        
        category = file_chunks[0].metadata.get("category", file_chunks[0].metadata.get("role", "unknown"))
        filename = file_chunks[0].metadata.get("source", "")
        
        # Xóa các chunk cũ trong DB nếu có
        db.query(DocumentChunk).filter(DocumentChunk.source == url).delete()
        db.commit()
        delete_qdrant_vectors_for_url(qdrant, url)
        
        texts = [c.page_content for c in file_chunks]
        
        # Sinh Dense Vector (OpenAI)
        try:
            dense_embeddings = embedder.embed_documents(texts)
        except Exception as e:
            log_error("INGESTION", f"Failed to dense embed chunks for {url}: {e}")
            summary["failed_files"].append({"url": url, "source": filename, "error": str(e)})
            continue
            
        # Sinh Sparse Vector (FastEmbed / Splade)
        try:
            sparse_embeddings = list(sparse_model.embed(texts))
        except Exception as e:
            log_error("INGESTION", f"Failed to sparse embed chunks for {url}: {e}")
            summary["failed_files"].append({"url": url, "source": filename, "error": str(e)})
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
        summary["files_processed"] += 1
        summary["chunks_inserted"] += len(file_chunks)
        summary["qdrant_points_upserted"] += len(points)
        log_info("INGESTION", f"Đã nạp thành công {url}.")

    db.close()
    log_info("INGESTION", "Quá trình Ingestion hoàn tất!")
    return summary

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Green SM Data Ingestion Pipeline")
    parser.add_argument("--category", type=str, default=None, help="Only ingest files in this category folder")
    parser.add_argument("--reset-collection", action="store_true", help="Recreate Qdrant collection before ingest")
    args = parser.parse_args()
    
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data")
    result = ingest_data(DATA_DIR, category_filter=args.category, reset_collection=args.reset_collection)
    print(json.dumps(result, ensure_ascii=False, indent=2))
