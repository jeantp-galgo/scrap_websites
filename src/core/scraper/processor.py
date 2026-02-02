from src.core.scraper.app import ScrapingUtils
from src.core.scraper.brands.vento.handle import handle_vento
from src.core.scraper.brands.italika.handle import handle_italika
from src.core.scraper.brands.honda.handle import handle_honda

def check_website(url):
    print("url", url)
    if "vento.com" in url:
        print("website: vento")
        return "vento"
    if "italika.mx" in url:
        print("website: italika")
        return "italika"
    if "honda.mx" in url:
        print("website: honda")
        return "honda"
    else:
        print("website: none")
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
            return handle_vento("images", content.images)
        if website == "italika":
            return handle_italika("images", content.images)
        if website == "honda":
            return handle_honda("images", content.images)
        return content

    def get_technical_specs(self, url: str) -> list:
        """
        Obtiene las fichas técnicas de un sitio web.
        Args:
            url: str
        Returns:
            technical_specs: list[str]
        """
        website = check_website(url)
        if website == "honda":
            actions = [
                {"type": "click", "selector": "a.btn-specs"},  # click para desplegar la ficha
                {"type": "wait", "milliseconds": 1200},        # espera a que cargue el contenido
            ]
            wait_for = 1200
            content = self.scraper.get_content_from_website(
                url,
                formats=["html"],
                actions=actions,
                wait_for=wait_for,
            )
            return handle_honda("technical_specs", content)

        if website == "vento":
            content = self.scraper.get_content_from_website(url, formats=["links"])
            return handle_vento("technical_specs", content)

        if website == "italika":
            content = self.scraper.get_content_from_website(url, formats=["html"])
            return handle_italika("technical_specs", content)
        return content