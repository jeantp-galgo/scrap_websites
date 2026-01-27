# Ejemplos de Uso - Scraper de Fichas Técnicas

## Ejemplo 1: Uso Básico

```python
from scripts.scrap_technical_specs import TechnicalSpecsScraper
import os

scraper = TechnicalSpecsScraper(api_key=os.getenv("FIRECRAWL_API_KEY"))

result = scraper.scrape_technical_specs(
    url="https://motoavanzada.mx/raptor-70cc/",
    product_name="raptor_70"
)

print(f"PDFs descargados: {len(result['pdfs'])}")
print(f"HTML guardado en: {result['html_file']}")
```

## Ejemplo 2: Procesar Lista de URLs desde JSON

```python
import json
from scripts.scrap_technical_specs import TechnicalSpecsScraper
import os

# Leer URLs desde archivo JSON
with open('src/data/urls_from_websites/Kove-urls.json', 'r') as f:
    urls = json.load(f)

scraper = TechnicalSpecsScraper(api_key=os.getenv("FIRECRAWL_API_KEY"))

# Procesar cada URL
for i, url in enumerate(urls):
    product_name = f"kove_producto_{i+1}"

    try:
        result = scraper.scrape_technical_specs(
            url=url,
            product_name=product_name,
            output_folder="src/data/scraped_data_downloaded/Kove/fichas_tecnicas"
        )
        print(f"✅ {product_name}: OK")
    except Exception as e:
        print(f"❌ {product_name}: {e}")
```

## Ejemplo 3: Extraer Solo PDFs

```python
from scripts.scrap_technical_specs import TechnicalSpecsScraper
import os

scraper = TechnicalSpecsScraper(api_key=os.getenv("FIRECRAWL_API_KEY"))

url = "https://ejemplo.com/producto"
result = scraper.scrape_technical_specs(url=url, product_name="producto")

# Trabajar solo con PDFs
if result['pdfs']:
    print("PDFs encontrados:")
    for pdf_path in result['pdfs']:
        print(f"  - {pdf_path}")

        # Opcional: extraer texto del PDF con pdfplumber
        # import pdfplumber
        # with pdfplumber.open(pdf_path) as pdf:
        #     for page in pdf.pages:
        #         text = page.extract_text()
        #         print(text)
else:
    print("No se encontraron PDFs")
```

## Ejemplo 4: Parsear HTML Extraído

```python
from scripts.scrap_technical_specs import TechnicalSpecsScraper
from bs4 import BeautifulSoup
import pandas as pd
import os

scraper = TechnicalSpecsScraper(api_key=os.getenv("FIRECRAWL_API_KEY"))

result = scraper.scrape_technical_specs(
    url="https://ejemplo.com/producto",
    product_name="producto"
)

# Parsear HTML con BeautifulSoup
if result['html_content']:
    soup = BeautifulSoup(result['html_content'], 'html.parser')

    # Buscar tabla de especificaciones
    tabla = soup.find('table')

    if tabla:
        # Convertir tabla HTML a DataFrame de pandas
        rows = []
        for tr in tabla.find_all('tr'):
            cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
            if cells:
                rows.append(cells)

        df = pd.DataFrame(rows[1:], columns=rows[0] if rows else None)
        print(df)

        # Guardar en CSV
        df.to_csv('especificaciones.csv', index=False)
```

## Ejemplo 5: Integración con Scraping de Imágenes

```python
from scripts.scrap_technical_specs import TechnicalSpecsScraper
from utils.scraping_utils import ScrapingUtils
import os

api_key = os.getenv("FIRECRAWL_API_KEY")

# 1. Extraer ficha técnica
tech_scraper = TechnicalSpecsScraper(api_key=api_key)
specs_result = tech_scraper.scrape_technical_specs(
    url="https://ejemplo.com/producto",
    product_name="producto"
)

# 2. Extraer imágenes del mismo producto
scraping_utils = ScrapingUtils(api_key=api_key)
images_doc = scraping_utils.get_images_from_website("https://ejemplo.com/producto")

# 3. Guardar todo junto
output_folder = "src/data/scraped_data_downloaded/producto_completo"
os.makedirs(output_folder, exist_ok=True)

print(f"✅ Ficha técnica: {specs_result['html_file']}")
print(f"📷 Imágenes encontradas: {len(images_doc.json.get('imagenes', []))}")
```

## Ejemplo 6: Batch Processing con Logging

