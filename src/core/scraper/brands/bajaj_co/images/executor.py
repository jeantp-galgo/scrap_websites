from bs4 import BeautifulSoup
import asyncio, threading


def detect_url_patterns_from_html(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    rotators = soup.find_all("image-rotator")
    patterns = []

    for specs_div in rotators:
        src = specs_div.get("src")
        total_images = specs_div.get("total-images")

        if not src or not total_images:
            continue

        clean_src = src.replace("-${var}", "")
        if "." not in clean_src:
            continue

        image_src, extension = clean_src.rsplit(".", 1)
        patterns.append((image_src, extension, total_images))

    return patterns


def create_urls_from_pattern(image_src: str, extension: str, total_images: int) -> list:
    """
    Crea las URLs de las imágenes de la marca Bajaj_co
    """
    urls = []
    url_base = "https://grupouma.com/"
    total = int(total_images)
    if total <= 1:
        # Para consistencia, cuando hay 1 imagen se normaliza con consecutivo -01.
        urls.append(f"{url_base}{image_src}-01.{extension}")
        return urls

    for i in range(1, total + 1):
        index = f"{i:02d}"
        urls.append(f"{url_base}{image_src}-{index}.{extension}")
    return urls


def fetch_rotators_with_playwright(url: str) -> str:
    """
    Navega a la URL con Playwright, hace click en el primer dsm_shapes para
    activar los image-rotator, y retorna el HTML del DOM resultante.

    Un solo click en el primer shape es suficiente para que aparezcan todos
    los rotators (todos los colores disponibles del modelo).

    Retorna el HTML completo de la página tras el click, o None si falla.
    """

    async def _run_async():
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 900},
            )
            page = await context.new_page()
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(3000)

            # Scroll para activar lazy load de los shapes
            for _ in range(4):
                await page.evaluate("window.scrollBy(0, 600)")
                await page.wait_for_timeout(500)
            await page.wait_for_timeout(1500)

            # Click en el primer dsm_shapes — activa todos los image-rotator
            first_shape = page.locator("div.dsm_shapes").first
            shape_count = await page.locator("div.dsm_shapes").count()
            print(f"[bajaj_co] dsm_shapes encontrados: {shape_count}")

            if shape_count > 0:
                await first_shape.click(force=True)
                await page.wait_for_timeout(2000)

            html = await page.content()
            await context.close()
            await browser.close()
            return html

    def _run_in_thread():
        import sys
        if sys.platform == "win32":
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_run_async())
        finally:
            loop.close()

    result_container = []
    exc_container = []

    def _thread_target():
        try:
            result_container.append(_run_in_thread())
        except Exception as e:
            exc_container.append(e)

    t = threading.Thread(target=_thread_target)
    t.start()
    t.join()

    if exc_container:
        raise exc_container[0]

    return result_container[0] if result_container else None


def handle_images(content) -> list:
    """
    Maneja el caso específico de la marca Bajaj_co.

    Acepta:
    - str (URL): nuevo flujo con Playwright (1 sesión, 1 click, todos los rotators)
    - dict {"dsm_shapes_N": "<html>", ...}: flujo legacy con HTMLs de Firecrawl
    - objeto con .html: flujo legacy original
    """
    all_urls = []

    # Nuevo flujo: URL directa → Playwright
    if isinstance(content, str):
        print(f"[bajaj_co] Usando Playwright para: {content}")
        html = fetch_rotators_with_playwright(content)
        if not html:
            print("[bajaj_co] Playwright no retornó HTML")
            return []

        patterns = detect_url_patterns_from_html(html)
        print(f"[bajaj_co] Rotators detectados: {len(patterns)}")

        seen = set()
        for image_src, extension, total_images in patterns:
            key = (image_src, extension)
            if key in seen:
                continue
            seen.add(key)
            urls = create_urls_from_pattern(image_src, extension, total_images)
            all_urls.extend(urls)

        print(f"[bajaj_co] URLs generadas: {len(all_urls)}")
        return list(dict.fromkeys(all_urls))

    # Flujo legacy: objeto con .html
    if hasattr(content, "html"):
        patterns = detect_url_patterns_from_html(content.html)
        for image_src, extension, total_images in patterns:
            return create_urls_from_pattern(image_src, extension, total_images)
        return []

    # Flujo legacy: diccionario {"dsm_shapes_0": "<html...>", ...}
    if isinstance(content, dict):
        print(f"[bajaj_co] HTMLs recibidos: {len(content)}")
        for shape_key, html in content.items():
            patterns = detect_url_patterns_from_html(html)
            print(f"[bajaj_co] {shape_key} -> rotators detectados: {len(patterns)}")

            shape_urls = []
            # Evita duplicar patrones iguales dentro del mismo HTML
            for image_src, extension, total_images in set(patterns):
                urls = create_urls_from_pattern(image_src, extension, total_images)
                shape_urls.extend(urls)

            print(f"[bajaj_co] {shape_key} -> urls generadas: {len(shape_urls)}")
            all_urls.extend(shape_urls)

        # Deduplicar manteniendo orden
        return list(dict.fromkeys(all_urls))

    return []
