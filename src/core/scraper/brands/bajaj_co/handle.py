from src.core.scraper.brands.bajaj_co.images.executor import handle_images
# from src.core.scraper.brands.bajaj_co.technical_specs.executor import handle_technical_specs


def handle_bajaj_co(handle_type:str, content) -> list:
    """
    Maneja el caso específico de la marca Bajaj_co
    """

    if handle_type == "images":
        print("Tipo de contenido: Images")
        return handle_images(content)

    # if handle_type == "technical_specs":
    #     print("Tipo de contenido: Technical Specs")
    #     return handle_technical_specs(content)
