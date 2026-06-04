import sys
import os
import re
import json
import argparse
import logging
from urllib.parse import urljoin, urlparse, parse_qs
from datetime import datetime
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from playwright.sync_api import sync_playwright
import markdownify
from openai import OpenAI
from app.core.config import settings as config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("AgentCrawler")

# Helper to print step markers for Frontend SSE parser
def print_agent_step(step_name: str, message: str = ""):
    print(f"\n[AGENT_STEP] {step_name}", flush=True)
    if message:
        print(f"[INFO] {message}", flush=True)

class AgentCrawler:
    def __init__(self, max_urls: int = 50):
        self.max_urls = max_urls
        self.output_dir = Path(root_dir) / "data" / "platform"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load API keys
        self.openai_client = None
        if config.OPENAI_API_KEY and "YOUR_OPENAI_API_KEY" not in config.OPENAI_API_KEY:
            self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
            
    def run(self):
        # 1. Discovery Phase
        print_agent_step("Discovery", "Starting Green SM Platform URL Discovery...")
        urls_to_crawl = self.discover_urls()
        logger.info(f"Discovered {len(urls_to_crawl)} URLs to crawl.")
        
        # Limit URLs
        urls_to_crawl = urls_to_crawl[:self.max_urls]
        print(f"[INFO] Queued {len(urls_to_crawl)} URLs for crawling.", flush=True)
        
        # 2. Crawl Phase
        crawled_pages = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            for i, url in enumerate(urls_to_crawl, 1):
                print_agent_step("Crawl", f"[{i}/{len(urls_to_crawl)}] Fetching: {url}")
                page_data = self.crawl_page(context, url)
                if page_data:
                    crawled_pages.append(page_data)
                    
            browser.close()
            
        print(f"[INFO] Crawled {len(crawled_pages)} pages successfully.", flush=True)
        
        # 3-6. LLM Extraction & Saving
        saved_count = 0
        skipped_count = 0
        
        print_agent_step("Classification", "Starting concurrent LLM classification & extraction...")
        
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def process_page(idx_page):
            idx, page = idx_page
            url = page["url"]
            title = page["title"]
            html = page["html"]
            
            print(f"[INFO] [{idx}/{len(crawled_pages)}] Classifying & extracting: {url}", flush=True)
            
            # Pre-convert HTML to Markdown to save LLM context window tokens
            raw_markdown = markdownify.markdownify(html, heading_style="ATX", strip=['a'])
            raw_markdown = re.sub(r'\n\n\n+', '\n\n', raw_markdown).strip()
            
            # Skip if practically empty
            if len(raw_markdown) < 150:
                print(f"[WARNING] Content too short ({len(raw_markdown)} chars), skipping: {url}", flush=True)
                return "skipped"
                
            # Call AI Agent (gpt-4o-mini) to extract/clean/restructure content
            analysis = self.analyze_content_with_llm(url, title, raw_markdown)
            
            if not analysis:
                print(f"[ERROR] LLM analysis failed for: {url}", flush=True)
                return "failed"
                
            score = analysis.get("knowledge_score", 0)
            category = analysis.get("category", "OTHER")
            
            print(f"[INFO] [{idx}/{len(crawled_pages)}] Result - Knowledge Score: {score}/100 | Category: {category} for {url}", flush=True)
            
            if score < 50:
                print(f"[INFO] Skipping page due to low Knowledge Score (<50): {url}", flush=True)
                return "skipped"
                
            # Save file
            self.save_cleaned_document(url, title, analysis)
            return "saved"

        # Limit thread pool to 10 workers to prevent rate limits or CPU overload
        max_workers = min(10, len(crawled_pages))
        logger.info(f"Processing {len(crawled_pages)} pages in parallel using {max_workers} threads...")
        
        indexed_pages = list(enumerate(crawled_pages, 1))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_page = {executor.submit(process_page, item): item for item in indexed_pages}
            
            for future in as_completed(future_to_page):
                idx, page = future_to_page[future]
                try:
                    res = future.result()
                    if res == "saved":
                        saved_count += 1
                    else:
                        skipped_count += 1
                except Exception as exc:
                    logger.error(f"Error classifying {page['url']}: {exc}")
                    skipped_count += 1
                    
        print_agent_step("Complete", f"Successfully saved {saved_count} documents, skipped {skipped_count} documents.")
        
    def discover_urls(self) -> list:
        discovered = set()
        base_url = "https://platform.greensm.com/VN-vi"
        
        # Helper helpers
        def hide_modals(page):
            try:
                style_content = """
                .ant-modal, .ant-modal-root, .ant-modal-wrap, .ant-modal-mask, .ant-modal-centered {
                    display: none !important;
                    pointer-events: none !important;
                }
                """
                page.add_style_tag(content=style_content)
                page.wait_for_timeout(300)
            except:
                pass

        def click_visible_dropdown_element(page, text):
            loc = page.locator(f"text='{text}'")
            count = loc.count()
            for i in range(count):
                el = loc.nth(i)
                if el.is_visible():
                    bbox = el.bounding_box()
                    if bbox and bbox['y'] < 400:
                        logger.info(f"Clicking visible dropdown element '{text}' (y={bbox['y']})")
                        el.click()
                        return True
            return False

        def click_visible_text(page, text):
            loc = page.locator(f"text='{text}'")
            count = loc.count()
            for i in range(count):
                el = loc.nth(i)
                if el.is_visible():
                    logger.info(f"Clicking visible text '{text}'")
                    el.click()
                    return True
            return False

        def get_dropdown_options(page, min_y=100, max_y=350):
            options = []
            loc = page.locator("[class*='cursor-pointer']")
            for i in range(loc.count()):
                el = loc.nth(i)
                if el.is_visible():
                    bbox = el.bounding_box()
                    if bbox and min_y <= bbox['y'] <= max_y:
                        txt = el.text_content().strip()
                        if txt and txt not in ["Ô tô", "Xe máy điện", "Giới thiệu", "Chính sách", "Tin tức", "Tiện ích", "Mua xe", "Thuê xe", "Khám phá", "Xem chính sách", "Đăng ký tư vấn", "Xem thêm"]:
                            options.append(txt)
            return sorted(list(set(options)))

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                
                def load_home_clean():
                    page.goto(base_url, wait_until="load", timeout=30000)
                    page.wait_for_timeout(2000)
                    page.evaluate("window.scrollTo(0, 0)")
                    hide_modals(page)

                load_home_clean()
                
                # 1. VEHICLES DISCOVERY (Ô tô and Xe máy điện)
                for menu_name in ["Ô tô", "Xe máy điện"]:
                    for tab_name in ["Mua xe", "Thuê xe"]:
                        logger.info(f"Scanning Menu '{menu_name}' -> Tab '{tab_name}'")
                        try:
                            if page.url != base_url:
                                load_home_clean()
                            
                            # Open dropdown to discover models
                            page.evaluate("window.scrollTo(0, 0)")
                            if click_visible_text(page, menu_name):
                                page.wait_for_timeout(500)
                                hide_modals(page)
                                if click_visible_dropdown_element(page, tab_name):
                                    page.wait_for_timeout(1000)
                                    hide_modals(page)
                                    
                                    # Dynamically read models
                                    discovered_models = get_dropdown_options(page, min_y=110, max_y=320)
                                    logger.info(f"Dynamically discovered models for {menu_name} -> {tab_name}: {discovered_models}")
                                    
                                    for model in discovered_models:
                                        try:
                                            # Check if the element is visible, if not, reopen menu
                                            loc = page.locator(f"text='{model}'")
                                            visible_el = None
                                            for idx in range(loc.count()):
                                                el = loc.nth(idx)
                                                if el.is_visible():
                                                    bbox = el.bounding_box()
                                                    if bbox and bbox['y'] < 400:
                                                        visible_el = el
                                                        break
                                            
                                            if not visible_el:
                                                logger.info(f"Dropdown closed, reopening for model '{model}'...")
                                                if page.url != base_url:
                                                    load_home_clean()
                                                page.evaluate("window.scrollTo(0, 0)")
                                                click_visible_text(page, menu_name)
                                                page.wait_for_timeout(500)
                                                hide_modals(page)
                                                click_visible_dropdown_element(page, tab_name)
                                                page.wait_for_timeout(1000)
                                                hide_modals(page)
                                                
                                                loc = page.locator(f"text='{model}'")
                                                for idx in range(loc.count()):
                                                    el = loc.nth(idx)
                                                    if el.is_visible():
                                                        bbox = el.bounding_box()
                                                        if bbox and bbox['y'] < 400:
                                                            visible_el = el
                                                            break
                                            
                                            if visible_el:
                                                logger.info(f"Clicking model '{model}' in dropdown...")
                                                # Click the parent or the element itself
                                                parent = visible_el.locator("xpath=..")
                                                parent_class = parent.evaluate("el => el.className")
                                                if "cursor-pointer" in parent_class:
                                                    parent.click()
                                                else:
                                                    visible_el.click()
                                                    
                                                page.wait_for_timeout(2000)
                                                hide_modals(page)
                                                
                                                if page.url != base_url:
                                                    logger.info(f"Found vehicle page: {page.url}")
                                                    discovered.add(page.url)
                                                    page.go_back()
                                                    page.wait_for_timeout(1000)
                                                    page.evaluate("window.scrollTo(0, 0)")
                                                    hide_modals(page)
                                        except Exception as m_err:
                                            logger.error(f"Error checking model {model}: {m_err}")
                        except Exception as t_err:
                            logger.error(f"Error on {menu_name} -> {tab_name}: {t_err}")

                # 2. POLICIES DISCOVERY
                logger.info("Scanning Policies...")
                try:
                    if page.url != base_url:
                        load_home_clean()
                    page.evaluate("window.scrollTo(0, 0)")
                    if click_visible_text(page, "Chính sách"):
                        page.wait_for_timeout(1000)
                        hide_modals(page)
                        
                        # Dynamically find policies in the dropdown (bbox y: 100 to 500)
                        discovered_policies = get_dropdown_options(page, min_y=100, max_y=500)
                        logger.info(f"Dynamically discovered policies: {discovered_policies}")
                        
                        for item in discovered_policies:
                            try:
                                # Re-open dropdown if closed
                                loc = page.locator(f"text='{item}'")
                                visible_item = None
                                for i in range(loc.count()):
                                    el = loc.nth(i)
                                    if el.is_visible():
                                        bbox = el.bounding_box()
                                        if bbox and bbox['y'] < 500:
                                            visible_item = el
                                            break
                                            
                                if not visible_item:
                                    logger.info(f"Policies dropdown closed, reopening for '{item}'...")
                                    if page.url != base_url:
                                        load_home_clean()
                                    page.evaluate("window.scrollTo(0, 0)")
                                    click_visible_text(page, "Chính sách")
                                    page.wait_for_timeout(1000)
                                    hide_modals(page)
                                    
                                    loc = page.locator(f"text='{item}'")
                                    for i in range(loc.count()):
                                        el = loc.nth(i)
                                        if el.is_visible():
                                            bbox = el.bounding_box()
                                            if bbox and bbox['y'] < 500:
                                                visible_item = el
                                                break
                                
                                if visible_item:
                                    logger.info(f"Clicking policy item: {item}")
                                    visible_item.click()
                                    page.wait_for_timeout(2000)
                                    hide_modals(page)
                                    
                                    if page.url != base_url:
                                        logger.info(f"Found direct policy URL: {page.url}")
                                        discovered.add(page.url)
                                        page.go_back()
                                        page.wait_for_timeout(1000)
                                        page.evaluate("window.scrollTo(0, 0)")
                                        hide_modals(page)
                                        continue
                                        
                                    # If page URL didn't change, check for Xem thêm or links
                                    xem_them = page.locator("text='Xem thêm'").first
                                    if xem_them.is_visible():
                                        xem_them.click()
                                        page.wait_for_timeout(2000)
                                        hide_modals(page)
                                        logger.info(f"Found policy details URL: {page.url}")
                                        discovered.add(page.url)
                                        page.go_back()
                                        page.wait_for_timeout(1000)
                                        page.evaluate("window.scrollTo(0, 0)")
                                        hide_modals(page)
                                    else:
                                        links = page.query_selector_all("a")
                                        for link in links:
                                            href = link.get_attribute("href")
                                            if href and (".pdf" in href or "policy" in href or "driver" in href):
                                                abs_href = urljoin(page.url, href)
                                                logger.info(f"Found policy link in body: {abs_href}")
                                                discovered.add(abs_href)
                            except Exception as p_err:
                                logger.error(f"Error on policy {item}: {p_err}")
                except Exception as e:
                    logger.error(f"Policies scanning error: {e}")

                # 3. NEWS DISCOVERY
                logger.info("Scanning News...")
                try:
                    news_url = "https://platform.greensm.com/VN-vi/news/all/page/1"
                    logger.info(f"Navigating directly to News page: {news_url}")
                    page.goto(news_url, wait_until="load", timeout=30000)
                    page.wait_for_timeout(2000)
                    hide_modals(page)
                    
                    try:
                        page.wait_for_selector("text='Tất cả'", timeout=8000)
                    except Exception as wait_err:
                        logger.error(f"Timeout waiting for news tags: {wait_err}")
                    
                    tags = ["Tất cả", "Báo chí", "Chính sách", "Sự kiện"]
                    for tag in tags:
                        try:
                            loc = page.locator(f"text='{tag}'")
                            tag_clicked = False
                            for i in range(loc.count()):
                                el = loc.nth(i)
                                if el.is_visible():
                                    bbox = el.bounding_box()
                                    if bbox and bbox['y'] > 150:
                                        logger.info(f"Clicking news tag: {tag}")
                                        el.click()
                                        page.wait_for_timeout(1500)
                                        hide_modals(page)
                                        tag_clicked = True
                                        break
                                        
                            if tag_clicked:
                                for page_num in range(1, 4):
                                    a_tags = page.query_selector_all("a")
                                    count = 0
                                    for a in a_tags:
                                        href = a.get_attribute("href")
                                        if href and "/news/" in href:
                                            abs_url = urljoin(page.url, href)
                                            clean_url = abs_url.split("#")[0].rstrip("/")
                                            if clean_url not in discovered:
                                                discovered.add(clean_url)
                                                logger.info(f"Found news article: {clean_url}")
                                                count += 1
                                    logger.info(f"Page {page_num} of news tag '{tag}': Found {count} new URLs")
                                    
                                    next_btn = page.locator(".ant-pagination-next").first
                                    if next_btn.is_visible() and next_btn.is_enabled():
                                        next_btn.click()
                                        page.wait_for_timeout(1500)
                                        hide_modals(page)
                                    else:
                                        break
                        except Exception as tag_err:
                            logger.error(f"Error on news tag {tag}: {tag_err}")
                except Exception as e:
                    logger.error(f"News scanning error: {e}")

                # 4. UTILITY DISCOVERY
                logger.info("Scanning Utilities...")
                try:
                    if page.url != base_url:
                        load_home_clean()
                    page.evaluate("window.scrollTo(0, 0)")
                    if click_visible_text(page, "Tiện ích"):
                        page.wait_for_timeout(1000)
                        hide_modals(page)
                        
                        # Dynamically find utilities in the dropdown box (bbox y: 100 to 400)
                        discovered_utilities = get_dropdown_options(page, min_y=100, max_y=400)
                        logger.info(f"Dynamically discovered utilities: {discovered_utilities}")
                        
                        for item in discovered_utilities:
                            try:
                                # Re-open dropdown if closed
                                loc = page.locator(f"text='{item}'")
                                visible_item = None
                                for i in range(loc.count()):
                                    el = loc.nth(i)
                                    if el.is_visible():
                                        bbox = el.bounding_box()
                                        if bbox and bbox['y'] < 400:
                                            visible_item = el
                                            break
                                            
                                if not visible_item:
                                    logger.info(f"Utilities dropdown closed, reopening for '{item}'...")
                                    if page.url != base_url:
                                        load_home_clean()
                                    page.evaluate("window.scrollTo(0, 0)")
                                    click_visible_text(page, "Tiện ích")
                                    page.wait_for_timeout(1000)
                                    hide_modals(page)
                                    
                                    loc = page.locator(f"text='{item}'")
                                    for i in range(loc.count()):
                                        el = loc.nth(i)
                                        if el.is_visible():
                                            bbox = el.bounding_box()
                                            if bbox and bbox['y'] < 400:
                                                visible_item = el
                                                break
                                                
                                if visible_item:
                                    logger.info(f"Clicking utility item: {item}")
                                    visible_item.click()
                                    page.wait_for_timeout(2000)
                                    hide_modals(page)
                                    
                                    if page.url != base_url:
                                        logger.info(f"Found utility URL: {page.url}")
                                        discovered.add(page.url)
                                        page.go_back()
                                        page.wait_for_timeout(1000)
                                        page.evaluate("window.scrollTo(0, 0)")
                                        hide_modals(page)
                            except Exception as u_err:
                                logger.error(f"Error on utility item {item}: {u_err}")
                except Exception as e:
                    logger.error(f"Utilities scanning error: {e}")

                browser.close()
            except Exception as e:
                logger.error(f"Discovery error: {e}")
                
        return sorted(list(discovered))

    def crawl_page(self, context, url: str) -> dict:
        page = context.new_page()
        try:
            if url.lower().endswith(".pdf"):
                # Handle PDF files by returning a mock html representation with the link
                title = os.path.basename(url)
                html = f"<html><body>This is a PDF file: <a href='{url}'>{url}</a></body></html>"
                page.close()
                return {"url": url, "title": title, "html": html}
                
            page.goto(url, wait_until="load", timeout=30000)
            page.wait_for_timeout(2000) # wait 2s for React state
            
            # Dismiss popup modals if any
            try:
                close_btn = page.locator(".ant-modal-close").first
                if close_btn.is_visible():
                    close_btn.click()
                    page.wait_for_timeout(500)
            except:
                pass
                
            title = page.title()
            html = page.content()
            
            page.close()
            return {"url": url, "title": title, "html": html}
        except Exception as e:
            logger.error(f"Failed to crawl {url}: {e}")
            try:
                page.close()
            except:
                pass
            return None

    def analyze_content_with_llm(self, url: str, title: str, content_markdown: str) -> dict:
        """Uses OpenAI LLM to classify, score, and extract clean specs/prices from page"""
        if not self.openai_client:
            # Fallback mock analysis if no OpenAI Key is defined
            logger.warning("No OpenAI API key found. Using rule-based metadata extraction fallback.")
            return {
                "knowledge_score": 80 if len(content_markdown) > 200 else 40,
                "category": "SERVICE" if "dat_coc" in url or "evo" in url or "vf" in url else "POLICY",
                "cleaned_content": content_markdown,
                "title": title,
                "summary": f"Scraped data from {url}",
                "keywords": ["greensm", "platform"]
            }
            
        system_prompt = """You are a precision AI Knowledge Extraction Agent for Green SM Platform RAG.
Your task is to analyze scraped raw Markdown of a webpage, rate its usefulness for RAG, clean it of clutter, preserve image links, and reconstruct it into structured Markdown.

Follow these rules strictly:
1. Rate the page's "knowledge_score" (0-100). If it has pricing, specs, policies, or FAQs, score it 80-95. If it's a completely empty checkout form, cookie notice, or contact form with no content, score it < 50.
2. Classify its category into one of: SERVICE, FAQ, POLICY, PRICING, PROMOTION, NEWS, GUIDE, SUPPORT, DRIVER, CORPORATE, OTHER.
3. Remove JUNK boilerplate:
   - Header menus, footer navigation, copyrights.
   - Contact form fields, input box labels ("Họ và tên", "Số điện thoại", "Số CCCD", "Email").
   - Static checkout terms agreements & checklist tickboxes.
4. Keep & Format:
   - Title, main section headers.
   - Detailed pricing, prices (e.g. "689.000.000 VNĐ", "25.600.000 VNĐ", "300k/tháng").
   - Specifications, parameters (dimensions, speed, power, battery).
   - Variations (colors, colors list).
   - Complete FAQs (question and answers).
   - Keep ALL valid image links `![alt text](url)` if they show vehicles, product variations, specification charts, or diagrams. Keep them in context!
5. Output must be valid JSON in the format:
{
  "knowledge_score": 85,
  "category": "PRICING",
  "title": "Clean Page Title",
  "cleaned_content": "# Structured Markdown Here...",
  "summary": "Short 1-2 sentence summary of content.",
  "keywords": ["vehicle", "price", "specs"]
}"""

        user_content = f"Page URL: {url}\nPage Title: {title}\nRaw Scraped Markdown:\n{content_markdown}"
        
        try:
            response = self.openai_client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
                timeout=30.0
            )
            res_txt = response.choices[0].message.content.strip()
            return json.loads(res_txt)
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def save_cleaned_document(self, url: str, title: str, analysis: dict):
        cleaned_markdown = analysis.get("cleaned_content", "")
        category = analysis.get("category", "OTHER")
        score = analysis.get("knowledge_score", 0)
        summary = analysis.get("summary", "")
        keywords = analysis.get("keywords", [])
        
        # Build YAML frontmatter
        frontmatter = f"""---
url: {url}
category: platform
crawl_date: {datetime.now().strftime("%Y-%m-%d")}
title: {title}
agent_category: {category}
knowledge_score: {score}
summary: {summary}
keywords: {json.dumps(keywords, ensure_ascii=False)}
---

"""
        full_content = frontmatter + cleaned_markdown
        
        # Generate safe filename
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        path = parsed.path.strip("/").replace("/", "_")
        if not path or path == "VN_vi":
            path = "home"
            
        # Append sanitized query parameters to avoid duplicate filename overwrites
        if parsed.query:
            query_str = parsed.query.replace('?', '&')
            params = parse_qs(query_str)
            query_parts = []
            for k, vals in sorted(params.items()):
                for v in vals:
                    clean_k = re.sub(r'[^\w]', '_', k.replace('-', '_'))
                    clean_v = re.sub(r'[^\w]', '_', v.replace('-', '_'))
                    query_parts.append(f"{clean_k}_{clean_v}")
            if query_parts:
                path += "_" + "_".join(query_parts)
                
        # Strip illegal filename chars and limit length
        safe_name = re.sub(r'[^\w_]', '', path.replace('-', '_'))
        safe_name = re.sub(r'_+', '_', safe_name).strip('_')
        filename = f"{safe_name}.md"
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.output_dir / filename
        filepath.write_text(full_content, encoding="utf-8")
        logger.info(f"Saved: {filepath}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Green SM Platform AI Agentic Crawler")
    parser.add_argument("--max-urls", type=int, default=30, help="Max URLs to crawl")
    args = parser.parse_args()
    
    crawler = AgentCrawler(max_urls=args.max_urls)
    crawler.run()
