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

    def get_data_from_website(self, url: str, extract_prices: bool = False):
        """
        Trae los datos de un sitio web.

        Args:
            url: URL del sitio web a scrapear
            extract_prices: Si es True, incluye extracción de precios usando prompt JSON
        """
        formats = ["markdown", "html", "links", "images"]

        if extract_prices:
            # Agregar formato JSON con prompt para extraer precios y colores
            price_prompt = {
                "type": "json",
                "prompt": "Extract product pricing information and available colors from this page. Return a JSON object with the following structure: {\"precio_base\": number or null (base price without discount/bonus), \"precio_neto\": number or null (final price with discount/bonus applied),\"descuento\": number or null (discount amount), \"modelo\": string or null (product model name), \"colores\": array of strings or null (list of available colors for this product model, e.g. [\"Rojo\", \"Negro\", \"Blanco\"] or null if not found)}. If prices are not found or not available, return null for price fields. Extract prices as numbers without currency symbols, dots, or commas. Extract colors as an array of color names in Spanish or English."
            }
            formats.append(price_prompt)

        doc = self.firecrawl.scrape(url=url, formats=formats)
        return doc