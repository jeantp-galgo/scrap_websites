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

def check_website(url, **kwargs):
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
    if "auteco.com.co" in url:
        sitio = kwargs.get("sitio")
        if sitio == "victory":
            print("website: auteco victory")
            return "auteco_victory"
        if sitio == "tvs":
            print("website: auteco tvs")
            return "auteco_tvs"
        if sitio == "ceronte":
            print("website: auteco ceronte")
            return "auteco_ceronte"
    else:
        print("website: none")
        return None

class ImagesProcessor:
    def __init__(self):
        self.scraper = ScrapingUtils()
        self.generic_extractor = GenericExtractor()

    def test_extract(self, url: str, formats: list) -> list:
        content = self.scraper.get_content_from_website(url, formats=formats, wait_for=5000)
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
        website = check_website(url, sitio=kwargs.get("sitio"))

        if website == "vento":
            content = self.scraper.get_content_from_website(url, formats=["images"])
            return handle_vento("images", content.images)
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

        if website == "auteco_tvs":
            content = self.scraper.get_content_from_website(url, formats=["images"], wait_for=5000)
            return handle_auteco_tvs("images", content)
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
        if website == None:
            print("No se encontró sitio, se usa el formato genérico de ficha técnica")
            technical_specs_data = self.generic_extractor.get_technical_specs_data(url)
            print("technical_specs_data", technical_specs_data)
            if technical_specs_data is None:
                return None
            # Convertir el modelo Pydantic a dict para mantener compatibilidad
            return technical_specs_data.model_dump(exclude_none=False)