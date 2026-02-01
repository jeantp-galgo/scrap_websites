import re

def extract_main_images(images_list: list[str]):
    main_images = []
    for image in images_list:
        if "/gallery/" in image:
            if not "/thumbs/" in image:
                main_images.append(image)
    return main_images

def extract_model_colors(image_list):
    available_colors = []
    for image in image_list:
        match = re.search(r'/thumbs/([^/]+)', image)
        if match:
            text = match.group(1)
            if not text[0].isdigit():
                # Lo unico que lo diferencia es que tiene thumbs, se quita para ir a la principal
                texto_eliminar = image.replace("/thumbs/", "/")
                # La extensión parece ser la .png en todas
                extension_modificar = texto_eliminar.replace(".jpg", ".png")
                available_colors.append(extension_modificar)
    return available_colors