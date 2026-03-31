from src.core.scraper.brands.vento.images.executor import handle_images
from src.core.scraper.brands.vento.technical_specs.executor import handle_technical_specs

def handle_vento(handle_type: str, content: list[str], url: str = "") -> list:
    """
    Maneja el caso específico de la marca Vento
    """
    if handle_type == "images":
        # Extraer el slug del modelo desde la URL para filtrar imágenes relevantes
        from urllib.parse import urlparse
        slug = urlparse(url).path if url else ""
        return handle_images(content, model_slug=slug)

    if handle_type == "technical_specs":
        return handle_technical_specs(content)