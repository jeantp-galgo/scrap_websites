import os
import asyncio
import threading
from pathlib import Path
import requests
from urllib.parse import urlparse
from typing import Any
import re

def get_urls_from_firecrawl_map(url_list: Any):
    """ Obtiene las URLs de un sitio web desde la respuesta de Firecrawl """
    links = getattr(url_list, "links", []) or []
    tuplas_urls = [(link.url, link.title, link.description) for link in links]
    return [tupla[0] for tupla in tuplas_urls]


def extract_image_urls_from_html(html: str) -> list:
    """ Extrae URLs de imágenes desde HTML sin depender de clases específicas """
    if not html:
        return []

    urls = []
    seen = set()

    def add_url(url: str):
        if not url:
            return
        cleaned = url.strip().strip("\"'")
        if not cleaned or cleaned.startswith("data:"):
            return
        if cleaned in seen:
            return
        seen.add(cleaned)
        urls.append(cleaned)

    # comentario en español: src / data-src / data-lazy-src / data-original
    img_src_pattern = re.compile(
        r"<img[^>]+(?:src|data-src|data-lazy-src|data-original)\s*=\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE,
    )
    for match in img_src_pattern.findall(html):
        add_url(match)

    # comentario en español: srcset con multiples URLs
    srcset_pattern = re.compile(
        r"srcset\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE
    )
    for srcset in srcset_pattern.findall(html):
        for part in srcset.split(","):
            candidate = part.strip().split(" ")[0]
            add_url(candidate)

    # comentario en español: background-image en estilos inline o bloques
    url_pattern = re.compile(r"url\(([^)]+)\)", re.IGNORECASE)
    for match in url_pattern.findall(html):
        candidate = match.strip().strip("\"'")
        # comentario en español: evitar recursos no imagen
        if re.search(r"\.(js|css|woff2?|ttf|eot|map)(\?|#|$)", candidate, re.IGNORECASE):
            continue
        add_url(candidate)

    return urls

