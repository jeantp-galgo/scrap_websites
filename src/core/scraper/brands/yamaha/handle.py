from src.core.scraper.brands.yamaha.images.executor import handle_images
from src.core.scraper.brands.yamaha.technical_specs.executor import handle_technical_specs

def handle_yamaha(url: str, handle_type:str, content: list[str]) -> list:
    """
    Maneja el caso específico de la marca yamaha
    """

    if handle_type == "images":
        return handle_images(url, content)

    if handle_type == "technical_specs":
        return handle_technical_specs(url, content)