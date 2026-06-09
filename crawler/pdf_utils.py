import hashlib
import re
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import requests


def _is_table_separator(line: str) -> bool:
    return bool(re.match(r"^\s*\|?[\s:\-|\u2014]+\|[\s:\-|\u2014]*$", line))


def _is_page_artifact_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if re.match(r"^\d+\s*/\s*\d+\s*$", stripped):
        return True
    if "picture" in stripped.lower() and "omitted" in stripped.lower():
        return True
    return False


def _is_heading_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("#") or bool(re.match(r"^\*{0,2}\d+(?:\.\d+)+\s+", stripped))


def _split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return stripped.split("|")


def _join_table_row(cells: list[str]) -> str:
    return "|" + "|".join(cells) + "|"


def _cell_text(cell: str) -> str:
    return re.sub(r"[*_`<br>/\s]+", "", cell, flags=re.IGNORECASE).lower()


def _header_key(header_line: str) -> tuple[str, ...]:
    return tuple(_cell_text(cell) for cell in _split_table_row(header_line))


def _looks_like_header(line: str) -> bool:
    cells = [_cell_text(cell) for cell in _split_table_row(line)]
    if not cells:
        return False
    if cells[0] in {"tt", "stt"}:
        return True
    return "ghichú" in cells and ("hạngmục" in cells or "chươngtrình" in cells)


def _is_valid_table_block(lines: list[str]) -> bool:
    return any(_is_table_separator(line) for line in lines)


def _extract_table_layouts(pdf_path: Path) -> list[dict]:
    import fitz

    layouts = []
    with fitz.open(str(pdf_path)) as doc:
        for page_index, page in enumerate(doc):
            page_height = float(page.rect.height)
            for table in page.find_tables().tables:
                x_positions = sorted({round(cell[0], 1) for cell in table.cells if cell})
                x_positions.append(round(float(table.bbox[2]), 1))
                layouts.append({
                    "page": page_index,
                    "page_height": page_height,
                    "bbox": tuple(float(v) for v in table.bbox),
                    "column_count": int(table.col_count),
                    "x_positions": x_positions,
                })
    return layouts


def _similar_column_positions(left: dict, right: dict, tolerance: float = 10.0) -> bool:
    left_positions = left.get("x_positions") or []
    right_positions = right.get("x_positions") or []
    if len(left_positions) != len(right_positions):
        return False
    if not left_positions:
        return True
    deltas = [abs(a - b) for a, b in zip(left_positions, right_positions)]
    return max(deltas) <= tolerance


def _layout_supports_table_merge(
    previous: dict | None,
    current: dict | None,
    *,
    same_header: bool,
    continuation: bool,
) -> bool:
    if not previous or not current:
        return same_header or continuation
    if current["page"] != previous["page"] + 1:
        return False
    if previous["column_count"] != current["column_count"]:
        return False
    if not _similar_column_positions(previous, current):
        return False

    previous_bottom = previous["bbox"][3] / max(previous["page_height"], 1.0)
    current_top = current["bbox"][1] / max(current["page_height"], 1.0)
    score = 0
    if previous_bottom > 0.65:
        score += 1
    if current_top < 0.30:
        score += 1
    if same_header:
        score += 2
    if continuation:
        score += 2
    score += 2  # same column count + aligned x positions already proved above
    return score >= 5


def _find_table_blocks(lines: list[str]) -> list[tuple[int, int]]:
    blocks: list[tuple[int, int]] = []
    start = None
    current: list[str] = []
    for index, line in enumerate(lines):
        if "|" in line:
            if start is None:
                start = index
            current.append(line)
            continue
        if start is not None:
            if _is_valid_table_block(current):
                blocks.append((start, index))
            start = None
            current = []
    if start is not None and _is_valid_table_block(current):
        blocks.append((start, len(lines)))
    return blocks


def _has_real_content_between(lines: list[str]) -> bool:
    for line in lines:
        stripped = line.strip()
        if not stripped or _is_page_artifact_line(stripped):
            continue
        if stripped.startswith("_") and stripped.endswith("_"):
            continue
        return True
    return False


