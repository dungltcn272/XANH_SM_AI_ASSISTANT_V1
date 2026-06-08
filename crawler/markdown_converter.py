"""
Phase 4: HTML → Markdown
Cải thiện xử lý text dính vào nhau, xóa header/footer tốt hơn
"""

from bs4 import BeautifulSoup, NavigableString
import logging
import re
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarkdownConverter:
    """Chuyển HTML thành Markdown với xử lý tốt hơn"""
    
    def __init__(self):
        self.tags_to_remove = ["header", "nav", "footer", "script", "style", "iframe", "noscript", "aside"]
        self.block_tags = ["div", "section", "article", "main", "p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "table", "blockquote"]
    
    def html_to_markdown(self, html: str, title: str = "", url: str = "") -> str:
        """Chuyển HTML thành Markdown"""
        soup = BeautifulSoup(html, "html.parser")
        
        # Trích xuất dữ liệu bảng giá và FAQ từ __NEXT_DATA__ (phải làm trước khi xóa tag script)
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        dynamic_table_md = ""
        dynamic_faq_md = ""
        if next_data_script and next_data_script.string:
            try:
                import json
                nd = json.loads(next_data_script.string)
                dynamic_table_md = self._extract_next_tables(nd)
                dynamic_faq_md = self._extract_next_faq(nd, url)
            except Exception as e:
                logger.error(f"Error parsing __NEXT_DATA__: {e}")
        
        # Xóa tag không cần
        for tag in self.tags_to_remove:
            for elem in soup.find_all(tag):
                elem.decompose()
                
        # Xóa các tag có class liên quan tới header/footer
        for elem in soup.find_all(class_=lambda c: c and any(kw in c.lower() for kw in ['footer', 'header', 'nav', 'sidebar'])):
            elem.decompose()
        
        # Xóa các banner chung (VD: Tải ứng dụng, Tin tức)
        for elem in soup.find_all(class_=lambda c: c and any(kw in c.lower() for kw in ['footer-widget', 'download-app'])):
            elem.decompose()
            
        # Xóa nội dung bị lặp lại do responsive
        for elem in soup.find_all(class_=lambda c: c and any(kw in c for kw in ['md:hidden', 'sm:hidden', 'lg:hidden'])):
            elem.decompose()
            
        # Xóa block CÂU HỎI THƯỜNG GẶP tĩnh ở trong HTML để tránh trùng lặp với phần dữ liệu động
        for t in soup.find_all(string=lambda t: t and 'CÂU HỎI THƯỜNG GẶP' in t.upper()):
            if hasattr(t, 'parent'):
                parent = t.parent
                if parent and parent.name != 'script' and parent.parent and parent.parent.parent:
                    parent.parent.parent.decompose()
                
        # Xóa block html của trang terms-policies/general vì ta sẽ lấy toàn bộ từ generalItems
        if 'terms-policies' in url:
            for elem in soup.find_all('div', class_=lambda c: c and 'md:w-[235px]' in c):
                if elem.parent and elem.parent.parent:
                    elem.parent.parent.decompose()
                    
        # Xóa các block rác phổ biến trong trang tin tức/chi tiết
        junk_strings = [
            'Danh mục khác', 'Bài viết gần đây', 'Tin tức liên quan', 
            'Xem thêm', 'Có thể bạn quan tâm', 'Chủ đề hot',
            'Bài viết mới nhất', 'Tin tức mới nhất'
        ]
        for js in junk_strings:
            for tag in soup.find_all(string=lambda t: t and js in t):
                if hasattr(tag, 'parent') and tag.parent:
                    curr = getattr(tag, 'parent', None)
                    to_decompose = curr
                    depth = 0
                    while curr and getattr(curr, 'name', None) not in {"main", "article", "body", "html"} and depth < 4:
                        if getattr(curr, 'name', None) in {"section", "aside", "div"}:
                            to_decompose = curr
                        curr = getattr(curr, 'parent', None)
                        depth += 1
                    if to_decompose and getattr(to_decompose, 'name', None) not in {"body", "html"}:
                        try:
                            to_decompose.decompose()
                        except Exception:
                            pass
            
        # Xóa các ảnh rác/banner thừa dựa trên alt text
        for img in soup.find_all('img'):
            alt = img.get('alt', '').strip().lower()
            if 'banner' in alt or 'icon' in alt or 'download app' in alt or 'related driver' in alt or 'term menu' in alt:
                img.decompose()
        
        # Lấy nội dung chính
        for selector in ["main", "article", "[role='main']"]:
            main_elem = soup.select_one(selector)
            if main_elem:
                content = main_elem
                break
        else:
            content = soup.find("body") or soup
        
        # Chuyển sang Markdown dùng markdownify (fix lỗi nối chữ)
        self._absolutize_urls(content, url)

        import markdownify
        markdown = markdownify.markdownify(str(content), heading_style="ATX", strip=['a'])
        
        if dynamic_faq_md:
            if "terms-policies" in url:
                markdown += "\n\n## Nội dung chi tiết\n\n" + dynamic_faq_md
            else:
                markdown += "\n\n## Câu hỏi thường gặp\n\n" + dynamic_faq_md
        
        if dynamic_table_md:
            markdown += "\n\n## Bảng giá chi tiết (Dữ liệu động)\n\n" + dynamic_table_md

        # Clean up multiple newlines
        markdown = re.sub(r'\n\n\n+', '\n\n', markdown)
        
        return markdown.strip()

    def _absolutize_urls(self, soup: BeautifulSoup, base_url: str) -> None:
        if not base_url:
            return

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
    
    def _extract_next_tables(self, data) -> str:
        md = ""
        def find_tables_and_columns(d, name="Bảng giá"):
            found = []
            if isinstance(d, dict):
                if "rows" in d and isinstance(d["rows"], list):
                    found.append((name, d))
                else:
                    for k, v in d.items():
                        if isinstance(v, (dict, list)):
                            found.extend(find_tables_and_columns(v, k))
            elif isinstance(d, list):
                for item in d:
                    if isinstance(item, (dict, list)):
                        found.extend(find_tables_and_columns(item, name))
            return found

        tables = find_tables_and_columns(data)
        
        # Deduplicate tables by looking at their content
        seen_tables = []
        
        for name, table_obj in tables:
            rows = table_obj.get("rows", [])
            if not rows: continue
            
            # Quick hash of row count and first row keys to avoid duplicates
            table_id = (len(rows), str(rows[0])[:100])
            if table_id in seen_tables: continue
            seen_tables.append(table_id)

            display_name = name.replace("_", " ").title()
            md += f"### {display_name}\n\n"
            
            columns_value = table_obj.get("columns", "")
            headers = []
            if isinstance(columns_value, str) and columns_value:
                headers = [c.strip() for c in columns_value.split("|")]
            elif isinstance(columns_value, list):
                headers = [str(c).strip() for c in columns_value if str(c).strip()]
            
            # Check if rows are grouped by city
            city_grouped = False
            for row_item in rows:
                if isinstance(row_item, dict) and "city" in row_item and "items" in row_item:
                    city_grouped = True
                    city = row_item.get("city", "Khác")
                    md += f"#### Tỉnh/Thành phố: {city}\n\n"
                    items = row_item.get("items", [])
                    md += self._format_table_from_items(items, headers)
            
            # If not city-grouped, format as one table
            if not city_grouped:
                md += self._format_table_from_items(rows, headers)
        return md

    def _format_table_from_items(self, items, headers=None) -> str:
        if not items: return ""
        
        # Find all value keys
        all_val_keys = set()
        for item in items:
            if isinstance(item, dict):
                for k in item.keys():
                    if k.startswith("value"):
                        all_val_keys.add(k)
        
        if not all_val_keys: return ""
        
        # Sort keys: value1, value2... value_1, value_2...
        def key_sorter(k):
            digits = re.findall(r'\d+', k)
            num = int(digits[0]) if digits else 0
            is_underscore = "_" in k
            return (is_underscore, num)
            
        sorted_keys = sorted(list(all_val_keys), key=key_sorter)
        num_cols = len(sorted_keys)
        
        # Use provided headers or generate defaults
        if headers and len(headers) > 0:
            if len(headers) >= num_cols:
                actual_headers = headers[:num_cols]
            else:
                actual_headers = headers + [f"Giá trị {i}" for i in range(len(headers)+1, num_cols+1)]
        else:
            actual_headers = ["Hạng mục"] + [f"Giá trị {i}" for i in range(2, num_cols + 1)]
            
        markdown = "| " + " | ".join(actual_headers) + " |\n"
        markdown += "|" + "|".join(["---"] * len(actual_headers)) + "|\n"
        
        for item in items:
            if not isinstance(item, dict): continue
            vals = []
            for k in sorted_keys:
                v = item.get(k, "")
                if v is None: v = ""
                vals.append(str(v).replace('\n', ' ').strip())
            
            if any(v for v in vals):
                markdown += "| " + " | ".join(vals) + " |\n"
        
        return markdown + "\n"
        
    def _extract_next_faq(self, data, url: str) -> str:
        md = ""
        def find_faq(d, path):
            faqs = []
            if isinstance(d, dict):
                # Green SM frequently uses label and value for FAQs in setUpTitle array
                if 'label' in d and 'value' in d and isinstance(d['label'], str) and isinstance(d['value'], str):
                    if len(d['label']) > 10 and len(d['value']) > 10:
                        faqs.append((d['label'], d['value']))
                for k, v in d.items():
                    if isinstance(v, (dict, list)):
                        faqs.extend(find_faq(v, path + [k]))
            elif isinstance(d, list):
                for idx, item in enumerate(d):
                    if isinstance(item, (dict, list)):
                        faqs.extend(find_faq(item, path + [idx]))
            return faqs

        faqs_found = find_faq(data, [])
        
        # Extract items for terms-policies pages
        if "terms-policies" in url:
            try:
                term_keys = ["generalTerms", "privacyNotice", "serviceData", "protectionPolicy", "regulationsData"]
                page_props = data.get("props", {}).get("pageProps", {})
                
                items = []
                for tk in term_keys:
                    if tk in page_props and isinstance(page_props[tk], dict):
                        # Find the list of items (usually ends in 'Items')
                        for k, v in page_props[tk].items():
                            if k.endswith("Items") and isinstance(v, list):
                                items = v
                                break
                        if items: break
                
                if not items:
                    # Fallback for some structures where items might be at top level of pageProps
                    for k, v in page_props.items():
                        if k.endswith("Items") and isinstance(v, list):
                            items = v
                            break

                for item in items:
                    title = item.get("title") or item.get("label")
                    desc = item.get("description") or item.get("value")
                    if title and desc:
                        faqs_found.append((title, desc))
            except Exception as e:
                logger.error(f"Error parsing term items: {e}")
        
        # Also extract from i18nStore (for insurance / green care pages)
        valid_prefix = None
        if "khach-hang" in url:
            valid_prefix = "customer"
        elif "hang-hoa" in url:
            valid_prefix = "cargo"
        elif "giao-do-an" in url:
            valid_prefix = "food"
        elif "bac-tai" in url:
            valid_prefix = "driver"
            
        if valid_prefix:
            try:
                i18n = data.get("props", {}).get("pageProps", {}).get("_nextI18Next", {}).get("initialI18nStore", {}).get("vn-vi", {})
                for ns, trans in i18n.items():
                    if isinstance(trans, dict):
                        questions = {}
                        answers = {}
                        for k, v in trans.items():
                            if k.startswith(valid_prefix) and "_question_" in k:
                                parts = k.split("_question_")
                                if len(parts) == 2:
                                    questions[(parts[0], parts[1])] = v
                            elif k.startswith(valid_prefix) and "_answer_" in k:
                                parts = k.split("_answer_")
                                if len(parts) == 2:
                                    answers[(parts[0], parts[1])] = v
                        
                        # Pair them up
                        for key, q in questions.items():
                            a = answers.get(key)
                            if q and a and isinstance(q, str) and isinstance(a, str):
                                faqs_found.append((q, a))
            except Exception as e:
                logger.error(f"Error parsing i18nStore for FAQ: {e}")
        
        # Deduplicate
        seen = set()
        for label, value in faqs_found:
            if label not in seen:
                seen.add(label)
                # Clean up html in value if any
                import markdownify
                clean_value = markdownify.markdownify(value).strip()
                md += f"### {label}\n{clean_value}\n\n"
                
        return md

    def _convert_element_with_newlines(self, elem) -> str:
        """Chuyển element thành Markdown với newlines giữa các block elements"""
        if isinstance(elem, NavigableString):
            text = str(elem).strip()
            if text:
                # Thêm space giữa các từ dính vào nhau (tiếng Việt)
                text = re.sub(r'([a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ0-9])([A-ZÀÁẢÃẠĂẰẮẨẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ])', r'\1 \2', text)
                return text
            return ""
        
        if not hasattr(elem, 'name'):
            return str(elem)
        
        tag = elem.name
        
        # Headings
        if tag == "h1":
            text = self._get_text_clean(elem)
            return f"# {text}\n\n" if text else ""
        elif tag == "h2":
            text = self._get_text_clean(elem)
            return f"## {text}\n\n" if text else ""
        elif tag == "h3":
            text = self._get_text_clean(elem)
            return f"### {text}\n\n" if text else ""
        elif tag in ["h4", "h5", "h6"]:
            hashes = "#" * int(tag[1])
            text = self._get_text_clean(elem)
            return f"{hashes} {text}\n\n" if text else ""
        
        # Paragraph
        elif tag == "p":
            text = self._get_text_clean(elem)
            if text and len(text) > 2:
                return f"{text}\n\n"
            return ""
        
        # Lists
        elif tag == "ul":
            result = self._convert_ul(elem)
            return result if result.strip() else ""
        elif tag == "ol":
            result = self._convert_ol(elem)
            return result if result.strip() else ""
        elif tag == "li":
            text = self._get_text_clean(elem)
            return f"- {text}\n" if text else ""
        
        # Links
        elif tag == "a":
            href = elem.get("href", "").strip()
            text = self._get_text_clean(elem)
            if text:
                return f"[{text}]({href})" if href else text
            return ""
        
        # Bold, Italic
        elif tag in ["strong", "b"]:
            text = self._get_text_clean(elem)
            return f"**{text}**" if text else ""
        elif tag in ["em", "i"]:
            text = self._get_text_clean(elem)
            return f"*{text}*" if text else ""
        
        # Images
        elif tag == "img":
            src = elem.get("src", "").strip()
            alt = elem.get("alt", "").strip()
            if src:
                # Resolve relative Next.js image paths if any
                if src.startswith("/_next/image?url="):
                    import urllib.parse
                    parsed = urllib.parse.urlparse(src)
                    qs = urllib.parse.parse_qs(parsed.query)
                    if "url" in qs:
                        src = qs["url"][0]
                return f"![{alt}]({src})\n\n"
            return ""
        
        # Code
        elif tag == "code":
            text = self._get_text_clean(elem)
            return f"`{text}`" if text else ""
        elif tag == "pre":
            code_text = self._get_text_clean(elem)
            return f"```\n{code_text}\n```\n\n" if code_text else ""
        
        # Table
        elif tag == "table":
            result = self._convert_table(elem)
            return result if result.strip() else ""
        
        # BlockQuote
        elif tag == "blockquote":
            text = self._get_text_clean(elem)
            return f"> {text}\n\n" if text else ""
        
        # HR
        elif tag == "hr":
            return "\n---\n\n"
        
        # Br
        elif tag == "br":
            return "\n"
        
        # Container elements - process children with block handling
        else:
            markdown = ""
            for child in elem.children:
                if isinstance(child, NavigableString):
                    text = str(child).strip()
                    if text:
                        # Apply text joining fix
                        text = re.sub(r'([a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ0-9])([A-ZÀÁẢÃẠĂẰẮẨẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ])', r'\1 \2', text)
                        markdown += text
                elif hasattr(child, 'name') and child.name in self.block_tags:
                    # Add newline before block element
                    if markdown and not markdown.endswith('\n\n'):
                        markdown += '\n'
                    child_md = self._convert_element_with_newlines(child)
                    markdown += child_md
                else:
                    child_md = self._convert_element_with_newlines(child)
                    if child_md:
                        markdown += child_md
            return markdown
    
    def _get_text_clean(self, elem) -> str:
        """Lấy text từ element với proper spacing"""
        # Tách các inline elements bằng space
        text = elem.get_text(separator=' ', strip=True)
        # Clean multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Apply text joining fix
        text = re.sub(r'([a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ0-9])([A-ZÀÁẢÃẠĂẰẮẨẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ])', r'\1 \2', text)
        return text.strip()
    
    def _convert_ul(self, elem) -> str:
        """Chuyển <ul> thành Markdown"""
        markdown = ""
        for li in elem.find_all("li", recursive=False):
            text = self._get_text_clean(li)
            if text:
                markdown += f"- {text}\n"
        return markdown + "\n" if markdown else ""
    
    def _convert_ol(self, elem) -> str:
        """Chuyển <ol> thành Markdown"""
        markdown = ""
        for i, li in enumerate(elem.find_all("li", recursive=False), 1):
            text = self._get_text_clean(li)
            if text:
                markdown += f"{i}. {text}\n"
        return markdown + "\n" if markdown else ""
    
    def _convert_table(self, elem) -> str:
        """Chuyển <table> thành Markdown"""
        rows = []
        
        all_rows = elem.find_all("tr")
        if not all_rows:
            return ""
        
        for row in all_rows:
            cells = []
            for cell in row.find_all(["th", "td"]):
                cell_text = cell.get_text().strip()
                cell_text = re.sub(r'\s+', ' ', cell_text)
                cells.append(cell_text)
            if cells:
                rows.append(cells)
        
        if len(rows) < 2:
            return ""
        
        num_cols = len(rows[0])
        
        # Header
        header = rows[0]
        markdown = "| " + " | ".join(header) + " |\n"
        markdown += "|" + "|".join(["---"] * num_cols) + "|\n"
        
        # Body
        for row in rows[1:]:
            while len(row) < num_cols:
                row.append("")
            row = row[:num_cols]
            markdown += "| " + " | ".join(row) + " |\n"
        
        return markdown + "\n"