```python
from scripts.scrap_technical_specs import TechnicalSpecsScraper
import os
import logging
from datetime import datetime

# Configurar logging
log_file = f"scraping_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Lista de productos
productos = [
    {"url": "https://ejemplo.com/producto1", "name": "producto_1"},
    {"url": "https://ejemplo.com/producto2", "name": "producto_2"},
    {"url": "https://ejemplo.com/producto3", "name": "producto_3"},
]

scraper = TechnicalSpecsScraper(api_key=os.getenv("FIRECRAWL_API_KEY"))

# Procesar con logging
exitosos = 0
fallidos = 0

for producto in productos:
    logging.info(f"Iniciando scraping: {producto['name']}")

    try:
        result = scraper.scrape_technical_specs(
            url=producto['url'],
            product_name=producto['name']
        )

        logging.info(f"✅ {producto['name']}: {len(result['pdfs'])} PDFs, HTML: {bool(result['html_file'])}")
        exitosos += 1

    except Exception as e:
        logging.error(f"❌ {producto['name']}: {str(e)}")
        fallidos += 1

logging.info(f"Finalizado: {exitosos} exitosos, {fallidos} fallidos")
```

## Ejemplo 7: Extraer Especificaciones Específicas

```python
from scripts.scrap_technical_specs import TechnicalSpecsScraper
from bs4 import BeautifulSoup
import re
import os

def extract_motor_specs(html_content):
    """Extrae solo especificaciones del motor"""
    soup = BeautifulSoup(html_content, 'html.parser')

    motor_specs = {}

    # Buscar por keywords
    keywords = ['cilindrada', 'potencia', 'torque', 'motor', 'displacement', 'hp', 'cc']

    for element in soup.find_all(['tr', 'li', 'p', 'div']):
        text = element.get_text().lower()

        for keyword in keywords:
            if keyword in text:
                # Extraer números y unidades
                numbers = re.findall(r'\d+\.?\d*\s*(?:cc|hp|nm|kw|cv)', text, re.IGNORECASE)
                if numbers:
                    motor_specs[keyword] = numbers

    return motor_specs

# Usar
scraper = TechnicalSpecsScraper(api_key=os.getenv("FIRECRAWL_API_KEY"))
result = scraper.scrape_technical_specs(
    url="https://ejemplo.com/moto",
    product_name="moto"
)

if result['html_content']:
    motor_info = extract_motor_specs(result['html_content'])
    print("Especificaciones del motor:")
    for key, values in motor_info.items():
        print(f"  {key}: {values}")
```

## Ejemplo 8: Comparar Fichas Técnicas

```python
from scripts.scrap_technical_specs import TechnicalSpecsScraper
from bs4 import BeautifulSoup
import pandas as pd
import os

scraper = TechnicalSpecsScraper(api_key=os.getenv("FIRECRAWL_API_KEY"))

# Scrapear varios productos para comparar
productos = [
    "https://ejemplo.com/moto-a",
    "https://ejemplo.com/moto-b",
    "https://ejemplo.com/moto-c"
]

specs_data = []

for i, url in enumerate(productos):
    result = scraper.scrape_technical_specs(
        url=url,
        product_name=f"moto_{i+1}"
    )

    if result['html_content']:
        soup = BeautifulSoup(result['html_content'], 'html.parser')

        # Extraer specs clave (personalizar según estructura del sitio)
        specs = {
            'producto': f"moto_{i+1}",
            'url': url
        }

        # Buscar valores específicos
        for row in soup.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if len(cells) == 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                specs[key] = value

        specs_data.append(specs)

# Crear DataFrame comparativo
df = pd.DataFrame(specs_data)
print(df)

# Guardar comparación
df.to_excel('comparacion_fichas_tecnicas.xlsx', index=False)
```

## Tips de Uso

### 1. Manejo de Errores
Siempre usar try/except cuando proceses múltiples URLs para que un error no detenga todo el proceso.

### 2. Rate Limiting
Si scrapeeas muchas URLs, considera agregar delays:
```python
import time
time.sleep(2)  # 2 segundos entre requests
```

### 3. Validación
Verifica que el contenido descargado sea válido:
```python
if result['pdfs']:
    for pdf_path in result['pdfs']:
        file_size = os.path.getsize(pdf_path)
        if file_size < 1000:  # Menos de 1KB probablemente sea inválido
            print(f"⚠️  PDF sospechoso: {pdf_path} ({file_size} bytes)")
```

### 4. Personalización del Prompt
Si los resultados no son buenos, modifica el prompt en `_scrape_with_technical_specs_prompt()` para ser más específico a tu caso de uso.