def _collect_notes(lines: list[str]) -> list[str]:
    notes = []
    for line in lines:
        stripped = line.strip()
        if not stripped or _is_page_artifact_line(stripped):
            continue
        notes.append(line)
    return notes


def _extract_table_parts(block: list[str]) -> tuple[list[str], list[str], list[str]]:
    separator_index = next((idx for idx, line in enumerate(block) if _is_table_separator(line)), -1)
    if separator_index <= 0:
        return [], [], block
    header = block[:separator_index]
    separator = [block[separator_index]]
    rows = block[separator_index + 1 :]
    return header, separator, rows


def _continuation_rows(block: list[str], previous_col_count: int) -> list[str]:
    header, _separator, rows = _extract_table_parts(block)
    if not header:
        return block
    if len(header) == 1 and not _looks_like_header(header[0]):
        first_cells = _split_table_row(header[0])
        if len(first_cells) == previous_col_count:
            return header + rows
    return rows


def _expand_empty_merged_cells(rows: list[str]) -> list[str]:
    expanded = []
    for row in rows:
        cells = _split_table_row(row)
        if len(cells) < 8:
            expanded.append(row)
            continue
        next_cells = []
        previous = ""
        for idx, cell in enumerate(cells):
            if idx < 2 or idx == len(cells) - 1:
                next_cells.append(cell)
                previous = cell.strip() or previous
                continue
            if cell.strip():
                previous = cell
                next_cells.append(cell)
            else:
                next_cells.append(previous)
        expanded.append(_join_table_row(next_cells))
    return expanded


def _normalize_markdown_tables(markdown: str, table_layouts: list[dict] | None = None) -> tuple[str, int, int]:
    lines = markdown.splitlines()
    blocks = _find_table_blocks(lines)
    if not blocks:
        cleaned = [line for line in lines if not _is_page_artifact_line(line)]
        return "\n".join(cleaned), 0, 0

    output: list[str] = []
    cursor = 0
    index = 0
    repaired = 0
    merged = 0

    while index < len(blocks):
        start, end = blocks[index]
        output.extend(line for line in lines[cursor:start] if not _is_page_artifact_line(line))

        header, separator, rows = _extract_table_parts(lines[start:end])
        if not header:
            output.extend(lines[start:end])
            cursor = end
            index += 1
            continue

        table_header = header[:1]
        table_separator = separator[:1]
        table_rows = rows[:]
        notes: list[str] = []
        current_end = end
        current_key = _header_key(table_header[0])
        current_col_count = len(_split_table_row(table_header[0]))

        next_index = index + 1
        while next_index < len(blocks):
            next_start, next_end = blocks[next_index]
            between = lines[current_end:next_start]
            if any(_is_heading_line(line) for line in between):
                break
            next_block = lines[next_start:next_end]
            next_header, _next_separator, next_rows = _extract_table_parts(next_block)
            if not next_header:
                break

            same_header = _looks_like_header(next_header[0]) and _header_key(next_header[0]) == current_key
            continuation = (
                not _looks_like_header(next_header[0])
                and len(_split_table_row(next_header[0])) == current_col_count
                and not _has_real_content_between(between)
            )
            if not same_header and not continuation:
                break
            previous_layout = table_layouts[next_index - 1] if table_layouts and next_index - 1 < len(table_layouts) else None
            current_layout = table_layouts[next_index] if table_layouts and next_index < len(table_layouts) else None
            if not _layout_supports_table_merge(
                previous_layout,
                current_layout,
                same_header=same_header,
                continuation=continuation,
            ):
                break

            notes.extend(_collect_notes(between))
            if same_header:
                table_rows.extend(next_rows)
            else:
                table_rows.extend(_continuation_rows(next_block, current_col_count))
            current_end = next_end
            next_index += 1
            merged += 1

        output.extend(table_header)
        output.extend(table_separator)
        output.extend(_expand_empty_merged_cells(table_rows))
        if notes:
            output.append("")
            output.extend(notes)
        repaired += 1
        cursor = current_end
        index = next_index

    output.extend(line for line in lines[cursor:] if not _is_page_artifact_line(line))
    text = "\n".join(output)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text, repaired, merged


