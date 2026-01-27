# Scraper de Fichas Técnicas

Script simple para extraer fichas técnicas de sitios web usando Firecrawl.

## Qué Hace

1. **Busca fichas técnicas** en PDFs o incrustadas en HTML
2. **Descarga PDFs** automáticamente cuando los encuentra
3. **Extrae secciones HTML** con especificaciones técnicas
4. **Guarda todo** en archivos organizados por producto

## Casos de Uso

- Extraer especificaciones de productos de sitios de fabricantes
- Descargar PDFs de fichas técnicas automáticamente
- Guardar tablas de especificaciones en formato HTML portable

## Cómo Funciona

El script usa Firecrawl con un prompt específico que:
- Identifica enlaces a PDFs con fichas técnicas
- Detecta secciones HTML con especificaciones (tablas, listas, etc.)
- Filtra contenido relevante (motor, dimensiones, peso, capacidad, etc.)

## Uso

### Opción 1: Desde Notebook (Recomendado)

Abre `src/notebooks/scrap_technical_specs.ipynb` y:

1. Configura la URL y nombre del producto:
```python
url = "https://ejemplo.com/producto"
product_name = "mi_producto"
```

2. Ejecuta todas las celdas

### Opción 2: Desde Script Python

```python
from scripts.scrap_technical_specs import TechnicalSpecsScraper
import os

scraper = TechnicalSpecsScraper(api_key=os.getenv("FIRECRAWL_API_KEY"))

result = scraper.scrape_technical_specs(
    url="https://ejemplo.com/producto",
    product_name="mi_producto",
    output_folder=None  # None = usa carpeta por defecto
)

# Ver resultado
print(f"PDFs: {result['pdfs']}")
print(f"HTML: {result['html_file']}")
```

### Opción 3: Desde Terminal

```bash
cd src/scripts
python scrap_technical_specs.py
```

El script te pedirá la URL y el nombre del producto.

## Output

Los archivos se guardan en `src/data/scraped_data_downloaded/technical_specs/` (o carpeta personalizada):

- **PDFs**: `{product_name}_ficha_tecnica.pdf`
- **HTML**: `{product_name}_ficha_tecnica.html` (con estilos básicos)
- **Fallback**: `{product_name}_full_page.html` (si no encuentra specs específicas)

## Estructura del Resultado

```python
{
    'pdfs': [
        '/path/to/product_ficha_tecnica.pdf',
        # ... más PDFs si existen
    ],
    'html_file': '/path/to/product_ficha_tecnica.html',
    'html_content': '<div>...</div>'  # Contenido HTML crudo
}
```

## Limitaciones

- **Depende de Firecrawl**: Necesita API key válida
- **Sitios dinámicos**: Algunos sitios con mucho JavaScript pueden necesitar más tiempo de espera
- **PDFs protegidos**: No puede descargar PDFs que requieren autenticación
- **Precisión**: Puede no detectar specs en formatos muy personalizados

## Mejoras Posibles

Si necesitas más control:

1. **Ajustar timeout**: Modifica `wait_for` y `timeout` en `_scrape_with_technical_specs_prompt()`
2. **Más keywords**: Agrega palabras clave en `_extract_html_specs()` o `_extract_technical_pdfs()`
3. **Parseo personalizado**: Usa BeautifulSoup directamente sobre `result['html_content']`

## Alternativas

Si Firecrawl no funciona bien:

- **Selenium/Playwright**: Para sitios muy dinámicos
- **PDFPlumber**: Para extraer texto de PDFs descargados
- **Scrapy**: Para scraping a escala de múltiples productos
