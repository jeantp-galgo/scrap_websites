from src.core.scraper.app import ScrapingUtils
from src.core.scraper.generic_extractor import GenericExtractor
from src.core.scraper.brands.vento.handle import handle_vento
from src.core.scraper.brands.italika.handle import handle_italika
from src.core.scraper.brands.honda.handle import handle_honda
from src.core.scraper.brands.yamaha.handle import handle_yamaha
from src.core.scraper.brands.ryder.handle import handle_ryder
from src.core.scraper.brands.zmoto.handle import handle_zmoto
from src.core.scraper.brands.tvs.handle import handle_tvs
from src.core.scraper.brands.auteco_tvs.handle import handle_auteco_tvs
from src.core.scraper.brands.akt.handle import handle_akt
from src.core.scraper.brands.auteco_victory.handle import handle_auteco_victory
from src.core.scraper.brands.bajaj_co.handle import handle_bajaj_co
from src.core.scraper.brands.suzuki_co.handle import handle_suzuki_co


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
    if "yamaha-motor" in url:
        print("website: yamaha")
        return "yamaha"
    if "rydermx.com" in url :
        print("website: ryder")
        return "ryder"
    if "zmoto.com.mx" in url:
        print("website: zmoto")
        return "zmoto"
    if "tvsmotor.com" in url:
        print("website: tvsmotor")
        return "tvs"
    if "aktmotos.com" in url:
        print("website: aktmotos")
        return "aktmotos"
    if "grupouma.com" in url:
        print("website: bajaj_co")
        return "bajaj_co"
    if "suzuki.com.co" in url:
        print("website: suzuki_co")
        return "suzuki_co"
    if "auteco.com.co" in url:
        # Victory, Kawasaki y Kymco tienen su propio handler
        if "victory" in url or "kawasaki" in url or "kymco" in url:
            print("website: auteco victory o kawasaki o kymco")
            return "auteco_victory"
        # Todo lo demás en auteco.com.co es TVS (Apache, Raider, etc.)
        # No se puede confiar en el slug para detectar TVS (ej. /apache-rtr-... no contiene "tvs")
        print("website: auteco tvs")
        return "auteco_tvs"
    else:
        print("website: none")
        return None

class ImagesProcessor:
    def __init__(self):
        self.scraper = ScrapingUtils()
        self.generic_extractor = GenericExtractor()

    def test_extract(self, url: str, formats: list, **kwargs) -> list:
        content = self.scraper.get_content_from_website(url, formats=formats, **kwargs)
        return content

    def get_model_data(self, url: str):
        """Delega la extracción de datos del modelo al extractor genérico"""
        return self.generic_extractor.get_model_data(url)

    # TODO: Identificar qué característica está disponible para cada marca, es decir, extraer imágenes, ficha técnica o modeldata, o todos.
    def get_images_from_website(self, url: str, **kwargs) -> list:
        """
        Obtiene las imágenes de un sitio web. Se maneja el caso específico de una marca.
        Args:
            url: str
        Returns:
            images: list[str]
            image_urls: list[str]
        """
        website = check_website(url)

        if website == "suzuki_co":
            content = self.scraper.get_content_from_website(url, formats=["images"])
            return handle_suzuki_co("images", content)

        if website == "bajaj_co":
            # Playwright: 1 sesión, 1 click en el primer dsm_shapes → todos los rotators
            return handle_bajaj_co("images", url)
        if website == "vento":
            content = self.scraper.get_content_from_website(url, formats=["images"])
            return handle_vento("images", content.images, url=url)
        if website == "italika":
            content = self.scraper.get_content_from_website(url, formats=["images"])
            return handle_italika("images", content.images)
        if website == "honda":
            content = self.scraper.get_content_from_website(url, formats=["images"])
            return handle_honda("images", content.images)
        if website == "yamaha":
            content = self.scraper.get_content_from_website(url, formats=["images"])
            return handle_yamaha(url, "images", content.images)
        if website == "ryder":
            content = self.scraper.get_content_from_website(url, formats=["html", "images"])
            return handle_ryder("images", content)
        if website == "zmoto":
            content = self.scraper.get_content_from_website(url, formats=["html"])
            return handle_zmoto("images", content)
            # return content
        if website == "tvsmotor":
            content = self.scraper.get_content_from_website(url, formats=["html"])
            return handle_tvs("images", content)
        if website == "aktmotos":
            content = self.scraper.get_content_from_website(url, formats=["html"])
            return handle_akt("images", content)
        if website == "auteco_tvs":
            # Playwright obtiene og_image y captura las imágenes del canvas directamente.
            # No se necesita Firecrawl: og_image se lee del DOM en la misma sesión de Playwright.
            content_to_send = {
                "content": None,
                "og_image": None,
                "page_url": url,
            }
            return handle_auteco_tvs("images", content_to_send)
        if website == "auteco_victory":
            content = self.scraper.get_content_from_website(url, formats=["images"], wait_for=5000)
            return handle_auteco_victory("images", content.images)
        if website == None:
            print("No se encontró sitio, se usa el formato de imágenes por defecto")
            content = self.scraper.get_content_from_website(url, formats=["images"], wait_for=5000)
            return content.images
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
            content = self.scraper.get_content_from_website(
                url,
                formats=["html"],
                actions=actions,
                wait_for=1200,
            )
            return handle_honda("technical_specs", content)

        if website == "vento":
            content = self.scraper.get_content_from_website(url, formats=["links"])
            return handle_vento("technical_specs", content)

        if website == "italika":
            content = self.scraper.get_content_from_website(url, formats=["html"])
            return handle_italika("technical_specs", content)

        if website == "yamaha":
            content = self.scraper.get_content_from_website(url, formats=["html"])
            return handle_yamaha(url, "technical_specs", content)

        if website == "ryder":
            content = self.scraper.get_content_from_website(url, formats=["html"])
            return handle_ryder("technical_specs", content)

        if website == "zmoto":
            content = self.scraper.get_content_from_website(url, formats=["html"])
            return handle_zmoto("technical_specs", content)

        if website == "tvs":
            content = self.scraper.get_content_from_website(url,
            formats=["html"],
            wait_for=5000)
            return handle_tvs("technical_specs", content)

        if website == "auteco_tvs":
            # El componente de specs es 100% JS (VTEX), Firecrawl no lo renderiza.
            # Pasamos un objeto con la URL para que el executor use Playwright directamente.
            class _UrlContent:
                def __init__(self, u):
                    self.html = None
                    class _Meta:
                        def __init__(self, u): self.url = u
                    self.metadata = _Meta(u)
            return handle_auteco_tvs("technical_specs", _UrlContent(url))

        if website == "auteco_victory":
            print("Ejecutando auteco victory")
            return self.generic_technical_specs(url)

        if website == "aktmotos":
            return self.generic_technical_specs(url)

        if website == "bajaj_co":
            return self.generic_technical_specs(url)

        if website == "suzuki_co":
            return self.generic_technical_specs(url)

        if website == None:
            print("No se encontró sitio, se usa el formato genérico de ficha técnica")
            return self.generic_technical_specs(url)

    def generic_technical_specs(self, url: str) -> list:
        """
        Obtiene las fichas técnicas de un sitio web usando el extractor genérico.
        Args:
            url: str
        Returns:
            technical_specs: list[str]
        """
        technical_specs_data = self.generic_extractor.get_technical_specs_data(url)
        return technical_specs_data.model_dump(exclude_none=False)