def download_images_with_playwright(urls: list, base_name: str, output_dir: str = "downloads", page_url: str = "", min_size_kb: int = 10) -> list:
    """
    Descarga imágenes usando Playwright para sitios protegidos por Cloudflare.
    Intercepta las respuestas de imagen que el propio browser solicita al renderizar
    la página — evita el 403 que Cloudflare da cuando se navega directamente a cada imagen.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    min_bytes = int(min_size_kb) * 1024 if min_size_kb else 0

    async def _run_async():
        from playwright.async_api import async_playwright

        # Normalizar URLs a un set para lookup O(1)
        target_urls = set(urls)
        captured = {}  # url -> bytes

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

            # Interceptar respuestas y capturar el body de las imágenes objetivo
            async def on_response(response):
                if response.url in target_urls and response.status == 200:
                    try:
                        body = await response.body()
                        captured[response.url] = body
                        print(f"[playwright_download] Capturada: {response.url.split('/')[-1]} ({len(body)//1024}KB)")
                    except Exception:
                        pass

            page.on("response", on_response)

            # Cargar la página del modelo — el browser pide todas las imágenes automáticamente
            if page_url:
                print(f"[playwright_download] Cargando página del modelo: {page_url}")
                await page.goto(page_url, wait_until="domcontentloaded", timeout=60000)
                # Scroll completo para activar lazy-load de imágenes
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(4000)
                await page.evaluate("window.scrollTo(0, 0)")
                await page.wait_for_timeout(2000)

            print(f"[playwright_download] Imágenes capturadas por interception: {len(captured)}/{len(urls)}")

            # Para las imágenes no capturadas (no estaban en el viewport o son lazy),
            # intentar con fetch() ejecutado desde el contexto de la página ya autenticada
            missing = [u for u in urls if u not in captured]
            if missing:
                print(f"[playwright_download] Intentando {len(missing)} imágenes faltantes via fetch en página...")
                for img_url in missing:
                    try:
                        result = await page.evaluate("""async (url) => {
                            const r = await fetch(url, {credentials: 'include'});
                            if (!r.ok) return null;
                            const buf = await r.arrayBuffer();
                            return Array.from(new Uint8Array(buf));
                        }""", img_url)
                        if result:
                            captured[img_url] = bytes(result)
                            print(f"[playwright_download] Capturada via fetch: {img_url.split('/')[-1]}")
                    except Exception as e:
                        print(f"[playwright_download] fetch falló para {img_url.split('/')[-1]}: {e}")

            await context.close()
            await browser.close()

        # Guardar archivos y construir resultados
        results = []
        for idx, url in enumerate(urls, start=1):
            parsed = urlparse(url)
            ext = os.path.splitext(parsed.path)[1].lower()
            if not ext or ext not in {".jpg", ".jpeg", ".png", ".webp", ".svg"}:
                ext = ".jpg"
            filename = f"{base_name}_{idx}{ext}"
            file_path = output_path / filename

            if url not in captured:
                results.append({"url": url, "error": "No capturada por interception ni fetch", "ok": False})
                continue

            body = captured[url]
            if min_bytes and len(body) < min_bytes:
                results.append({"url": url, "ok": True, "skipped": True, "reason": "below_min_size", "bytes": len(body)})
                continue

            with open(file_path, "wb") as f:
                f.write(body)
            results.append({"url": url, "file": str(file_path), "ok": True, "skipped": False, "bytes": len(body)})
            print(f"[playwright_download] Guardada ({idx}/{len(urls)}): {filename}")

        return results

    def _run_in_thread():
        if os.name == "nt":
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

    return result_container[0] if result_container else []


def download_images(urls, base_name, output_dir="downloads", timeout=30, min_size_kb: int = 100, page_url: str = ""):
    """Descarga imágenes desde una lista de URLs y las guarda numeradas.

    comentario en español: para evitar iconos/thumbnails, se omiten imágenes por debajo
    de un tamaño mínimo. Si el servidor no envía Content-Length, se valida con el tamaño
    real del contenido descargado.

    page_url: URL de la página de origen. Si se provee, se visita primero para obtener
    cookies de sesión antes de descargar las imágenes (evita 403 en sitios con hotlink protection).
    """
    if not urls:
        print("⚠️ No hay URLs para descargar")
        return []

    print(f"Ejecutando descarga de imágenes... Total URLs: {len(urls)}. Guardando en: {output_dir}")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

    # Usar sesión para propagar cookies entre la visita a la página y la descarga de imágenes
    session = requests.Session()
    session.headers.update({
        'User-Agent': ua,
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
    })

    # Visitar la página primero para obtener cookies de sesión
    referer = page_url or ""
    if page_url:
        try:
            session.get(page_url, timeout=timeout)
            print(f"[download_images] Sesión establecida visitando: {page_url}")
        except Exception as e:
            print(f"[download_images] No se pudo visitar page_url ({e}); se continúa sin cookies.")

    results = []
    min_bytes = None if min_size_kb is None else int(min_size_kb) * 1024
    for idx, url in enumerate(urls, start=1):
        try:
            # Si no hay page_url, usar el dominio de la imagen como Referer
            if not referer:
                parsed_url = urlparse(url)
                img_referer = f"{parsed_url.scheme}://{parsed_url.netloc}/"
            else:
                img_referer = referer

            headers = {
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Referer': img_referer,
            }

            response = session.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()

            if min_bytes:
                content_length = response.headers.get("Content-Length")
                if content_length:
                    try:
                        if int(content_length) < min_bytes:
                            results.append(
                                {
                                    "url": url,
                                    "ok": True,
                                    "skipped": True,
                                    "reason": "below_min_size",
                                    "bytes": int(content_length),
                                }
                            )
                            continue
                    except Exception:
                        # comentario en español: si Content-Length es inválido, seguimos con validación por contenido
                        pass

            parsed = urlparse(url)
            ext = os.path.splitext(parsed.path)[1].lower()
            # Si no hay extensión o viene rara, usar .jpg por defecto
            if not ext or ext not in {".jpg", ".jpeg", ".png", ".webp"}:
                ext = ".jpg"
            filename = f"{base_name}_{idx}{ext}"
            file_path = output_path / filename

            if min_bytes and len(response.content) < min_bytes:
                results.append(
                    {
                        "url": url,
                        "ok": True,
                        "skipped": True,
                        "reason": "below_min_size",
                        "bytes": len(response.content),
                    }
                )
                continue

            with open(file_path, "wb") as file:
                file.write(response.content)

            results.append(
                {"url": url, "file": str(file_path), "ok": True, "skipped": False, "bytes": len(response.content)}
            )
        except Exception as exc:
            # Registrar error sin detener todo el proceso
            results.append({"url": url, "error": str(exc), "ok": False})

    print("Finalizó descarga de imágenes.")
    return results