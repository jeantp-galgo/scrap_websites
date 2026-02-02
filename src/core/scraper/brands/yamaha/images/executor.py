# from src.core.scraper.brands.vento.utils import create_urls_from_pattern

def detect_url_pattern(url: str):
    """
    Detecta el patrón de las imágenes de la marca y devuelve la URL base.
    """
    return url.split("/")[-1]

def extract_main_images(base_url: str, images_list: list[str]):
    main_images = []
    for images in images_list:
        if base_url in images:
            main_images.append(images)
    return main_images


def handle_images(url: str, extracted_images_list: list[str]):

    # Detecta el patrón de la URL de las imágenes
    base_url = detect_url_pattern(url)
    # Se filtran las imágenes principales en base a la url base
    main_images = extract_main_images(base_url, extracted_images_list)

    return main_images