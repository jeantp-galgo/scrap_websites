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


def capture_vtex_carousel_images(url: str, wait_ms: int = 8000) -> list[str]:
    """
    Captura las URLs de imágenes del carrusel de VTEX interceptando los requests de red.
    Funciona incluso cuando las imágenes se renderizan dentro de un canvas.

    Filtra solo las URLs del CDN de VTEX (auteco.vtexassets.com/arquivos/ids/).
    No depende de patrones de nombre ni de IDs consecutivos.

    Args:
        url: URL de la página del modelo
        wait_ms: Tiempo de espera adicional tras el scroll (ms)

    Returns:
        Lista de URLs únicas del carrusel (normalizadas a .../arquivos/ids/{ID}/)
    """
    import asyncio, threading

    VTEX_CDN_PATTERN = "auteco.vtexassets.com/arquivos/ids/"
    # Palabras clave para excluir imágenes que no son del carrusel (logos, iconos, etc.)
    EXCLUDE_KEYWORDS = ("logo", "icon", "favicon", "banner", "sprite", "badge", "selo")
    # Patrones de URL que indican thumbnails de selector de color (ej. ids/1502319-30px-30px?width=...)
    THUMBNAIL_PATTERNS = ("-30px-", "width=30", "height=30")

    async def _run_playwright_async():
        """Lógica de intercepción usando Playwright Async API."""
        from playwright.async_api import async_playwright

        captured = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            def on_response(response):
                req_url = response.url
                ctype = response.headers.get("content-type", "")
                resource_type = response.request.resource_type

                if VTEX_CDN_PATTERN not in req_url:
                    return

                is_image = (resource_type == "image" or "image/" in ctype.lower())
                if not is_image or response.status != 200:
                    return

                req_url_lower = req_url.lower()
                if any(kw in req_url_lower for kw in EXCLUDE_KEYWORDS):
                    return

                # Excluir thumbnails de selector de color (30x30px con query params de dimensión)
                if any(p in req_url for p in THUMBNAIL_PATTERNS):
                    return

                # Normalizar: quedarse solo con la URL base hasta el ID numérico
                # Ejemplo: .../arquivos/ids/1502300/nombre.jpg.png -> .../arquivos/ids/1502300/
                parts = req_url.split("/")
                try:
                    ids_idx = parts.index("ids")
                    normalized_url = "/".join(parts[:ids_idx + 2]) + "/"
                    captured.append(normalized_url)
                except ValueError:
                    captured.append(req_url)

            page.on("response", on_response)

            await page.goto(url, wait_until="domcontentloaded")

            # Espera inicial para que el JS de VTEX inicialice el carrusel
            await page.wait_for_timeout(3000)

            # Scroll progresivo para activar lazy loading del carrusel canvas
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(1000)
            await page.evaluate("window.scrollBy(0, 300)")
            await page.wait_for_timeout(1500)
            await page.evaluate("window.scrollBy(0, 300)")
            await page.wait_for_timeout(1500)
            await page.evaluate("window.scrollBy(0, 500)")
            await page.wait_for_timeout(2000)
            # Volver al inicio — el carrusel suele estar en el viewport superior
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(int(wait_ms * 0.5))

            await browser.close()

        return captured

    def _run_in_thread():
        """
        Ejecuta el event loop de asyncio en un thread separado.
        Necesario cuando se llama desde Jupyter (que ya tiene su propio event loop).
        En Windows, SelectorEventLoop no soporta subprocesos en threads secundarios:
        se debe usar ProactorEventLoop explícitamente.
        """
        import sys
        if sys.platform == "win32":
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_run_playwright_async())
        finally:
            loop.close()

    # Ejecutar siempre en thread separado para evitar conflicto con el event loop de Jupyter
    result_container = []
    exc_container = []

    def _thread_target():
        try:
            result_container.extend(_run_in_thread())
        except Exception as e:
            exc_container.append(e)

    t = threading.Thread(target=_thread_target)
    t.start()
    t.join()

    if exc_container:
        raise exc_container[0]

    captured_urls = result_container

    # Eliminar duplicados preservando orden de aparición
    seen = set()
    unique_urls = []
    for u in captured_urls:
        if u not in seen:
            seen.add(u)
            unique_urls.append(u)

    print(f"[capture_vtex_carousel_images] URLs capturadas: {len(unique_urls)}")
    return unique_urls


def extract_canva_images(og_image_url: str, iterations: int = 6) -> list[str]:
    """
    Extrae imágenes iterando el número en la URL de og_image.
    Fallback de último recurso cuando Playwright no captura nada.

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

    url_base = "https://auteco.vtexassets.com/arquivos/ids/"

    canva_urls = []
    for i in range(iterations):
        number = base_number + i
        url = f"{url_base}{number}/"
        canva_urls.append(url)

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

    Flujo de prioridad:
    1. Playwright (canvas vtexassets) — si og_image apunta a vtexassets/arquivos/ids/
    2. Imágenes tradicionales (patrón URL estándar con nombres de archivo)
    3. Fallback: og_image con incremento secuencial (último recurso)
    """
    all_image_urls = []

    # Extraer datos de la estructura recibida
    content = content_data.get("content")
    og_image = content_data.get("og_image")
    page_url = content_data.get("page_url")

    # 1. Interceptar requests de red con Playwright cuando hay canvas vtexassets
    # El og_image apuntando a vtexassets/arquivos/ids/ es la señal de que hay carrusel canvas
    canvas_urls = []
    if page_url and og_image and "vtexassets.com/arquivos/ids/" in og_image:
        try:
            print(f"Interceptando requests de red (canvas detectado por og_image vtexassets): {page_url}")
            canvas_urls = capture_vtex_carousel_images(page_url)
            print(f"Imágenes capturadas por intercepción de red: {len(canvas_urls)}")
        except Exception as e:
            print(f"Error capturando imágenes por red: {e}")

    if canvas_urls:
        all_image_urls.extend(canvas_urls)
        return all_image_urls

    # 2. Procesar imágenes tradicionales (patrón de nombre de archivo)
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

    if all_image_urls:
        return all_image_urls

    # 3. Fallback: og_image con incremento secuencial (solo si todo lo anterior falló)
    if og_image:
        try:
            print(f"Fallback: procesando og_image con incremento secuencial: {og_image}")
            canva_urls = extract_canva_images(og_image)
            print(f"Imágenes encontradas por fallback: {len(canva_urls)}")
            all_image_urls.extend(canva_urls)
        except Exception as e:
            print(f"Error procesando fallback og_image: {e}")

    return all_image_urls
