from bs4 import BeautifulSoup

def detect_url_pattern(uri_pattern:str) -> str:
    """
    Detecta el patrón de la URL de las imágenes de la marca Akt
    """
    text_to_extract_extension = uri_pattern.split("/")[-1] # 'akt-jet-evo-negro-01.webp'
    uri_base = uri_pattern.replace(text_to_extract_extension, "") # /wp-content/uploads/2026/01/ <-- Apartir de acá armaremos la URL
    model_name_uri = text_to_extract_extension.split(".")[0] # akt-jet-evo-negro-01 <-- Se tiene parte del nombre de la imagen
    model_name = model_name_uri.replace("-01", "") # akt-jet-evo-negro <-- Se quita el consecutivo final # ! Posiblemente no todos inicien con -01
    extension = text_to_extract_extension.split(".")[-1] # webp <-- Usada para completar la extensión de la URL

    return uri_base, model_name, extension #/wp-content/uploads/2026/01/, akt-jet-evo-negro, webp

def extract_total_images_and_uri_pattern(content: list[str]) -> tuple[str, str]:
    """ Extrae el total de imágenes y el patrón de la URL de las imágenes de la marca Akt """
    html = content.html
    soup = BeautifulSoup(html, "html.parser")
    specs_div = soup.find("div", id="contenedor-rotador-1")

    # Extraer el valor de total-images del tag image-rotator
    image_rotator = specs_div.find("image-rotator") if specs_div else None
    total_images = image_rotator.get("total-images") if image_rotator else None
    uri_pattern = image_rotator.get("src") if image_rotator else None
    return total_images, uri_pattern

def create_urls_from_pattern(uri_base:str, model_name:str, extension:str, total_images:str) -> list[str]:
    """ Crea las URLs de las imágenes de la marca Akt """
    image_list = []
    for i in range(0,int(total_images)):
        image_list.append(f"https://aktmotos.com/{uri_base}{model_name}-0{i+1}.{extension}")
    return image_list

def handle_images(content):
    total_images, uri_pattern = extract_total_images_and_uri_pattern(content)
    uri_base, model_name, extension = detect_url_pattern(uri_pattern)
    urls_list = create_urls_from_pattern(uri_base, model_name, extension, total_images)
    return urls_list