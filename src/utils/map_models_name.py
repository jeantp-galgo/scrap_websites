import json
from pathlib import Path
from typing import Dict
import re
import unicodedata

# Ruta base del módulo para construir rutas absolutas
_SRC_DIR = Path(__file__).resolve().parents[1]  # .../src/
_MAPPING_DIR = _SRC_DIR / "data" / "json" / "name_mapping"


def _canonical_model_key(modelo: str) -> str:
    """Genera una clave canónica para comparar nombres de modelo con variaciones."""
    text = (modelo or "").strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    # Normalizaciones frecuentes en catálogos de motos.
    text = re.sub(r"\bgo\s*pro\b", "gopro", text)
    text = re.sub(r"\b(victory)(mrx)\b", r"\1 \2", text)
    text = re.sub(r"\b(\d+)\s*s\b", r"\1s", text)  # "125 s" == "125s"
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_brand_name(marca: str) -> str:
    """Normaliza el identificador de marca al nombre de archivo JSON correspondiente.

    Los identificadores vienen de check_website() en processor.py.
    Ejemplos:
        "aktmotos"        -> "aktmotos"
        "auteco_tvs"      -> "auteco_tvs"
        "auteco_victory"  -> "auteco_victory"
        "vento"           -> "vento"
    """
    # La mayoría ya tienen el formato correcto; se deja el hook para casos especiales
    return marca.lower()


def get_mapping_file_path(marca: str) -> Path:
    """Devuelve la ruta absoluta del archivo JSON de mapeo para una marca.

    Args:
        marca: Identificador de marca (tal como lo retorna check_website())

    Returns:
        Path al archivo JSON de mapeo
    """
    marca_normalizada = normalize_brand_name(marca)
    return _MAPPING_DIR / f"{marca_normalizada}_mapeo_nombres.json"


def load_mapping_file(marca: str) -> Dict[str, str]:
    """Carga el archivo JSON de mapeo de nombres para una marca.

    Si el archivo no existe, crea el directorio y el archivo vacío.

    Args:
        marca: Identificador de marca (tal como lo retorna check_website())

    Returns:
        Diccionario con el mapeo {nombre_scraping: nombre_marketplace}
    """
    filepath = get_mapping_file_path(marca)

    if filepath.exists():
        with open(filepath, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        print(f"Archivo de mapeo cargado: {filepath}")
        return data
    else:
        # Crear directorio y archivo vacío
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=4)
        print(f"Archivo de mapeo creado (vacío): {filepath}")
        return {}


def save_mapping_file(marca: str, mapeo_nombres: Dict[str, str]) -> None:
    """Guarda el archivo JSON de mapeo de nombres para una marca.

    Args:
        marca: Identificador de marca
        mapeo_nombres: Diccionario con el mapeo a guardar
    """
    filepath = get_mapping_file_path(marca)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(mapeo_nombres, f, ensure_ascii=False, indent=4)
    print(f"Archivo de mapeo guardado: {filepath}")


def map_model_name(modelo: str, mapeo_nombres: Dict[str, str]) -> str:
    """Mapea un nombre de modelo usando el diccionario de mapeo.

    Si el modelo no está en el mapeo, devuelve el nombre original.

    Args:
        modelo: Nombre del modelo a mapear
        mapeo_nombres: Diccionario con el mapeo de nombres

    Returns:
        Nombre mapeado si existe, o el nombre original si no
    """
    modelo_limpio = modelo.strip()
    modelo_key = _canonical_model_key(modelo_limpio)

    for raw_key, mapped_value in mapeo_nombres.items():
        if _canonical_model_key(raw_key) == modelo_key:
            return mapped_value if mapped_value.strip() else modelo_limpio

    return modelo_limpio


def get_brand_from_url(url: str) -> str | None:
    """Obtiene el identificador de marca a partir de una URL.

    Usa la misma lógica que check_website() de processor.py pero sin
    importarla directamente para evitar dependencias circulares.

    Args:
        url: URL del producto

    Returns:
        Identificador de marca o None si no se reconoce
    """
    if "vento.com" in url:
        return "vento"
    if "italika.mx" in url:
        return "italika"
    if "grupouma.com" in url:
        return "bajaj_co"
    if "honda.mx" in url:
        return "honda"
    if "yamaha-motor" in url:
        return "yamaha"
    if "rydermx.com" in url:
        return "ryder"
    if "zmoto.com.mx" in url:
        return "zmoto"
    if "tvsmotor.com" in url:
        return "tvs"
    if "aktmotos.com" in url:
        return "aktmotos"
    if "suzuki.com.co" in url:
        return "suzuki"
    if "auteco.com.co" in url:
        if "tvs" in url:
            return "auteco_tvs"
        if "victory" in url or "kawasaki" in url:
            return "auteco_victory"
    return None


def map_and_validate_model(model_data, marca: str | None):
    """Mapea el nombre del modelo y valida que esté correctamente mapeado.

    Si el modelo no está en el archivo JSON o tiene valor vacío:
      - Lo agrega al JSON con valor vacío (si aún no existe)
      - Lanza ValueError con instrucciones claras para el usuario

    Si está mapeado correctamente:
      - Actualiza model_data.model con el nombre mapeado
      - Retorna el model_data modificado

    Args:
        model_data: Objeto ModelData con el campo .model
        marca: Identificador de marca (de get_brand_from_url o check_website)

    Returns:
        model_data con .model actualizado al nombre del marketplace

    Raises:
        ValueError: Si el modelo no está mapeado o tiene valor vacío
        ValueError: Si marca es None (URL no reconocida)
    """
    if marca is None:
        raise ValueError(
            "No se pudo determinar la marca desde la URL. "
            "Verifica que la URL sea de un sitio conocido."
        )

    if model_data is None or model_data.model is None:
        raise ValueError(
            "model_data o model_data.model es None. "
            "Verifica que el scraping haya extraído el nombre del modelo correctamente."
        )

    modelo_original = model_data.model.strip()
    modelo_canonico = _canonical_model_key(modelo_original)
    filepath = get_mapping_file_path(marca)

    # Cargar mapeo actual
    mapeo = load_mapping_file(marca)

    # Resolver por coincidencia canónica para tolerar variaciones
    raw_key_match = None
    for raw_key in mapeo.keys():
        if _canonical_model_key(raw_key) == modelo_canonico:
            raw_key_match = raw_key
            break

    modelo_en_mapeo = raw_key_match is not None
    valor_mapeado = mapeo.get(raw_key_match, "").strip() if raw_key_match else ""

    if not modelo_en_mapeo:
        # Agregar al JSON con valor vacío para que el usuario lo complete
        mapeo[modelo_original] = ""
        save_mapping_file(marca, mapeo)
        raise ValueError(
            f"Modelo '{modelo_original}' no encontrado en el mapeo para marca '{marca}'.\n"
            f"Se agregó al archivo: {filepath}\n"
            f"Por favor, edita el archivo y agrega el nombre correcto del marketplace, "
            f"luego vuelve a ejecutar."
        )

    if valor_mapeado == "":
        raise ValueError(
            f"Modelo '{raw_key_match}' existe en el mapeo pero tiene valor vacío para marca '{marca}'.\n"
            f"Por favor, edita el archivo: {filepath}\n"
            f"y agrega el nombre correcto del marketplace, luego vuelve a ejecutar."
        )

    # Mapeo correcto: actualizar model_data
    model_data.model = valor_mapeado
    print(f"Modelo mapeado: '{modelo_original}' -> '{valor_mapeado}' (match: '{raw_key_match}')")
    return model_data
