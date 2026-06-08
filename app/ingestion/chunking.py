import os
import re
import hashlib
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from app.core.logger import log_info, log_warn, log_error

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
            ("####", "Header 4"),
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

    def is_valid_markdown_table(self, content: str) -> bool:
        """Checks if the block of text has a valid markdown table separator row."""
        lines = content.split("\n")
        if len(lines) < 2:
            return False
        for line in lines:
            if "|" in line and "-" in line and not any(c.isalnum() for c in line):
                return True
        return False

    def split_text_with_table_awareness(self, text: str) -> List[str]:
        """
        Parses text into blocks (text and tables) and packages them into chunks.
        Markdown tables under 1500 characters are kept completely intact.
        """
        lines = text.split("\n")
        blocks = []
        current_block = []
        in_table = False
        
        for line in lines:
            is_table_line = "|" in line
            if is_table_line:
                if not in_table:
                    if current_block:
                        blocks.append({"type": "text", "content": "\n".join(current_block)})
                        current_block = []
                    in_table = True
                current_block.append(line)
            else:
                if in_table:
                    if current_block:
                        blocks.append({"type": "table", "content": "\n".join(current_block)})
                        current_block = []
                    in_table = False
                current_block.append(line)
                
        if current_block:
            blocks.append({
                "type": "table" if in_table else "text",
                "content": "\n".join(current_block)
            })
            
        # Refine blocks: convert false table blocks back to text
        refined_blocks = []
        for b in blocks:
            if b["type"] == "table" and not self.is_valid_markdown_table(b["content"]):
                refined_blocks.append({"type": "text", "content": b["content"]})
            else:
                refined_blocks.append(b)
                
        chunks = []
        current_chunk = []
        current_len = 0
        
        for block in refined_blocks:
            block_content = block["content"].strip()
            if not block_content:
                continue
                
            block_len = len(block_content)
            
            if block["type"] == "table":
                # Flush current text chunk if it has contents
                if current_chunk:
                    chunks.append("\n\n".join(current_chunk))
                    current_chunk = []
                    current_len = 0
                
                # For tables under 1500 characters, keep them intact
                if block_len < 1500:
                    chunks.append(block_content)
                else:
                    # Giant table fallback: split row by row, carrying table headers
                    table_lines = block_content.split("\n")
                    if len(table_lines) > 2:
                        header = "\n".join(table_lines[:2])
                        sub_table = []
                        sub_len = len(header)
                        
                        for line in table_lines[2:]:
                            if sub_len + len(line) > self.chunk_size:
                                chunks.append(header + "\n" + "\n".join(sub_table))
                                sub_table = [line]
                                sub_len = len(header) + len(line)
                            else:
                                sub_table.append(line)
                                sub_len += len(line) + 1
                        if sub_table:
                            chunks.append(header + "\n" + "\n".join(sub_table))
                    else:
                        chunks.append(block_content)
            else:
                # Use standard recursive character splitter for text blocks
                sub_chunks = self.recursive_splitter.split_text(block_content)
                for sub_chunk in sub_chunks:
                    sub_chunk_len = len(sub_chunk)
                    if current_chunk and current_len + sub_chunk_len > self.chunk_size:
                        chunks.append("\n\n".join(current_chunk))
                        current_chunk = [sub_chunk]
                        current_len = sub_chunk_len
                    else:
                        current_chunk.append(sub_chunk)
                        current_len += sub_chunk_len
                        
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))
            
        return chunks

    def split_file(self, filepath: str, category: str) -> List[Document]:
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
                log_error("INGESTION", f"Failed to parse PDF with PyMuPDF4LLM {filename}: {e}")
                body = ""
        else:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    raw_content = f.read()
                try:
                    from crawler.markdown_quality import validate_markdown
                    quality = validate_markdown(raw_content)
                    if quality.warnings:
                        log_warn("INGESTION", f"Markdown quality warnings for {filename}: {quality.warnings}")
                    if not quality.passed:
                        log_warn("INGESTION", f"Skipping {filename}: failed critical markdown quality gate.")
                        return []
                    raw_content = quality.content
                except Exception as e:
                    log_warn("INGESTION", f"Markdown quality gate skipped for {filename}: {e}")
                frontmatter_meta, body = self.parse_frontmatter(raw_content)
            except Exception as e:
                log_error("INGESTION", f"Failed to read Markdown {filename}: {e}")
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
            
            # Split section using table-aware parser
            sub_chunks = self.split_text_with_table_awareness(parent_content)
            
            for idx, sub_chunk in enumerate(sub_chunks):
                meta = {
                    "source": filename,
                    "url": frontmatter_meta.get("url", f"file://{filename}"),
                    "category": category,
                    "parent_chunk_id": parent_chunk_id,
                }
                
                meta.update(frontmatter_meta)
                
                headers = []
                for h in ["Header 1", "Header 2", "Header 3", "Header 4"]:
                    if h in doc.metadata:
                        headers.append(doc.metadata[h])
                
                meta["section"] = " > ".join(headers) if headers else "Introduction"
                
                # Enforce clean ASCII MD5 key to avoid DB crashes
                unique_str = f"{filename}_{meta['section']}_{idx}"
                meta["chunk_id"] = hashlib.md5(unique_str.encode('utf-8')).hexdigest()
                
                # Prepend semantic header path to subsequent chunks to preserve search relevance
                chunk_text = sub_chunk
                if idx > 0 and meta["section"] != "Introduction":
                    chunk_text = f"### {meta['section']}\n\n{sub_chunk}"
                
                enriched_doc = Document(
                    page_content=chunk_text,
                    metadata=meta
                )
                final_docs.append(enriched_doc)
                
        return final_docs

    def split_directory(self, data_dir: str, category_filter: str = None) -> List[Document]:
        """
        Walks the structured folders and splits all markdown and PDF files.
        Duyệt động thay vì hardcode tên thư mục.
        """
        all_documents = []
        
        if not os.path.exists(data_dir):
            log_warn("INGESTION", f"Directory not found: {data_dir}")
            return []
            
        # Lặp qua tất cả thư mục con trong data_dir thay vì hardcode
        categories = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
        
        for category in categories:
            # Bỏ qua thư mục raw
            if category.lower() == "raw":
                continue
                
            if category_filter and category.lower() != category_filter.lower():
                continue
                
            cat_path = os.path.join(data_dir, category)
            for root, _, files in os.walk(cat_path):
                for file in files:
                    if file.lower().endswith((".md", ".pdf")):
                        filepath = os.path.join(root, file)
                        log_info("INGESTION", f"Splitting: {filepath} (Category: {category})")
                        try:
                            chunks = self.split_file(filepath, category=category)
                            all_documents.extend(chunks)
                        except Exception as e:
                            log_error("INGESTION", f"Error splitting {file}: {e}")
                            
        return all_documents
