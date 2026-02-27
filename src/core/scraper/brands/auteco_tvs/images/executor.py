# Lista de marcas conocidas (escalable)
MARCAS_CONOCIDAS = ["TVS", "Ceronte"]  # Agregar más marcas aquí según sea necesario

def detect_url_pattern(content: list[str]):
    """
    Detecta el patrón de URL base y si hay marca presente.
    Busca en todas las URLs con "interna-de-producto" para detectar si alguna contiene una marca.

    Retorna: (url_base, marca_detectada)
    - marca_detectada: str o None
    """
    url_base_to_process = None
    marca_detectada = None

    # Buscar en todas las URLs con "interna-de-producto" para detectar marca
    for image in content:
        print(image)
        if "interna-de-producto" in image:
            # Si aún no tenemos URL base, guardarla
            if url_base_to_process is None:
                url_base_to_process = image

            # Extraer nombre del archivo y verificar si contiene alguna marca
            filename = image.split("/")[-1]
            filename_without_ext = filename.split(".")[0]

            # Verificar si el nombre del archivo termina con alguna marca conocida
            for marca in MARCAS_CONOCIDAS:
                # Buscar marca al final del nombre (puede estar separada por _ o -)
                if filename_without_ext.upper().endswith(f"_{marca.upper()}") or \
                   filename_without_ext.upper().endswith(f"-{marca.upper()}"):
                    marca_detectada = marca.upper()
                    print(f"Marca detectada: {marca_detectada} en {filename}")
                    break

            # Si ya detectamos marca, no necesitamos seguir buscando
            if marca_detectada:
                break

    if url_base_to_process is None:
        raise ValueError("No se encontró URL con 'interna-de-producto'")

    # Extraer la URL base
    text_to_eliminate = url_base_to_process.split("/")[-1]
    url_base = url_base_to_process.replace(text_to_eliminate, "")

    return url_base, marca_detectada


def create_urls_from_pattern(url_base: str, marca: str = None):
    """
    Crea las URLs con todos los patrones posibles.
    Genera URLs con diferentes patrones y la validación determinará cuáles realmente existen.

    Patrones soportados:
    1. Galeria-imagen-{i} (patrón estándar con números)
    2. Galeria_imagen_{i}_{marca} (con marca y guiones bajos)
    3. galeria-imagen-nuevo{i} (patrón "nuevo" con número)
    """
    urls_list = []

    if marca:
        # Si hay marca detectada, crear URLs con AMBOS patrones
        # Patrón 1: Con marca (guiones bajos)
        for i in range(0, 7):
            urls_list.append(f"{url_base}Galeria_imagen_{i+1}_{marca}")

        # Patrón 2: Sin marca (guiones) - también intentar este patrón
        for i in range(0, 7):
            urls_list.append(f"{url_base}Galeria-imagen-{i+1}")
    else:
        # Si no hay marca, solo crear patrón con guiones
        for i in range(0, 7):
            urls_list.append(f"{url_base}Galeria-imagen-{i+1}")

    # Patrón 3: galeria-imagen-nuevo{i} - siempre intentar este patrón
    for i in range(1, 8):  # nuevo1, nuevo2, ..., nuevo7
        urls_list.append(f"{url_base}galeria-imagen-nuevo{i}")

    return urls_list


def get_images_from_url_pattern(urls_list: list[str]):
    import requests
    default_extension = "webp"
    alt_extension = "png"
    url_list_checked = []

    for url in urls_list:
        url_to_check = f"{url}.{default_extension}"
        response = requests.get(url_to_check)

        if response.status_code == 404:
            print(f"No se encontró la imagen con la extensión por defecto, se intenta con la extensión alternativa")
            url_alt_to_check = f"{url}.{alt_extension}"
            print(f"Probando con extensión alternativa: {url_alt_to_check}")
            response = requests.get(url_alt_to_check)

            if response.status_code == 200:
                url_list_checked.append(url_alt_to_check)
            elif response.status_code == 404:
                print(f"No se encontró la imagen con ninguna extensión: {url}")
        elif response.status_code == 200:
            url_list_checked.append(url_to_check)

    return url_list_checked


def handle_images(content: list[str]):
    """
    Maneja la extracción de imágenes de galería.
    Detecta automáticamente la marca en las URLs y prueba todos los patrones posibles:
    - Galeria-imagen-{i} (patrón estándar)
    - Galeria_imagen_{i}_{marca} (con marca, si se detecta)
    - galeria-imagen-nuevo{i} (patrón "nuevo")
    Solo retorna las URLs que realmente existen (validadas con requests).
    """
    # Detectar el patrón de URL y si hay marca
    url_base, marca = detect_url_pattern(content.images)
    print(f"URL base: {url_base}")
    print(f"Marca detectada: {marca}")

    # Crear las URLs con ambos patrones si hay marca, o solo con guiones si no hay marca
    urls_list = create_urls_from_pattern(url_base, marca)
    print(f"URLs list (con ambos patrones si aplica): {urls_list}")

    # Verificar las URLs y agregar solo las que existen
    # Esta función descartará automáticamente las que no existen
    urls_list_checked = get_images_from_url_pattern(urls_list)
    print(f"URLs list checked (solo las que existen): {urls_list_checked}")

    return urls_list_checked