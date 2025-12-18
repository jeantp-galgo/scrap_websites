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

    def get_data_from_website(self, url: str):
        """ Trae los datos de un sitio web """
        doc = self.firecrawl.scrape(url=url, formats=["markdown", "html"])
        return doc