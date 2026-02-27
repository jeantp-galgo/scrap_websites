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


def extract_canva_images(og_image_url: str, iterations: int = 6) -> list[str]:
    """
    Extrae imágenes de Canva iterando el número en la URL de og_image.

    Args:
        og_image_url: URL de og_image, ej: https://auteco.vtexassets.com/arquivos/ids/1506638/...
        iterations: Número de iteraciones (default: 6)

    Returns:
        Lista de URLs de imágenes que existen
    """
    import requests

    # Extraer el número de la URL
    # Ejemplo: https://auteco.vtexassets.com/arquivos/ids/1506638/... -> 1506638
    parts = og_image_url.split("/")
    ids_index = -1
    for i, part in enumerate(parts):
        if part == "ids":
            ids_index = i
            break

    if ids_index == -1 or ids_index + 1 >= len(parts):
        print(f"Error: No se encontró número después de 'ids' en {og_image_url}")
        return []

    try:
        base_number = int(parts[ids_index + 1])
    except ValueError:
        print(f"Error: No se pudo convertir a número: {parts[ids_index + 1]}")
        return []

    # Construir URL base
    url_base = f"https://auteco.vtexassets.com/arquivos/ids/"

    # Iterar y construir URLs
    # Las URLs de VTEX suelen funcionar directamente con el número
    canva_urls = []
    for i in range(iterations):
        number = base_number + i
        url = f"{url_base}{number}/"
        canva_urls.append(url)

    # Validar que las URLs existan
    valid_urls = []
    for url in canva_urls:
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                valid_urls.append(url)
        except Exception as e:
            print(f"Error validando URL {url}: {e}")

    return valid_urls


def handle_images(content_data):
    """
    Maneja la extracción de imágenes de galería.
    Procesa imágenes tradicionales (si existen) y imágenes de Canva (si og_image está presente).
    """
    all_image_urls = []

    # Extraer content y og_image de la estructura recibida
    content = content_data.get("content")
    og_image = content_data.get("og_image")

    # 1. Procesar imágenes tradicionales (como siempre)
    if content and content.images:
        try:
            url_base, marca = detect_url_pattern(content.images)
            print(f"URL base tradicional: {url_base}")
            print(f"Marca detectada: {marca}")

            urls_list = create_urls_from_pattern(url_base, marca)
            urls_list_checked = get_images_from_url_pattern(urls_list)
            all_image_urls.extend(urls_list_checked)
        except Exception as e:
            print(f"Error procesando imágenes tradicionales: {e}")

    # 2. Procesar imágenes de Canva (si og_image existe)
    if og_image:
        try:
            print(f"Procesando imágenes de Canva desde og_image: {og_image}")
            canva_urls = extract_canva_images(og_image)
            print(f"Imágenes de Canva encontradas: {len(canva_urls)}")
            all_image_urls.extend(canva_urls)
        except Exception as e:
            print(f"Error procesando imágenes de Canva: {e}")

    return all_image_urls