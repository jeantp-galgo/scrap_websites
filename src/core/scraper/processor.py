import json
import re
from typing import Optional, List, Any

from pydantic import BaseModel, Field

from src.core.scraper.app import ScrapingUtils
from src.core.scraper.brands.vento.handle import handle_vento
from src.core.scraper.brands.italika.handle import handle_italika
from src.core.scraper.brands.honda.handle import handle_honda
from src.core.scraper.brands.yamaha.handle import handle_yamaha
from src.core.scraper.brands.ryder.handle import handle_ryder
from src.core.scraper.brands.zmoto.handle import handle_zmoto
from src.core.scraper.brands.tvs.handle import handle_tvs

def check_website(url):
    print("url", url)
    if "vento.com" in url:
        print("website: vento")
        return "vento"
    if "italika.mx" in url:
        print("website: italika")
        return "italika"
    if "honda.mx" in url:
        print("website: honda")
        return "honda"
    if "yamaha-motor" in url:
        print("website: yamaha")
        return "yamaha"
    if "rydermx.com" in url :
        print("website: ryder")
        return "ryder"
    if "zmoto.com.mx" in url:
        print("website: zmoto")
        return "zmoto"
    if "tvsmotor.com" in url:
        print("website: tvsmotor")
        return "tvs"
    else:
        print("website: none")
        return None

class ImagesProcessor:
    def __init__(self):
        self.scraper = ScrapingUtils()

    def test_extract(self, url: str, formats: list) -> list:
        content = self.scraper.get_content_from_website(url, formats=formats)
        return content

    class ModelData(BaseModel):
        base_price: Optional[float] = Field(default=None)
        net_price: Optional[float] = Field(default=None)
        discount_amount: Optional[float] = Field(default=None)
        model: Optional[str] = Field(default=None)
        colors: Optional[List[str]] = Field(default=None)

    def _coerce_model_payload(self, payload: dict) -> dict:
        # Normaliza números y colors para que el schema sea más robusto
        normalized = dict(payload)
        for field in ["base_price", "net_price", "discount_amount"]:
            value = normalized.get(field)
            if isinstance(value, str):
                value = re.sub(r"[^\d]", "", value)
                normalized[field] = int(value) if value else None
        if isinstance(normalized.get("colors"), str):
            normalized["colors"] = [c.strip() for c in normalized["colors"].split(",") if c.strip()]
        return normalized

    def _parse_model_payload(self, raw_data: Any) -> "ImagesProcessor.ModelData":
        # Acepta dict o JSON string producido por el prompt
        if isinstance(raw_data, str):
            raw_data = json.loads(raw_data)
        payload = self._coerce_model_payload(raw_data or {})
        try:
            return self.ModelData.model_validate(payload)
        except AttributeError:
            # Compatibilidad con Pydantic v1
            return self.ModelData.parse_obj(payload)

    def get_model_data(self, url: str) -> "ImagesProcessor.ModelData | None":
        default_prompt = """
Extract product pricing information and available colors from this page.
Return ONLY a valid JSON object with this exact structure:
{
  "base_price": number or null,
  "net_price": number or null,
  "discount_amount": number or null,
  "model": string or null,
  "colors": array of strings or null
}

Rules:
- If a value is not found, return null for that field.
- net_price is base_price - discount_amount. If not discount_amount, net_price is base_price
- Prices must be numbers without currency symbols, commas, or dots as thousand separators.
- Colors must be an array of color names (e.g., ["Rojo", "Negro"]).
- Do not include any text outside the JSON object.
        """
        actions = [
            {"type": "scroll", "direction": "down"},  # Scroll inicial
            {"type": "wait", "milliseconds": 2000},  # Esperar 2 segundos después del scroll
        ]

        content = self.scraper.get_content_from_website(
            url,
            formats=[{
                "type": "json",
                "prompt": default_prompt
            }],
            actions=actions,
            wait_for=1200,
        )
        # TODO: Acá se debe llamar al LLM con default_prompt y luego parsear el JSON


        # return content
        if content is None:
            return None
        raw_payload = getattr(content, "json", None)
        if raw_payload is None:
            return None
        return self._parse_model_payload(raw_payload)

    # TODO: Identificar qué característica está disponible para cada marca, es decir, extraer imágenes, ficha técnica o modeldata, o todos.
    def get_images_from_website(self, url: str) -> list:
        """
        Obtiene las imágenes de un sitio web. Se maneja el caso específico de una marca.
        Args:
            url: str
        Returns:
            images: list[str]
            image_urls: list[str]
        """
        website = check_website(url)
        if website == "vento":
            content = self.scraper.get_content_from_website(url, formats=["images"])
            return handle_vento("images", content.images)
        if website == "italika":
            content = self.scraper.get_content_from_website(url, formats=["images"])
            return handle_italika("images", content.images)
        if website == "honda":
            content = self.scraper.get_content_from_website(url, formats=["images"])
            return handle_honda("images", content.images)
        if website == "yamaha":
            content = self.scraper.get_content_from_website(url, formats=["images"])
            return handle_yamaha(url, "images", content.images)
        if website == "ryder":
            content = self.scraper.get_content_from_website(url, formats=["html", "images"])
            return handle_ryder("images", content)
        if website == "zmoto":
            content = self.scraper.get_content_from_website(url, formats=["html"])
            return handle_zmoto("images", content)
            # return content
        if website == "tvsmotor":
            content = self.scraper.get_content_from_website(url, formats=["html"])
            return handle_tvs("images", content)
        return content

    def get_technical_specs(self, url: str) -> list:
        """
        Obtiene las fichas técnicas de un sitio web.
        Args:
            url: str
        Returns:
            technical_specs: list[str]
        """
        website = check_website(url)
        if website == "honda":
            actions = [
                {"type": "click", "selector": "a.btn-specs"},  # click para desplegar la ficha
                {"type": "wait", "milliseconds": 1200},        # espera a que cargue el contenido
            ]
            content = self.scraper.get_content_from_website(
                url,
                formats=["html"],
                actions=actions,
                wait_for=1200,
            )
            return handle_honda("technical_specs", content)

        if website == "vento":
            content = self.scraper.get_content_from_website(url, formats=["links"])
            return handle_vento("technical_specs", content)

        if website == "italika":
            content = self.scraper.get_content_from_website(url, formats=["html"])
            return handle_italika("technical_specs", content)

        if website == "yamaha":
            content = self.scraper.get_content_from_website(url, formats=["html"])
            return handle_yamaha(url, "technical_specs", content)

        if website == "ryder":
            content = self.scraper.get_content_from_website(url, formats=["html"])
            return handle_ryder("technical_specs", content)

        if website == "zmoto":
            content = self.scraper.get_content_from_website(url, formats=["html"])
            return handle_zmoto("technical_specs", content)

        if website == "tvs":
            content = self.scraper.get_content_from_website(url,
            formats=["html"],
            wait_for=5000)
            return handle_tvs("technical_specs", content)
        return content