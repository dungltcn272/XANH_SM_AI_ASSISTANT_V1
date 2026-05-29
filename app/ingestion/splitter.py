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
    Uses clean ASCII MD5 hashes for chunk IDs to prevent ChromaDB Unicode crashes.
    """
    
    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 150):
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
        """
        filename = os.path.basename(filepath)
        frontmatter_meta = {}
        
        if filepath.lower().endswith(".pdf"):
            import pypdf
            try:
                reader = pypdf.PdfReader(filepath)
                pdf_lines = []
                
                # Simple layout-aware heuristics to convert PDF text to hierarchy Markdown
                for page_num, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    for line in text.split("\n"):
                        trimmed = line.strip()
                        if not trimmed:
                            continue
                        
                        is_header = False
                        # Regular expressions to check if line is a header
                        if (
                            re.match(r"^(Chương|Điều|Mục|Phần)\s+\d+", trimmed, re.IGNORECASE) or
                            re.match(r"^[I|V|X|L|C|D|M]+\.\s+", trimmed) or
                            re.match(r"^\d+(\.\d+)+\s+", trimmed) or
                            (len(trimmed) < 80 and not trimmed.endswith(('.', ':', ';', ',')) and trimmed[0].isupper())
                        ):
                            is_header = True
                            
                        if is_header:
                            if re.match(r"^(Chương|Phần)\s+", trimmed, re.IGNORECASE):
                                pdf_lines.append(f"# {trimmed}")
                            elif re.match(r"^(Mục|Điều)\s+\d+", trimmed, re.IGNORECASE):
                                pdf_lines.append(f"## {trimmed}")
                            else:
                                pdf_lines.append(f"### {trimmed}")
                        else:
                            pdf_lines.append(trimmed)
                
                body = "\n\n".join(pdf_lines)
            except Exception as e:
                print(f"[ERROR] Failed to parse PDF {filename}: {e}")
                body = ""
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                raw_content = f.read()
            frontmatter_meta, body = self.parse_frontmatter(raw_content)
            
        if not body.strip():
            return []
            
        # Split by markdown headers
        header_docs = self.markdown_splitter.split_text(body)
        
        final_docs = []
        
        for doc in header_docs:
            parent_content = doc.page_content.strip()
            parent_chunk_id = hashlib.md5(parent_content.encode('utf-8')).hexdigest()
            
            sub_docs = self.recursive_splitter.split_documents([doc])
            
            for idx, sub_doc in enumerate(sub_docs):
                meta = {
                    "source": filename,
                    "role": role,
                    "version": "2026-05",
                    "parent_chunk_id": parent_chunk_id,
                    "parent_content": parent_content,
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
                
                # Enforce clean ASCII MD5 key to avoid SQLite/hnswlib Unicode crashes on Windows host environments
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
        """
        all_documents = []
        categories = ["customer", "driver", "merchant", "faq"]
        
        for category in categories:
            cat_path = os.path.join(data_dir, category)
            if not os.path.exists(cat_path):
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

if __name__ == "__main__":
    splitter = HeadingAwareSplitter()
    docs = splitter.split_directory("./data")
    print(f"[SUCCESS] Total chunks created: {len(docs)}")
    if docs:
        print(f"Sample Chunk ID: {docs[0].metadata['chunk_id']}")
