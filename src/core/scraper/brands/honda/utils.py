import re

def extract_main_images(images_list: list[str]):
    """
    Extrae las imágenes galeria de la moto filtrando URLs no deseadas.
    Args:
        images_list: list[str]
    Returns:
        main_images: list[str]
    """
    main_images = []
    for image in images_list:
    # Imagen correcta: https://www.honda.mx/web/img/motorcycles/models/naked/cb650r/gallery/2.jpg
        if "/gallery/" in image:
            # No buscamos: https://www.honda.mx/web/img/motorcycles/models/naked/cb650r/gallery/thumbs/4.jpg
            if not "/thumbs/" in image:
                main_images.append(image)
    return main_images

def extract_model_colors(image_list):
    """
    Extrae las imágenes principales de la moto apartir de los colores disponibles.
    Args:
        image_list: list[str]
    Returns:
        available_colors: list[str]
    """
    available_colors = []
    for image in image_list:
        match = re.search(r'/thumbs/([^/]+)', image)
        # Match esperado ejemplo: https://www.honda.mx/web/img/motorcycles/models/naked/cb650r/colors/thumbs/rojo.jpg
        # Match no esperado ejemplo: https://www.honda.mx/web/img/motorcycles/models/naked/cb650r/gallery/thumbs/5.jpg
        if match:
            text = match.group(1)
            if not text[0].isdigit(): # El esperado inicia por texto, el no esperado es un número (urls de arriba)
                # Se reemplaza el texto /thumbs/ por /, y se cambia la extensión de .jpg a .png
                texto_eliminar = image.replace("/thumbs/", "/")
                extension_modificar = texto_eliminar.replace(".jpg", ".png")
                # Quedando como: https://www.honda.mx/web/img/motorcycles/models/naked/cb650r/colors/rojo.png
                available_colors.append(extension_modificar)
    return available_colors