# 🏍️ Web Scraper de Motocicletas - Extracción Multimedia

Sistema avanzado de web scraping diseñado para extraer información de productos de motocicletas de sitios web de fabricantes, con enfoque especial en la extracción de contenido multimedia (imágenes) y especificaciones técnicas.

## 🎯 Características Principales

- **Extracción Híbrida de Imágenes**: Combina Firecrawl con técnicas personalizadas de scraping para detectar imágenes que los scrapers tradicionales no pueden capturar
- **Extracción de Datos del Modelo**: Obtiene automáticamente nombre del modelo, precios (base, neto, descuentos), colores disponibles y más
- **Fichas Técnicas Completas**: Extrae especificaciones técnicas detalladas (motor, dimensiones, rendimiento, etc.)
- **Arquitectura Modular por Marca**: Cada fabricante tiene su propio handler personalizado para manejar las particularidades de su sitio web
- **Extractor Genérico**: Para sitios que no requieren lógica específica, utiliza un extractor basado en prompts inteligentes con IA
- **Scraper Genérico con Schemas**: Usa modelos Pydantic para estructurar la extracción de datos con validación automática

## 🚀 Estado del Proyecto

**Fase**: Desarrollo activo - En construcción

### ✅ Funcional

- Extracción de imágenes para múltiples marcas
- Fichas técnicas para marcas seleccionadas
- Scraper genérico para marcas sin handler específico
- Descarga automática de imágenes
- Exportación de fichas técnicas en formato HTML
- Extracción de información del modelo (marca, modelo, precio, año, colores)

### 🔄 En Progreso

- **Imágenes**: Agregar más marcas (CF Moto, CFLite, Bajaj, Suzuki, etc.)
- **Fichas Técnicas**: Identificar y manejar diferentes formatos (imágenes, PDF, tablas HTML)
- **Datos del Modelo**: Mejorar output y consolidar información en CSV/JSON

### 📋 Por Hacer

- Refactorización para mejorar estructura del código
- Sistema de tracking de precios
- Detección automática de nuevos modelos/años

## 🏗️ Arquitectura

### Estructura del Proyecto

```
scrape_websites_refactorv2/
├── src/
│   ├── config/
│   │   └── settings.py              # Configuración del proyecto
│   └── core/
│       └── scraper/
│           ├── app.py               # Utilidades de scraping (ScrapingUtils)
│           ├── processor.py         # Procesador principal (ImagesProcessor)
│           ├── generic_extractor.py # Extractor genérico con IA
│           ├── models.py            # Modelos Pydantic de datos
│           ├── utils.py             # Funciones auxiliares
│           └── brands/              # Handlers específicos por marca
│               ├── akt/
│               ├── auteco_tvs/
│               ├── dinamo/
│               ├── honda/
│               ├── italika/
│               ├── ryder/
│               ├── tvs/
│               ├── vento/
│               ├── yamaha/
│               └── zmoto/
├── scripts/
│   └── create_new_brand.py          # Script para crear estructura de nueva marca
├── notebooks/
│   └── app.ipynb                    # Notebook principal de pruebas
└── requirements.txt                 # Dependencias del proyecto
```

### Componentes Principales

#### 1. **ScrapingUtils** (`app.py`)
Clase base que encapsula la funcionalidad de Firecrawl:
- Obtención de contenido web en múltiples formatos
- Mapeo de URLs de sitios web
- Configuración de tiempos de espera y parámetros de scraping

#### 2. **ImagesProcessor** (`processor.py`)
Procesador central que:
- Identifica automáticamente el sitio web por URL
- Delega a handlers específicos de marca
- Maneja extracción de imágenes, datos de modelo y fichas técnicas
- Usa el extractor genérico cuando no hay handler específico

#### 3. **GenericExtractor** (`generic_extractor.py`)
Extractor basado en IA que usa prompts estructurados:
- Extrae datos de modelo usando JSON schemas
- Extrae fichas técnicas con prompts multilingües
- Utiliza acciones de scroll y wait para contenido dinámico

#### 4. **Brand Handlers** (`brands/*/`)
Cada marca tiene su propia estructura:
```
marca/
├── handle.py                 # Punto de entrada del handler
├── utils.py                  # Utilidades específicas de la marca
├── images/
│   └── executor.py          # Lógica de extracción de imágenes
└── technical_specs/
    └── executor.py          # Lógica de extracción de fichas técnicas
```

## 🔧 Técnicas de Scraping

### 1. Firecrawl Estándar
Para sitios simples, usa los formatos nativos de Firecrawl:
- `images`: Extrae todas las imágenes de la página
- `html`: Obtiene el HTML completo
- `links`: Extrae todos los enlaces
- `json`: Extracción estructurada con schemas

