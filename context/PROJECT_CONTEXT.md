# scrape_websites_refactorv2 — Contexto del Proyecto

## Que es

Sistema avanzado de web scraping disenado para extraer informacion de productos de motocicletas de sitios web de fabricantes. Se especializa en la extraccion de contenido multimedia (imagenes), especificaciones tecnicas y datos del modelo (precios, colores).

Usa Firecrawl como API principal de scraping, complementado con tecnicas personalizadas para sitios que no responden bien al scraping estandar.

## Estado

Desarrollo activo — En construccion (v2.0, Refactor). Ultima actualizacion: 2026-02-17.

## Funcionalidades

### Funcionales
- Extraccion de imagenes para multiples marcas
- Fichas tecnicas para marcas seleccionadas
- Scraper generico basado en IA para marcas sin handler especifico
- Descarga automatica de imagenes
- Exportacion de fichas tecnicas en formato HTML
- Extraccion de informacion del modelo (marca, modelo, precio, ano, colores)

### En progreso
- Agregar mas marcas (CF Moto, CFLite, Bajaj, Suzuki, etc.)
- Identificar y manejar diferentes formatos de fichas tecnicas (imagenes, PDF, tablas HTML)
- Mejorar output y consolidar informacion en CSV/JSON

### Por hacer
- Refactorizacion de estructura del codigo
- Sistema de tracking de precios
- Deteccion automatica de nuevos modelos/anos
- Mejorar scraping de pagina de Yamaha Mexico (div accordion-faq requiere clicks)

## Marcas soportadas

| Marca | Imagenes | Ficha Tecnica | Estado |
|---|---|---|---|
| AKT | Personalizado | En progreso | Activo |
| Auteco TVS | Si | Si | Activo |
| Dinamo | Si | Si | Activo |
| Honda | Si | Si | Activo |
| Italika | Si | Si | Activo |
| Ryder | Si | Si | Activo |
| TVS | Si | Si | Activo |
| Vento | Si | Si | Activo |
| Yamaha | Si | Si | Activo |
| ZMoto | Si | Si | Activo |
| Otras | Generico | Generico | Funcional |

## Arquitectura

```
scrape_websites_refactorv2/
├── src/
│   ├── config/
│   │   └── settings.py
│   └── core/
│       └── scraper/
│           ├── app.py               # ScrapingUtils: base Firecrawl
│           ├── processor.py         # ImagesProcessor: orquestador central
│           ├── generic_extractor.py # Extractor generico con IA
│           ├── models.py            # Modelos Pydantic (ModelData, TechnicalSpecsData)
│           ├── utils.py
│           └── brands/              # Handlers especificos por marca
│               ├── akt/
│               ├── honda/
│               ├── yamaha/
│               └── ...
├── scripts/
│   └── create_new_brand.py          # Script para crear estructura de nueva marca
├── notebooks/
│   └── app.ipynb                    # Notebook principal de pruebas
└── requirements.txt
```

## Modelos de datos

### ModelData
```python
base_price: Optional[float]        # Precio base
net_price: Optional[float]         # Precio neto (con descuento)
discount_amount: Optional[float]   # Monto del descuento
model: Optional[str]               # Nombre del modelo
colors: Optional[List[str]]        # Colores disponibles
```

### TechnicalSpecsData
Incluye campos de motor (cilindrada, potencia, torque), frenos, dimensiones y mas.

## Stack tecnico

| Tecnologia | Uso |
|---|---|
| Firecrawl 4.14.0 | API principal de scraping |
| Python 3.x | Lenguaje principal |
| Pydantic 2.12.5 | Validacion de datos y schemas |
| BeautifulSoup4 | Parsing HTML para casos especificos |
| requests 2.32.5 | Descarga de imagenes |

## Relacion con otros proyectos

- Los archivos HTML de fichas tecnicas generados por este scraper son input para `crear_ficha_tecnica`
- Los datos de modelo (precios) pueden alimentar el proceso de `update_marketplace_prices`
