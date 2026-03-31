# SOP — scrape_websites_refactorv2

## Proposito

Extraer imagenes, fichas tecnicas y datos de modelo de sitios web de fabricantes de motocicletas.

## Configuracion inicial

### Instalacion

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Variables de entorno

```bash
cp .env_example .env
```

Editar `.env` y agregar la API key de Firecrawl:

```
FIRECRAWL_API_KEY=fc-tu-api-key-aqui
```

Obtener el token en: https://firecrawl.dev

## Uso desde el Notebook

Abrir `notebooks/app.ipynb` y configurar la URL del modelo a extraer:

```python
from src.core.scraper.processor import ImagesProcessor

images_processor = ImagesProcessor()
url_to_scrap = 'https://aktmotos.com/motos-akt/calle/cr4-125/'

# Datos del modelo
model_data = images_processor.get_model_data(url=url_to_scrap)

# Imagenes
images = images_processor.get_images_from_website(url=url_to_scrap)

# Ficha tecnica
technical_specs = images_processor.get_technical_specs(url=url_to_scrap)
```

## Descargar imagenes extraidas

```python
from pathlib import Path
import requests

def download_images(urls, base_name, output_dir="downloads"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    for idx, url in enumerate(urls, start=1):
        response = requests.get(url, timeout=30)
        ext = Path(url).suffix or ".jpg"
        filename = f"{base_name}_{idx}{ext}"
        with open(output_path / filename, "wb") as f:
            f.write(response.content)

download_images(images, model_data.model, f"data/images/{model_data.model}")
```

## Agregar soporte para una nueva marca

### Metodo 1: Script automatico (recomendado)

```bash
python scripts/create_new_brand.py suzuki
```

Crea automaticamente la estructura de carpetas en `src/core/scraper/brands/suzuki/`.

### Metodo 2: Manual

1. Crear la estructura de carpetas:
   ```
   src/core/scraper/brands/nueva_marca/
   ├── handle.py
   ├── utils.py
   ├── images/executor.py
   └── technical_specs/executor.py
   ```
2. Implementar `handle.py`, `images/executor.py` y `technical_specs/executor.py`
3. Registrar la nueva marca en `src/core/scraper/processor.py`

## Solucionar problemas comunes

| Problema | Causa probable | Solucion |
|---|---|---|
| "FIRECRAWL_API_KEY not found" | Archivo `.env` no existe o variable mal escrita | Verificar `.env` y reiniciar el kernel |
| Imagenes no detectadas | Sitio usa lazy loading o componentes personalizados | Probar con formato `html` en lugar de `images`; considerar handler especifico |
| Fichas tecnicas vacias | Requiere click para expandir el contenedor | Agregar acciones de `click` + `wait` al handler; aumentar `wait_for` timeout |

## Tecnicas de scraping disponibles

| Tecnica | Cuando usarla |
|---|---|
| Firecrawl estandar (formato `images`) | Sitios simples donde Firecrawl detecta bien las imagenes |
| Firecrawl + parsing HTML (BeautifulSoup) | Sitios con componentes web personalizados (caso AKT) |
| Extractor generico con IA | Marcas sin handler especifico |
| Acciones de navegacion (scroll, click, wait) | Contenido dinamico o que requiere interaccion |
