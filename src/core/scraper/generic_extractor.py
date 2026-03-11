import time
import re
import unicodedata
from bs4 import BeautifulSoup
from src.core.scraper.app import ScrapingUtils
from src.core.scraper.models import (
    ModelData,
    TechnicalSpecsData,
    parse_model_payload,
    parse_technical_specs_payload,
)


class GenericExtractor:
    """Extractor genérico para datos de productos cuando no hay un handler específico de marca"""

    def __init__(self):
        self.scraper = ScrapingUtils()
        self._field_aliases = {
            "encendido": ["encendido", "ignition", "sistema de encendido", "tipo de encendido"],
            "posicion_manejo": ["posicion de manejo", "riding position", "postura", "ergonomia"],
            "cilindrada": ["cilindrada", "cilindraje", "displacement", "engine capacity", "capacidad del motor"],
            "diametro_por_carrera": ["diametro por carrera", "diametro x carrera", "bore x stroke", "stroke"],
            "potencia": ["potencia", "potencia maxima", "power", "max power"],
            "torque_maximo": ["torque", "torque maximo", "par motor", "max torque"],
            "tipo_motor": ["tipo de motor", "motor", "engine type", "configuracion del motor"],
            "arranque": ["arranque", "starting", "start system", "sistema de arranque"],
            "freno_delantero": ["freno delantero", "front brake"],
            "freno_trasero": ["freno trasero", "rear brake"],
            "neumatico_delantero": ["neumatico delantero", "llanta delantera", "front tire", "front tyre"],
            "neumatico_trasero": ["neumatico trasero", "llanta trasera", "rear tire", "rear tyre"],
            "suspension_delantera": ["suspension delantera", "front suspension"],
            "suspension_trasera": ["suspension trasera", "rear suspension"],
            "combustible": ["combustible", "fuel", "tipo de combustible"],
            "sistema_alimentacion": ["sistema de alimentacion", "fuel system", "inyeccion", "carburador", "efi", "fi"],
            "capacidad_combustible": ["capacidad de combustible", "capacidad del tanque", "fuel tank capacity", "tanque"],
            "rendimiento": ["rendimiento", "consumo", "autonomia", "fuel economy"],
            "tipo_transmision": ["transmision", "tipo de transmision", "gearbox"],
            "numero_cambios": ["numero de cambios", "velocidades", "marchas", "gears"],
            "longitud_total": ["longitud total", "largo total", "overall length"],
            "ancho_total": ["ancho total", "overall width"],
            "altura_total": ["altura total", "overall height"],
            "altura_asiento": ["altura del asiento", "altura al sillin", "seat height"],
            "distancia_entre_ejes": ["distancia entre ejes", "wheelbase", "entre ejes"],
            "distancia_minima_suelo": ["distancia minima al suelo", "despeje al suelo", "ground clearance"],
            "peso_total_liquidos": ["peso total con liquidos", "peso con fluidos", "curb weight", "peso en seco", "peso neto"],
        }

    @staticmethod
    def _normalize_text(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text or "")
        normalized = "".join(c for c in normalized if not unicodedata.combining(c))
        normalized = normalized.lower().strip()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _map_label_to_field(self, label: str) -> str | None:
        normalized_label = self._normalize_text(label)
        for field, aliases in self._field_aliases.items():
            for alias in aliases:
                if alias in normalized_label:
                    return field
        return None

    @staticmethod
    def _prefer_value(existing_value: str | None, new_value: str | None) -> str | None:
        if not new_value:
            return existing_value
        if not existing_value:
            return new_value
        existing_clean = existing_value.strip()
        new_clean = new_value.strip()
        if len(new_clean) > len(existing_clean):
            return new_clean
        return existing_clean

    def _extract_specs_from_html(self, html: str | None) -> dict:
        if not html:
            return {}

        extracted = {}
        soup = BeautifulSoup(html, "html.parser")

        # Caso común: tarjetas de specs con nombre/valor separados.
        for item in soup.select(".spec-item"):
            name_el = item.select_one(".spec-name")
            value_el = item.select_one(".spec-value")
            if not name_el or not value_el:
                continue
            label = name_el.get_text(" ", strip=True)
            value = value_el.get_text(" ", strip=True)
            field = self._map_label_to_field(label)
            if field and value:
                extracted[field] = self._prefer_value(extracted.get(field), value)

        # Fallback genérico para listas "label: value"
        for li in soup.find_all("li"):
            text = li.get_text(" ", strip=True)
            if ":" not in text:
                continue
            label, value = text.split(":", 1)
            field = self._map_label_to_field(label)
            if field and value.strip():
                extracted[field] = self._prefer_value(extracted.get(field), value.strip())

        return extracted

    @staticmethod
    def _model_to_dict(data: TechnicalSpecsData) -> dict:
        try:
            return data.model_dump(exclude_none=False)
        except AttributeError:
            return data.dict(exclude_none=False)

    def get_model_data(self, url: str) -> ModelData | None:
        """
        Extrae información de precio y colores del producto usando un prompt estructurado.
        """
        default_prompt = """
Extract product pricing information and available colors from this page.
Return ONLY a valid JSON object with this exact structure:
{
  "base_price": number or null,
  "net_price": number or null,
  "discount_amount": number or null,
  "model": string or null,
  "colors": array of strings or null,
}

Rules:
- If a value is not found, return null for that field.
- net_price is base_price - discount_amount. If not discount_amount, net_price is base_price
- Prices must be numbers without currency symbols, commas, or dots as thousand separators.
- Colors must be an array of color names (e.g., ["Rojo", "Negro"]).
- For "model", copy the product name exactly as shown in the page title or main H1.
- Do not translate, abbreviate, split words, or change casing for "model".
- Do not include any text outside the JSON object.
        """
        actions = [
            {"type": "scroll", "direction": "down"},
            {"type": "wait", "milliseconds": 2000},
        ]

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            content = self.scraper.get_content_from_website(
                url,
                formats=[{
                    "type": "json",
                    "prompt": default_prompt
                }],
                actions=actions,
                wait_for=5000,
            )

            if content is None:
                print(f"[get_model_data] intento {attempt}/{max_retries}: content es None — {url}")
            else:
                raw_payload = getattr(content, "json", None)
                if raw_payload is not None:
                    return parse_model_payload(raw_payload), content
                else:
                    print(f"[get_model_data] intento {attempt}/{max_retries}: content.json es None — {url}")

            if attempt < max_retries:
                time.sleep(attempt * 3)  # 3s, 6s entre reintentos

        return None, None

    def get_technical_specs_data(self, url: str) -> TechnicalSpecsData | None:
        """
        Extrae las fichas técnicas usando un schema estructurado con campos específicos.
        """
        # Generar schema desde el modelo Pydantic
        schema = TechnicalSpecsData.model_json_schema()
        # Agregar prompt de guía para ayudar al LLM
        extraction_prompt = """
Extract all motorcycle technical specifications from this page and return values for the schema fields.
The specs can be in tables, cards, lists (<li>), divs, accordions, tabs, or any visual layout.

IMPORTANT:
- Do NOT rely on exact label matching.
- Interpret synonyms, spelling variants, accents, abbreviations, uppercase/lowercase, and multilingual labels.
- If the page uses "label/value" pairs (for example "spec-name" and "spec-value"), map each pair semantically.
- Keep original value text and units exactly as shown.
- If not found, return null.

Field mapping with common aliases (non-exhaustive):
- encendido: ignition, sistema de encendido, encendido, CDI, TCI.
- posicion_manejo: riding position, posición de manejo, ergonomía, postura.
- cilindrada: cilindrada, cilindraje, displacement, engine capacity, cm3/cc.
- diametro_por_carrera: diámetro x carrera, bore x stroke.
- potencia: potencia, potencia máxima, power, max power.
- torque_maximo: torque, torque máximo, par motor, max torque.
- tipo_motor: motor, tipo de motor, engine type, configuración del motor.
- arranque: arranque, starting, electric start, kick start, eléctrico y pedal.
- freno_delantero: freno delantero, front brake.
- freno_trasero: freno trasero, rear brake.
- neumatico_delantero: neumático delantero, llanta delantera, tire front, front tyre.
- neumatico_trasero: neumático trasero, llanta trasera, tire rear, rear tyre.
- suspension_delantera: suspensión delantera, front suspension.
- suspension_trasera: suspensión trasera, rear suspension.
- combustible: combustible, fuel, tipo de combustible, gasolina, diesel, eléctrico, flex.
- sistema_alimentacion: sistema de alimentación, fuel system, carburador, inyección, EFI/FI/PGM-FI/TBI/MPI/DFI.
- capacidad_combustible: capacidad de combustible, capacidad del tanque, fuel tank capacity, tank.
- rendimiento: rendimiento, consumo, autonomía, fuel economy, km/l.
- tipo_transmision: transmisión, tipo de transmisión, gearbox, mecánica, automática, CVT.
- numero_cambios: número de cambios, velocidades, marchas, gears, "5 velocidades", "6-speed".
- longitud_total: longitud total, largo total, overall length.
- ancho_total: ancho total, overall width.
- altura_total: altura total, overall height.
- altura_asiento: altura del asiento, altura al sillín, seat height.
- distancia_entre_ejes: distancia entre ejes, entre-ejes, wheelbase.
- distancia_minima_suelo: distancia mínima al suelo, despeje al suelo, ground clearance.
- peso_total_liquidos: peso total con líquidos, peso con fluidos, curb weight; if unavailable, use closest available weight (peso neto/en seco) as fallback.

Disambiguation rules:
- combustible = only energy source/type (gasolina, diesel, eléctrico, flex, etc.).
- sistema_alimentacion = only delivery technology (carburador, inyección, EFI, etc.).
- If transmission text includes gear count (e.g., "Mecánica 5 velocidades"), set:
  - tipo_transmision = full transmission text
  - numero_cambios = extracted gear count text (e.g., "5 velocidades")
        """

        actions = [
            {"type": "scroll", "direction": "down"},
            {"type": "wait", "milliseconds": 2000},
        ]

        max_retries = 3
        for attempt in range(1, max_retries + 1):
            content = self.scraper.get_content_from_website(
                url,
                formats=[{
                    "type": "json",
                    "schema": schema,
                    "prompt": extraction_prompt
                }],
                actions=actions,
                wait_for=5000,
            )

            if content is None:
                print(f"[get_technical_specs_data] intento {attempt}/{max_retries}: content es None — {url}")
            else:
                raw_payload = getattr(content, "json", None)
                html_content = self.scraper.get_content_from_website(
                    url,
                    formats=["html"],
                    actions=actions,
                    wait_for=5000,
                )
                html_payload = getattr(html_content, "html", None)
                html_specs = self._extract_specs_from_html(html_payload)

                llm_specs = None
                if raw_payload is not None:
                    try:
                        llm_specs = parse_technical_specs_payload(raw_payload)
                    except Exception as e:
                        print(f"[get_technical_specs_data] intento {attempt}/{max_retries}: parse LLM falló — {e}")
                else:
                    print(f"[get_technical_specs_data] intento {attempt}/{max_retries}: content.json es None — {url}")

                merged_payload = {}
                if llm_specs is not None:
                    merged_payload.update(self._model_to_dict(llm_specs))

                for field, value in html_specs.items():
                    merged_payload[field] = self._prefer_value(merged_payload.get(field), value)

                if merged_payload:
                    try:
                        return parse_technical_specs_payload(merged_payload)
                    except Exception as e:
                        print(f"[get_technical_specs_data] intento {attempt}/{max_retries}: parse merge falló — {e}")

            if attempt < max_retries:
                time.sleep(attempt * 3)

        return None
