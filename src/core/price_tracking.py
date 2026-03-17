"""
Seguimiento de precios con Firecrawl Change Tracking.

Dos modos: con JSON (schema price/availability, 5 cr/pág) y sin JSON
(markdown + git-diff, parseo por regex). Salida normalizada a filas CSV.
"""

import os
import re
from typing import Any


# Schema para modo JSON: precios (base, descuento, neto) y disponibilidad.
# El LLM debe distinguir si la página muestra un solo precio (neto) o dos (base + descuento).
CHANGE_TRACKING_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "price_base": {
            "type": "string",
            "description": "Precio base o listado (antes de descuento). Vacío si solo hay precio neto.",
        },
        "price_discount": {
            "type": "string",
            "description": "Descuento aplicado o segundo precio mostrado (ej. precio tachado). Vacío si no aplica.",
        },
        "price_net": {
            "type": "string",
            "description": "Precio final a pagar por el cliente. Si solo hay un precio en la página, es este.",
        },
        "availability": {"type": "string"},
    },
}

# Prompt para guiar al LLM: identificar si es precio base+descuento o solo precio neto
CHANGE_TRACKING_JSON_PROMPT = (
    "Identifica los precios mostrados en la página. "
    "Si hay un solo precio visible, es el precio neto (price_net); deja price_base y price_discount vacíos. "
    "Si hay dos precios (ej. uno tachado y otro destacado, o 'antes/después'), "
    "extrae el precio base/listado en price_base, el descuento o segundo precio en price_discount si aplica, "
    "y el precio final que paga el cliente en price_net. "
    "Siempre rellena price_net con el monto final cuando exista."
)


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Acceso seguro a atributo o clave."""
    if obj is None:
        return default
    if hasattr(obj, key):
        return getattr(obj, key, default)
    if isinstance(obj, dict):
        return obj.get(key, default)
    return default


def _build_formats_json(tag: str | None = None) -> list:
    """Construye formats para changeTracking en modo JSON (base, descuento, neto)."""
    ct: dict[str, Any] = {
        "type": "changeTracking",
        "modes": ["json"],
        "schema": CHANGE_TRACKING_JSON_SCHEMA,
        "prompt": CHANGE_TRACKING_JSON_PROMPT,
    }
    if tag:
        ct["tag"] = tag
    return ["markdown", ct]


def _build_formats_markdown(tag: str | None = None) -> list:
    """Construye formats para changeTracking sin JSON (git-diff opcional)."""
    ct: dict[str, Any] = {"type": "changeTracking", "modes": ["git-diff"]}
    if tag:
        ct["tag"] = tag
    return ["markdown", ct]


def _model_name_from_url(url: str) -> str:
    """Deriva model_name desde la URL (slug sin ID numérico final)."""
    url = url.rstrip("/")
    if "/p" in url:
        url = url.split("/p")[0]
    segment = url.split("/")[-1] if "/" in url else url
    # Quitar uno o más sufijos numéricos largos (ej. -34006713 o -34006713-1300703478)
    segment = re.sub(r"(-\d{6,})+$", "", segment)
    return segment.replace("-", " ").strip() or url


def _model_name_from_metadata(metadata: Any) -> str | None:
    """Obtiene título desde metadata de Firecrawl para usar como model_name."""
    if metadata is None:
        return None
    title = _get(metadata, "title") or _get(metadata, "ogTitle")
    if isinstance(title, str) and title.strip():
        return title.strip()
    return None


def _find_all_prices_in_markdown(markdown: str) -> list[tuple[str, int]]:
    """Devuelve todos los precios encontrados y su posición (start). [(precio, start), ...]."""
    if not markdown or not isinstance(markdown, str):
        return []
    patterns = [
        r"\$\s*([\d,]+(?:\.\d{2})?)",
        r"([\d]{1,3}(?:,[\d]{3})*(?:\.[\d]{2})?)\s*MXN",
        r"([\d]{1,3}(?:\.[\d]{3})*(?:,[\d]{2})?)\s*MXN",
        r"precio[:\s]+[\$]?\s*([\d,\.]+)",
    ]
    out: list[tuple[str, int]] = []
    for pat in patterns:
        for m in re.finditer(pat, markdown, re.IGNORECASE):
            out.append((m.group(1).strip(), m.start()))
    return sorted(out, key=lambda x: x[1])


def parse_price_from_markdown(markdown: str, prefer_second: bool = True) -> str:
    """
    Extrae precio del markdown. Si prefer_second y hay al menos 2 matches, devuelve el segundo
    (en Italika: primero suele ser "Pago de contado", segundo el precio oferta vigente).
    """
    all_m = _find_all_prices_in_markdown(markdown)
    if not all_m:
        return ""
    if prefer_second and len(all_m) >= 2:
        return all_m[1][0]
    return all_m[0][0]


def parse_availability_from_markdown(markdown: str) -> str:
    """Detecta disponibilidad en el texto (No disponible, Agregar al carrito, etc.)."""
    if not markdown or not isinstance(markdown, str):
        return ""
    lower = markdown.lower()
    if "no disponible" in lower or "agotado" in lower:
        return "No disponible"
    if "agregar al carrito" in lower or "disponible" in lower or "en stock" in lower:
        return "Disponible"
    return ""


def _row_from_json_mode(
    url: str,
    brand_name: str,
    page_data: Any,
    metadata: Any,
) -> dict[str, Any]:
    """Construye una fila CSV a partir de la respuesta en modo JSON (base, neto, descuento)."""
    ct = _get(page_data, "changeTracking") or _get(page_data, "change_tracking")
    # Siempre desde URL para evitar títulos incorrectos o mezcla de resultados en batch
    model = _model_name_from_url(url)
    row: dict[str, Any] = {
        "brand_name": brand_name,
        "model_name": model,
        "url": url,
        "change_status": _get(ct, "changeStatus") or _get(ct, "change_status") or "",
        "previous_scrape_at": _get(ct, "previousScrapeAt") or _get(ct, "previous_scrape_at") or "",
        "visibility": _get(ct, "visibility") or "",
        "price_base_current": "",
        "price_net_current": "",
        "price_discount_current": "",
        "price_base_previous": "",
        "price_net_previous": "",
        "price_discount_previous": "",
        "price_current": "",
        "price_previous": "",
        "availability_current": "",
        "availability_previous": "",
        "extraction_mode": "json",
    }
    json_diff = _get(ct, "json")
    if json_diff:
        for key, col_current, col_previous in (
            ("price_base", "price_base_current", "price_base_previous"),
            ("price_net", "price_net_current", "price_net_previous"),
            ("price_discount", "price_discount_current", "price_discount_previous"),
        ):
            field = _get(json_diff, key)
            if field is not None:
                row[col_current] = str(_get(field, "current") or "")
                row[col_previous] = str(_get(field, "previous") or "")
        price_net_cur = row["price_net_current"]
        price_base_cur = row["price_base_current"]
        row["price_current"] = price_net_cur or price_base_cur
        price_net_prev = row["price_net_previous"]
        price_base_prev = row["price_base_previous"]
        row["price_previous"] = price_net_prev or price_base_prev
        avail = _get(json_diff, "availability")
        if avail is not None:
            row["availability_current"] = str(_get(avail, "current") or "")
            row["availability_previous"] = str(_get(avail, "previous") or "")
    else:
        # change_tracking.json solo viene cuando status es "changed". Intentar extracción
        # actual en page_data.json (nivel ítem) o fallback a markdown.
        current_extraction = _get(page_data, "json")
        if isinstance(current_extraction, dict):
            for key, col in (
                ("price_base", "price_base_current"),
                ("price_net", "price_net_current"),
                ("price_discount", "price_discount_current"),
            ):
                row[col] = str(current_extraction.get(key) or "")
            row["price_current"] = row["price_net_current"] or row["price_base_current"]
            if current_extraction.get("availability") is not None:
                row["availability_current"] = str(current_extraction.get("availability") or "")
        if not row["price_current"]:
            markdown = _get(page_data, "markdown") or ""
            row["price_net_current"] = parse_price_from_markdown(markdown)
            row["price_current"] = row["price_net_current"]
    return row


def _row_from_markdown_mode(
    url: str,
    brand_name: str,
    page_data: Any,
    metadata: Any,
) -> dict[str, Any]:
    """Construye una fila CSV a partir de la respuesta en modo markdown (sin JSON)."""
    ct = _get(page_data, "changeTracking") or _get(page_data, "change_tracking")
    markdown = _get(page_data, "markdown") or ""
    model = _model_name_from_url(url)
    all_prices = _find_all_prices_in_markdown(markdown)
    # Italika: primer precio = "Pago de contado", segundo = oferta vigente (no tachado)
    price_cur = (all_prices[1][0] if len(all_prices) >= 2 else all_prices[0][0]) if all_prices else ""
    row = {
        "brand_name": brand_name,
        "model_name": model,
        "url": url,
        "change_status": _get(ct, "changeStatus") or _get(ct, "change_status") or "",
        "previous_scrape_at": _get(ct, "previousScrapeAt") or _get(ct, "previous_scrape_at") or "",
        "visibility": _get(ct, "visibility") or "",
        "price_base_current": "",
        "price_net_current": price_cur,
        "price_discount_current": "",
        "price_base_previous": "",
        "price_net_previous": "",
        "price_discount_previous": "",
        "price_current": price_cur,
        "price_previous": "",
        "availability_current": parse_availability_from_markdown(markdown),
        "availability_previous": "",
        "extraction_mode": "markdown",
    }
    return row


def run_price_tracking(
    urls: list[str],
    brand_name: str,
    mode: str = "json",
    tag: str | None = None,
) -> list[dict[str, Any]]:
    """
    Ejecuta seguimiento de precios para una lista de URLs.

    Args:
        urls: Lista de URLs de producto.
        brand_name: Nombre de la marca (ej. 'italika').
        mode: 'json' (schema + LLM) o 'markdown' (parseo por regex).
        tag: Tag opcional para changeTracking (ej. 'italika-prices').

    Returns:
        Lista de dicts con columnas: brand_name, model_name, url, change_status,
        previous_scrape_at, visibility, price_current, price_previous,
        availability_current, availability_previous, extraction_mode.
    """
    if not urls:
        return []
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY no está configurada")
    from firecrawl import Firecrawl
    firecrawl = Firecrawl(api_key=api_key)
    tag = tag or f"{brand_name}-prices"
    formats = _build_formats_json(tag) if mode == "json" else _build_formats_markdown(tag)
    rows: list[dict[str, Any]] = []
    # batch_scrape devuelve lista de resultados en el mismo orden que urls
    try:
        # Parámetros fijos para que change_status sea estable: la doc indica que variar
        # onlyMainContent entre scrapes da comparaciones poco fiables.
        result = firecrawl.batch_scrape(
            urls,
            formats=formats,
            only_main_content=True,
            poll_interval=2,
            wait_timeout=300,
        )
    except Exception as e:
        raise RuntimeError(f"Error en batch_scrape: {e}") from e
    data = _get(result, "data")
    if data is None and isinstance(result, list):
        data = result
    if not data:
        return []
    if isinstance(data, dict):
        data = [data]
    # Emparejar por URL: el batch puede no devolver en el mismo orden que urls.
    # Mapa respuesta URL normalizada -> item (usa sourceURL del metadata cuando exista).
    def _norm(u: str) -> str:
        return (u or "").rstrip("/").split("?")[0]
    url_to_item: dict[str, Any] = {}
    for item in data:
        meta = _get(item, "metadata")
        resp_url = _get(meta, "sourceURL") or _get(meta, "url") or ""
        if resp_url:
            url_to_item[_norm(resp_url)] = item
    for i, requested_url in enumerate(urls):
        norm_req = _norm(requested_url)
        item = url_to_item.get(norm_req)
        if item is None and i < len(data):
            item = data[i]
        if item is None:
            continue
        url = requested_url
        metadata = _get(item, "metadata")
        if mode == "json":
            row = _row_from_json_mode(url, brand_name, item, metadata)
        else:
            row = _row_from_markdown_mode(url, brand_name, item, metadata)
        if not row["url"]:
            row["url"] = url
        rows.append(row)
    return rows
