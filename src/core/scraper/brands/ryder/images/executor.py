from bs4 import BeautifulSoup
import re

def extract_all_input_values(html_input_with_colors_value):
    values = []
    for input_tag in html_input_with_colors_value:
        value = input_tag.get("value")
        values.append(value)
    return values

def extract_all_colors_name_available_with_values(model_name, html_span_with_colors_name, colors_value_list):
    # Detectar cada span con los nombres de los colores
    span_color_list = [] # Se guarda los span que contiene cada nombre de color

    for span in html_span_with_colors_name:
        if f"{model_name} (" in span.get_text(strip=True): # Solo traerá: <span>AD-1 (AZUL)</span>
            # Extraer solo el texto dentro de los paréntesis
            match = re.search(r'\(([^)]+)\)', span.get_text(strip=True)) # <span>AD-1 (AZUL)</span> -> AZUL
            if match:
                color = match.group(1)
                span_color_list.append(color)

    color_dict = [{"color": color, "value": value} for color, value in zip(span_color_list, colors_value_list)]

    # Se crea un diciconario de listas con cada color y valor para luego armar la URL
    return color_dict

def extract_html_content(content: str) -> str:
    soup = BeautifulSoup(content, "html.parser")
    model_name = soup.find("h1").get_text(strip=True)
    html_input_with_colors_value = soup.find_all("input", class_="js_product_change")
    html_span_with_colors_name = soup.find_all("span")
    return model_name, html_input_with_colors_value, html_span_with_colors_name

def handle_main_colors_images(content:list[str]) -> list:
    main_images_list = []
    model_name, html_input_with_colors_value, html_span_with_colors_name = extract_html_content(content)

    colors_value_list = extract_all_input_values(html_input_with_colors_value)
    dict_colors_and_values = extract_all_colors_name_available_with_values(model_name, html_span_with_colors_name, colors_value_list)
    for color_dict in dict_colors_and_values:
        main_images_list.append(f"https://www.rydermx.com/web/image/product.product/{color_dict['value']}/image_1024/{model_name}%20%28{color_dict['color']}%29?unique=b3a6ac0")
    return main_images_list

def handle_gallery_images(content: list[str]) -> list:
    gallery_images_list = []
    for images in content:
        if "/image_1024/" in images:
            gallery_images_list.append(images)
    return gallery_images_list

def handle_images(content: list[str]) -> list:
    final_list_images = []
    main_images_list = handle_main_colors_images(content.html)
    gallery_images_list = handle_gallery_images(content.images)

    for principal_image in main_images_list:
        final_list_images.append(principal_image)

    for gallery in gallery_images_list:
        final_list_images.append(gallery)

    return final_list_images