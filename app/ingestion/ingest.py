import os
import sys
# Make sure app directory is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.ingestion.splitter import HeadingAwareSplitter
from app.vectordb.chroma_client import XanhSMVectorDB
from app.config import config

def run_ingestion():
    print("[INFO] Starting legal document ingestion pipeline for Xanh SM...")
    
    # 1. Initialize DB and Splitter
    db = XanhSMVectorDB()
    splitter = HeadingAwareSplitter(chunk_size=700, chunk_overlap=150)
    
    # 2. Split directory
    data_dir = config.DATA_DIR
    print(f"[INFO] Reading documents from: {data_dir}")
    chunks = splitter.split_directory(data_dir)
    
    if not chunks:
        print("[WARN] No chunks created! Please run crawler or check if 'data/' contains md files.")
        return
        
    print(f"[INFO] Successfully split documents into {len(chunks)} logical chunks.")
    
    # 3. Add to ChromaDB
    db.add_documents(chunks)
    print("[SUCCESS] Ingestion complete. Vector store successfully populated!")

if __name__ == "__main__":
    run_ingestion()
