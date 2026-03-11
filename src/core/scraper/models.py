import json
import re
from typing import Optional, List, Any

from pydantic import BaseModel, Field


class ModelData(BaseModel):
    base_price: Optional[float] = Field(default=None)
    net_price: Optional[float] = Field(default=None)
    discount_amount: Optional[float] = Field(default=None)
    model: Optional[str] = Field(default=None)
    colors: Optional[List[str]] = Field(default=None)


class TechnicalSpecsData(BaseModel):
    # Especificaciones Generales
    encendido: Optional[str] = Field(default=None)
    posicion_manejo: Optional[str] = Field(default=None)

    # Motor
    cilindrada: Optional[str] = Field(default=None)
    diametro_por_carrera: Optional[str] = Field(default=None)
    potencia: Optional[str] = Field(default=None)
    torque_maximo: Optional[str] = Field(default=None)
    tipo_motor: Optional[str] = Field(default=None)
    arranque: Optional[str] = Field(default=None)

    # Frenos
    freno_delantero: Optional[str] = Field(default=None)
    freno_trasero: Optional[str] = Field(default=None)

    # Llantas-neumáticos
    neumatico_delantero: Optional[str] = Field(default=None)
    neumatico_trasero: Optional[str] = Field(default=None)

    # Suspensión
    suspension_delantera: Optional[str] = Field(default=None)
    suspension_trasera: Optional[str] = Field(default=None)

    # Rendimiento
    combustible: Optional[str] = Field(default=None)
    sistema_alimentacion: Optional[str] = Field(default=None)
    capacidad_combustible: Optional[str] = Field(default=None)
    rendimiento: Optional[str] = Field(default=None)

    # Transmisión
    tipo_transmision: Optional[str] = Field(default=None)
    numero_cambios: Optional[str] = Field(default=None)

    # Dimensiones
    longitud_total: Optional[str] = Field(default=None)
    ancho_total: Optional[str] = Field(default=None)
    altura_total: Optional[str] = Field(default=None)
    altura_asiento: Optional[str] = Field(default=None)
    distancia_entre_ejes: Optional[str] = Field(default=None)
    distancia_minima_suelo: Optional[str] = Field(default=None)
    peso_total_liquidos: Optional[str] = Field(default=None)


def coerce_model_payload(payload: dict) -> dict:
    """Normaliza números y colors para que el schema sea más robusto"""
    normalized = dict(payload)
    for field in ["base_price", "net_price", "discount_amount"]:
        value = normalized.get(field)
        if isinstance(value, str):
            value = re.sub(r"[^\d]", "", value)
            normalized[field] = int(value) if value else None
    if isinstance(normalized.get("colors"), str):
        normalized["colors"] = [c.strip() for c in normalized["colors"].split(",") if c.strip()]
    return normalized


def parse_model_payload(raw_data: Any) -> ModelData:
    """Acepta dict o JSON string producido por el prompt"""
    if isinstance(raw_data, str):
        raw_data = json.loads(raw_data)
    payload = coerce_model_payload(raw_data or {})
    try:
        return ModelData.model_validate(payload)
    except AttributeError:
        # Compatibilidad con Pydantic v1
        return ModelData.parse_obj(payload)


def coerce_technical_specs_payload(payload: dict) -> dict:
    """Normaliza el payload, manteniendo strings ya que las especificaciones son texto"""
    normalized = dict(payload)
    # Si algún campo viene como lista o tiene formato extraño, lo normalizamos
    for key, value in normalized.items():
        if isinstance(value, list) and len(value) > 0:
            normalized[key] = str(value[0]) if value[0] else None
        elif value is not None:
            normalized[key] = str(value).strip() if str(value).strip() else None

    # Fallback: extraer número de cambios desde el texto de transmisión.
    if not normalized.get("numero_cambios") and normalized.get("tipo_transmision"):
        transmission = normalized["tipo_transmision"].lower()
        match = re.search(r"\b(\d+)\s*(velocidades|marchas|gears?|speed)\b", transmission)
        if match:
            normalized["numero_cambios"] = match.group(0)

    # Fallback: corregir confusión entre tipo de combustible y sistema de alimentación.
    combustible = (normalized.get("combustible") or "").strip()
    sistema = (normalized.get("sistema_alimentacion") or "").strip()
    sistema_keywords = ("carbur", "inye", "efi", "fi", "pgm-fi", "tbi", "mpi", "dfi")
    combustible_keywords = ("gasolina", "petrol", "diesel", "diésel", "electr", "flex", "etanol", "hibr")

    if combustible and any(k in combustible.lower() for k in sistema_keywords) and not sistema:
        normalized["sistema_alimentacion"] = combustible
        normalized["combustible"] = None

    if sistema and any(k in sistema.lower() for k in combustible_keywords) and not combustible:
        normalized["combustible"] = sistema
        normalized["sistema_alimentacion"] = None

    return normalized


def parse_technical_specs_payload(raw_data: Any) -> TechnicalSpecsData:
    """Acepta dict o JSON string producido por el prompt"""
    if isinstance(raw_data, str):
        try:
            raw_data = json.loads(raw_data)
        except Exception as e:
            raise

    payload = coerce_technical_specs_payload(raw_data or {})

    try:
        return TechnicalSpecsData.model_validate(payload)
    except AttributeError:
        # Compatibilidad con Pydantic v1
        return TechnicalSpecsData.parse_obj(payload)