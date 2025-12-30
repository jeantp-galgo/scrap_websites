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


def extract_image_and_pdf_links_from_html(html_content):
    """
    Extrae todos los links de imágenes y PDFs del HTML usando BeautifulSoup.
    Busca en tags <img>, <a> y atributos src, href, data-src, etc.
    """
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, "html.parser")
    links = []

    # Extensiones a buscar
    image_extensions = ['.webp', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg']
    pdf_extensions = ['.pdf']
    all_extensions = image_extensions + pdf_extensions

    # Buscar en tags <img> - atributos src, data-src, data-lazy-src, etc.
    img_tags = soup.find_all('img')
    for img in img_tags:
        # Revisar múltiples atributos comunes para imágenes lazy-load
        for attr in ['src', 'data-src', 'data-lazy-src', 'data-original', 'srcset']:
            url = img.get(attr)
            if url:
                # Si es srcset, puede tener múltiples URLs separadas por comas
                if attr == 'srcset':
                    # srcset tiene formato: "url1 1x, url2 2x" o solo URLs
                    urls = [u.strip().split()[0] for u in url.split(',')]
                    for u in urls:
                        if any(u.lower().endswith(ext) for ext in all_extensions):
                            links.append(u)
                else:
                    if any(url.lower().endswith(ext) for ext in all_extensions):
                        links.append(url)

    # Buscar en tags <a> - links a PDFs
    a_tags = soup.find_all('a', href=True)
    for a in a_tags:
        href = a.get('href')
        if href and any(href.lower().endswith(ext) for ext in pdf_extensions):
            links.append(href)

    # Buscar en tags <source> (usados en <picture>)
    source_tags = soup.find_all('source')
    for source in source_tags:
        srcset = source.get('srcset')
        if srcset:
            urls = [u.strip().split()[0] for u in srcset.split(',')]
            for url in urls:
                if any(url.lower().endswith(ext) for ext in all_extensions):
                    links.append(url)

    return links


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
    # if hasattr(data_scraped, 'images') and data_scraped.images:
    #     all_links.extend(data_scraped.images)

    # 2. Extraer del markdown
    # if hasattr(data_scraped, 'markdown') and data_scraped.markdown:
    #     markdown_links = extract_image_and_pdf_links_from_markdown(data_scraped.markdown)
    #     all_links.extend(markdown_links)

    # # 3. Extraer del HTML
    # if hasattr(data_scraped, 'html') and data_scraped.html:
    #     html_links = extract_image_and_pdf_links_from_html(data_scraped.html)
    #     all_links.extend(html_links)

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
    Extrae información de precios y colores del campo JSON retornado por Firecrawl.

    Returns:
        tuple: (precio_base, precio_neto, colores) o (None, None, None) si no se encuentran
    """
    precio_base = None
    precio_neto = None
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
        print(f"  ⚠️  Error al extraer precios y colores del JSON: {e}")

    return precio_base, precio_neto, colores


def download_files(list_urls, destination_folder):
    """
    Descarga archivos desde una lista de URLs y los guarda en la carpeta de destino.
    Si se recibe un error 406, lo intenta de nuevo enviando headers de navegador.
    """
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # Headers tipo navegador para evadir errores como 406
    browser_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
        'Referer': 'https://fratelliglobal.com/',
    }

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

            try:
                response = requests.get(url, stream=True, timeout=20)
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                if response.status_code == 406:
                    print(f"  406 recibido para {url}, reintentando con headers de navegador...")
                    response = requests.get(url, stream=True, timeout=20, headers=browser_headers)
                    response.raise_for_status()
                else:
                    raise

            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filtra paquetes vacíos
                        f.write(chunk)
            print(f"  Descargado: {filename}")
        except Exception as e:
            print(f"  Error al descargar {url}: {e}")


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
        "Colores": None,
        "URL": url
    }

    try:
        # Obtener datos del sitio web (incluyendo extracción de precios)
        print("Obteniendo datos del sitio web...")
        data_scraped = scraping_utils.get_data_from_website(url, extract_prices=True)

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

        # Extraer información de precios y colores
        print("Extrayendo información de precios y colores...")
        precio_base, precio_neto, colores = extract_price_from_json(data_scraped)
        product_data["Precio base"] = precio_base
        product_data["Precio neto"] = precio_neto
        product_data["Colores"] = colores

        if precio_base:
            print(f"  Precio base: ${precio_base:,.0f}")
        if precio_neto:
            print(f"  Precio neto: ${precio_neto:,.0f}")
        if colores:
            print(f"  Colores: {', '.join(colores)}")
        if not precio_base and not precio_neto:
            print(f"  ⚠️  No se encontraron precios")
        if not colores:
            print(f"  ⚠️  No se encontraron colores")

        # Extraer links de imágenes y PDFs
        print("Extrayendo links de imágenes y PDFs...")
        links = extract_image_and_pdf_links(data_scraped)

        # Separar imágenes y PDFs
        imagenes = []
        pdfs = []
        for item in links:
            image_extensions = [".webp", ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".svg"]
            if any(ext in item.lower() for ext in image_extensions):
                if '300x300' not in item:
                    imagenes.append(item)
            elif ".pdf" in item:
                pdfs.append(item)

        # Eliminar duplicados
        imagenes = list(set(imagenes))
        pdfs = list(set(pdfs))

        print(f"  Imágenes encontradas: {len(imagenes)}")
        print(f"  PDFs encontrados: {len(pdfs)}")

        # Crear carpeta de destino (usando el título ya saneado)
        destination_folder = os.path.join(SRC_DIR, "data", "scraped_data_downloaded", safe_product_title)

        # Descargar archivos
        if pdfs:
            print(f"\nDescargando PDFs...")
            download_files(pdfs, destination_folder)

        if imagenes:
            print(f"\nDescargando imágenes...")
            download_files(imagenes, destination_folder)

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
        default='CF Moto',
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
        "https://cfmotocolombia.com/motos-cfmotos/450mt-sport",
        "https://cfmotocolombia.com/motos-cfmotos/450mt-rally",
        "https://cfmotocolombia.com/motos-cfmotos/300sr-s",
        "https://cfmotocolombia.com/motos-cfmotos/800-mt-x",
        "https://cfmotocolombia.com/motos-cfmotos/450clc-bobber",
        "https://cfmotocolombia.com/motos-cfmotos/250-sr-fun",
        "https://cfmotocolombia.com/motos-cfmotos/xo-papio-trail",
        "https://cfmotocolombia.com/motos-cfmotos/450sr-s",
        "https://cfmotocolombia.com/motos-cfmotos/250clx",
        "https://cfmotocolombia.com/motos-cfmotos/300clx",
        "https://cfmotocolombia.com/motos-cfmotos/675nk",
        "https://cfmotocolombia.com/motos-cfmotos/zeeho-ae8-plus",
        "https://cfmotocolombia.com/motos-cfmotos/250nk-fun",
        "https://cfmotocolombia.com/motos-cfmotos/450-clc",
        "https://cfmotocolombia.com/motos-cfmotos/700clx-a",
        "https://cfmotocolombia.com/motos-cfmotos/700clx-h",
        "https://cfmotocolombia.com/motos-cfmotos/800nk-high",
        "https://cfmotocolombia.com/motos-cfmotos/675-sr-r",
        "https://cfmotocolombia.com/motos-cfmotos/cx-2e",
        "https://cfmotocolombia.com/motos-cfmotos/cx-5e"
    ]

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

