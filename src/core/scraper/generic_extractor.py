import time
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
Extract all technical specifications of the motorcycle model from this page.
Look for specifications in tables, divs styled as tables, lists, or any other format.

Search for these fields using their names in ANY language (Spanish, English, or other):
- Ignition/Encendido: ignition system type
- Riding position/Posición de manejo: rider position
- Displacement/Cilindrada: engine displacement (cc, cm³, liters)
- Bore x Stroke/Diametro por carrera: cylinder dimensions
- Power/Potencia: engine power (HP, kW, PS)
- Maximum torque/Torque máximo: torque value
- Engine type/Tipo de motor: engine configuration
- Starting/Arranque: starting system
- Front brake/Freno delantero: front braking system
- Rear brake/Freno trasero: rear braking system
- Front tire/Neumático delantero: front tire size
- Rear tire/Neumático trasero: rear tire size
- Front suspension/Suspensión delantera: front suspension type
- Rear suspension/Suspensión trasera: rear suspension type
- Fuel/Combustible: fuel type (e.g., gasoline/petrol, diesel, flex, electric)
- Fuel system/Sistema alimentación: fuel delivery system (e.g., carburetor, fuel injection, EFI/FI, PGM-FI, TBI, MPI, DFI)
- Fuel capacity/Capacidad de combustible: fuel tank capacity
- Fuel economy/Rendimiento: fuel consumption
- Transmission type/Tipo de transmisión: transmission system
- Number of gears/Número de cambios: gear count
- Total length/Longitud total: overall length
- Total width/Ancho total: overall width
- Total height/Altura total: overall height
- Seat height/Altura del asiento: seat height
- Wheelbase/Distancia entre ejes: distance between axles
- Ground clearance/Distancia mínima al suelo: minimum ground clearance
- Curb weight/Peso total con líquidos: weight with fluids

If a value is not found, return null for that field.
Keep the original text format of the specification (do not convert units).
Look for variations in naming and units across different languages.
Important disambiguation:
- "Fuel/Combustible" must capture only the energy source/type of fuel.
- "Fuel system/Sistema alimentación" must capture only the delivery technology (carbureted vs injected, and variants).
- If text says only "Gasolina/Petrol/Flex/Electrico", map it to Fuel/Combustible, not Fuel system.
- If text says "Carburador/Carburada/Inyeccion/Inyeccion electronica/EFI/FI/PGM-FI", map it to Fuel system/Sistema alimentación.
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
                if raw_payload is not None:
                    try:
                        return parse_technical_specs_payload(raw_payload)
                    except Exception as e:
                        print(f"[get_technical_specs_data] intento {attempt}/{max_retries}: parse falló — {e}")
                else:
                    print(f"[get_technical_specs_data] intento {attempt}/{max_retries}: content.json es None — {url}")

            if attempt < max_retries:
                time.sleep(attempt * 3)

        return None
