from src.core.scraper.app import ScrapingUtils
from src.core.scraper.images.brands.vento.handle import handle_vento
from src.core.scraper.images.brands.italika.handle import handle_italika

def check_website(url):
    print("url", url)
    if "vento.com" in url:
        return "vento"
    if "italika.mx" in url:
        return "italika"
    else:
        return None

class ImagesProcessor:
    def __init__(self):
        self.scraper = ScrapingUtils()

    def get_images_from_website(self, url: str) -> list:
        """
        Obtiene las imágenes de un sitio web. Se maneja el caso específico de una marca.
        Args:
            url: str
        Returns:
            images: list[str]
            image_urls: list[str]
        """
        website = check_website(url)
        content = self.scraper.get_content_from_website(url, formats=["images"])
        if website == "vento":
            return handle_vento(content.images)
        if website == "italika":
            return handle_italika(content.images)
        return content
