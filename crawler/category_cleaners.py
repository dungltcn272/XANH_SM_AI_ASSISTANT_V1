import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import markdownify
from bs4 import BeautifulSoup, Tag

try:
    from markdown_converter import MarkdownConverter
except ImportError:
    from .markdown_converter import MarkdownConverter


JUNK_CLASS_RE = re.compile(
    r"(header|footer|nav|menu|sidebar|breadcrumb|social|share|pagination|"
    r"modal|popup|floating|hotline|zalo|contact|form|button|register|"
    r"download|app|related|recent)",
    re.IGNORECASE,
)


@dataclass
class CleanedDocument:
    markdown: str
    title: str
    summary: str = ""
    document_type: str = "service"


class DeterministicCleaner:
    """Rule-based page cleaners for curated Green SM URLs.

    The goal is not to be clever; it is to preserve source text, tables, links,
    and images while removing navigation/CTA noise before chunking.
    """

    def __init__(self):
        self.default_converter = MarkdownConverter()

    def clean(
        self,
        html: str,
        title: str,
        url: str,
        category: str = "",
        source_profile: str = "main_site",
        document_type: str = "service",
    ) -> CleanedDocument:
        lower = url.lower()
        if document_type in {"news", "news_list"} or "/news/" in lower:
            if re.search(r"/news/(all/)?page/\d+", lower) or lower.rstrip("/").endswith("/news"):
                return self.clean_news_list(html, title, url)
            return self.clean_news_detail(html, title, url)

        if source_profile == "platform":
            if document_type == "platform_overview":
                return self.clean_platform_overview(html, title, url)
            if document_type == "vehicle" or self._looks_like_vehicle_url(url):
                return self.clean_vehicle_page(html, title, url)
            return self.clean_platform_page(html, title, url, document_type=document_type)

        markdown = self.default_converter.html_to_markdown(html, title, url)
        return CleanedDocument(
            markdown=markdown,
            title=self._best_title(BeautifulSoup(html, "html.parser"), title, url),
            summary=self._first_sentence(markdown),
            document_type=document_type or "service",
        )

    def clean_news_detail(self, html: str, title: str, url: str) -> CleanedDocument:
        soup = BeautifulSoup(html, "html.parser")
        next_data = self._load_next_data(soup)
        self._remove_junk(soup)
        self._absolutize_images(soup, url)

        page_title = self._best_title(soup, title, url)
        category = self._meta_content(soup, "article:section") or self._find_news_category(soup)
        date = self._meta_content(soup, "article:published_time") or self._find_date_text(soup)

        article = self._select_main_content(soup, selectors=["article", "main", "[class*='detail']", "[class*='content']"])
        markdown = self._markdownify(article)

        next_text = self._extract_next_text(next_data)
        if len(next_text) > len(markdown) * 1.25:
            markdown = next_text

        parts = [f"# {page_title}", ""]
        parts.append("## Thong tin bai viet")
        parts.append(f"- URL: {url}")
        if category:
            parts.append(f"- Danh muc: {category}")
        if date:
            parts.append(f"- Ngay dang/cap nhat: {date}")
        parts.extend(["", "## Noi dung", "", markdown.strip()])

        return CleanedDocument(
            markdown=self._clean_markdown("\n".join(parts)),
            title=page_title,
            summary=self._first_sentence(markdown),
            document_type="news",
        )

    def clean_news_list(self, html: str, title: str, url: str) -> CleanedDocument:
        soup = BeautifulSoup(html, "html.parser")
        self._remove_junk(soup)
        cards = self._extract_news_cards(soup, url)
        page_title = self._best_title(soup, title, url) or "Tin tuc Green SM"

        parts = [f"# {page_title}", "", "## Danh sach tin tuc", ""]
        if not cards:
            markdown = self._markdownify(self._select_main_content(soup))
            parts.append(markdown)
        else:
            seen = set()
            for index, card in enumerate(cards, 1):
                if card["url"] in seen:
                    continue
                seen.add(card["url"])
                parts.append(f"### {index}. {card['title']}")
                parts.append(f"- URL: {card['url']}")
                if card.get("category"):
                    parts.append(f"- Danh muc: {card['category']}")
                if card.get("date"):
                    parts.append(f"- Ngay dang/cap nhat: {card['date']}")
                if card.get("summary"):
                    parts.append(f"- Tom tat: {card['summary']}")
                if card.get("image"):
                    parts.append(f"- Anh: {card['image']}")
                parts.append("")

        return CleanedDocument(
            markdown=self._clean_markdown("\n".join(parts)),
            title=page_title,
            summary=f"Danh sach {len(cards)} tin tuc tu {url}",
            document_type="news_list",
        )

    def clean_platform_page(self, html: str, title: str, url: str, document_type: str = "policy_page") -> CleanedDocument:
        soup = BeautifulSoup(html, "html.parser")
        next_data = self._load_next_data(soup)
        self._remove_junk(soup)
        self._absolutize_images(soup, url)

        page_title = self._best_title(soup, title, url)
        content = self._select_main_content(soup, selectors=["main", "article", "[class*='page']", "[class*='content']"])
        markdown = self._markdownify(content)

        dynamic_md = self._extract_next_text(next_data)
        if len(dynamic_md) > len(markdown) * 1.2:
            markdown = dynamic_md

        doc_type = self._platform_doc_type(url, document_type)
        parts = [
            f"# {page_title}",
            "",
            "## Thong tin nguon",
            f"- URL: {url}",
            f"- Loai tai lieu: {doc_type}",
            "",
            "## Noi dung",
            "",
            markdown.strip(),
        ]
        return CleanedDocument(
            markdown=self._clean_markdown("\n".join(parts)),
            title=page_title,
            summary=self._first_sentence(markdown),
            document_type=doc_type,
        )

    def clean_platform_overview(self, html: str, title: str, url: str) -> CleanedDocument:
        soup = BeautifulSoup(html, "html.parser")
        next_data = self._load_next_data(soup)
        self._remove_junk(soup)
        self._absolutize_images(soup, url)

        page_title = self._best_title(soup, title, url) or "Green SM Platform"
        content = self._select_main_content(soup, selectors=["main", "body"])
        markdown = self._markdownify(content)
        dynamic_md = self._extract_next_text(next_data)
        if len(dynamic_md) > len(markdown):
            markdown = dynamic_md

        vehicle_cards = self._extract_vehicle_cards(soup, url)
        parts = [
            f"# {page_title}",
            "",
            "## Thong tin nguon",
            f"- URL: {url}",
            "- Loai tai lieu: platform_overview",
            "",
        ]
        if vehicle_cards:
            parts.extend(["## Danh muc xe tren Green SM Platform", ""])
            for index, card in enumerate(vehicle_cards, 1):
                parts.append(f"### {index}. {card['name']}")
                if card.get("price"):
                    parts.append(f"- Gia hien thi: {card['price']}")
                if card.get("mode"):
                    parts.append(f"- Hinh thuc: {card['mode']}")
                if card.get("url"):
                    parts.append(f"- URL chi tiet: {card['url']}")
                if card.get("image"):
                    parts.append(f"- Anh: {card['image']}")
                parts.append("")

        parts.extend(["## Noi dung trang", "", markdown])
        return CleanedDocument(
            markdown=self._clean_markdown("\n".join(parts)),
            title=page_title,
            summary=self._first_sentence(markdown),
            document_type="platform_overview",
        )

    def clean_vehicle_page(self, html: str, title: str, url: str) -> CleanedDocument:
        soup = BeautifulSoup(html, "html.parser")
        next_data = self._load_next_data(soup)
        self._remove_junk(soup)
        self._absolutize_images(soup, url)

        page_title = self._best_title(soup, title, url)
        content = self._select_main_content(soup, selectors=["main", "article", "body"])
        markdown = self._markdownify(content)
        dynamic_md = self._extract_next_text(next_data)
        if len(dynamic_md) > len(markdown) * 1.15:
            markdown = dynamic_md

        flat_text = re.sub(r"\s+", " ", content.get_text(" ", strip=True))
        price = self._extract_price(flat_text)
        specs = self._extract_vehicle_specs(flat_text)
        images = self._extract_images(content, url, limit=12)

        parts = [
            f"# {page_title}",
            "",
            "## Thong tin xe",
            f"- URL: {url}",
            "- Loai tai lieu: vehicle",
        ]
        if price:
            parts.append(f"- Gia hien thi: {price}")
        if images:
            parts.extend(["", "## Hinh anh chinh"])
            for image in images:
                parts.append(f"- {image}")
        if specs:
            parts.extend(["", "## Thong so / dac diem trich xuat"])
            for key, value in specs:
                parts.append(f"- {key}: {value}")
        parts.extend(["", "## Noi dung chi tiet", "", markdown])

        return CleanedDocument(
            markdown=self._clean_markdown("\n".join(parts)),
            title=page_title,
            summary=self._first_sentence(markdown),
            document_type="vehicle",
        )

    def _remove_junk(self, soup: BeautifulSoup) -> None:
        for tag_name in ["script", "style", "noscript", "iframe", "svg", "header", "footer", "nav", "aside", "form", "button"]:
            for elem in soup.find_all(tag_name):
                elem.decompose()

        for elem in list(soup.find_all(True)):
            classes = " ".join(elem.get("class", []))
            elem_id = elem.get("id", "")
            role = elem.get("role", "")
            text_key = " ".join([classes, elem_id, role])
            if text_key and JUNK_CLASS_RE.search(text_key):
                elem.decompose()

        for text in soup.find_all(string=lambda t: t and re.search(r"(Hotline|Zalo chat|Dang ky tu van|Tai ung dung)", t, re.I)):
            parent = text.parent
            if parent and parent.name not in {"main", "article", "body"}:
                parent.decompose()

    def _select_main_content(self, soup: BeautifulSoup, selectors: list[str] | None = None) -> Tag:
        selectors = selectors or ["article", "main", "[role='main']", "body"]
        candidates: list[Tag] = []
        for selector in selectors:
            candidates.extend([item for item in soup.select(selector) if isinstance(item, Tag)])
        if not candidates:
            body = soup.find("body")
            return body if isinstance(body, Tag) else soup
        return max(candidates, key=lambda tag: len(tag.get_text(" ", strip=True)))

    def _markdownify(self, node: Any) -> str:
        markdown = markdownify.markdownify(str(node), heading_style="ATX", bullets="-", strip=["a"])
        return self._clean_markdown(markdown)

    def _clean_markdown(self, markdown: str) -> str:
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)
        markdown = re.sub(r"[ \t]+\n", "\n", markdown)
        markdown = re.sub(r"\n\s*!\[\]\(\)\s*\n", "\n", markdown)
        markdown = re.sub(r"(?m)^\s*(Xem them|Dang ky tu van|Zalo chat|Hotline)\s*$", "", markdown, flags=re.I)
        markdown = re.sub(r"(?m)^\s*(Dang ky tu van lai thu|Dang ky tu van|Coc mua xe)\s*$", "", markdown, flags=re.I)
        return markdown.strip()

    def _best_title(self, soup: BeautifulSoup, fallback: str, url: str) -> str:
        for selector in ["h1", "meta[property='og:title']", "title"]:
            elem = soup.select_one(selector)
            if not elem:
                continue
            value = elem.get("content") if elem.name == "meta" else elem.get_text(" ", strip=True)
            value = (value or "").strip()
            if value:
                return re.sub(r"\s+", " ", value)
        return fallback or urlparse(url).path.rstrip("/").split("/")[-1].replace("-", " ").title()

    def _meta_content(self, soup: BeautifulSoup, prop: str) -> str:
        elem = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
        return elem.get("content", "").strip() if elem else ""

    def _find_news_category(self, soup: BeautifulSoup) -> str:
        for elem in soup.find_all(string=lambda t: t and re.search(r"(Báo chí|Chính sách|Sự kiện|Tin tức|Tin noi bat)", t, re.I)):
            text = re.sub(r"\s+", " ", str(elem)).strip()
            if 3 <= len(text) <= 40:
                return text
        return ""

    def _find_date_text(self, soup: BeautifulSoup) -> str:
        time_tag = soup.find("time")
        if time_tag:
            return time_tag.get("datetime") or time_tag.get_text(" ", strip=True)
        text = soup.get_text(" ", strip=True)
        match = re.search(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b", text)
        return match.group(0) if match else ""

    def _first_sentence(self, markdown: str) -> str:
        text = re.sub(r"[*_#`>|!\[\]\(\)]", " ", markdown)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:240]

    def _extract_news_cards(self, soup: BeautifulSoup, base_url: str) -> list[dict]:
        cards = []
        for link in soup.find_all("a", href=True):
            href = link["href"]
            absolute = urljoin(base_url, href)
            if "/vn-vi/news/" not in absolute:
                continue
            container = link
            for parent in link.parents:
                if not isinstance(parent, Tag):
                    continue
                text_len = len(parent.get_text(" ", strip=True))
                if text_len > 80:
                    container = parent
                    break
            title = link.get_text(" ", strip=True) or self._best_card_title(container)
            title = re.sub(r"\s+", " ", title).strip()
            if not title or len(title) < 8:
                continue
            img = container.find("img")
            image = ""
            if img:
                image = img.get("src") or img.get("data-src") or ""
                image = urljoin(base_url, image) if image else ""
            text = container.get_text(" ", strip=True)
            summary = text.replace(title, "", 1).strip()
            cards.append({
                "title": title[:180],
                "url": absolute,
                "summary": summary[:260],
                "image": image,
                "date": self._find_date_text(container),
                "category": self._find_news_category(container),
            })
        return cards

    def _extract_vehicle_cards(self, soup: BeautifulSoup, base_url: str) -> list[dict]:
        cards = []
        model_re = re.compile(r"\b(VF\s*6|VF\s*5|Herio|Limo|Minio|EC\s*Van|Evo(?:\s*Grand)?|Feliz\s*II|Viper)\b", re.I)
        for elem in soup.find_all(["section", "article", "div", "a"]):
            text = re.sub(r"\s+", " ", elem.get_text(" ", strip=True))
            model_match = model_re.search(text)
            if not model_match:
                continue
            name = re.sub(r"\s+", " ", model_match.group(1)).strip()
            price = self._extract_price(text)
            href = elem.get("href", "") if elem.name == "a" else ""
            link = elem.find("a", href=True)
            if not href and link:
                href = link["href"]
            img = elem.find("img")
            image = ""
            if img:
                image = img.get("src") or img.get("data-src") or ""
            cards.append({
                "name": name,
                "price": price,
                "mode": self._extract_order_mode(text),
                "url": urljoin(base_url, href) if href else "",
                "image": urljoin(base_url, image) if image else "",
            })

        deduped = []
        seen = set()
        for card in cards:
            marker = (card["name"].lower(), card.get("url") or card.get("price") or card.get("image"))
            if marker in seen:
                continue
            seen.add(marker)
            deduped.append(card)
        return deduped[:30]

    def _extract_images(self, node: Tag, base_url: str, limit: int = 8) -> list[str]:
        images = []
        seen = set()
        for img in node.find_all("img"):
            src = img.get("src") or img.get("data-src") or ""
            if not src:
                continue
            src = urljoin(base_url, src)
            alt = img.get("alt", "").strip()
            marker = src.split("?", 1)[0]
            if marker in seen:
                continue
            seen.add(marker)
            images.append(f"{alt}: {src}" if alt else src)
            if len(images) >= limit:
                break
        return images

    def _extract_price(self, text: str) -> str:
        match = re.search(r"(\d{1,3}(?:[.,]\d{3}){2,}(?:\s*VND|VNĐ|d|đ)?)", text, re.I)
        return match.group(1).strip() if match else ""

    def _extract_order_mode(self, text: str) -> str:
        modes = []
        if re.search(r"\bmua\b|gia ban|coc mua", text, re.I):
            modes.append("Mua")
        if re.search(r"\bthue\b|so huu de dang|chia se doanh thu", text, re.I):
            modes.append("Thue/van doanh")
        return ", ".join(modes)

    def _extract_vehicle_specs(self, text: str) -> list[tuple[str, str]]:
        patterns = [
            ("Dong co", r"Dong co\s+([^|]{2,80})"),
            ("Cong suat toi da", r"Cong suat toi da\s+([^|]{2,80})"),
            ("Quang duong", r"Quang duong[^0-9]{0,40}([0-9.,]+\s*km[^|]{0,60})"),
            ("Cong suat sac", r"Cong suat sac[^0-9]{0,40}([0-9.,]+\s*kW[^|]{0,60})"),
            ("Mam sanh cuc dai", r"Mam sanh[^0-9]{0,40}([0-9.,]+\s*inch[^|]{0,40})"),
            ("Kich thuoc la-zang", r"Kich thuoc la-?zang[^0-9]{0,40}([0-9.,]+\s*inch[^|]{0,40})"),
            ("Dung luong pin", r"Dung luong pin[^0-9]{0,40}([0-9.,]+\s*kWh[^|]{0,40})"),
            ("Thoi gian sac", r"Thoi gian sac[^0-9]{0,40}([0-9.,]+\s*phut[^|]{0,80})"),
        ]
        specs = []
        for label, pattern in patterns:
            match = re.search(pattern, text, re.I)
            if match:
                specs.append((label, match.group(1).strip()))
        return specs

    def _best_card_title(self, container: Tag) -> str:
        heading = container.find(["h1", "h2", "h3", "h4"])
        return heading.get_text(" ", strip=True) if heading else container.get_text(" ", strip=True)[:120]

    def _absolutize_images(self, soup: BeautifulSoup, base_url: str) -> None:
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src:
                img["src"] = urljoin(base_url, src)

    def _load_next_data(self, soup: BeautifulSoup) -> Any:
        script = soup.find("script", id="__NEXT_DATA__")
        if not script or not script.string:
            return None
        try:
            return json.loads(script.string)
        except json.JSONDecodeError:
            return None

    def _extract_next_text(self, data: Any) -> str:
        if not data:
            return ""
        lines: list[str] = []

        def visit(node: Any, key: str = "") -> None:
            if isinstance(node, dict):
                if "rows" in node and isinstance(node["rows"], list):
                    table = self._table_from_rows(node)
                    if table:
                        lines.append(table)
                for child_key, value in node.items():
                    if child_key.lower() in {"html", "description", "content", "title", "name", "label", "value", "summary"}:
                        self._append_text(lines, value)
                    elif isinstance(value, (dict, list)):
                        visit(value, child_key)
            elif isinstance(node, list):
                for item in node:
                    visit(item, key)
            elif isinstance(node, str):
                self._append_text(lines, node)

        visit(data)
        deduped = []
        seen = set()
        for line in lines:
            clean = self._clean_markdown(line)
            marker = clean[:180]
            if clean and marker not in seen:
                seen.add(marker)
                deduped.append(clean)
        return "\n\n".join(deduped)

    def _append_text(self, lines: list[str], value: Any) -> None:
        if not isinstance(value, str):
            return
        value = value.strip()
        if len(value) < 20:
            return
        if "<" in value and ">" in value:
            value = markdownify.markdownify(value, heading_style="ATX", bullets="-", strip=["a"])
        lines.append(value)

    def _table_from_rows(self, node: dict) -> str:
        rows = node.get("rows") or []
        if not rows:
            return ""
        if rows and isinstance(rows[0], dict) and "items" in rows[0]:
            parts = []
            for group in rows:
                city = group.get("city") or group.get("title") or group.get("name")
                if city:
                    parts.append(f"### {city}")
                parts.append(self._table_from_rows({"rows": group.get("items", [])}))
            return "\n\n".join(part for part in parts if part)

        keys = []
        for row in rows:
            if isinstance(row, dict):
                for key in row:
                    if key not in keys and not isinstance(row.get(key), (dict, list)):
                        keys.append(key)
        if not keys:
            return ""
        header = "| " + " | ".join(keys) + " |"
        sep = "|" + "|".join(["---"] * len(keys)) + "|"
        body = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            body.append("| " + " | ".join(str(row.get(key, "")).replace("\n", " ").strip() for key in keys) + " |")
        return "\n".join([header, sep, *body])

    def _platform_doc_type(self, url: str, fallback: str) -> str:
        lower = url.lower()
        path = re.sub(r"/+$", "", lower.split("?", 1)[0])
        if "/news/" in lower:
            return "news_list" if "/news/all/page/" in lower or path.endswith("/news") else "news"
        if path.endswith("/vn-vi"):
            return "platform_overview"
        if self._looks_like_vehicle_url(url):
            return "vehicle"
        return fallback or "platform_page"

    def _looks_like_vehicle_url(self, url: str) -> bool:
        lower = url.lower()
        terms = [
            "order_type", "order-type", "model", "vf", "limo", "herio", "minio",
            "ec-van", "ec_van", "evo", "feliz", "feliz2", "viper", "bike", "car",
        ]
        return any(term in lower for term in terms)
