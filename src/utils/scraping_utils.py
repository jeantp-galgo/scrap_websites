from firecrawl import Firecrawl
from utils.process_firecrawl_response import get_urls_from_firecrawl_map

class ScrapingUtils:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.firecrawl = Firecrawl(api_key=self.api_key)

    def get_all_urls_from_website(self, url: str):
        """ Trae todas las URLs de un sitio web """
        url_list = self.firecrawl.map(url=url)
        return get_urls_from_firecrawl_map(url_list)

    def get_data_from_website(self, url: str, extract_prices: bool = False, prompt: str = None):
        """
        Trae los datos de un sitio web.

        Args:
            url: URL del sitio web a scrapear
            extract_prices: Si es True, incluye extracción de precios usando prompt JSON
        """
        formats = ["markdown", "html", "links", "images"]

        default_prompt = "Extract product pricing information and available colors from this page. Return a JSON object with the following structure: {\"precio_base\": number or null (base price without discount/bonus), \"precio_neto\": number or null (final price with discount/bonus applied),\"descuento\": number or null (discount amount), \"modelo\": string or null (product model name), \"colores\": array of strings or null (list of available colors for this product model, e.g. [\"Rojo\", \"Negro\", \"Blanco\"] or null if not found)}. If prices are not found or not available, return null for price fields. Extract prices as numbers without currency symbols, dots, or commas. Extract colors as an array of color names in Spanish or English."

        if prompt is None:
            prompt = default_prompt

        if extract_prices:
            # Agregar formato JSON con prompt para extraer precios y colores
            price_prompt = {
                "type": "json",
                "prompt": prompt
            }
            formats.append(price_prompt)

        # Configurar acciones para mejorar la carga de contenido lazy-load
        # Hacer scroll hacia abajo para activar la carga de imágenes lazy-load
        actions = [
            {"type": "scroll", "direction": "down"},  # Scroll inicial
            {"type": "wait", "milliseconds": 2000},  # Esperar 2 segundos después del scroll
            {"type": "scroll", "direction": "down"},  # Scroll adicional
            {"type": "wait", "milliseconds": 2000},  # Esperar otros 2 segundos
        ]

        # Opciones de scraping mejoradas
        doc = self.firecrawl.scrape(
            url=url,
            formats=formats,
            wait_for=3000,  # Esperar 3 segundos iniciales para que la página cargue
            timeout=120000,  # Aumentar timeout a 120 segundos (2 minutos) para páginas lentas
            only_main_content=True,  # Enfocarse solo en el contenido principal (elimina headers, footers, sidebars)
            block_ads=True,  # Bloquear anuncios que pueden interferir
            exclude_tags=["script", "style", "noscript"],  # Excluir tags innecesarios
            actions=actions  # Ejecutar acciones de scroll y wait
        )
        return doc

    def get_images_from_website(self, url: str):
        """
        Trae las imágenes de un sitio web usando un prompt JSON.
        Útil para extraer imágenes que pueden estar en srcset, noscript, o lazy-loaded.

        Args:
            url: URL del sitio web a scrapear
        """
        formats = ["links", "images"]

        # Agregar formato JSON con prompt para extraer imágenes
        images_prompt = {
            "type": "json",
            "prompt": "Extract all image URLs from this page. Return a JSON object with the following structure: {\"imagenes\": array of strings (list of all image URLs found on the page, including those in img src, img srcset, img data-src, img data-srcset, noscript img tags, background-image styles, and any other image sources). Include only direct URLs to image files (jpg, jpeg, png, gif, webp, svg, bmp, tiff). For srcset attributes, extract all URLs. Exclude placeholder images (data:image URLs). Return an empty array if no images are found."
        }
        formats.append(images_prompt)

        # Configurar acciones para mejorar la carga de contenido lazy-load
        # Hacer scroll hacia abajo para activar la carga de imágenes lazy-load
        actions = [
            {"type": "scroll", "direction": "down"},  # Scroll inicial
            {"type": "wait", "milliseconds": 2000},  # Esperar 2 segundos después del scroll
            {"type": "scroll", "direction": "down"},  # Scroll adicional
            {"type": "wait", "milliseconds": 2000},  # Esperar otros 2 segundos
        ]

        # Opciones de scraping mejoradas
        doc = self.firecrawl.scrape(
            url=url,
            formats=formats,
            wait_for=3000,  # Esperar 3 segundos iniciales para que la página cargue
            timeout=120000,  # Aumentar timeout a 120 segundos (2 minutos) para páginas lentas
            only_main_content=True,  # Enfocarse solo en el contenido principal (elimina headers, footers, sidebars)
            block_ads=True,  # Bloquear anuncios que pueden interferir
            exclude_tags=["script", "style"],  # Excluir script y style, pero NO noscript (necesitamos esas imágenes)
            actions=actions  # Ejecutar acciones de scroll y wait
        )
        return doc