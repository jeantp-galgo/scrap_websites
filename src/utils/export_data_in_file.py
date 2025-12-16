import json
import os

def save_json_file(data: list, output_path: str):
    """ Guarda un archivo JSON con los datos proporcionados """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Archivo JSON guardado correctamente en '{output_path}'")
    except Exception as e:
        print(f"Error al guardar el archivo JSON '{output_path}': {e}")