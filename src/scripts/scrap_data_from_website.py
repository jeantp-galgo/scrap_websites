"""
Script para extraer datos de productos desde sitios web.
Permite procesar una URL específica o una lista de URLs predefinida.
"""

import sys
import os
import re
import argparse
import json
import requests
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Agregar el directorio src al path
sys.path.append(str(Path(__file__).parent.parent))

from config.paths import SRC_DIR
from utils.scraping_utils import ScrapingUtils

def sanitize_folder_name(name):
    """
    Remueve caracteres no válidos en nombres de archivos y carpetas, incluyendo saltos de línea.
    """
    if not name:
        return "sin_titulo"
    # Primero reemplaza saltos de línea y caracteres de control
    name = name.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    # Reemplaza \ / : * ? " < > | (caracteres no válidos en Windows)
    name = re.sub(r'[\\/:*?"<>|]', "", name)
    # Quita espacios iniciales/finales y múltiples espacios juntos
    name = re.sub(r'\s+', ' ', name).strip()
    # Si quedó vacío después de limpiar, usar nombre genérico
    if not name:
        return "sin_titulo"
    return name


def sanitize_filename(filename):
    """
    Limpia el nombre de archivo removiendo parámetros de consulta y caracteres inválidos.
    """
    if not filename:
        return "archivo"
    # Remover parámetros de consulta (todo después de ? o &)
    filename = filename.split('?')[0].split('&')[0]
    # Remover fragmentos (todo después de #)
    filename = filename.split('#')[0]
    # Remover caracteres no válidos en Windows
    filename = re.sub(r'[\\/:*?"<>|]', "", filename)
    # Limpiar espacios
    filename = re.sub(r'\s+', '_', filename).strip()
    # Si quedó vacío, usar nombre genérico
    if not filename:
        return "archivo"
    return filename

