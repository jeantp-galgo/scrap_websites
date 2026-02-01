from src.core.scraper.images.brands.vento.utils import create_urls_from_pattern

def detect_url_pattern(images_list: list[str]):
    """
    Detecta el patrón de las imágenes de la marca Vento y devuelve las imágenes y las URLs de las imágenes.
    """
    for image in images_list:
        if image.endswith("-01.jpg"):
            base_url = image.split("-01.jpg")[0]
            print(base_url)
            return base_url
    return None

def extract_main_images(base_url: str, images_list: list[str]):
    main_images = []
    for images in images_list:
        if base_url in images:
            main_images.append(images)
    return main_images

def handle_vento(extracted_images_list: list[str]) -> list:
    """
    Maneja el caso específico de la marca Vento
    """
    final_urls_list = []
    # Detecta el patrón de la URL de las imágenes
    base_url = detect_url_pattern(extracted_images_list)
    # Se crea las URLs apartir de la URL base
    urls_created_from_pattern = create_urls_from_pattern(base_url)
    # Se filtran las imágenes principales en base a la url base
    main_images = extract_main_images(base_url, extracted_images_list)

    # Se agregan todos los resultados en una sola lista
    for image in main_images:
        final_urls_list.append(image)

    for url in urls_created_from_pattern:
        final_urls_list.append(url)

    return final_urls_list