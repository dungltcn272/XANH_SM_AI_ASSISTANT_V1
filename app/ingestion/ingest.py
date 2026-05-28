import os
import sys
# Make sure app directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.ingestion.splitter import HeadingAwareSplitter
from app.vectordb.chroma_client import XanhSMVectorDB
from app.config import config

def run_ingestion(progress_callback=None):
    msg_start = "Starting legal document ingestion pipeline for Xanh SM..."
    print(f"[INFO] {msg_start}")
    if progress_callback:
        progress_callback("START", msg_start)
    
    # 1. Initialize DB, Splitter, and Cache
    db = XanhSMVectorDB()
    splitter = HeadingAwareSplitter(chunk_size=700, chunk_overlap=150)
    
    try:
        from app.rag.cache import XanhSMRAGCache
        cache = XanhSMRAGCache()
        cache.clear()
    except Exception as e:
        print(f"[WARN] Failed to clear cache on ingestion: {e}")

    
    # 2. Split directory
    data_dir = config.DATA_DIR
    msg_read = f"Reading documents from: {data_dir}"
    print(f"[INFO] {msg_read}")
    if progress_callback:
        progress_callback("READING", msg_read)
        
    chunks = splitter.split_directory(data_dir)
    
    if not chunks:
        msg_warn = "No chunks created! Please run crawler or check if 'data/' contains md files."
        print(f"[WARN] {msg_warn}")
        if progress_callback:
            progress_callback("WARN", msg_warn)
        return
        
    msg_split = f"Successfully split documents into {len(chunks)} logical chunks."
    print(f"[INFO] {msg_split}")
    if progress_callback:
        progress_callback("SPLIT", msg_split)
    
    # 3. Add to ChromaDB
    db.add_documents(chunks)
    
    msg_complete = "Ingestion complete. Vector store successfully populated!"
    print(f"[SUCCESS] {msg_complete}")
    if progress_callback:
        progress_callback("SUCCESS", msg_complete)

if __name__ == "__main__":
    run_ingestion()
