import asyncio
import json
import csv
import random
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from tqdm import tqdm

BASE_URL = "https://www.greensm.com/vn-vi/news"
TOTAL_PAGES = 84

OUTPUT_JSON = "greensm_news_urls.json"
OUTPUT_CSV = "greensm_news_urls.csv"

DELAY_BETWEEN_PAGES = (1.5, 3)


def is_valid_news_url(url: str) -> bool:
    if not url:
        return False

    parsed = urlparse(url)

    # Chỉ lấy bài viết, không lấy /news?page=...
    if parsed.path == "/vn-vi/news":
        return False

    return parsed.path.startswith("/vn-vi/news/")


async def auto_scroll(page):
    """Scroll để lazy-load nội dung"""
    await page.evaluate("""
        async () => {
            await new Promise(resolve => {
                let totalHeight = 0;
                const distance = 500;
                const timer = setInterval(() => {
                    window.scrollBy(0, distance);
                    totalHeight += distance;

                    if (totalHeight >= document.body.scrollHeight) {
                        clearInterval(timer);
                        resolve();
                    }
                }, 200);
            });
        }
    """)


async def get_news_urls_from_page(page, page_num: int) -> list[str]:
    url = f"{BASE_URL}?page={page_num}"

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(2000)

        await auto_scroll(page)
        await page.wait_for_timeout(1000)

        urls = await page.evaluate("""
            () => {
                const urls = new Set();

                document.querySelectorAll("a[href]").forEach(a => {
                    const href = new URL(a.getAttribute("href"), location.origin).href;

                    if (href.includes("/vn-vi/news/")) {
                        urls.add(href.split("#")[0]);
                    }
                });

                return Array.from(urls);
            }
        """)

        return [u for u in urls if is_valid_news_url(u)]

    except Exception as e:
        print(f"❌ Lỗi trang {page_num}: {e}")
        return []


async def main():
    all_urls = []
    seen = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )

        context = await browser.new_context(
            viewport={"width": 1366, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )

        page = await context.new_page()

        for page_num in tqdm(range(1, TOTAL_PAGES + 1), desc="Crawling news pages"):
            urls = await get_news_urls_from_page(page, page_num)

            print(f"Page {page_num}: {len(urls)} urls")

            for url in urls:
                if url not in seen:
                    seen.add(url)
                    all_urls.append(url)

            await asyncio.sleep(random.uniform(*DELAY_BETWEEN_PAGES))

        await browser.close()

    result = {
        "news": all_urls
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["url"])
        for url in all_urls:
            writer.writerow([url])

    print(f"\n✅ Tổng số URL lấy được: {len(all_urls)}")
    print(f"📄 JSON: {OUTPUT_JSON}")
    print(f"📄 CSV: {OUTPUT_CSV}")


if __name__ == "__main__":
    asyncio.run(main())