### 2. Scraping Personalizado (Caso AKT)
Algunas marcas requieren técnicas especiales. Ejemplo de AKT:
- **Problema**: Las imágenes están en un componente web personalizado (`<image-rotator>`)
- **Solución**:
  1. Extraer HTML con Firecrawl
  2. Parsear con BeautifulSoup para encontrar el componente
  3. Extraer atributos `total-images` y `src`
  4. Generar URLs siguiendo el patrón descubierto

### 3. Extracción con IA (Genérico)
Para sitios sin handler específico:
- Usa prompts estructurados que describen qué extraer
- Soporta múltiples idiomas automáticamente
- Valida datos con modelos Pydantic

### 4. Acciones de Navegación
Manejo de contenido dinámico:
```python
actions = [
    {"type": "scroll", "direction": "down"},
    {"type": "wait", "milliseconds": 2000},
    {"type": "click", "selector": "a.btn-specs"},
]
```

## 📦 Instalación

### Prerrequisitos
- Python 3.8+
- Cuenta en Firecrawl con API Key

### Pasos

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd scrape_websites_refactorv2
```

2. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env_example .env
```
Editar `.env` y agregar tu API key de Firecrawl:
```
FIRECRAWL_API_KEY=fc-tu-api-key-aqui
```

## 💻 Uso

### Desde Jupyter Notebook

El notebook principal `notebooks/app.ipynb` proporciona una interfaz interactiva:

```python
import sys
sys.path.append('../')
from src.core.scraper.processor import ImagesProcessor

# Inicializar procesador
images_processor = ImagesProcessor()

# Configurar URL y opciones
url_to_scrap = 'https://aktmotos.com/motos-akt/calle/cr4-125/'

# Extraer datos del modelo
model_data = images_processor.get_model_data(url=url_to_scrap)
print(f"Modelo: {model_data.model}")
print(f"Precio base: {model_data.base_price}")
print(f"Colores: {model_data.colors}")

# Extraer imágenes
images = images_processor.get_images_from_website(url=url_to_scrap)
print(f"Total de imágenes: {len(images)}")

# Extraer ficha técnica
technical_specs = images_processor.get_technical_specs(url=url_to_scrap)
```

### Desde Python Script

```python
from src.core.scraper.processor import ImagesProcessor

processor = ImagesProcessor()

# Extracción completa
url = "https://example.com/moto-modelo"
model_data = processor.get_model_data(url)
images = processor.get_images_from_website(url)
specs = processor.get_technical_specs(url)
```

### Descargar Imágenes

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

# Usar
download_images(images, model_data.model, f"data/images/{model_data.model}")
```

## 🆕 Agregar Nueva Marca

### Método 1: Script Automático

```bash
python scripts/create_new_brand.py suzuki
```

Esto crea automáticamente:
```
src/core/scraper/brands/suzuki/
├── handle.py
├── utils.py
├── images/
│   └── executor.py
└── technical_specs/
    └── executor.py
```

### Método 2: Implementación Manual

1. **Crear estructura de carpetas** (o usar el script)

2. **Implementar `handle.py`**:
```python
from src.core.scraper.brands.suzuki.images.executor import handle_images
from src.core.scraper.brands.suzuki.technical_specs.executor import handle_technical_specs

def handle_suzuki(handle_type: str, content: list[str]) -> list:
    if handle_type == "images":
        return handle_images(content)

    if handle_type == "technical_specs":
        return handle_technical_specs(content)
```

3. **Implementar `images/executor.py`**:
```python
def handle_images(content):
    # Lógica específica para extraer imágenes de Suzuki
    # Puede usar content.images, content.html, etc.
    return image_urls_list
```

4. **Implementar `technical_specs/executor.py`**:
```python
def handle_technical_specs(content):
    # Lógica para extraer fichas técnicas
    # Retornar HTML, dict, o string según necesidad
    return technical_data
```

5. **Registrar en `processor.py`**:
```python
from src.core.scraper.brands.suzuki.handle import handle_suzuki

def check_website(url, **kwargs):
    # ... código existente ...
    if "suzuki.com" in url:
        return "suzuki"
    # ...

class ImagesProcessor:
    def get_images_from_website(self, url: str, **kwargs):
        website = check_website(url)
        # ...
        if website == "suzuki":
            content = self.scraper.get_content_from_website(url, formats=["images"])
            return handle_suzuki("images", content)
