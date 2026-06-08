import re
from dataclasses import dataclass, field


CTA_PATTERNS = [
    r"^\s*ĐĂNG KÝ( NGAY)?\s*$",
    r"^\s*Đăng ký( ngay)?\s*$",
    r"^\s*Ứng tuyển ngay\s*$",
    r"^\s*Chỉ đường\s*$",
    r"^\s*Khám phá\s*$",
    r"^\s*Xem thêm\s*$",
    r"^\s*Tải ngay App.*$",
    r"^\s*Hotline\s*$",
    r"^\s*Zalo chat\s*$",
]

FORM_PATTERNS = [
    r"^\s*Họ và tên\s*\*?\s*$",
    r"^\s*Email\s*\*?\s*$",
    r"^\s*Số điện thoại\s*\*?\s*$",
    r"^\s*Số CCCD\s*\*?\s*$",
    r"^\s*Tỉnh/ Thành phố.*Chọn\s*$",
    r"^\s*Nội dung cần tư vấn thêm\s*$",
    r"^\s*Chọn\s*$",
]

GLUED_FIXES = [
    (r"([a-zà-ỹ])([A-ZĐ])", r"\1 \2"),
    (r"(doanh thu)(Hưởng)", r"\1 \2"),
    (r"(gói vay)(Gói)", r"\1 \2"),
    (r"(ĐẶC QUYỀN)(Tài xế)", r"\1 \2"),
]


@dataclass
class MarkdownQualityResult:
    content: str
    warnings: list[str] = field(default_factory=list)
    passed: bool = True


def clean_markdown_content(content: str) -> str:
    text = (content or "").replace("\x00", "")
    text = re.sub(r"\r\n?", "\n", text)

    for pattern, repl in GLUED_FIXES:
        text = re.sub(pattern, repl, text)

    cleaned_lines = []
    junk_patterns = [re.compile(p, re.IGNORECASE) for p in CTA_PATTERNS + FORM_PATTERNS]
    for line in text.split("\n"):
        stripped = line.strip()
        if any(p.match(stripped) for p in junk_patterns):
            continue
        if re.match(r"^#{1,4}\s*$", stripped):
            continue
        cleaned_lines.append(line.rstrip())

    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _has_frontmatter(content: str, key: str) -> bool:
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return False
    return re.search(rf"^{re.escape(key)}\s*:", match.group(1), re.MULTILINE) is not None


def validate_markdown(content: str) -> MarkdownQualityResult:
    warnings: list[str] = []
    clean = clean_markdown_content(content)

    if re.search(r"^#{1,4}\s*$", clean, re.MULTILINE):
        warnings.append("empty_heading")

    for key in ["url", "category", "title"]:
        if not _has_frontmatter(clean, key):
            warnings.append(f"missing_frontmatter_{key}")

    body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", clean, flags=re.DOTALL).strip()
    if not re.search(r"^#\s+\S+", body, re.MULTILINE):
        warnings.append("missing_h1")
    if not re.search(r"^##\s+\S+", body, re.MULTILINE):
        warnings.append("missing_h2")

    cta_count = 0
    form_count = 0
    lines = [line.strip() for line in body.split("\n") if line.strip()]
    for line in lines:
        if any(re.match(p, line, re.IGNORECASE) for p in CTA_PATTERNS):
            cta_count += 1
        if any(re.match(p, line, re.IGNORECASE) for p in FORM_PATTERNS):
            form_count += 1
    if lines and (cta_count + form_count) / len(lines) > 0.08:
        warnings.append("high_cta_form_ratio")

    if re.search(r"(doanh thuHưởng|vayGói|QUYỀNTài)", clean):
        warnings.append("glued_text_pattern")

    table_lines = [line for line in body.split("\n") if "|" in line]
    if table_lines:
        has_separator = any(re.match(r"^\s*\|?[\s:\-|\u2014]+\|[\s:\-|\u2014]*$", line) for line in table_lines)
        if not has_separator:
            warnings.append("table_without_separator")

    critical = {"missing_frontmatter_url", "missing_frontmatter_category", "missing_frontmatter_title"}
    passed = not any(w in critical for w in warnings)
    return MarkdownQualityResult(content=clean, warnings=warnings, passed=passed)
