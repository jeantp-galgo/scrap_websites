from bs4 import BeautifulSoup
import re

def extract_all_input_values(html_input_with_colors_value):
    values = []
    for input_tag in html_input_with_colors_value:
        value = input_tag.get("title")
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
    # model_name = soup.find("h1").get_text(strip=True)
    html_input_with_colors_value = soup.find_all("input", class_="js_variant_change")
    return html_input_with_colors_value

def handle_images(content: list[str]):
    main_images_list = []
    html_input_with_colors_value = extract_html_content(content.html)
    colors_value_list = extract_all_input_values(html_input_with_colors_value)
    print("extract_all_input_values: colors_value_list")
    for color_dict in colors_value_list:
        main_images_list.append(f"https://www.zmoto.com.mx/web/image/product.product/104795/image_1024/")
    return main_images_list