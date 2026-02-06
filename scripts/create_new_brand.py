"""
Script para crear la estructura de carpetas y archivos de una nueva marca.

Uso:
    python scripts/create_new_brand.py <nombre_marca>

Ejemplo:
    python scripts/create_new_brand.py suzuki
    python scripts/create_new_brand.py auteco_victory
"""

import os
import sys
from pathlib import Path


def get_handle_template(brand_name: str) -> str:
    """
    Genera el contenido del archivo handle.py para la marca especificada.
    """
    return f'''from src.core.scraper.brands.{brand_name}.images.executor import handle_images
from src.core.scraper.brands.{brand_name}.technical_specs.executor import handle_technical_specs


def handle_{brand_name}(handle_type:str, content: list[str]) -> list:
    """
    Maneja el caso específico de la marca {brand_name.capitalize()}
    """

    if handle_type == "images":
        print("Tipo de contenido: Images")
        return handle_images(content)

    if handle_type == "technical_specs":
        print("Tipo de contenido: Technical Specs")
        return handle_technical_specs(content)
'''


def create_brand_structure(brand_name: str) -> None:
    """
    Crea la estructura de carpetas y archivos para una nueva marca.
    """
    # Ruta base del proyecto (relativa al script)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    brands_path = project_root / "src" / "core" / "scraper" / "brands"
    brand_path = brands_path / brand_name

    # Validar que no exista la marca
    if brand_path.exists():
        print(f"Error: La marca '{brand_name}' ya existe en {brand_path}")
        sys.exit(1)

    # Crear estructura de carpetas
    folders_to_create = [
        brand_path,
        brand_path / "images",
        brand_path / "technical_specs",
    ]

    for folder in folders_to_create:
        folder.mkdir(parents=True, exist_ok=True)
        print(f"Carpeta creada: {folder}")

    # Crear archivos vacíos
    empty_files = [
        brand_path / "utils.py",
        brand_path / "images" / "executor.py",
        brand_path / "technical_specs" / "executor.py",
    ]

    for file_path in empty_files:
        file_path.touch()
        print(f"Archivo creado: {file_path}")

    # Crear handle.py con el template
    handle_path = brand_path / "handle.py"
    handle_content = get_handle_template(brand_name)
    handle_path.write_text(handle_content, encoding="utf-8")
    print(f"Archivo creado: {handle_path}")

    print(f"\n✓ Estructura de marca '{brand_name}' creada exitosamente.")


def main():
    if len(sys.argv) != 2:
        print("Uso: python scripts/create_new_brand.py <nombre_marca>")
        print("Ejemplo: python scripts/create_new_brand.py suzuki")
        print("Ejemplo: python scripts/create_new_brand.py auteco_victory")
        sys.exit(1)

    brand_name = sys.argv[1].lower().strip()

    # Validación básica del nombre: permite letras, números y guiones bajos
    # Debe empezar con una letra
    if not brand_name[0].isalpha():
        print("Error: El nombre de la marca debe empezar con una letra.")
        sys.exit(1)

    # Validar que solo contenga caracteres alfanuméricos y guiones bajos
    if not all(c.isalnum() or c == '_' for c in brand_name):
        print("Error: El nombre de la marca solo puede contener letras, números y guiones bajos (_).")
        sys.exit(1)

    create_brand_structure(brand_name)


if __name__ == "__main__":
    main()