```

## 🛠️ Tecnologías Utilizadas

- **[Firecrawl](https://firecrawl.dev)** - API principal para scraping con IA
- **Python 3.x** - Lenguaje principal
- **Pydantic** - Validación de datos y schemas
- **BeautifulSoup4** - Parsing HTML para casos específicos
- **Requests** - Descarga de imágenes
- **Jupyter** - Entorno de desarrollo interactivo
- **aiohttp** - Operaciones asíncronas

### Dependencias Principales

```
firecrawl==4.14.0
pydantic==2.12.5
requests==2.32.5
python-dotenv==1.2.1
ipython==9.10.0
jupyter_client==8.8.0
```

## 📊 Modelos de Datos

### ModelData
```python
class ModelData(BaseModel):
    base_price: Optional[float]        # Precio base del producto
    net_price: Optional[float]         # Precio neto (con descuento)
    discount_amount: Optional[float]   # Monto del descuento
    model: Optional[str]               # Nombre del modelo
    colors: Optional[List[str]]        # Lista de colores disponibles
```

### TechnicalSpecsData
```python
class TechnicalSpecsData(BaseModel):
    # Motor
    cilindrada: Optional[str]
    potencia: Optional[str]
    torque_maximo: Optional[str]
    tipo_motor: Optional[str]

    # Frenos
    freno_delantero: Optional[str]
    freno_trasero: Optional[str]

    # Dimensiones
    longitud_total: Optional[str]
    altura_asiento: Optional[str]
    peso_total_liquidos: Optional[str]

    # ... y muchos más campos
```

## 🎯 Casos de Uso

### Tracking de Precios
Monitorear cambios de precio en tiempo real:
1. Mapear todas las URLs de productos
2. Extraer periódicamente los precios
3. Validar que se mantiene el precio más bajo del mercado
4. Generar alertas de cambios

### Tracking de Nuevos Modelos
Detectar automáticamente nuevos lanzamientos:
1. Mantener lista de URLs conocidas
2. Ejecutar periódicamente el mapeo de sitios
3. Identificar nuevas URLs no catalogadas
4. Extraer información de nuevos modelos

### Base de Datos de Productos
Consolidar información de múltiples fabricantes:
1. Extraer datos de todas las marcas
2. Normalizar información en formato común
3. Exportar a CSV/JSON
4. Alimentar sistemas downstream

## 🤝 Marcas Soportadas

| Marca | Imágenes | Ficha Técnica | Estado |
|-------|----------|---------------|--------|
| AKT | ✅ Personalizado | 🔄 | Activo |
| Auteco TVS | ✅ | ✅ | Activo |
| Dinamo | ✅ | ✅ | Activo |
| Honda | ✅ | ✅ | Activo |
| Italika | ✅ | ✅ | Activo |
| Ryder | ✅ | ✅ | Activo |
| TVS | ✅ | ✅ | Activo |
| Vento | ✅ | ✅ | Activo |
| Yamaha | ✅ | ✅ | Activo |
| ZMoto | ✅ | ✅ | Activo |
| Otras | ✅ Genérico | ✅ Genérico | Funcional |

## 📝 Notas Técnicas

### Manejo de Imágenes con Firecrawl

**Limitación conocida**: Firecrawl puede no detectar todas las imágenes, especialmente aquellas cargadas dinámicamente o en componentes web personalizados.

**Solución híbrida**:
1. Intentar con formato `images` de Firecrawl
2. Si no es suficiente, usar formato `html` y parsing personalizado
3. Para sitios complejos, crear handler específico (la mayoría de las páginas)

### Schemas y Prompts

El extractor genérico usa dos enfoques:
- **Con Schema**: Define estructura exacta con Pydantic, mayor precisión
- **Con Prompt**: Describe qué buscar, más flexible pero menos estructurado

Recomendación: Usar schemas cuando la estructura es conocida y consistente.

### Acciones y Timing

Algunos sitios requieren interacción:
```python
actions = [
    {"type": "scroll", "direction": "down"},
    {"type": "wait", "milliseconds": 2000},
]
```

Tips:
- Siempre incluir `wait` después de acciones
- Para contenido lazy-loaded, usar scroll + wait
- Para modales/tabs, usar click + wait

## 🐛 Troubleshooting

### Error: "FIRECRAWL_API_KEY not found"
- Verificar que el archivo `.env` existe
- Confirmar que la variable está correctamente definida
- Reiniciar el kernel de Jupyter si es necesario

### Imágenes no detectadas
- Probar con formato `html` en lugar de `images`
- Revisar si el sitio usa lazy loading (agregar scroll)
- Considerar crear handler personalizado

### Fichas técnicas vacías
- Verificar si requiere click para expandir (ver caso Honda)
- Aumentar `wait_for` timeout
- Revisar si usa formato no estándar (PDF, imágenes)

---

**Última actualización**: 2026-02-17
**Versión**: 2.0 (Refactor)
