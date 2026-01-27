"""
Script para scrapear fichas técnicas de sitios web.
Busca fichas técnicas en PDF o incrustadas en HTML usando Firecrawl.
"""

import os
import sys
import re
import requests
from pathlib import Path
from dotenv import load_dotenv

# Agregar el path del proyecto
sys.path.append(str(Path(__file__).parent.parent))

from config.paths import SRC_DIR
from utils.scraping_utils import ScrapingUtils


class TechnicalSpecsScraper:
    def __init__(self, api_key: str):
        self.scraping_utils = ScrapingUtils(api_key=api_key)

    def scrape_technical_specs(self, url: str, output_folder: str = None, product_name: str = None):
        """
        Extrae la ficha técnica de una URL.

        Args:
            url: URL del producto a scrapear
            output_folder: Carpeta donde guardar los archivos (default: scraped_data_downloaded/technical_specs)
            product_name: Nombre del producto para nombrar archivos (default: extraído de la URL)

        Returns:
            dict con info de lo descargado: {'pdfs': [...], 'html_file': '...', 'html_content': '...'}
        """
        # Configurar carpeta de salida
        if output_folder is None:
            output_folder = f"{SRC_DIR}/data/scraped_data_downloaded/technical_specs"

        os.makedirs(output_folder, exist_ok=True)

        # Generar nombre de producto si no se proporciona
        if product_name is None:
            product_name = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
            product_name = re.sub(r'[^\w\-]', '_', product_name)  # Limpiar caracteres especiales

        print(f"🔍 Buscando ficha técnica en: {url}")
        print(f"📁 Guardando en: {output_folder}")

        # Hacer scraping con prompt específico para fichas técnicas
        doc = self._scrape_with_technical_specs_prompt(url)

        result = {
            'pdfs': [],
            'html_file': None,
            'html_content': None
        }

        # 1. Buscar PDFs de fichas técnicas
        pdfs = self._extract_technical_pdfs(doc)
        if pdfs:
            print(f"📄 Encontrados {len(pdfs)} PDF(s) de ficha técnica")
            downloaded_pdfs = self._download_pdfs(pdfs, output_folder, product_name)
            result['pdfs'] = downloaded_pdfs

        # 2. Extraer ficha técnica del HTML si existe
        html_specs = self._extract_html_specs(doc)
        if html_specs:
            print(f"📋 Ficha técnica encontrada en HTML")
            html_file = self._save_html_specs(html_specs, output_folder, product_name)
            result['html_file'] = html_file
            result['html_content'] = html_specs

        # Si no se encontró nada
        if not result['pdfs'] and not result['html_content']:
            print("⚠️  No se encontró ficha técnica en PDF ni en HTML")
            print("💾 Guardando página completa como fallback...")
            fallback_file = self._save_full_page(doc, output_folder, product_name)
            result['html_file'] = fallback_file
            result['html_content'] = doc.html if hasattr(doc, 'html') else None

        return result

    def _scrape_with_technical_specs_prompt(self, url: str):
        """Hace scraping con prompt específico para extraer fichas técnicas"""
        formats = ["markdown", "html", "links"]

        # Prompt para extraer ficha técnica estructurada
        tech_specs_prompt = {
            "type": "json",
            "prompt": """Extract technical specifications from this page. Look for:
            - Technical specification tables or sections (especificaciones técnicas, ficha técnica, specs)
            - Links to PDF files containing technical specs
            - Motor specifications (engine, motor)
            - Dimensions (dimensiones)
            - Weight (peso)
            - Capacity (capacidad)
            - Performance data

            Return a JSON object: {
                "pdf_urls": [list of URLs to PDF files with technical specs],
                "has_html_specs": boolean (true if technical specs are embedded in the page),
                "specs_section_html": string or null (HTML of the technical specs section if found)
            }"""
        }
        formats.append(tech_specs_prompt)

        # Configurar acciones de scroll para cargar contenido lazy-load
        actions = [
            {"type": "scroll", "direction": "down"},
            {"type": "wait", "milliseconds": 2000},
            {"type": "scroll", "direction": "down"},
            {"type": "wait", "milliseconds": 2000},
        ]

        doc = self.scraping_utils.firecrawl.scrape(
            url=url,
            formats=formats,
            wait_for=3000,
            timeout=120000,
            only_main_content=True,
            block_ads=True,
            exclude_tags=["script", "style", "noscript"],
            actions=actions
        )

        return doc

    def _extract_technical_pdfs(self, doc):
        """Extrae URLs de PDFs que contengan fichas técnicas"""
        pdfs = []

        # 1. Intentar obtener del JSON response
        if hasattr(doc, 'json') and doc.json:
            try:
                import json
                json_data = doc.json if isinstance(doc.json, dict) else json.loads(doc.json)
                if 'pdf_urls' in json_data and json_data['pdf_urls']:
                    pdfs.extend(json_data['pdf_urls'])
            except Exception as e:
                print(f"⚠️  Error parseando JSON: {e}")

        # 2. Buscar PDFs en markdown/links manualmente
        if hasattr(doc, 'markdown'):
            pdf_pattern = r'\((https?://[^\s)]+\.pdf[^\s)]*)\)'
            pdf_matches = re.findall(pdf_pattern, doc.markdown, re.IGNORECASE)
            pdfs.extend(pdf_matches)

        # Eliminar duplicados y filtrar solo PDFs relevantes (ficha técnica)
        pdfs = list(set(pdfs))

        # Filtrar por keywords relevantes (opcional, pero útil si hay muchos PDFs)
        relevant_keywords = ['ficha', 'tecnica', 'especificacion', 'spec', 'specs', 'bikes-specs', 'datasheet', 'manual']
        filtered_pdfs = []
        for pdf_url in pdfs:
            pdf_lower = pdf_url.lower()
            if any(keyword in pdf_lower for keyword in relevant_keywords):
                filtered_pdfs.append(pdf_url)

        # Si no hay PDFs con keywords, retornar todos los PDFs encontrados
        return filtered_pdfs if filtered_pdfs else pdfs

    def _extract_html_specs(self, doc):
        """Extrae la sección de especificaciones técnicas del HTML"""
        if not hasattr(doc, 'html') or not doc.html:
            return None

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(doc.html, 'html.parser')

        # Buscar secciones con palabras clave de especificaciones
        keywords = [
            'especificacion', 'ficha', 'tecnica', 'caracteristica',
            'specification', 'specs', 'technical', 'features'
        ]

        specs_section = None

        # Buscar por ID o clase
        for keyword in keywords:
            # Buscar por ID
            element = soup.find(id=re.compile(keyword, re.IGNORECASE))
            if element:
                specs_section = str(element)
                break

            # Buscar por clase
            element = soup.find(class_=re.compile(keyword, re.IGNORECASE))
            if element:
                specs_section = str(element)
                break

        # Si no se encontró por ID/clase, buscar por encabezados
        if not specs_section:
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4']):
                heading_text = heading.get_text().lower()
                if any(keyword in heading_text for keyword in keywords):
                    # Tomar el heading y todos los siguientes elementos hasta el próximo heading del mismo nivel
                    specs_section = str(heading.parent)
                    break

        return specs_section

    def _download_pdfs(self, pdf_urls: list, output_folder: str, product_name: str):
        """Descarga PDFs a la carpeta especificada"""
        downloaded_files = []

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/pdf,*/*',
        }

        for i, pdf_url in enumerate(pdf_urls):
            try:
                # Generar nombre de archivo
                original_name = pdf_url.split('/')[-1].split('?')[0]  # Remover query params
                if not original_name.endswith('.pdf'):
                    original_name = f"ficha_tecnica_{i+1}.pdf"

                filename = f"{product_name}_{original_name}"
                filepath = os.path.join(output_folder, filename)

                # Descargar
                print(f"  📥 Descargando: {filename}")
                response = requests.get(pdf_url, headers=headers, timeout=30)
                response.raise_for_status()

                with open(filepath, 'wb') as f:
                    f.write(response.content)

                downloaded_files.append(filepath)
                print(f"  ✅ Guardado: {filename}")

            except Exception as e:
                print(f"  ❌ Error descargando {pdf_url}: {e}")

        return downloaded_files

    def _save_html_specs(self, html_content: str, output_folder: str, product_name: str):
        """Guarda las especificaciones HTML en un archivo"""
        filename = f"{product_name}_ficha_tecnica.html"
        filepath = os.path.join(output_folder, filename)

        # Crear HTML completo con estilos básicos
        full_html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ficha Técnica - {product_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Ficha Técnica: {product_name}</h1>
    {html_content}
</body>
</html>"""

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_html)

        print(f"  ✅ Guardado: {filename}")
        return filepath

    def _save_full_page(self, doc, output_folder: str, product_name: str):
        """Guarda la página completa como fallback"""
        filename = f"{product_name}_full_page.html"
        filepath = os.path.join(output_folder, filename)

        html_content = doc.html if hasattr(doc, 'html') else str(doc)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"  💾 Guardada página completa: {filename}")
        return filepath


def main():
    """Función principal para ejecutar el script desde línea de comandos"""
    load_dotenv()

    # Ejemplo de uso
    url = input("Ingresa la URL del producto: ").strip()
    if not url:
        print("❌ URL no proporcionada")
        return

    # Opcional: nombre del producto
    product_name = input("Nombre del producto (Enter para usar default): ").strip()
    product_name = product_name if product_name else None

    # Inicializar scraper
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        print("❌ FIRECRAWL_API_KEY no encontrada en .env")
        return

    scraper = TechnicalSpecsScraper(api_key=api_key)

    # Scrapear
    result = scraper.scrape_technical_specs(url, product_name=product_name)

    # Mostrar resumen
    print("\n" + "="*50)
    print("📊 RESUMEN")
    print("="*50)
    print(f"PDFs descargados: {len(result['pdfs'])}")
    if result['pdfs']:
        for pdf in result['pdfs']:
            print(f"  - {pdf}")

    if result['html_file']:
        print(f"Archivo HTML: {result['html_file']}")

    print("="*50)


if __name__ == "__main__":
    main()
