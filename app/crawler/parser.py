import re
from bs4 import BeautifulSoup, NavigableString, Tag

class GreenSMHTMLParser:
    """
    Highly robust HTML-to-Markdown parser for legal, terms, and policies documents.
    Preserves tables, lists, hierarchy, and metadata elements while stripping out
    navigation, headers, footers, and scripts.
    """
    
    def __init__(self):
        pass

    def clean_html(self, soup: BeautifulSoup) -> BeautifulSoup:
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "header", "footer", "iframe", "noscript"]):
            element.decompose()
        return soup

    def element_to_markdown(self, element) -> str:
        if isinstance(element, NavigableString):
            return str(element)
            
        if not isinstance(element, Tag):
            return ""

        tag_name = element.name
        
        # Handle Headings
        if tag_name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag_name[1])
            text = self.get_inner_text(element)
            return f"\n\n{'#' * level} {text}\n\n"
            
        # Handle Paragraphs
        elif tag_name == "p":
            text = self.get_inner_text(element)
            return f"\n\n{text}\n\n"
            
        # Handle Bold/Strong
        elif tag_name in ["strong", "b"]:
            text = self.get_inner_text(element)
            return f"**{text}**"
            
        # Handle Italics
        elif tag_name in ["em", "i"]:
            text = self.get_inner_text(element)
            return f"*{text}*"
            
        # Handle Lists
        elif tag_name == "ul":
            items = []
            for child in element.find_all("li", recursive=False):
                child_text = self.get_inner_text(child).strip()
                if child_text:
                    items.append(f"- {child_text}")
            return "\n" + "\n".join(items) + "\n"
            
        elif tag_name == "ol":
            items = []
            for idx, child in enumerate(element.find_all("li", recursive=False)):
                child_text = self.get_inner_text(child).strip()
                if child_text:
                    items.append(f"{idx + 1}. {child_text}")
            return "\n" + "\n".join(items) + "\n"
            
        # Handle Links
        elif tag_name == "a":
            href = element.get("href", "")
            text = self.get_inner_text(element)
            if href and text:
                return f"[{text}]({href})"
            return text
            
        # Handle Tables (Crucial for legal documents)
        elif tag_name == "table":
            return self.table_to_markdown(element)
            
        # Generic block/inline container fallback
        else:
            markdown = ""
            for child in element.children:
                markdown += self.element_to_markdown(child)
            return markdown

    def get_inner_text(self, tag: Tag) -> str:
        text = ""
        for child in tag.children:
            if isinstance(child, NavigableString):
                text += str(child)
            elif isinstance(child, Tag):
                text += self.get_inner_text(child)
        # Normalize whitespace
        return re.sub(r'\s+', ' ', text).strip()

    def table_to_markdown(self, table_tag: Tag) -> str:
        rows = table_tag.find_all("tr")
        if not rows:
            return ""
            
        markdown_rows = []
        
        # Parse header row
        headers = []
        header_cells = rows[0].find_all(["th", "td"])
        for cell in header_cells:
            headers.append(self.get_inner_text(cell).strip())
            
        if not headers:
            return ""
            
        markdown_rows.append("\n\n| " + " | ".join(headers) + " |")
        markdown_rows.append("| " + " | ".join(["---"] * len(headers)) + " |")
        
        # Parse data rows
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            row_text = []
            for cell in cells:
                row_text.append(self.get_inner_text(cell).strip())
            # Fill missing cells with empty spaces
            while len(row_text) < len(headers):
                row_text.append("")
            # Truncate extra cells
            row_text = row_text[:len(headers)]
            markdown_rows.append("| " + " | ".join(row_text) + " |")
            
        markdown_rows.append("\n\n")
        return "\n".join(markdown_rows)

    def parse(self, html_content: str) -> str:
        soup = BeautifulSoup(html_content, "html.parser")
        soup = self.clean_html(soup)
        
        # Look for article or main content tags first to drop header/footer
        content_element = soup.find(["article", "main", "div", "section"], class_=re.compile("policy|content|terms|terms-policies", re.I))
        if not content_element:
            content_element = soup.find("body")
            
        if not content_element:
            content_element = soup
            
        markdown = self.element_to_markdown(content_element)
        
        # Post processing: clean up excessive newlines
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        return markdown.strip()

def html_to_markdown(html_content: str) -> str:
    parser = GreenSMHTMLParser()
    return parser.parse(html_content)
