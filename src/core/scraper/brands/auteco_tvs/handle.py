from src.core.scraper.brands.auteco_tvs.images.executor import handle_images
# from src.core.scraper.brands.auteco_tvs.technical_specs.executor import handle_technical_specs


def handle_auteco_tvs(handle_type:str, content: list[str]) -> list:
    """
    Maneja el caso específico de la marca Auteco_tvs
    """

    if handle_type == "images":
        print("Tipo de contenido: Images")
        return handle_images(content)

    # if handle_type == "technical_specs":
    #     print("Tipo de contenido: Technical Specs")
    #     return handle_technical_specs(content)
