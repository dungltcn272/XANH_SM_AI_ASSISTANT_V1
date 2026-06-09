import json
import re
import unicodedata
from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import markdownify
import requests
from bs4 import BeautifulSoup, Tag

try:
    from markdown_converter import MarkdownConverter
except ImportError:
    from .markdown_converter import MarkdownConverter


JUNK_CLASS_RE = re.compile(
    r"(header|footer|nav|menu|sidebar|breadcrumb|social|share|pagination|"
    r"modal|popup|floating|hotline|zalo|contact|form|button|register|"
    r"download|app|related|recent|suggested|comment|author|tag|category)",
    re.IGNORECASE,
)

VEHICLE_STATIC_BASE = "https://platform-static.car-trading.gsm-api.net/public"
VEHICLE_PRODUCT_API = "https://admin.car-trading.gsm-api.net/public/api/v1/masterdata/products?filters[country_code]=VN&sort=-created_at"
VEHICLE_PRICE_CONFIG_API = "https://admin.car-trading.gsm-api.net/public/api/v1/masterdata/price-configs?sort=price"

VEHICLE_SPEC_LABELS = {
    "productInfo.dimensions": "Dài x Rộng x Cao (mm)",
    "productInfo.dimensionsValue": "Dài x Rộng x Cao (mm)",
    "productInfo.wheelbase": "Chiều dài cơ sở (mm)",
    "productInfo.wheelbaseValue": "Chiều dài cơ sở (mm)",
    "productInfo.range": "Quãng đường chạy một lần sạc đầy (km) - NEDC",
    "productInfo.rangeFullCharge": "Quãng đường chạy một lần sạc đầy (km) - NEDC",
    "productInfo.rangeFullChargeValue": "Quãng đường chạy một lần sạc đầy (km) - NEDC",
    "productInfo.maxPower": "Công suất tối đa (kW)",
    "productInfo.maxPowerValue": "Công suất tối đa (kW)",
    "productInfo.maxTorque": "Mô men xoắn cực đại (Nm)",
    "productInfo.maxTorqueValue": "Mô men xoắn cực đại (Nm)",
    "productInfo.drivetrain": "Hệ dẫn động",
    "productInfo.drivetrainValue": "Hệ dẫn động",
    "productInfo.fastChargeTime": "Thời gian nạp pin nhanh nhất",
    "productInfo.fastChargingTime": "Thời gian nạp pin nhanh nhất",
    "productInfo.fastChargingTimeValue": "Thời gian nạp pin nhanh nhất",
    "productInfo.batteryCapacity": "Dung lượng pin (kWh) - khả dụng",
    "productInfo.dcFastChargingPower": "Công suất sạc nhanh DC",
    "productInfo.dcFastChargingPowerValue": "Công suất sạc nhanh DC",
    "productInfo.luggageVolume": "Thể tích khoang chứa hàng",
    "productInfo.luggageVolumeValue": "Thể tích khoang chứa hàng",
    "productInfo.brakeSystem": "Hệ thống phanh",
    "productInfo.brakeSystemValue": "Hệ thống phanh",
    "productInfoAdvanced.maxTorque": "Mô men xoắn cực đại (Nm)",
    "productInfoAdvanced.wheel_type": "Kích thước la-zăng",
    "productInfoAdvanced.fastChargeTime": "Thời gian nạp pin nhanh nhất",
    "productInfoAdvanced.batteryCapacity": "Dung lượng pin (kWh) - khả dụng",
}


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
        self._http = requests.Session()
        self._http.headers.update({"User-Agent": "Mozilla/5.0"})
        self._vehicle_products_cache: list[dict] | None = None
        self._vehicle_price_configs_cache: list[dict] | None = None
        self._vehicle_js_text_cache: dict[str, str] = {}
        self._script_text_cache: dict[str, str] = {}

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
                return self.clean_vehicle_page(html, title, url, category=category)
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
        self._absolutize_urls(soup, url)

        page_title = self._best_title(soup, title, url)
        category = self._meta_content(soup, "article:section") or self._find_news_category(soup)
        date = self._meta_content(soup, "article:published_time") or self._find_date_text(soup)

        article = self._select_main_content(soup, selectors=["article", "main", "[class*='detail']", "[class*='content']"])
        markdown = self._markdownify(article)

        next_text = self._extract_next_text(next_data, url)
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
        self._absolutize_urls(soup, url)

        page_title = self._best_title(soup, title, url)
        content = self._select_main_content(soup, selectors=["main", "article", "[class*='page']", "[class*='content']"])
        markdown = self._markdownify(content)

        dynamic_md = self._extract_next_text(next_data, url)
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
        self._absolutize_urls(soup, url)

        page_title = self._best_title(soup, title, url) or "Green SM Platform"
        content = self._select_main_content(soup, selectors=["main", "body"])
        markdown = self._markdownify(content)
        dynamic_md = self._extract_next_text(next_data, url)
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

    def clean_vehicle_page(self, html: str, title: str, url: str, category: str = "") -> CleanedDocument:
        soup = BeautifulSoup(html, "html.parser")
        next_data = self._load_next_data(soup)
        vehicle_kind = self._vehicle_kind_from_category(category)
        rich = self._extract_vehicle_rich_data(html, url, next_data, vehicle_kind=vehicle_kind)
        self._remove_junk(soup)
        self._absolutize_urls(soup, url)

        page_title = rich.get("title") or self._best_title(soup, title, url)
        content = self._select_main_content(soup, selectors=["main", "article", "body"])
        markdown = self._markdownify(content)
        dynamic_md = self._extract_next_text(next_data, url)
        if len(dynamic_md) > len(markdown) * 1.15:
            markdown = dynamic_md
        markdown = self._filter_vehicle_detail_markdown(markdown, page_title)

        flat_text = re.sub(r"\s+", " ", content.get_text(" ", strip=True))
        price = rich.get("price") or self._extract_price(flat_text)
        specs = rich.get("specs") or self._extract_vehicle_specs(flat_text)
        images = rich.get("images") or self._extract_images(content, url, limit=12)
        highlights = rich.get("highlights") or []

        parts = [
            f"# {page_title}",
            "",
            "## Thông tin xe",
            f"- URL: {url}",
            "- Loại tài liệu: vehicle",
        ]
        if price:
            parts.append(f"- Giá hiển thị: {price}")
        if vehicle_kind:
            parts.append(f"- Nhom xe: {vehicle_kind}")
        if rich.get("versions"):
            parts.append(f"- Phiên bản: {', '.join(rich['versions'])}")
        if images:
            parts.extend(["", "## Hình ảnh xe và màu sắc"])
            for image in images:
                parts.append(f"- {image}")
        if specs:
            parts.extend(["", "## Thông số kỹ thuật"])
            if isinstance(specs[0], dict):
                parts.extend([
                    "| Thông số | Phiên bản | Giá trị |",
                    "|---|---|---|",
                ])
                for spec in specs:
                    parts.append(f"| {spec['label']} | {spec.get('version') or 'Chung'} | {spec['value']} |")
            else:
                for key, value in specs:
                    parts.append(f"- {key}: {value}")
        if highlights:
            parts.extend(["", "## Nội dung nổi bật"])
            parts.extend(f"- {item}" for item in highlights)
        parts.extend(["", "## Nội dung chi tiết", "", markdown])

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
            if not isinstance(elem, Tag) or elem.attrs is None:
                continue
            classes_value = elem.get("class") or []
            if isinstance(classes_value, str):
                classes_value = [classes_value]
            classes = " ".join(classes_value)
            elem_id = elem.get("id", "")
            role = elem.get("role", "")
            text_key = " ".join([classes, elem_id, role])
            if text_key and JUNK_CLASS_RE.search(text_key):
                elem.decompose()

        for text in soup.find_all(string=lambda t: t and re.search(r"(Hotline|Zalo chat|Dang ky tu van|Tai ung dung|Bài viết gần đây|Tin tức liên quan|Xem thêm|Có thể bạn quan tâm)", t, re.I)):
            parent = getattr(text, 'parent', None)
            if parent:
                # Find the highest container that is still "junk"
                # usually a section or a div that wraps the header and its list
                curr = parent
                to_decompose = parent
                depth = 0
                while curr and getattr(curr, 'name', None) not in {"main", "article", "body", "html"} and depth < 4:
                    # If we find a section or a div with many siblings, maybe it's the right container
                    if getattr(curr, 'name', None) in {"section", "aside", "div"}:
                        to_decompose = curr
                    curr = getattr(curr, 'parent', None)
                    depth += 1
                
                if to_decompose and getattr(to_decompose, 'name', None) not in {"body", "html"}:
                    try:
                        to_decompose.decompose()
                    except Exception:
                        pass

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

    def _extract_vehicle_rich_data(self, html: str, url: str, next_data: Any = None, vehicle_kind: str = "") -> dict:
        slug = self._vehicle_slug(url)
        data: dict[str, Any] = {
            "title": "",
            "price": "",
            "versions": [],
            "images": [],
            "specs": [],
            "highlights": [],
        }
        if not slug:
            return data

        product = self._fetch_vehicle_product(slug)
        if product:
            data["title"] = product.get("name") or ""
            data["versions"] = self._product_versions(product)
            data["images"].extend(self._product_images(product))
            data["price"] = self._fetch_vehicle_price(product, url, vehicle_kind=vehicle_kind)

        js_text = self._fetch_vehicle_js_text(html, url, slug)
        if js_text:
            data["images"].extend(self._extract_vehicle_asset_images(js_text, slug))
            if self._is_bike_vehicle(slug, vehicle_kind):
                data["specs"].extend(self._extract_motorbike_js_specs(js_text, slug, next_data))
            else:
                data["specs"].extend(self._extract_vehicle_js_specs(js_text))
        if next_data:
            if self._is_bike_vehicle(slug, vehicle_kind):
                data["specs"].extend(self._extract_motorbike_message_specs(next_data, slug))
            else:
                data["specs"].extend(self._extract_vehicle_message_specs(next_data, slug))

        data["images"] = self._dedupe_lines(data["images"])[:40]
        data["specs"] = self._dedupe_specs(data["specs"])
        data["highlights"] = self._extract_vehicle_highlights(html, slug)
        return data

    def _vehicle_slug(self, url: str) -> str:
        lower = url.lower()
        path = urlparse(lower).path.rstrip("/").split("/")[-1]
        aliases = {
            "ec-van": "ec_van",
            "ec_van": "ec_van",
            "herio_green": "herio_green",
            "minio_green": "minio_green",
            "limo_green": "limo_green",
            "vf6": "vf6",
            "vf5": "vf5",
            "vf3": "vf3",
            "evo_grand": "evo_grand",
            "feliz2": "feliz2",
            "feliz": "feliz",
            "vero-x": "vero-x",
            "viper": "viper",
            "evo": "evo",
        }
        for key, slug in aliases.items():
            if key in lower:
                return slug
        return path.replace("-", "_")

    def _fetch_vehicle_product(self, slug: str) -> dict:
        items = self._fetch_vehicle_products()
        if not items:
            return {}

        target = self._normalize_vehicle_key(slug)
        for item in items:
            if not isinstance(item, dict):
                continue
            candidates = [
                item.get("slug"),
                item.get("code"),
                item.get("name"),
            ]
            if any(self._normalize_vehicle_key(str(candidate or "")) == target for candidate in candidates):
                return item
        for item in items:
            text = " ".join(str(item.get(key) or "") for key in ("slug", "code", "name"))
            if target and target in self._normalize_vehicle_key(text):
                return item
        return {}

    def _fetch_vehicle_products(self) -> list[dict]:
        if self._vehicle_products_cache is not None:
            return self._vehicle_products_cache
        try:
            resp = self._http.get(VEHICLE_PRODUCT_API, timeout=15)
            resp.raise_for_status()
            items = resp.json().get("items") or []
            self._vehicle_products_cache = [item for item in items if isinstance(item, dict)]
        except Exception:
            self._vehicle_products_cache = []
        return self._vehicle_products_cache

    def _normalize_vehicle_key(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", value.lower())

    def _product_images(self, product: dict) -> list[str]:
        images: list[str] = []
        for label, key in [
            ("thumbnail", "thumbnail"),
            ("cover", "cover_image"),
            ("background", "background_image"),
        ]:
            for url in self._split_asset_values(product.get(key)):
                images.append(f"{label}: {url}")

        for color in product.get("colors") or []:
            if not isinstance(color, dict):
                continue
            color_name = color.get("name") or color.get("code") or "Mau xe"
            color_type = color.get("type") or "color"
            for key in ["images", "cover_images"]:
                for url in self._split_asset_values(color.get(key)):
                    images.append(f"{color_type} - {color_name}: {url}")
        return images

    def _product_versions(self, product: dict) -> list[str]:
        versions = product.get("versions")
        if not versions:
            return []
        if isinstance(versions, dict):
            versions = versions.values()
        elif isinstance(versions, str):
            versions = [versions]
        elif not isinstance(versions, list):
            return []

        names = []
        for version in versions:
            if isinstance(version, dict):
                name = version.get("name") or version.get("code")
            else:
                name = version
            name = str(name or "").strip()
            if name:
                names.append(name)
        return self._dedupe_lines(names)

    def _fetch_vehicle_price(self, product: dict, url: str, vehicle_kind: str = "") -> str:
        model = str(product.get("code") or "").strip()
        if not model:
            return ""
        order_type = "rent" if "order-type=rent" in url.lower() or "order_type=rent" in url.lower() else "buy"
        items = self._fetch_vehicle_price_configs()
        if not items:
            return ""

        rows = []
        for item in items:
            if not isinstance(item, dict):
                continue
            if str(item.get("Model") or "").lower() != model.lower():
                continue
            if str(item.get("Country") or "").upper() != "VN":
                continue
            if str(item.get("Type") or "").lower() != order_type:
                continue
            if item.get("Color"):
                continue
            amount = item.get("RentalPrice") if order_type == "rent" else item.get("Price")
            if not amount:
                continue
            version = str(item.get("Version") or "").strip()
            label = self._vehicle_price_label(item, version, vehicle_kind, order_type)
            rows.append((label, int(amount)))
        if not rows:
            return ""
        rows.sort(key=lambda row: row[0].lower())
        return "; ".join(f"{label}: {self._format_vnd(amount)}" for label, amount in rows)

    def _vehicle_price_label(self, item: dict, version: str, vehicle_kind: str, order_type: str) -> str:
        if vehicle_kind == "bike":
            if item.get("BatteryIncluded") is True:
                label = "Kem pin"
            elif item.get("BatteryIncluded") is False:
                label = "Khong kem pin"
            else:
                label = "Gia"
            if order_type == "rent":
                unit = str(item.get("RentalUnit") or "").strip()
                label = f"{label} - gia thue" + (f"/{unit}" if unit else "")
            return label
        return version.title() if version else "Gia"

    def _fetch_vehicle_price_configs(self) -> list[dict]:
        if self._vehicle_price_configs_cache is not None:
            return self._vehicle_price_configs_cache
        try:
            resp = self._http.get(VEHICLE_PRICE_CONFIG_API, timeout=15)
            resp.raise_for_status()
            items = resp.json().get("items") or []
            self._vehicle_price_configs_cache = [item for item in items if isinstance(item, dict)]
        except Exception:
            self._vehicle_price_configs_cache = []
        return self._vehicle_price_configs_cache

    def _format_vnd(self, amount: int) -> str:
        return f"{amount:,}".replace(",", ".") + " VND"

    def _split_asset_values(self, value: Any) -> list[str]:
        if not value:
            return []
        raw_items: list[str] = []
        if isinstance(value, list):
            for item in value:
                raw_items.extend(str(item).split(","))
        else:
            raw_items.extend(str(value).split(","))

        urls = []
        for item in raw_items:
            item = item.strip().strip('"').strip("'")
            if not item:
                continue
            urls.append(self._vehicle_asset_url(item))
        return urls

    def _vehicle_asset_url(self, path: str) -> str:
        if path.startswith("url("):
            match = re.search(r"url\((.*?)\)", path)
            path = match.group(1).strip("'\" ") if match else path
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = "/" + path
        return VEHICLE_STATIC_BASE + path

    def _fetch_vehicle_js_text(self, html: str, url: str, slug: str) -> str:
        if slug in self._vehicle_js_text_cache:
            return self._vehicle_js_text_cache[slug]
        script_urls = re.findall(r'<script[^>]+src=["\']([^"\']+\.js(?:\?[^"\']*)?)["\']', html)
        chunks: list[str] = []
        aliases = self._vehicle_asset_aliases(slug)
        for script_url in script_urls[:80]:
            absolute = urljoin(url, script_url)
            try:
                if absolute in self._script_text_cache:
                    text = self._script_text_cache[absolute]
                else:
                    resp = self._http.get(absolute, timeout=15)
                    if not resp.ok:
                        continue
                    text = resp.text
                    self._script_text_cache[absolute] = text
            except Exception:
                continue
            lower = text.lower()
            if any(alias in lower or f"/product/{alias}" in lower for alias in aliases):
                chunks.append(text)
        js_text = "\n".join(chunks)
        self._vehicle_js_text_cache[slug] = js_text
        return js_text

    def _extract_vehicle_asset_images(self, js_text: str, slug: str) -> list[str]:
        slug_patterns = set(self._vehicle_asset_aliases(slug))
        images = []
        for slug_pattern in slug_patterns:
            pattern = rf'["\'](/product/{re.escape(slug_pattern)}[^"\']+\.(?:png|jpe?g|webp))(?:\?[^"\']*)?["\']'
            for match in re.finditer(pattern, js_text, re.I):
                path = match.group(1)
                label = "asset"
                if "/header-banner/" in path:
                    label = "hero"
                elif "/sec" in path:
                    label = "section"
                elif "/order/" in path:
                    label = "color"
                images.append(f"{label}: {self._vehicle_asset_url(path)}")
        return images

    def _vehicle_asset_aliases(self, slug: str) -> list[str]:
        aliases = {
            "herio_green": ["herio_green", "heriogreen", "herio"],
            "minio_green": ["minio_green", "miniogreen", "minio"],
            "limo_green": ["limo_green", "limogreen", "limo"],
            "ec_van": ["ec_van", "ecvan", "van"],
            "evo_grand": ["evo_grand", "evogrand"],
            "vero-x": ["vero-x", "verox"],
        }
        values = aliases.get(slug, [slug, slug.replace("_", "-"), slug.replace("_", "")])
        return list(dict.fromkeys(value.lower() for value in values if value))

    def _is_motorbike_slug(self, slug: str) -> bool:
        return slug in {"evo", "feliz2", "feliz", "evo_grand", "vero-x", "viper"}

    def _vehicle_kind_from_category(self, category: str) -> str:
        normalized = (category or "").strip().lower().replace("_", "-")
        if normalized == "vehicle-bike":
            return "bike"
        if normalized == "vehicle-car":
            return "car"
        return ""

    def _is_bike_vehicle(self, slug: str, vehicle_kind: str = "") -> bool:
        if vehicle_kind:
            return vehicle_kind == "bike"
        return self._is_motorbike_slug(slug)

    def _extract_motorbike_message_specs(self, data: Any, slug: str) -> list[dict]:
        messages = self._find_vehicle_messages(data, slug)
        spec = messages.get("spec") if isinstance(messages, dict) else None
        if not isinstance(spec, dict):
            return []

        rows: list[dict] = []
        titles = spec.get("title")
        values = spec.get("value")
        if isinstance(titles, list) and isinstance(values, list):
            for label, value in zip(titles, values):
                self._append_motorbike_spec(rows, label, value)
            return rows

        indexes = sorted({
            int(match.group(1))
            for key in spec
            if (match := re.fullmatch(r"label(\d+)", str(key)))
        })
        for index in indexes:
            self._append_motorbike_spec(rows, spec.get(f"label{index}"), spec.get(f"value{index}"))
        return rows

    def _extract_motorbike_js_specs(self, js_text: str, slug: str, next_data: Any = None) -> list[dict]:
        rows: list[dict] = []
        label_map = self._motorbike_spec_label_map(next_data, slug)
        model_key = self._vehicle_message_key(slug)
        model_pattern = re.escape(model_key)

        for match in re.finditer(r"data:\[(.*?)\]\s*,[^{}]*(?:model:[^,})]*" + model_pattern + r"|priceDescription)", js_text, re.S):
            self._extract_motorbike_js_specs_from_array(match.group(1), rows, label_map)
        if not rows:
            for match in re.finditer(r"data:\[(.*?)\]", js_text, re.S):
                array_text = match.group(1)
                if "spec." in array_text or "label:" in array_text:
                    self._extract_motorbike_js_specs_from_array(array_text, rows, label_map)
        return rows

    def _extract_motorbike_js_specs_from_array(self, array_text: str, rows: list[dict], label_map: dict[str, str]) -> None:
        pattern = re.compile(
            r"label:(?:\w+\(\"spec\.([^\"]+)\"\)|\"((?:\\.|[^\"])*)\"),value:\"((?:\\.|[^\"])*)\"",
            re.S,
        )
        for key, raw_label, raw_value in pattern.findall(array_text):
            label = label_map.get(key) if key else self._decode_js_string(raw_label)
            value = self._decode_js_string(raw_value)
            self._append_motorbike_spec(rows, label, value)

    def _motorbike_spec_label_map(self, data: Any, slug: str) -> dict[str, str]:
        messages = self._find_vehicle_messages(data, slug)
        spec = messages.get("spec") if isinstance(messages, dict) else None
        if not isinstance(spec, dict):
            return {}
        return {
            str(key): str(value).strip()
            for key, value in spec.items()
            if isinstance(value, str) and value.strip()
        }

    def _append_motorbike_spec(self, rows: list[dict], label: Any, value: Any) -> None:
        label = str(label or "").strip()
        value = str(value or "").strip()
        if not label or not value or label == "$undefined" or value == "$undefined":
            return
        rows.append({
            "label": label,
            "version": "Chung",
            "value": re.sub(r"\s+", " ", value),
        })

    def _decode_js_string(self, value: str) -> str:
        try:
            return json.loads(f'"{value}"')
        except Exception:
            return value.replace(r"\/", "/").replace(r"\"", '"').replace(r"\n", "\n")

    def _extract_vehicle_js_specs(self, js_text: str) -> list[dict]:
        specs = []
        patterns = [
            r'(?:title|label):\w+\("([^"]+)"\),value:\w+\("([^"]+)","([^"]*)"\)',
            r'(?:title|label):\w+\("([^"]+)"\),value:\w+\("([^"]+)",\{defaultValue:"([^"]*)"\}\)',
        ]
        for pattern in patterns:
            for label_key, value_key, value in re.findall(pattern, js_text):
                label = VEHICLE_SPEC_LABELS.get(label_key)
                if not label or not value:
                    continue
                specs.append({
                    "label": label,
                    "version": self._spec_version(value_key),
                    "value": value.strip(),
                })
        return specs

    def _extract_vehicle_message_specs(self, data: Any, slug: str) -> list[dict]:
        specs = []
        message_dicts: list[dict] = []
        vehicle_key = self._vehicle_message_key(slug)

        def collect_vehicle_messages(node: Any, key: str = "") -> None:
            if isinstance(node, dict):
                if key == "messages" and vehicle_key and isinstance(node.get(vehicle_key), dict):
                    visit_product_info(node[vehicle_key])
                    return
                for child_key, child in node.items():
                    if isinstance(child, (dict, list)):
                        collect_vehicle_messages(child, child_key)
            elif isinstance(node, list):
                for child in node:
                    collect_vehicle_messages(child, key)

        def visit_product_info(node: Any, key: str = "") -> None:
            if isinstance(node, dict):
                if key == "productInfo":
                    message_dicts.append(node)
                for child_key, child in node.items():
                    if isinstance(child, (dict, list)):
                        visit_product_info(child, child_key)
            elif isinstance(node, list):
                for child in node:
                    visit_product_info(child, key)

        collect_vehicle_messages(data)
        if vehicle_key and not message_dicts:
            return []
        if not message_dicts:
            visit_product_info(data)
        for info in message_dicts:
            for key, value in info.items():
                label = VEHICLE_SPEC_LABELS.get(f"productInfo.{key}")
                if not label or not isinstance(value, str):
                    continue
                if key.endswith("Value") or re.search(r"\d", value):
                    specs.append({
                        "label": label,
                        "version": "Chung",
                        "value": value.strip(),
                    })
        return specs

    def _find_vehicle_messages(self, data: Any, slug: str) -> dict:
        vehicle_key = self._vehicle_message_key(slug)

        def visit(node: Any, key: str = "") -> dict:
            if isinstance(node, dict):
                if key == "messages" and isinstance(node.get(vehicle_key), dict):
                    return node[vehicle_key]
                for child_key, child in node.items():
                    if isinstance(child, (dict, list)):
                        result = visit(child, child_key)
                        if result:
                            return result
            elif isinstance(node, list):
                for child in node:
                    result = visit(child, key)
                    if result:
                        return result
            return {}

        return visit(data)

    def _vehicle_message_key(self, slug: str) -> str:
        return {
            "ec_van": "van",
            "herio_green": "HerioGreen",
            "minio_green": "minio",
            "limo_green": "LimoGreen",
            "evo_grand": "EVOGRAND",
            "feliz2": "FELIZ_II",
            "feliz": "FELIZ2025",
            "vero-x": "VEROX",
            "vf6": "vf6",
            "vf5": "vf5",
            "vf3": "vf3",
            "evo": "EVO",
            "viper": "Viper",
        }.get(slug, slug)

    def _spec_version(self, value_key: str) -> str:
        key = value_key.lower()
        if key.endswith("_eco") or "_eco_" in key:
            return "Eco"
        if key.endswith("_plus") or "_plus_" in key:
            return "Plus"
        return "Chung"

    def _dedupe_lines(self, lines: list[str]) -> list[str]:
        deduped = []
        seen = set()
        for line in lines:
            marker = re.sub(r"\?.*$", "", line.strip())
            if not marker or marker in seen:
                continue
            seen.add(marker)
            deduped.append(line.strip())
        return deduped

    def _dedupe_specs(self, specs: list[dict]) -> list[dict]:
        deduped = []
        seen = set()
        for spec in specs:
            marker = (spec.get("label"), spec.get("version"), spec.get("value"))
            if marker in seen:
                continue
            seen.add(marker)
            deduped.append(spec)
        return deduped

    def _extract_vehicle_highlights(self, html: str, slug: str) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        next_text = self._extract_next_text(self._load_next_data(soup), slug)
        highlights = []
        for block in re.split(r"\n{2,}", next_text):
            text = re.sub(r"\s+", " ", block).strip()
            if not self._is_vehicle_content_block(text, slug):
                continue
            highlights.append(text)
        return self._dedupe_lines(highlights)[:8]

    def _filter_vehicle_detail_markdown(self, markdown: str, title: str) -> str:
        blocks = []
        slug = self._normalize_vehicle_key(title)
        for block in re.split(r"\n{2,}", markdown):
            text = re.sub(r"\s+", " ", block).strip()
            if self._is_vehicle_content_block(text, slug):
                blocks.append(text)
        return "\n\n".join(self._dedupe_lines(blocks))

    def _is_vehicle_content_block(self, text: str, slug: str) -> bool:
        if len(text) < 35 or len(text) > 420:
            return False
        folded = self._fold_text(text)
        normalized_slug = self._normalize_vehicle_key(slug)
        if text.startswith("http") or "platform-static.car-trading" in text:
            return False
        junk_terms = [
            "du toan", "dang ky", "coc mua", "tai ngay", "hotline", "footer",
            "chinh sach", "tin tuc", "uu dai hap dan", "so huu xe", "ra mat",
            "xem them", "thu nhap", "doanh so", "tai xe xanh", "xanh platform",
            "doi tac dong hanh", "mien phi sac", "dat coc", "tai chinh linh hoat",
            "mua xe may dien",
        ]
        if any(term in folded for term in junk_terms):
            return False
        vehicle_terms = [
            normalized_slug,
            normalized_slug.replace("green", ""),
            "thiet ke",
            "noi that",
            "van hanh",
            "dong co",
            "kich thuoc",
            "mau sac",
            "thong so ky thuat",
            "quang duong",
            "cong suat",
        ]
        vehicle_terms = [term for term in vehicle_terms if len(term) >= 3]
        return any(term in folded or term in self._normalize_vehicle_key(text) for term in vehicle_terms)

    def _fold_text(self, value: str) -> str:
        value = value.replace("đ", "d").replace("Đ", "D")
        value = unicodedata.normalize("NFKD", value)
        value = "".join(ch for ch in value if not unicodedata.combining(ch))
        return re.sub(r"\s+", " ", value.lower()).strip()

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

    def _absolutize_urls(self, soup: BeautifulSoup, base_url: str) -> None:
        for link in soup.find_all(["a", "link"]):
            href = link.get("href")
            if href:
                link["href"] = urljoin(base_url, href.strip())

        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src:
                img["src"] = urljoin(base_url, src.strip())
            srcset = img.get("srcset")
            if srcset:
                img["srcset"] = self._absolutize_srcset(srcset, base_url)

        for source in soup.find_all("source"):
            src = source.get("src")
            if src:
                source["src"] = urljoin(base_url, src.strip())
            srcset = source.get("srcset")
            if srcset:
                source["srcset"] = self._absolutize_srcset(srcset, base_url)

    def _absolutize_srcset(self, srcset: str, base_url: str) -> str:
        parts = []
        for item in srcset.split(","):
            bits = item.strip().split()
            if not bits:
                continue
            bits[0] = urljoin(base_url, bits[0])
            parts.append(" ".join(bits))
        return ", ".join(parts)

    def _load_next_data(self, soup: BeautifulSoup) -> Any:
        script = soup.find("script", id="__NEXT_DATA__")
        if script and script.string:
            try:
                return json.loads(script.string)
            except json.JSONDecodeError:
                pass

        # Fallback to Next.js App Router RSC payload
        html = str(soup)
        pushes = re.findall(r'self\.__next_f\.push\(\[\d+,\s*"(.*?)"\]\)', html, flags=re.DOTALL)
        if pushes:
            full_payload = ""
            for p in pushes:
                try:
                    full_payload += json.loads(f'"{p}"')
                except Exception:
                    pass
            parsed_data = []
            for line in full_payload.split('\n'):
                parts = line.split(':', 1)
                if len(parts) == 2:
                    data_str = parts[1]
                    if data_str.startswith('[') or data_str.startswith('{'):
                        try:
                            parsed_data.append(json.loads(data_str))
                        except json.JSONDecodeError:
                            pass
            if parsed_data:
                return parsed_data

        return None


    def _extract_next_text(self, data: Any, url: str = "") -> str:
        if not data:
            return ""
        lines: list[str] = []
        key_blacklist = {"newestposts", "relatedposts", "sidebar", "footer", "header", "menu", "nav"}

        # Define all known vehicle keys in the messages dict
        all_vehicles = {"EVO", "EVOGRAND", "FELIZ2025", "FELIZ_II", "HerioGreen", "LimoGreen", "NerioGreen", "VEROX", "minio", "van", "vf3", "vf5", "vf6"}
        
        # Determine the current vehicle key from the URL
        current_vehicle = None
        lower_url = url.lower()
        if "vf6" in lower_url: current_vehicle = "vf6"
        elif "vf5" in lower_url: current_vehicle = "vf5"
        elif "vf3" in lower_url: current_vehicle = "vf3"
        elif "ec_van" in lower_url: current_vehicle = "van"
        elif "herio" in lower_url: current_vehicle = "HerioGreen"
        elif "minio" in lower_url: current_vehicle = "minio"
        elif "limo" in lower_url: current_vehicle = "LimoGreen"
        elif "feliz2" in lower_url: current_vehicle = "FELIZ_II"
        elif "feliz" in lower_url: current_vehicle = "FELIZ2025"
        elif "evo_grand" in lower_url: current_vehicle = "EVOGRAND"
        elif "evo" in lower_url: current_vehicle = "EVO"

        def visit(node: Any, key: str = "") -> None:
            if isinstance(node, dict):
                if key.lower() in key_blacklist:
                    return
                
                # If we are in the 'messages' dict, filter out other vehicles
                if key == "messages" and current_vehicle:
                    filtered_node = {}
                    for k, v in node.items():
                        if k in all_vehicles:
                            if k == current_vehicle:
                                filtered_node[k] = v
                        else:
                            filtered_node[k] = v
                    node = filtered_node

                if "rows" in node and isinstance(node["rows"], list):
                    table = self._table_from_rows(node)
                    if table:
                        lines.append(table)
                for child_key, value in node.items():
                    if isinstance(value, str):
                        if "__PAGE__" in value or "initial-scale" in value or value.startswith("width=") or value.startswith("viewport-fit="):
                            continue
                        if child_key.lower() in {"html", "description", "content", "title", "name", "label", "value", "summary"}:
                            self._append_text(lines, value)
                    elif isinstance(value, (dict, list)):
                        visit(value, child_key)
            elif isinstance(node, list):
                for item in node:
                    visit(item, key)
            elif isinstance(node, str):
                if "__PAGE__" in node or "initial-scale" in node or node.startswith("width=") or node.startswith("viewport-fit="):
                    return
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

        # Filter and sort keys
        all_keys = []
        for row in rows:
            if isinstance(row, dict):
                for key in row:
                    if key not in all_keys and not isinstance(row.get(key), (dict, list)):
                        all_keys.append(key)
        
        # Keep only value* keys or known content keys, exclude junk
        junk_keys = {"id", "_id", "slug", "date", "modified", "seo", "excerpt", "author", "commentCount", "categories"}
        keys = [k for k in all_keys if k.startswith("value") or (k.lower() in {"label", "title", "name", "content", "description"} and k not in junk_keys)]
        
        if not keys:
            # If no value keys, just use non-junk keys
            keys = [k for k in all_keys if k not in junk_keys]
            
        if not keys:
            return ""

        # Sort keys: title/label/name first, then value1, value2...
        def key_sorter(k):
            if k.lower() in {"title", "label", "name"}:
                return (0, 0)
            if k.startswith("value"):
                digits = re.findall(r"\d+", k)
                return (1, int(digits[0]) if digits else 0)
            return (2, k)
            
        keys.sort(key=key_sorter)

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
