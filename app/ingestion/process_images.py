import os
import re
import base64
import requests
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.core.logger import log_info, log_error

# Load environment variables
load_dotenv()

# Initialize VLM
vlm_model = os.getenv("VLM_MODEL", "gpt-4o")
llm = ChatOpenAI(model=vlm_model, max_tokens=2000)

def get_image_base64_from_url(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    return base64.b64encode(response.content).decode('utf-8')

def process_image(image_url: str, log_callback=None) -> str:
    msg = f"Đang xử lý ảnh: {image_url}"
    log_info("VLM", msg)
    if log_callback: log_callback(msg)
    try:
        base64_image = get_image_base64_from_url(image_url)
        message = HumanMessage(
            content=[
                {"type": "text", "text": "Extract all text and tables from this image. Format the output strictly as Markdown. Do not include any introductory or concluding text, only the extracted markdown content."},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                },
            ]
        )
        response = llm.invoke([message])
        markdown_text = response.content.strip()
        
        # Remove markdown code blocks if the model wrapped it
        if markdown_text.startswith("```markdown"):
            markdown_text = markdown_text[len("```markdown"):].strip()
        if markdown_text.startswith("```"):
            markdown_text = markdown_text[3:].strip()
        if markdown_text.endswith("```"):
            markdown_text = markdown_text[:-3].strip()
            
        return markdown_text
    except Exception as e:
        err_msg = f"Lỗi xử lý {image_url}: {e}"
        log_error("VLM", err_msg)
        if log_callback: log_callback(err_msg)
        return None

def process_file(file_path: str, log_callback=None):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to find markdown images: ![](url) or ![alt](url)
    image_pattern = re.compile(r'!\[.*?\]\((https?://[^\)]+)\)')
    
    matches = image_pattern.findall(content)
    if not matches:
        return
        
    # Lọc bỏ các ảnh rác (logo, icon, banner, v.v.)
    valid_matches = []
    junk_keywords = ['logo', 'icon', 'banner', 'avatar', 'header', 'footer', '.svg']
    for url in matches:
        if not any(junk in url.lower() for junk in junk_keywords):
            valid_matches.append(url)
            
    if not valid_matches:
        return
    
    msg = f"Tìm thấy {len(valid_matches)} ảnh hợp lệ trong {os.path.basename(file_path)}"
    log_info("VLM", msg)
    if log_callback: log_callback(msg)
    
    new_content = content
    
    for url in valid_matches:
        extracted_md = process_image(url, log_callback)
        if extracted_md:
            # Giữ nguyên thẻ ảnh và chèn nội dung phía dưới
            full_tag_pattern = re.compile(r'(!\[.*?\]\(' + re.escape(url) + r'\))')
            replacement = r'\1\n\n' + extracted_md.replace('\\', '\\\\') + r'\n'
            new_content = full_tag_pattern.sub(replacement, new_content, count=1)

    if new_content != content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        success_msg = f"Đã cập nhật file: {os.path.basename(file_path)}"
        log_info("VLM", success_msg)
        if log_callback: log_callback(success_msg)

def process_markdown_images_in_directory(data_dir: str, log_callback=None):
    """
    Scans the given directory for markdown files and processes any images found within them using VLM.
    Replaces image tags with the extracted markdown text.
    """
    if not os.path.exists(data_dir):
        log_error("VLM", f"Data directory not found: {data_dir}")
        return

    for root, _, files in os.walk(data_dir):
        for file in files:
            if file.endswith(".md"):
                process_file(os.path.join(root, file), log_callback)
