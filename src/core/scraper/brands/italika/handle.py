from src.core.scraper.brands.italika.images.executor import handle_images
from src.core.scraper.brands.italika.technical_specs.executor import handle_technical_specs
# *: Las URLs de interés son aquellas que tienen "width" o "height" incluída.

def handle_italika(handle_type:str, content: list[str]) -> list:
    """
    Maneja el caso específico de la marca Italika
    """
    # TODO ACÁ SE PODRIA MANEJAR EL FORMATO A RECIBIR / ENVIAR

    if handle_type == "images":
        print("Tipo de contenido: Images")
        return handle_images(content)

    if handle_type == "technical_specs":
        print("Tipo de contenido: Technical Specs")
        return handle_technical_specs(content)