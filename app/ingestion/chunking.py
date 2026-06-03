import os
import re
import hashlib
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

class HeadingAwareSplitter:
    """
    Heading-aware splitter for legal and policy documents.
    Uses MarkdownHeaderTextSplitter first to preserve logical headers,
    then RecursiveCharacterTextSplitter for sub-splitting.
    Uses clean ASCII MD5 hashes for chunk IDs to prevent Unicode crashes.
    """
    
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Headers to split on
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False
        )
        
        self.recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

    def parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """
        Parses YAML frontmatter metadata from markdown if present.
        """
        metadata = {}
        body = content
        
        if content.startswith("---"):
            match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
            if match:
                frontmatter_text = match.group(1)
                body = content[match.end():]
                
                for line in frontmatter_text.split("\n"):
                    if ":" in line:
                        k, v = line.split(":", 1)
                        metadata[k.strip()] = v.strip()
                        
        return metadata, body

    def split_file(self, filepath: str, role: str) -> List[Document]:
        """
        Splits a single markdown or PDF file into enriched Document chunks.
        Sử dụng pymupdf4llm thay thế pypdf để giữ được bảng và heading.
        """
        filename = os.path.basename(filepath)
        frontmatter_meta = {}
        
        if filepath.lower().endswith(".pdf"):
            try:
                import pymupdf4llm
                body = pymupdf4llm.to_markdown(filepath)
                # Cleanup null bytes if any
                body = body.replace("\x00", "")
            except Exception as e:
                print(f"[ERROR] Failed to parse PDF with PyMuPDF4LLM {filename}: {e}")
                body = ""
        else:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    raw_content = f.read()
                frontmatter_meta, body = self.parse_frontmatter(raw_content)
            except Exception as e:
                print(f"[ERROR] Failed to read Markdown {filename}: {e}")
                body = ""
            
        if not body.strip():
            return []
            
        # Split by markdown headers
        header_docs = self.markdown_splitter.split_text(body)
        
        final_docs = []
        
        for doc in header_docs:
            parent_content = doc.page_content.strip()
            if not parent_content:
                continue
                
            parent_chunk_id = hashlib.md5(parent_content.encode('utf-8')).hexdigest()
            
            sub_docs = self.recursive_splitter.split_documents([doc])
            
            for idx, sub_doc in enumerate(sub_docs):
                meta = {
                    "source": filename,
                    "url": frontmatter_meta.get("url", f"file://{filename}"),
                    "role": role,
                    "parent_chunk_id": parent_chunk_id,
                }
                
                meta.update(frontmatter_meta)
                
                headers = []
                if "Header 1" in sub_doc.metadata:
                    headers.append(sub_doc.metadata["Header 1"])
                if "Header 2" in sub_doc.metadata:
                    headers.append(sub_doc.metadata["Header 2"])
                if "Header 3" in sub_doc.metadata:
                    headers.append(sub_doc.metadata["Header 3"])
                
                meta["section"] = " > ".join(headers) if headers else "Introduction"
                
                # Enforce clean ASCII MD5 key to avoid DB crashes
                unique_str = f"{filename}_{meta['section']}_{idx}"
                meta["chunk_id"] = hashlib.md5(unique_str.encode('utf-8')).hexdigest()
                
                enriched_doc = Document(
                    page_content=sub_doc.page_content,
                    metadata=meta
                )
                final_docs.append(enriched_doc)
                
        return final_docs

    def split_directory(self, data_dir: str) -> List[Document]:
        """
        Walks the structured folders and splits all markdown and PDF files.
        Duyệt động thay vì hardcode tên thư mục.
        """
        all_documents = []
        
        if not os.path.exists(data_dir):
            print(f"[WARNING] Directory not found: {data_dir}")
            return []
            
        # Lặp qua tất cả thư mục con trong data_dir thay vì hardcode
        categories = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
        
        for category in categories:
            cat_path = os.path.join(data_dir, category)
            # Bỏ qua thư mục raw
            if category.lower() == "raw":
                continue
                
            for root, _, files in os.walk(cat_path):
                for file in files:
                    if file.lower().endswith((".md", ".pdf")):
                        filepath = os.path.join(root, file)
                        print(f"[INFO] Splitting: {filepath} (Role: {category})")
                        try:
                            chunks = self.split_file(filepath, role=category)
                            all_documents.extend(chunks)
                        except Exception as e:
                            print(f"[ERROR] Error splitting {file}: {e}")
                            
        return all_documents
