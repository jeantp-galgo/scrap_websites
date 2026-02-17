# STATUS

## Estado actual

El proyecto se encuentra en fase de desarrollo activo. Los componentes principales están funcionales y se está trabajando en expandir la cobertura de marcas y mejorar la extracción de datos.

Se busca consolidar la información extraída y mejorar la estructura del código para facilitar el mantenimiento y la escalabilidad.

De a poco se va añadiendo nuevas marcas para su manejo

## Qué funciona

- Extracción de imágenes para ciertas marcas
- Fichas técnicas para ciertas marcas
- Scraper genérico para marcas que no requieren un flujo específico
- Descarga de imágenes y exportación de fichas técnicas en HTML
- Extracción de información del modelo (marca, nombre de modelo, precio, año, colores) sin exportar aún

## En progreso

- Scrapear imágenes:
    - Agregar distintas marcas: CF Moto, CFLite, Bajaj, Yamaha, Suzuki, etc
    - Integrar código de descarga de imágenes (código listo pero no incluído)

- Scrapear fichas técnicas:
    - Identificar cómo se presenta la ficha técnica (imágenes, PDF o tablas HTML)
    - Aplicar lógica para cada posible presentación

- Descargar información del modelo:
    - Mejorar output
    - Consolidar la información en un CSV o JSON

## Por hacer:

Ojala pronto:
- Refactorizar para una mejor estructura de código. Actualmente está funcional.


## Posibles usos del scraper

A corto plazo:
- Tracking de precios:
    - Mapear todos los campos necesarios por marcas principales
    - Crear alguna página para ver la información recolectada
    - Validar que seamos el precio más bajo en internet y tener alertas de cambios de precios

- Tracking de nuevos modelos / años:
    - Tener todas las URLs mapeadas
    - Identificar nuevos modelos disponibles que no estén en el marketplace

## Ultima actualización

2026-01-XX