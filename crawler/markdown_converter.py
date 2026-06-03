"""
Phase 4: HTML → Markdown
Cải thiện xử lý text dính vào nhau, xóa header/footer tốt hơn
"""

from bs4 import BeautifulSoup, NavigableString
import logging
import re

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
                    
        # Xóa block "Danh mục khác"
        for tag in soup.find_all(string=lambda t: t and 'Danh mục khác' in t):
            if hasattr(tag, 'parent'):
                parent = tag.parent
                if parent and parent.parent and parent.parent.parent:
                    parent.parent.parent.decompose()
            
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
    
    def _extract_next_tables(self, data) -> str:
        md = ""
        def find_all_price_tables(d, path_name="Bảng giá"):
            tables = []
            if isinstance(d, dict):
                for k, v in d.items():
                    if isinstance(v, (dict, list)):
                        tables.extend(find_all_price_tables(v, k))
            elif isinstance(d, list):
                if len(d) > 0 and isinstance(d[0], dict) and "city" in d[0] and "items" in d[0]:
                    tables.append((path_name, d))
                else:
                    for item in d:
                        if isinstance(item, (dict, list)):
                            tables.extend(find_all_price_tables(item, path_name))
            return tables

        tables_found = find_all_price_tables(data)
        
        # Group by path_name and avoid exact duplicates if any
        grouped = {}
        for name, table in tables_found:
            # Format name nicely
            display_name = name.replace("_", " ").title()
            if display_name not in grouped:
                grouped[display_name] = []
            grouped[display_name].append(table)
            
        for group_name, table_lists in grouped.items():
            md += f"### {group_name}\n\n"
            # Since a group might have multiple identical lists (e.g., from different parts of state), 
            # we just take the first one or merge them. Usually taking the first one for the same name is enough,
            # but they might have different cities. Let's merge by city.
            cities_merged = {}
            for table_list in table_lists:
                for item in table_list:
                    c = item.get("city", "Khác")
                    if c not in cities_merged:
                        cities_merged[c] = item.get("items", [])
                        
            for city, items in cities_merged.items():
                if items and isinstance(items, list):
                    md += f"#### Tỉnh/Thành phố: {city}\n\n"
                    md += "| Loại phí | Mức giá |\n"
                    md += "|----------|---------|\n"
                    for item in items:
                        v1 = str(item.get("value1", "")).replace('\n', ' ') if item.get("value1") else ""
                        v2 = str(item.get("value2", "")).replace('\n', ' ') if item.get("value2") else ""
                        if v1 and v1.strip() != "None" and v1.strip() != "":
                            md += f"| {v1} | {v2} |\n"
                    md += "\n"
        return md
        
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
        
        # Extract general items for terms-policies pages
        if "terms-policies" in url:
            try:
                general_items = data.get("props", {}).get("pageProps", {}).get("generalTerms", {}).get("generalItems", [])
                for item in general_items:
                    title = item.get("title")
                    desc = item.get("description")
                    if title and desc:
                        faqs_found.append((title, desc))
            except Exception as e:
                logger.error(f"Error parsing generalItems: {e}")
        
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
        """Chuyển element thành Markdown với newlines giữa các block elements"""
        if isinstance(elem, NavigableString):
            text = str(elem).strip()
            if text:
                # Thêm space giữa các từ dính vào nhau (tiếng Việt)
                text = re.sub(r'([a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ0-9])([A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ])', r'\1 \2', text)
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
                        text = re.sub(r'([a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ0-9])([A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ])', r'\1 \2', text)
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
        text = re.sub(r'([a-zàáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềế ểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ0-9])([A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ])', r'\1 \2', text)
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
