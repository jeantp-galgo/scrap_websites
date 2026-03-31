from src.core.scraper.brands.vento.utils import create_urls_from_pattern

# Patrones de imágenes globales del sitio Vento que no pertenecen a ningún modelo
_GLOBAL_IMAGE_PATTERNS = [
    "poliza-contra-robo",
    "cintillo",
    "cascos",
    "close-x",
    "menu",
    "widget",
    "ocular",
    "data:image",
]

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

def filter_model_images(images_list: list[str], model_slug: str) -> list[str]:
    """
    Filtra imágenes que pertenecen al modelo usando el slug de la URL.
    Descarta imágenes globales del sitio (menú, banners, widgets).
    """
    slug_parts = [p for p in model_slug.strip("/").split("-") if len(p) > 2]

    filtered = []
    for img in images_list:
        img_lower = img.lower()
        # Descartar imágenes globales conocidas
        if any(pat in img_lower for pat in _GLOBAL_IMAGE_PATTERNS):
            continue
        # Incluir solo imágenes que contengan al menos una parte del slug del modelo
        if any(part in img_lower for part in slug_parts):
            filtered.append(img)

    return filtered


def handle_images(extracted_images_list: list[str], model_slug: str = ""):

    final_urls_list = []
    # Detecta el patrón de la URL de las imágenes
    base_url = detect_url_pattern(extracted_images_list)

    # Si no se detecta el patrón -01.jpg, filtrar por slug del modelo
    if base_url is None:
        print("[vento] No se detectó patrón -01.jpg; filtrando imágenes por slug del modelo.")
        return filter_model_images(extracted_images_list, model_slug)

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