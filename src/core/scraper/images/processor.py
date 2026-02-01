from src.core.scraper.app import ScrapingUtils
from src.core.scraper.images.utils import create_image_urls

def check_website(url):
    print("url", url)
    if "vento.com" in url:
        return "vento"
    else:
        return None

class ImagesProcessor:
    def __init__(self):
        self.scraper = ScrapingUtils()

    def get_images_from_website(self, url: str) -> list:
        """ Obtiene las imágenes de un sitio web """
        website = check_website(url)
        content = self.scraper.get_content_from_website(url, formats=["images"])
        if website == "vento":
            for image in content.images:
                if image.endswith("-01.jpg"):
                    base_url = image.split("-01.jpg")[0]
                    image_urls = create_image_urls(base_url)
                    return content.images, image_urls
        return content.images, []