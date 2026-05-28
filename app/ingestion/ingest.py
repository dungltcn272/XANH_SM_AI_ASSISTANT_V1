import os
import sys
import shutil
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
    data_dir = os.path.abspath(config.DATA_DIR)
    msg_read = f"Reading documents from: {data_dir}"
    print(f"[INFO] {msg_read}")
    if progress_callback:
        progress_callback("READING", msg_read)

    # If target data dir is missing or contains no markdown, attempt to populate it
    # from the bundled repo `data/` folder so ingestion can run on fresh deployments.
    def _has_markdown(dir_path):
        return os.path.isdir(dir_path) and any(
            fname.endswith('.md') for _, _, files in os.walk(dir_path) for fname in files
        )

    if not _has_markdown(data_dir):
        repo_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        if _has_markdown(repo_data_dir):
            try:
                print(f"[INFO] DATA_DIR '{data_dir}' is empty; copying bundled repo data from '{repo_data_dir}'...")
                os.makedirs(data_dir, exist_ok=True)
                files_copied = 0
                for root, dirs, files in os.walk(repo_data_dir):
                    rel = os.path.relpath(root, repo_data_dir)
                    dest_root = os.path.join(data_dir, rel) if rel != '.' else data_dir
                    os.makedirs(dest_root, exist_ok=True)
                    for f in files:
                        if f.endswith('.md'):
                            shutil.copy2(os.path.join(root, f), os.path.join(dest_root, f))
                            files_copied += 1
                print(f"[INFO] Copied {files_copied} markdown files into {data_dir}.")
            except Exception as e:
                msg_warn = f"Failed to copy bundled data into {data_dir}: {e}"
                print(f"[WARN] {msg_warn}")
                if progress_callback:
                    progress_callback("WARN", msg_warn)
                return
        else:
            msg_warn = (
                "No chunks created! Please run crawler or check if the configured data directory contains markdown files. "
                f"Checked paths: {config.DATA_DIR}, {repo_data_dir}"
            )
            print(f"[WARN] {msg_warn}")
            if progress_callback:
                progress_callback("WARN", msg_warn)
            return

    chunks = splitter.split_directory(data_dir)
        
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
