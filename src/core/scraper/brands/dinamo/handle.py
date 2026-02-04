from src.core.scraper.brands.dinamo.images.executor import handle_images
from src.core.scraper.brands.dinamo.technical_specs.executor import handle_technical_specs


def handle_dinamo(handle_type:str, content: list[str]) -> list:
    """
    Maneja el caso específico de la marca Dinamo
    """

    if handle_type == "images":
        print("Tipo de contenido: Images")
        return handle_images(content)

    if handle_type == "technical_specs":
        print("Tipo de contenido: Technical Specs")
        return handle_technical_specs(content)
