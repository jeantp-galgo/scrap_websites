from src.core.scraper.images.brands.honda.utils import *
# *: Las URLs de interés son aquellas que tienen "width" o "height" incluída.

def handle_honda(extracted_images_list):
    """
    Maneja el caso específico de la marca Vento
    """
    final_urls_list = []

    models_colors = extract_model_colors(extracted_images_list)
    main_images = extract_main_images(extracted_images_list)

    # Se agregan todos los resultados en una sola lista
    for image in main_images:
        final_urls_list.append(image)

    for url in models_colors:
        final_urls_list.append(url)

    return final_urls_list