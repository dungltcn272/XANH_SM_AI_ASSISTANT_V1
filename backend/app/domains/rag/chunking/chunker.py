from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from app.config.settings import settings


@dataclass
class Chunk:
    content: str
    section: str
    chunk_index: int
    chunk_type: str = "text"
    chunk_id: str = ""
    parent_chunk_id: str = ""
    metadata: dict = field(default_factory=dict)


def _stable_hash(*parts: object) -> str:
    raw = "|".join(str(part or "") for part in parts)
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def _normalize_ws(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _section_blocks(markdown: str) -> list[tuple[str, str]]:
    current_path: list[str] = []
    current_lines: list[str] = []
    blocks: list[tuple[str, str]] = []

    def flush() -> None:
        content = _normalize_ws("\n".join(current_lines))
        if content:
            blocks.append((" > ".join(current_path) or "Introduction", content))

    for line in markdown.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            flush()
            current_lines = [line]
            level = len(match.group(1))
            title = match.group(2).strip()
            del current_path[level - 1 :]
            current_path.append(title)
            continue
        current_lines.append(line)
    flush()
    return blocks


def _is_markdown_table(lines: list[str], index: int) -> bool:
    if index + 1 >= len(lines):
        return False
    return "|" in lines[index] and bool(re.match(r"^\s*\|?[\s:\-|]+\|[\s:\-|]*$", lines[index + 1]))


def _extract_tables(section_text: str) -> list[tuple[str, str]]:
    lines = section_text.splitlines()
    parts: list[tuple[str, str]] = []
    buffer: list[str] = []
    index = 0

    def flush_text() -> None:
        nonlocal buffer
        text = _normalize_ws("\n".join(buffer))
        if text:
            parts.append(("text", text))
        buffer = []

    while index < len(lines):
        line = lines[index]
        if line.strip().lower().startswith("<table"):
            flush_text()
            table = [line]
            index += 1
            while index < len(lines):
                table.append(lines[index])
                if lines[index].strip().lower().endswith("</table>"):
                    index += 1
                    break
                index += 1
            parts.append(("html_table", "\n".join(table)))
            continue

        if _is_markdown_table(lines, index):
            flush_text()
            table = [lines[index], lines[index + 1]]
            index += 2
            while index < len(lines) and "|" in lines[index]:
                table.append(lines[index])
                index += 1
            parts.append(("markdown_table", "\n".join(table)))
            continue

        buffer.append(line)
        index += 1
    flush_text()
    return parts


def _recursive_split(text: str, *, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    separators = ["\n\n", "\n", ". ", " ", ""]
    chunks: list[str] = []

    def split_block(block: str) -> None:
        block = block.strip()
        if not block:
            return
        if len(block) <= chunk_size:
            chunks.append(block)
            return
        for separator in separators:
            if separator and separator in block:
                parts = block.split(separator)
                current = ""
                for part in parts:
                    candidate = f"{current}{separator}{part}".strip() if current else part.strip()
                    if len(candidate) <= chunk_size:
                        current = candidate
                    else:
                        if current:
                            chunks.append(current)
                        current = part.strip()
                if current:
                    chunks.append(current)
                return
        for start in range(0, len(block), max(1, chunk_size - overlap)):
            chunks.append(block[start : start + chunk_size])

    split_block(text)
    if overlap <= 0 or len(chunks) <= 1:
        return chunks
    merged: list[str] = []
    previous_tail = ""
    for chunk in chunks:
        merged.append(_normalize_ws(f"{previous_tail}\n{chunk}") if previous_tail else chunk)
        previous_tail = chunk[-overlap:]
    return merged


def _table_rows(table_text: str) -> list[str]:
    if table_text.strip().lower().startswith("<table"):
        return [line.strip() for line in re.findall(r"<tr[\s\S]*?</tr>", table_text, flags=re.IGNORECASE)]
    lines = [line for line in table_text.splitlines() if "|" in line]
    return [line for line in lines if not re.match(r"^\s*\|?[\s:\-|]+\|[\s:\-|]*$", line)]


def _table_chunks(table_text: str, *, source_key: str, section: str, start_index: int) -> list[Chunk]:
    table_id = _stable_hash(source_key, section, "table", table_text[:300])
    parent_id = f"table_{table_id}"
    full_id = f"chunk_{_stable_hash(parent_id, 'full', table_text)}"
    chunks = [
        Chunk(
            content=table_text,
            section=section,
            chunk_index=start_index,
            chunk_type="html_table_full" if table_text.strip().lower().startswith("<table") else "markdown_table_full",
            chunk_id=full_id,
            parent_chunk_id=parent_id,
            metadata={"table_id": table_id, "table_title": section},
        )
    ]

    rows = _table_rows(table_text)
    if len(rows) > 3:
        header = rows[:2]
        body = rows[2:]
        row_index = 0
        for start in range(0, len(body), 3):
            selected = body[start : start + 3]
            content = "\n".join([*header, *selected])
            chunks.append(
                Chunk(
                    content=content,
                    section=section,
                    chunk_index=start_index + len(chunks),
                    chunk_type="table_row_index",
                    chunk_id=f"chunk_{_stable_hash(parent_id, 'rows', start, content)}",
                    parent_chunk_id=parent_id,
                    metadata={
                        "table_id": table_id,
                        "table_title": section,
                        "row_start": row_index,
                        "row_end": row_index + len(selected) - 1,
                        "derived_from": full_id,
                    },
                )
            )
            row_index += len(selected)
    return chunks


def chunk_markdown(
    markdown: str,
    *,
    source_key: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> list[Chunk]:
    chunk_size = chunk_size or settings.RAG_CHUNK_SIZE
    chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.RAG_CHUNK_OVERLAP
    output: list[Chunk] = []
    global_index = 0

    for section, section_text in _section_blocks(markdown):
        parent_id = f"parent_{_stable_hash(source_key, section)}"
        for part_type, part_text in _extract_tables(section_text):
            if part_type in {"html_table", "markdown_table"}:
                table_chunks = _table_chunks(part_text, source_key=source_key, section=section, start_index=global_index)
                output.extend(table_chunks)
                global_index += len(table_chunks)
                continue

            for local_index, text_chunk in enumerate(_recursive_split(part_text, chunk_size=chunk_size, overlap=chunk_overlap)):
                content = text_chunk
                if local_index > 0 and section != "Introduction":
                    content = f"### {section}\n\n{content}"
                chunk_id = f"chunk_{_stable_hash(source_key, section, global_index, content)}"
                output.append(
                    Chunk(
                        content=content,
                        section=section,
                        chunk_index=global_index,
                        chunk_type="text",
                        chunk_id=chunk_id,
                        parent_chunk_id=parent_id,
                        metadata={},
                    )
                )
                global_index += 1
    return output