def extract_image_and_pdf_links_from_markdown(markdown_text):
    """
    Extrae todos los links de imágenes y PDFs que aparecen en el markdown.
    """
    if not markdown_text:
        return []

    # Extensiones de imagen y PDF a buscar
    image_extensions = ['.webp', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg']
    pdf_extensions = ['.pdf']
    all_extensions = image_extensions + pdf_extensions

    # Busca los links en formato ![](url) y [nombre](url)
    pattern = r'\((https?://[^\s)]+|/[^)\s]+)\)'
    matches = re.findall(pattern, markdown_text)

    # Filtra links que terminen con alguna de las extensiones buscadas
    links = [link for link in matches if any(link.lower().endswith(ext) for ext in all_extensions)]
    return links


def normalize_wix_image_url(url):
    """
    Normaliza URLs de imágenes de Wix para obtener la versión original sin transformaciones.

    Ejemplo:
    https://static.wixstatic.com/media/214c6c_e0a5f4e390a54728ae18a061ea9f3bef~mv2.jpg/v1/fill/.../214c6c_e0a5f4e390a54728ae18a061ea9f3bef~mv2.jpg
    ->
    https://static.wixstatic.com/media/214c6c_e0a5f4e390a54728ae18a061ea9f3bef~mv2.jpg
    """
    if 'static.wixstatic.com' in url and '/v1/' in url:
        # Extraer la parte antes de /v1/ y agregar el nombre del archivo original
        parts = url.split('/v1/')
        if len(parts) > 0:
            base_url = parts[0]
            # Buscar el nombre del archivo original después de /v1/fill/...
            # El patrón es: /v1/fill/.../nombre_archivo.jpg
            if len(parts) > 1:
                # Extraer el nombre del archivo del final
                file_match = re.search(r'/([^/]+\.(jpg|jpeg|png|webp|gif|bmp|tiff|svg))', parts[1])
                if file_match:
                    filename = file_match.group(1)
                    return f"{base_url}/{filename}"
            return base_url
    return url


def extract_urls_from_srcset(srcset_value):
    """
    Extrae URLs de un atributo srcset y retorna la URL de mayor resolución.
    Formato srcset: "url1 1940w, url2 300w, url3 1024w" o "url1 1x, url2 2x"
    """
    if not srcset_value:
        return []

    urls_with_sizes = []
    for item in srcset_value.split(','):
        item = item.strip()
        parts = item.split()
        if len(parts) >= 1:
            url = parts[0]
            # Intentar extraer el tamaño (puede ser "1940w", "2x", etc.)
            size = None
            if len(parts) >= 2:
                size_str = parts[1]
                # Si termina en 'w', es ancho en píxeles
                if size_str.endswith('w'):
                    try:
                        size = int(size_str[:-1])
                    except ValueError:
                        pass
                # Si termina en 'x', es densidad de píxeles (1x, 2x, etc.)
                elif size_str.endswith('x'):
                    try:
                        size = float(size_str[:-1]) * 1000  # Convertir a un número comparable
                    except ValueError:
                        pass

            if url and not url.startswith('data:'):  # Filtrar placeholders
                urls_with_sizes.append((url, size or 0))

    # Ordenar por tamaño (mayor primero) y retornar todas las URLs
    # (pero priorizamos la de mayor resolución)
    urls_with_sizes.sort(key=lambda x: x[1], reverse=True)
    return [url for url, _ in urls_with_sizes]


def extract_image_and_pdf_links_from_html(html_content):
    """
    Extrae todos los links de imágenes y PDFs del HTML usando BeautifulSoup.
    Busca en tags <img>, <a>, <noscript> y atributos src, href, data-src, etc.
    Maneja lazy loading, srcset, y normaliza URLs de Wix.
    """
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, "html.parser")
    links = []

    # Extensiones a buscar
    image_extensions = ['.webp', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg']
    pdf_extensions = ['.pdf']
    all_extensions = image_extensions + pdf_extensions

    def is_valid_url(url):
        """Verifica si una URL es válida (no es placeholder de lazy loading)"""
        if not url:
            return False
        # Filtrar placeholders comunes de lazy loading
        if url.startswith('data:image'):
            return False
        # Verificar que tenga una extensión válida
        return any(url.lower().endswith(ext) for ext in all_extensions)

    # Buscar en tags <img> - atributos src, data-src, data-lazy-src, etc.
    img_tags = soup.find_all('img')
    for img in img_tags:
        img_urls = []

        # Prioridad 1: data-srcset y srcset (pueden tener múltiples URLs, tomar solo la de mayor resolución)
        for attr in ['data-srcset', 'srcset']:
            srcset_value = img.get(attr)
            if srcset_value:
                urls_from_srcset = extract_urls_from_srcset(srcset_value)
                # Tomar solo la primera URL (que es la de mayor resolución después de ordenar)
                if urls_from_srcset:
                    url = urls_from_srcset[0]
                    if is_valid_url(url):
                        normalized_url = normalize_wix_image_url(url)
                        if is_valid_url(normalized_url):
                            img_urls.append(normalized_url)
                if img_urls:
                    break  # Si encontramos URLs en srcset, usamos esas (son de mayor calidad)

        # Prioridad 2: data-src, data-lazy-src, data-original (imágenes lazy-load reales)
        if not img_urls:
            for attr in ['data-src', 'data-lazy-src', 'data-original']:
                url = img.get(attr)
                if url and is_valid_url(url):
                    normalized_url = normalize_wix_image_url(url)
                    if is_valid_url(normalized_url):
                        img_urls.append(normalized_url)
                        break

        # Prioridad 3: src (puede ser placeholder, pero verificar)
        if not img_urls:
            src = img.get('src')
            if src and is_valid_url(src):
                normalized_url = normalize_wix_image_url(src)
                if is_valid_url(normalized_url):
                    img_urls.append(normalized_url)

        links.extend(img_urls)

    # Buscar imágenes dentro de <noscript> tags (fallback para navegadores sin JS)
    noscript_tags = soup.find_all('noscript')
    for noscript in noscript_tags:
        noscript_imgs = noscript.find_all('img')
        for img in noscript_imgs:
            # En noscript, priorizar src y srcset
            noscript_urls = []

            # Primero srcset (puede tener múltiples URLs, tomar solo la de mayor resolución)
            srcset_value = img.get('srcset')
            if srcset_value:
                urls_from_srcset = extract_urls_from_srcset(srcset_value)
                # Tomar solo la primera URL (que es la de mayor resolución después de ordenar)
                if urls_from_srcset:
                    url = urls_from_srcset[0]
                    if is_valid_url(url):
                        normalized_url = normalize_wix_image_url(url)
                        if is_valid_url(normalized_url):
                            noscript_urls.append(normalized_url)

            # Si no hay srcset, usar src
            if not noscript_urls:
                src = img.get('src')
                if src and is_valid_url(src):
                    normalized_url = normalize_wix_image_url(src)
                    if is_valid_url(normalized_url):
                        noscript_urls.append(normalized_url)

            links.extend(noscript_urls)

    # Buscar en tags <a> - links a PDFs
    a_tags = soup.find_all('a', href=True)
    for a in a_tags:
        href = a.get('href')
        if href and any(href.lower().endswith(ext) for ext in pdf_extensions):
            links.append(href)

    # Buscar en tags <source> (usados en <picture>)
    source_tags = soup.find_all('source')
    for source in source_tags:
        srcset = source.get('srcset') or source.get('data-srcset')
        if srcset:
            urls_from_srcset = extract_urls_from_srcset(srcset)
            # Tomar solo la primera URL (que es la de mayor resolución después de ordenar)
            if urls_from_srcset:
                url = urls_from_srcset[0]
                if is_valid_url(url):
                    normalized_url = normalize_wix_image_url(url)
                    if is_valid_url(normalized_url):
                        links.append(normalized_url)

    # Buscar en atributos style con background-image
    elements_with_style = soup.find_all(attrs={'style': re.compile(r'background-image', re.I)})
    for elem in elements_with_style:
        style = elem.get('style', '')
        # Buscar URLs en background-image: url(...)
        url_matches = re.findall(r'url\(["\']?([^"\')]+)["\']?\)', style)
        for url_match in url_matches:
            if is_valid_url(url_match):
                normalized_url = normalize_wix_image_url(url_match)
                if is_valid_url(normalized_url):
                    links.append(normalized_url)

    return links


def extract_images_from_json(data_scraped):
    """
    Extrae imágenes del campo JSON retornado por Firecrawl cuando se usa get_images_from_website().

    Returns:
        list: Lista de URLs de imágenes o lista vacía si no se encuentran
    """
    imagenes = []

    try:
        # Verificar si existe el campo json en data_scraped
        if hasattr(data_scraped, 'json') and data_scraped.json:
            images_data = data_scraped.json

            # Si es un string, intentar parsearlo como JSON
            if isinstance(images_data, str):
                try:
                    images_data = json.loads(images_data)
                except json.JSONDecodeError:
                    pass

            # Si es un diccionario, extraer las imágenes
            if isinstance(images_data, dict):
                # Buscar el campo 'imagenes' (puede estar en diferentes keys)
                for key in ['imagenes', 'images', 'image_urls', 'urls']:
                    if key in images_data and images_data[key] is not None:
                        imagenes_value = images_data[key]
                        # Si es una lista, usarla directamente
                        if isinstance(imagenes_value, list):
                            imagenes = imagenes_value
                            break
                        # Si es un string, intentar convertirlo a lista
                        elif isinstance(imagenes_value, str):
                            # Si tiene comas, separar por comas
                            if ',' in imagenes_value:
                                imagenes = [img.strip() for img in imagenes_value.split(',')]
                            else:
                                imagenes = [imagenes_value.strip()]
                            break
    except Exception as e:
        print(f"  ⚠️  Error al extraer imágenes del JSON: {e}")

    return imagenes


def extract_image_and_pdf_links(data_scraped):
    """
    Extrae todos los links de imágenes y PDFs desde múltiples fuentes:
    - data_scraped.images (si está disponible, extraído por Firecrawl)
    - Markdown
    - HTML

    Combina todas las fuentes y elimina duplicados.
    """
    all_links = []

    # 1. Usar las imágenes ya extraídas por Firecrawl (si están disponibles)
    if hasattr(data_scraped, 'images') and data_scraped.images:
        all_links.extend(data_scraped.images)

    # 2. Extraer del markdown
    if hasattr(data_scraped, 'markdown') and data_scraped.markdown:
        markdown_links = extract_image_and_pdf_links_from_markdown(data_scraped.markdown)
        all_links.extend(markdown_links)

    # 3. Extraer del HTML
    if hasattr(data_scraped, 'html') and data_scraped.html:
        html_links = extract_image_and_pdf_links_from_html(data_scraped.html)
        all_links.extend(html_links)

    # Normalizar URLs (convertir relativas a absolutas si es necesario)
    # y eliminar duplicados
    normalized_links = []
    seen = set()

    for link in all_links:
        # Normalizar: remover parámetros de consulta y fragmentos para comparación
        normalized = link.split('?')[0].split('#')[0]
        if normalized not in seen:
            seen.add(normalized)
            normalized_links.append(link)

    return normalized_links


def extract_product_title(html_content):
    """
    Extrae el título del producto del HTML usando BeautifulSoup.
    Busca el primer elemento H1 en la página.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    title_element = soup.find('h1')
    product_title = title_element.get_text(strip=True) if title_element else None
    return product_title


def extract_price_from_json(data_scraped):
    """
    Extrae información de precios, descuento y colores del campo JSON retornado por Firecrawl.

    Returns:
        tuple: (precio_base, precio_neto, descuento, colores) o (None, None, None, None) si no se encuentran
    """
    precio_base = None
    precio_neto = None
    descuento = None
    colores = None

    try:
        # Verificar si existe el campo json en data_scraped
        if hasattr(data_scraped, 'json') and data_scraped.json:
            price_data = data_scraped.json

            # Si es un string, intentar parsearlo como JSON
            if isinstance(price_data, str):
                try:
                    price_data = json.loads(price_data)
                except json.JSONDecodeError:
                    pass

            # Si es un diccionario, extraer los valores
            if isinstance(price_data, dict):
                # Buscar precio_base (puede estar en diferentes keys)
                for key in ['precio_base', 'precioBase', 'precio_base', 'base_price', 'price_base']:
                    if key in price_data and price_data[key] is not None:
                        try:
                            precio_base = float(price_data[key])
                            break
                        except (ValueError, TypeError):
                            continue

                # Buscar precio_neto (puede estar en diferentes keys)
                for key in ['precio_neto', 'precioNeto', 'precio_neto', 'net_price', 'price_net', 'final_price']:
                    if key in price_data and price_data[key] is not None:
                        try:
                            precio_neto = float(price_data[key])
                            break
                        except (ValueError, TypeError):
                            continue

                # Buscar descuento (puede estar en diferentes keys)
                for key in ['descuento', 'discount', 'descuento_amount', 'discount_amount']:
                    if key in price_data and price_data[key] is not None:
                        try:
                            descuento = float(price_data[key])
                            break
                        except (ValueError, TypeError):
                            continue

                # Buscar colores (puede estar en diferentes keys)
                for key in ['colores', 'colors', 'color', 'colores_disponibles', 'available_colors']:
                    if key in price_data and price_data[key] is not None:
                        colores_value = price_data[key]
                        # Si es una lista, usarla directamente
                        if isinstance(colores_value, list):
                            colores = colores_value
                            break
                        # Si es un string, intentar convertirlo a lista
                        elif isinstance(colores_value, str):
                            # Si tiene comas, separar por comas
                            if ',' in colores_value:
                                colores = [c.strip() for c in colores_value.split(',')]
                            else:
                                colores = [colores_value.strip()]
                            break
    except Exception as e:
        print(f"  ⚠️  Error al extraer precios, descuento y colores del JSON: {e}")

    return precio_base, precio_neto, descuento, colores


def get_browser_headers(image_url, source_url=None):
    """
    Genera headers de navegador apropiados para descargar una imagen.

    Args:
        image_url: URL de la imagen a descargar
        source_url: URL de la página de origen (usada como Referer)
    """
    # Si no se proporciona source_url, usar el dominio de la imagen
    if source_url:
        referer = source_url
    else:
        parsed_url = urlparse(image_url)
        referer = f"{parsed_url.scheme}://{parsed_url.netloc}/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Referer': referer,  # URL de la página de origen
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'same-origin',
        'Cache-Control': 'no-cache',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
    }
    return headers


def download_files(list_urls, destination_folder, source_url=None):
    """
    Descarga archivos desde una lista de URLs y los guarda en la carpeta de destino.
    Usa headers de navegador desde el inicio para evitar errores 403/406.

    Args:
        list_urls: Lista de URLs a descargar
        destination_folder: Carpeta donde guardar los archivos
        source_url: URL de la página de origen (usada como Referer)
    """
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # Crear una sesión para mantener cookies y mejorar el rendimiento
    session = requests.Session()

    for url in list_urls:
        try:
            # Extraer nombre de archivo de la URL y limpiarlo
            raw_filename = url.split("/")[-1]
            filename = sanitize_filename(raw_filename)
            full_path = os.path.join(destination_folder, filename)

            # Si ya existe, no descargar de nuevo
            if os.path.exists(full_path):
                print(f"  Archivo ya existe: {filename}")
                continue

            # Obtener headers apropiados para esta URL
            headers = get_browser_headers(url, source_url=source_url)

            # Intentar descarga con headers desde el inicio
            try:
                response = session.get(url, stream=True, timeout=30, headers=headers, allow_redirects=True)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                # Si es 403 o 406, intentar con diferentes estrategias
                if response.status_code in [403, 406]:
                    print(f"  {response.status_code} recibido para {filename}, intentando estrategias alternativas...")

                    # Estrategia 1: Headers más simples (sin Sec-Fetch-*)
                    alt_headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                        'Accept': '*/*',
                        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                        'Referer': source_url if source_url else headers['Referer'],
                        'Connection': 'keep-alive',
                    }

                    try:
                        response = session.get(url, stream=True, timeout=30, headers=alt_headers, allow_redirects=True)
                        response.raise_for_status()
                    except requests.exceptions.HTTPError:
                        # Estrategia 2: Sin Referer (algunos servidores lo bloquean)
                        alt_headers2 = alt_headers.copy()
                        alt_headers2.pop('Referer', None)
                        try:
                            response = session.get(url, stream=True, timeout=30, headers=alt_headers2, allow_redirects=True)
                            response.raise_for_status()
                        except requests.exceptions.HTTPError:
                            # Si todas las estrategias fallan, lanzar el error original
                            raise e
                else:
                    raise

            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filtra paquetes vacíos
                        f.write(chunk)
            print(f"  ✓ Descargado: {filename}")
        except Exception as e:
            print(f"  ✗ Error al descargar {filename}: {e}")

    session.close()


def process_url(url, scraping_utils, brand_to_scrape="Fratelli"):
    """
    Procesa una URL individual: extrae datos, descarga imágenes y PDFs.
    Retorna un diccionario con la información del producto.
    """
    print(f"\n{'='*60}")
    print(f"Procesando: {url}")
    print(f"{'='*60}")

    # Inicializar diccionario con datos del producto
    product_data = {
        "Marca": brand_to_scrape,
        "Modelo": None,
        "Precio base": None,
        "Precio neto": None,
        "Descuento": None,
        "Colores": None,
        "URL": url
    }

    try:
        # Obtener datos del sitio web (incluyendo extracción de precios)
        print("Obteniendo datos del sitio web...")
        try:
            data_scraped = scraping_utils.get_data_from_website(url, extract_prices=True)
        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg or "timed out" in error_msg:
                print(f"  ⚠️  Timeout en la primera solicitud. Intentando versión simplificada...")
                # Intentar sin extracción de precios primero (más rápido)
                try:
                    data_scraped = scraping_utils.get_data_from_website(url, extract_prices=False)
                    print(f"  ✓ Datos obtenidos (sin precios por timeout)")
                except Exception as e2:
                    print(f"  ❌ Error también en versión simplificada: {e2}")
                    raise e  # Lanzar el error original
            else:
                raise  # Si no es timeout, lanzar el error original

        # Extraer título del producto
        print("Extrayendo título del producto...")
        product_title = extract_product_title(data_scraped.html)

        if not product_title:
            print(f"  ⚠️  No se pudo extraer el título del producto. Usando nombre genérico.")
            product_title = url.split("/")[-1].replace("-", " ").title()

        # Sanitizar el título para ser usado como carpeta
        safe_product_title = sanitize_folder_name(product_title)

        # Guardar modelo en los datos del producto
        product_data["Modelo"] = product_title

        print(f"  Título: {product_title}")

        # Extraer información de precios, descuento y colores
        print("Extrayendo información de precios, descuento y colores...")
        precio_base, precio_neto, descuento, colores = extract_price_from_json(data_scraped)
        product_data["Precio base"] = precio_base
        product_data["Precio neto"] = precio_neto
        product_data["Descuento"] = descuento
        product_data["Colores"] = colores

        if precio_base:
            print(f"  Precio base: ${precio_base:,.0f}")
        if precio_neto:
            print(f"  Precio neto: ${precio_neto:,.0f}")
        if descuento:
            print(f"  Descuento: ${descuento:,.0f}")
        if colores:
            print(f"  Colores: {', '.join(colores)}")
        if not precio_base and not precio_neto:
            print(f"  ⚠️  No se encontraron precios")
        if not colores:
            print(f"  ⚠️  No se encontraron colores")

        # Extraer imágenes usando get_images_from_website (más preciso con prompt JSON)
        print("Extrayendo imágenes usando prompt JSON...")
        try:
            images_data = scraping_utils.get_images_from_website(url)
            imagenes = extract_images_from_json(images_data)
        except Exception as e:
            error_msg = str(e).lower()
            if "timeout" in error_msg or "timed out" in error_msg:
                print(f"  ⚠️  Timeout al extraer imágenes. Intentando extracción desde HTML...")
                # Fallback: extraer imágenes del HTML ya obtenido
                imagenes = []
                if hasattr(data_scraped, 'html') and data_scraped.html:
                    html_links = extract_image_and_pdf_links_from_html(data_scraped.html)
                    imagenes = [link for link in html_links if any(ext in link.lower() for ext in [".webp", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg"])]
                print(f"  ✓ {len(imagenes)} imágenes extraídas desde HTML")
            else:
                print(f"  ⚠️  Error al extraer imágenes: {e}")
                imagenes = []

        # Filtrar imágenes pequeñas (thumbnails)
        imagenes = [img for img in imagenes if '300x300' not in img and '150x150' not in img]

        # Eliminar duplicados
        imagenes = list(set(imagenes))

        # Extraer PDFs del HTML/markdown (mantener método actual para PDFs)
        print("Extrayendo PDFs...")
        links = extract_image_and_pdf_links(data_scraped)
        pdfs = [item for item in links if ".pdf" in item.lower()]
        pdfs = list(set(pdfs))

        print(f"  Imágenes encontradas: {len(imagenes)}")
        if imagenes:
            print(f"  Primeras URLs de imágenes:")
            for img_url in imagenes[:5]:  # Mostrar primeras 5
                print(f"    - {img_url}")
            if len(imagenes) > 5:
                print(f"    ... y {len(imagenes) - 5} más")

        print(f"  PDFs encontrados: {len(pdfs)}")
        if pdfs:
            print(f"  URLs de PDFs:")
            for pdf_url in pdfs:
                print(f"    - {pdf_url}")

        # Crear carpeta de destino (usando el título ya saneado)
        destination_folder = os.path.join(SRC_DIR, "data", "scraped_data_downloaded", safe_product_title)

        # Descargar archivos (pasar la URL de origen como Referer)
        if pdfs:
            print(f"\nDescargando PDFs...")
            download_files(pdfs, destination_folder, source_url=url)

        if imagenes:
            print(f"\nDescargando imágenes...")
            download_files(imagenes, destination_folder, source_url=url)

        print(f"\n✅ Proceso completado para: {product_title}")
        print(f"   Archivos guardados en: {destination_folder}")

        return product_data

    except Exception as e:
        print(f"\n❌ Error al procesar {url}: {e}")
        import traceback
        traceback.print_exc()
        return product_data  # Retornar datos parciales incluso si hay error


def load_urls_from_json(json_path):
    """
    Carga las URLs desde un archivo JSON.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            urls = json.load(f)
        return urls
    except Exception as e:
        print(f"Error al cargar URLs desde {json_path}: {e}")
        return []


def main():
    """
    Función principal del script.
    """
    parser = argparse.ArgumentParser(
        description='Extrae datos de productos desde sitios web',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python scrap_data_from_website.py --url "https://fratelliglobal.com/producto/fratelli-xe-125-2-0"
  python scrap_data_from_website.py  # Procesa todas las URLs del archivo JSON
        """
    )

    parser.add_argument(
        '--url',
        type=str,
        help='URL del producto a procesar'
    )

    parser.add_argument(
        '--brand',
        type=str,
        default='None',
        help='Marca del producto (default: Fratelli)'
    )

    parser.add_argument(
        '--urls-file',
        type=str,
        default=None,
        help='Ruta al archivo JSON con lista de URLs (default: src/data/urls_from_websites/Fratelli-urls.json)'
    )

    args = parser.parse_args()

    # Cargar variables de entorno
    load_dotenv()

    # Inicializar ScrapingUtils
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("❌ Error: No se encontró la variable de entorno FIRECRAWL_API_KEY")
        print("   Por favor, asegúrate de tener un archivo .env con esta variable.")
        sys.exit(1)

    scraping_utils = ScrapingUtils(api_key=api_key)

    # Determinar URLs a procesar
    # Lista predefinida de URLs (se usa si no se proporciona --url)
    urls_predefinidas = [
    "https://www.morbidelli.com/ec-es/products/t250x"
    ]

    args.brand = "Italika"

    if args.url:
        # Si se proporciona una URL, procesar solo esa
        urls_to_process = [args.url]
        print(f"Procesando URL proporcionada: {args.url}")
    else:
        # Si no se proporciona URL, usar las URLs predefinidas
        urls_to_process = urls_predefinidas
        print(f"Usando URLs predefinidas: {len(urls_to_process)} URLs")

        # Opcional: Si se proporciona --urls-file, cargar desde ese archivo en lugar de las predefinidas
        if args.urls_file:
            urls_json_path = args.urls_file
            print(f"Cargando URLs desde archivo: {urls_json_path}")
            urls_from_file = load_urls_from_json(urls_json_path)
            if urls_from_file:
                urls_to_process = urls_from_file
                print(f"Se procesarán {len(urls_to_process)} URLs desde el archivo")
            else:
                print("⚠️  No se pudieron cargar URLs del archivo, usando URLs predefinidas")

        if not urls_to_process:
            print("❌ No se encontraron URLs para procesar.")
            sys.exit(1)

        print(f"Se procesarán {len(urls_to_process)} URLs")

    # Procesar cada URL
    successful = 0
    failed = 0
    products_data = []  # Lista para acumular datos de productos

    for url in urls_to_process:
        product_data = process_url(url, scraping_utils, args.brand)

        if product_data.get("Modelo"):  # Si se extrajo al menos el modelo
            products_data.append(product_data)
            successful += 1
        else:
            failed += 1

    # Exportar datos a JSON
    if products_data:
        output_file = os.path.join(SRC_DIR, "data", "scraped_data_downloaded",
                                   f"{args.brand}_precios.json")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(products_data, f, ensure_ascii=False, indent=2)
            print(f"\n📄 Datos de precios exportados a: {output_file}")
        except Exception as e:
            print(f"\n⚠️  Error al exportar datos a JSON: {e}")

    # Resumen final
    print(f"\n{'='*60}")
    print(f"RESUMEN")
    print(f"{'='*60}")
    print(f"✅ Procesadas exitosamente: {successful}")
    print(f"❌ Fallidas: {failed}")
    print(f"📊 Total: {len(urls_to_process)}")
    print(f"📄 Productos con datos: {len(products_data)}")


if __name__ == "__main__":
    main()

