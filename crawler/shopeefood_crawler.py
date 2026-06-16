"""ShopeeFood public catalog crawler.

This crawler is intentionally separate from the deterministic GreenSM knowledge
crawler. It uses a real browser session so the public web app can render and
emit its normal API calls, then normalizes public restaurant/card data into a
food catalog JSONL file.

Operational boundaries:
- public, unauthenticated pages only;
- no CAPTCHA/login bypass;
- small default limits and polite delays;
- raw network snapshots are saved for audit/debugging.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import time
import urllib.parse
import urllib.robotparser
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, sync_playwright


LOGGER = logging.getLogger("shopeefood_crawler")

START_URL = "https://shopeefood.vn/"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "food_catalog"


@dataclass
class FoodCatalogItem:
    item_id: str
    name: str
    description: str | None = None
    category: str | None = None
    cuisine: str | None = None
    taste_tags: list[str] | None = None
    diet_tags: list[str] | None = None
    ingredient_tags: list[str] | None = None
    price: int | None = None
    discount_percent: int | None = None
    final_price: int | None = None
    currency: str = "VND"
    image_url: str | None = None
    merchant_id: str | None = None
    merchant_name: str | None = None
    merchant_rating: float | None = None
    merchant_review_count: int | None = None
    merchant_address: str | None = None
    merchant_lat: float | None = None
    merchant_lng: float | None = None
    merchant_open_hours: Any = None
    avg_prep_minutes: int | None = None
    base_delivery_fee: int | None = None
    fee_per_km: int | None = None
    service_radius_km: float | None = None
    source: str = "shopeefood"
    source_url: str | None = None
    last_seen_at: str | None = None
    raw_ref: str | None = None


def configure_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def robots_allows(url: str, user_agent: str = "*") -> bool:
    parsed = urllib.parse.urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except Exception as exc:
        LOGGER.warning("Could not read robots.txt (%s): %s", robots_url, exc)
        return False
    return parser.can_fetch(user_agent, url)


def safe_text(value: Any) -> str | None:
    if value is None:
        return None
    text = repair_text(str(value)).strip()
    return text or None


def repair_text(text: str) -> str:
    """Repair common UTF-8 text decoded as latin-1/cp1252 by upstream clients."""
    if not any(marker in text for marker in ("Ã", "Â", "Ä", "Æ", "á»", "áº")):
        return text
    try:
        repaired = text.encode("latin1").decode("utf-8")
    except UnicodeError:
        return text
    return repaired if repaired.count("�") <= text.count("�") else text


def clean_value(value: Any) -> Any:
    if isinstance(value, str):
        return repair_text(value)
    if isinstance(value, list):
        return [clean_value(item) for item in value]
    if isinstance(value, dict):
        return {key: clean_value(item) for key, item in value.items()}
    return value


def first_present(data: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, "", []):
            return data[key]
    return None


def to_number(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?\d+(?:[.,]\d+)?", str(value))
    if not match:
        return None
    return float(match.group(0).replace(",", "."))


def to_int(value: Any) -> int | None:
    number = to_number(value)
    return int(number) if number is not None else None


def absolute_url(value: Any) -> str | None:
    text = safe_text(value)
    if not text:
        return None
    if text.startswith("//"):
        return "https:" + text
    if text.startswith("/"):
        return urllib.parse.urljoin(START_URL, text)
    return text


def find_nested(data: Any, keys: list[str]) -> Any:
    if isinstance(data, dict):
        found = first_present(data, keys)
        if found is not None:
            return found
        for value in data.values():
            nested = find_nested(value, keys)
            if nested is not None:
                return nested
    if isinstance(data, list):
        for item in data:
            nested = find_nested(item, keys)
            if nested is not None:
                return nested
    return None


def looks_like_restaurant(data: dict[str, Any]) -> bool:
    id_value = first_present(data, ["delivery_id", "restaurant_id", "merchant_id", "id"])
    name_value = first_present(data, ["name", "restaurant_name", "merchant_name"])
    address_value = first_present(data, ["address", "restaurant_address", "merchant_address"])
    return bool(id_value and name_value and (address_value or "delivery" in data or "restaurant" in data))


def iter_restaurant_objects(data: Any) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if isinstance(data, dict):
        for key in ("delivery_infos", "restaurant_infos", "restaurantInfos", "items", "data"):
            value = data.get(key)
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        results.extend(iter_restaurant_objects(item))
        if looks_like_restaurant(data):
            results.append(data)
        for value in data.values():
            if isinstance(value, (dict, list)):
                results.extend(iter_restaurant_objects(value))
    elif isinstance(data, list):
        for item in data:
            results.extend(iter_restaurant_objects(item))
    return results


def normalize_restaurant(raw: dict[str, Any], raw_ref: str) -> FoodCatalogItem | None:
    restaurant_id = first_present(raw, ["delivery_id", "restaurant_id", "merchant_id", "id"])
    name = safe_text(first_present(raw, ["name", "restaurant_name", "merchant_name"]))
    if not restaurant_id or not name:
        return None

    position = first_present(raw, ["position", "location", "geo"])
    lat = first_present(raw, ["lat", "latitude", "merchant_lat"])
    lng = first_present(raw, ["lng", "lon", "longitude", "merchant_lng"])
    if isinstance(position, dict):
        lat = lat if lat is not None else first_present(position, ["lat", "latitude"])
        lng = lng if lng is not None else first_present(position, ["lng", "lon", "longitude"])

    photos = first_present(raw, ["photos", "photo", "image", "image_url", "cover_photo"])
    image_url = None
    if isinstance(photos, list) and photos:
        image_url = absolute_url(first_present(photos[0], ["value", "url", "image_url"]) if isinstance(photos[0], dict) else photos[0])
    elif isinstance(photos, dict):
        image_url = absolute_url(first_present(photos, ["value", "url", "image_url"]))
    else:
        image_url = absolute_url(photos)

    url = first_present(raw, ["url", "source_url", "link"])
    source_url = absolute_url(url)
    if not source_url:
        slug = safe_text(first_present(raw, ["slug", "rewrite_name"]))
        source_url = urllib.parse.urljoin(START_URL, slug) if slug else START_URL

    cuisines = find_nested(raw, ["cuisines", "cuisine", "categories", "category"])
    cuisine_text = None
    if isinstance(cuisines, list):
        cuisine_text = ", ".join(
            filter(None, [safe_text(first_present(item, ["name", "title"]) if isinstance(item, dict) else item) for item in cuisines])
        )
    else:
        cuisine_text = safe_text(cuisines)

    discount = find_nested(raw, ["discount_percent", "discount", "promotion_percent"])
    return FoodCatalogItem(
        item_id=f"shopeefood_{restaurant_id}",
        name=name,
        description=safe_text(first_present(raw, ["description", "short_description", "summary"])),
        category=cuisine_text,
        cuisine=cuisine_text,
        taste_tags=[],
        diet_tags=[],
        ingredient_tags=[],
        price=to_int(find_nested(raw, ["price", "min_price"])),
        discount_percent=to_int(discount),
        final_price=to_int(find_nested(raw, ["final_price", "price_after_discount"])),
        image_url=image_url,
        merchant_id=str(restaurant_id),
        merchant_name=name,
        merchant_rating=to_number(find_nested(raw, ["rating", "avg_rating", "merchant_rating"])),
        merchant_review_count=to_int(find_nested(raw, ["review_count", "total_review", "reviews"])),
        merchant_address=safe_text(first_present(raw, ["address", "restaurant_address", "merchant_address"])),
        merchant_lat=to_number(lat),
        merchant_lng=to_number(lng),
        merchant_open_hours=find_nested(raw, ["open_hours", "operating", "working_time"]),
        avg_prep_minutes=to_int(find_nested(raw, ["avg_prep_minutes", "prepare_time", "delivery_time"])),
        base_delivery_fee=to_int(find_nested(raw, ["delivery_fee", "shipping_fee", "base_delivery_fee"])),
        source_url=source_url,
        last_seen_at=datetime.now(timezone.utc).isoformat(),
        raw_ref=raw_ref,
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


class ShopeeFoodCrawler:
    def __init__(
        self,
        start_url: str = START_URL,
        output_dir: Path = OUTPUT_DIR,
        max_items: int = 50,
        delay_seconds: float = 1.5,
        headful: bool = False,
    ) -> None:
        self.start_url = start_url
        self.output_dir = output_dir
        self.max_items = max_items
        self.delay_seconds = delay_seconds
        self.headful = headful
        self.raw_network: list[dict[str, Any]] = []
        self.items: dict[str, FoodCatalogItem] = {}

    def crawl(self, queries: list[str], categories: list[str]) -> Path:
        if not robots_allows(self.start_url):
            raise RuntimeError(f"robots.txt does not allow crawling {self.start_url}")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=not self.headful)
            context = browser.new_context(
                locale="vi-VN",
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1366, "height": 900},
            )
            page = context.new_page()
            page.on("response", self._capture_response)

            LOGGER.info("Opening %s", self.start_url)
            page.goto(self.start_url, wait_until="domcontentloaded", timeout=60000)
            self._settle(page)
            self._collect_dom_cards(page, "home")

            self._click_text_if_visible(page, "Xem tất cả")
            self._scroll_collect(page, "home_view_all")

            for category in categories:
                if len(self.items) >= self.max_items:
                    break
                LOGGER.info("Trying category: %s", category)
                if self._click_text_if_visible(page, category):
                    self._scroll_collect(page, f"category:{category}")
                time.sleep(self.delay_seconds)

            for query in queries:
                if len(self.items) >= self.max_items:
                    break
                LOGGER.info("Searching: %s", query)
                self._search(page, query)
                self._scroll_collect(page, f"search:{query}")
                time.sleep(self.delay_seconds)

            context.close()
            browser.close()

        return self._save()

    def _capture_response(self, response: Any) -> None:
        url = response.url
        if "/api/delivery/" not in url and "/api/promotion/" not in url:
            return
        try:
            payload = response.json()
        except Exception:
            return
        raw_ref = f"network_{len(self.raw_network) + 1:04d}"
        self.raw_network.append(
            {
                "ref": raw_ref,
                "url": url,
                "status": response.status,
                "captured_at": datetime.now(timezone.utc).isoformat(),
                "payload": payload,
            }
        )
        for raw in iter_restaurant_objects(payload):
            item = normalize_restaurant(raw, raw_ref)
            if item:
                self.items[item.item_id] = item
                if len(self.items) >= self.max_items:
                    break

    def _settle(self, page: Page) -> None:
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except PlaywrightTimeoutError:
            LOGGER.debug("networkidle timeout; continuing")
        time.sleep(self.delay_seconds)

    def _scroll_collect(self, page: Page, raw_ref: str) -> None:
        for _ in range(8):
            if len(self.items) >= self.max_items:
                return
            page.mouse.wheel(0, 900)
            self._settle(page)
            self._collect_dom_cards(page, raw_ref)

    def _search(self, page: Page, query: str) -> None:
        input_box = page.locator(
            "input[placeholder*='Tìm'], input[placeholder*='tìm'], input[type='search'], input[type='text']"
        ).first
        try:
            input_box.wait_for(timeout=7000)
            input_box.fill(query)
            input_box.press("Enter")
        except PlaywrightTimeoutError:
            LOGGER.warning("Search input not found")
            return
        self._settle(page)
        self._click_text_if_visible(page, query)

    def _click_text_if_visible(self, page: Page, text: str) -> bool:
        locator = page.get_by_text(text, exact=False).first
        try:
            locator.wait_for(timeout=5000)
            locator.click(timeout=5000)
            self._settle(page)
            return True
        except Exception:
            return False

    def _collect_dom_cards(self, page: Page, raw_ref: str) -> None:
        try:
            cards = page.evaluate(
                """
                () => {
                  const selectors = [
                    '.item-restaurant',
                    '.now-list-restaurant .item-content',
                    '[class*="restaurant"] [class*="item"]',
                    'a[href*="shopeefood.vn"], a[href^="/"]'
                  ];
                  const nodes = Array.from(new Set(selectors.flatMap((s) => Array.from(document.querySelectorAll(s)))));
                  return nodes.slice(0, 300).map((node) => {
                    const text = (node.innerText || '').trim();
                    const img = node.querySelector('img');
                    const link = node.closest('a') || node.querySelector('a');
                    const name =
                      node.querySelector('.name-res, [class*="name"], h2, h3, h4')?.innerText?.trim() ||
                      text.split('\\n').find((line) => line.trim().length > 3);
                    const address =
                      node.querySelector('.address-res, [class*="address"]')?.innerText?.trim() ||
                      text.split('\\n').find((line) => /quận|phường|đường|p\\.|q\\.|tp\\.|hcm|hà nội/i.test(line));
                    const promotion = text.split('\\n').find((line) => /giảm|mã/i.test(line));
                    return {
                      id: link?.getAttribute('href') || name,
                      name,
                      address,
                      promotion,
                      image_url: img?.src || img?.getAttribute('data-src'),
                      source_url: link?.href || null,
                      raw_text: text
                    };
                  }).filter((item) => item.name && item.raw_text && item.raw_text.length > 10);
                }
                """
            )
        except Exception as exc:
            LOGGER.debug("DOM card collection failed: %s", exc)
            return

        for card in cards:
            normalized = normalize_restaurant(
                {
                    "id": card.get("id"),
                    "name": card.get("name"),
                    "address": card.get("address"),
                    "image_url": card.get("image_url"),
                    "source_url": card.get("source_url"),
                    "description": card.get("promotion"),
                },
                f"dom:{raw_ref}",
            )
            if normalized:
                self.items[normalized.item_id] = normalized
                if len(self.items) >= self.max_items:
                    break

    def _save(self) -> Path:
        rows = [clean_value(asdict(item)) for item in self.items.values()]
        rows = rows[: self.max_items]
        catalog_path = self.output_dir / "shopeefood_catalog.jsonl"
        raw_path = self.output_dir / "shopeefood_raw_network.json"
        meta_path = self.output_dir / "shopeefood_crawl_metadata.json"

        write_jsonl(catalog_path, rows)
        raw_path.write_text(json.dumps(self.raw_network, ensure_ascii=False, indent=2), encoding="utf-8")
        meta_path.write_text(
            json.dumps(
                {
                    "source": "shopeefood",
                    "start_url": self.start_url,
                    "items": len(rows),
                    "network_snapshots": len(self.raw_network),
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "notes": [
                        "Public unauthenticated crawl only.",
                        "No CAPTCHA/login bypass.",
                        "Robots.txt checked before crawl.",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        LOGGER.info("Saved %s items to %s", len(rows), catalog_path)
        return catalog_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crawl public ShopeeFood restaurant cards/catalog data")
    parser.add_argument("--start-url", default=START_URL)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--max-items", type=int, default=50)
    parser.add_argument("--delay", type=float, default=1.5)
    parser.add_argument("--headful", action="store_true", help="Show browser window for selector/event debugging")
    parser.add_argument(
        "--queries",
        default="cơm,bún,phở,bánh mì,trà sữa",
        help="Comma-separated search keywords. Use empty string to skip search.",
    )
    parser.add_argument(
        "--categories",
        default="Đồ ăn,Đồ uống,Cơm hộp,Mì phở,Sushi",
        help="Comma-separated visible category labels to click. Use empty string to skip.",
    )
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    configure_logging(args.verbose)
    queries = [item.strip() for item in args.queries.split(",") if item.strip()]
    categories = [item.strip() for item in args.categories.split(",") if item.strip()]
    crawler = ShopeeFoodCrawler(
        start_url=args.start_url,
        output_dir=Path(args.output_dir),
        max_items=max(1, args.max_items),
        delay_seconds=max(0.5, args.delay),
        headful=args.headful,
    )
    crawler.crawl(queries=queries, categories=categories)


if __name__ == "__main__":
    main()
