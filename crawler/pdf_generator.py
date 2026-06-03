import requests
import io
import logging
import urllib.parse
from bs4 import BeautifulSoup
from PIL import Image
from pathlib import Path

logger = logging.getLogger(__name__)

class PDFGenerator:
    """Class to extract images from HTML and save them as a single PDF"""
    
    def __init__(self):
        pass

    def extract_images_and_save_pdf(self, html: str, base_url: str, output_path: str) -> bool:
        """
        Extract images from HTML, download them, and combine into a PDF
        """
        soup = BeautifulSoup(html, "html.parser")
        images = []
        
        # 1. Extract image URLs
        for img in soup.find_all('img'):
            src = img.get('src', '').strip()
            if not src:
                continue
                
            # Resolve Next.js image paths
            if src.startswith("/_next/image?url="):
                parsed = urllib.parse.urlparse(src)
                qs = urllib.parse.parse_qs(parsed.query)
                if "url" in qs:
                    src = qs["url"][0]
            
            # Document images are always hosted on cdn.xanhsm.com
            if "cdn.xanhsm.com" not in src:
                continue
                
            images.append(src)
            
        if not images:
            logger.warning(f"No valid images found for PDF generation on {base_url}")
            return False
            
        # Remove duplicates while preserving order
        seen = set()
        unique_images = []
        for img in images:
            if img not in seen:
                seen.add(img)
                unique_images.append(img)
                
        # 2. Download and convert images
        pil_images = []
        for url in unique_images:
            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                image = Image.open(io.BytesIO(response.content))
                
                # Convert to RGB (required for saving as PDF)
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                pil_images.append(image)
            except Exception as e:
                logger.error(f"Failed to download or convert image {url}: {e}")
                
        # 3. Save as PDF
        if not pil_images:
            logger.warning(f"No images successfully downloaded for {base_url}")
            return False
            
        try:
            # Create directory if it doesn't exist
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            first_image = pil_images[0]
            first_image.save(
                output_path, 
                "PDF", 
                resolution=100.0, 
                save_all=True, 
                append_images=pil_images[1:]
            )
            logger.info(f"Successfully saved PDF to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save PDF {output_path}: {e}")
            return False