def _normalize_pdf_lists(markdown: str) -> str:
    lines = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if re.match(r"^-\s*$", stripped):
            continue

        numbered_heading = re.match(r"^-\s+\*\*(\d+(?:\.\d+)*\.\s+.+?)\*\*\s*$", stripped)
        if numbered_heading:
            label = numbered_heading.group(1)
            level = "###" if re.match(r"^\d+\.\d+\.", label) else "##"
            lines.append(f"{level} **{label}**")
            continue

        bare_numbered_heading = re.match(r"^\*\*(\d+(?:\.\d+)*\.\s+.+?)\*\*\s*$", stripped)
        if bare_numbered_heading:
            label = bare_numbered_heading.group(1)
            level = "###" if re.match(r"^\d+\.\d+\.", label) else "##"
            lines.append(f"{level} **{label}**")
            continue

        lines.append(re.sub(r"^\s{2,}-\s+", "- ", line.rstrip()))

    text = "\n".join(lines)
    text = re.sub(
        r"\s+\*\*(\d+\.\d+\.\s+[^*\n]+?:)\*\*",
        r"\n### **\1**",
        text,
    )
    text = re.sub(r"(?m)^#{1,6}\s*$\n?", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def download_pdf(url: str, timeout: int = 45) -> tuple[bytes, str]:
    response = requests.get(url, timeout=timeout, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    content = response.content
    if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
        raise ValueError(f"URL did not return a PDF content-type: {content_type}")
    if len(content) < 1024:
        raise ValueError(f"PDF response too small: {len(content)} bytes")
    return content, content_type


def extract_pdf_markdown(url: str) -> dict:
    content, content_type = download_pdf(url)
    suffix = Path(urlparse(url).path).suffix or ".pdf"
    raw_md = ""
    page_count = 0
    repaired_table_count = 0
    merged_table_count = 0
    detected_table_count = 0

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        try:
            import pymupdf4llm

            table_layouts = []
            try:
                table_layouts = _extract_table_layouts(tmp_path)
                detected_table_count = len(table_layouts)
            except Exception:
                table_layouts = []
            raw_md = pymupdf4llm.to_markdown(str(tmp_path))
            raw_md = re.sub(r"<br\s*/?>", " ", raw_md, flags=re.IGNORECASE)
            raw_md, repaired_table_count, merged_table_count = _normalize_markdown_tables(raw_md, table_layouts)
            raw_md = _normalize_pdf_lists(raw_md)
        except Exception:
            import fitz

            parts = []
            with fitz.open(str(tmp_path)) as doc:
                page_count = doc.page_count
                for idx, page in enumerate(doc, 1):
                    text = page.get_text("text")
                    if text.strip():
                        parts.append(f"## Trang {idx}\n\n{text.strip()}")
            raw_md = "\n\n".join(parts)

        if page_count == 0:
            import fitz

            with fitz.open(str(tmp_path)) as doc:
                page_count = doc.page_count

        parsed = urlparse(url)
        title = Path(parsed.path).name.replace(".pdf", "").replace("_", " ").strip() or "Policy Document"
        markdown = raw_md.strip()
        if not re.search(r"^#\s+\S+", markdown, re.MULTILINE):
            markdown = f"# {title}\n\n{markdown}"

        return {
            "url": url,
            "title": title,
            "markdown": markdown,
            "audit": {
                "bytes": len(content),
                "content_type": content_type,
                "page_count": page_count,
                "raw_md_len": len(raw_md),
                "clean_md_len": len(markdown),
                "table_count": markdown.count("\n|"),
                "detected_table_count": detected_table_count,
                "repaired_table_count": repaired_table_count,
                "merged_table_count": merged_table_count,
                "sha256": hashlib.sha256(content).hexdigest(),
            },
        }
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
