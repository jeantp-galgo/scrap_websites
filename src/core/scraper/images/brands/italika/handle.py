from src.core.scraper.images.brands.italika.utils import extract_main_images
# *: Las URLs de interés son aquellas que tienen "width" o "height" incluída.

def handle_italika(extracted_images_list):
    return extract_main_images(extracted_images_list)