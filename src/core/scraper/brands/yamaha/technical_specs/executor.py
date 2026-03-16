from bs4 import BeautifulSoup
import asyncio, threading, re


def _fetch_html_with_playwright(url: str) -> str | None:
    """Obtiene el HTML de la página de Yamaha con Playwright (stealth mode)."""

    async def _run_async():
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 900},
            )
            page = await context.new_page()
            await page.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(4000)

            # Scroll para activar lazy load
            for _ in range(6):
                await page.evaluate("window.scrollBy(0, 600)")
                await page.wait_for_timeout(500)
            await page.wait_for_timeout(2000)

            html = await page.content()
            await context.close()
            await browser.close()
            return html

    def _run_in_thread():
        import sys
        if sys.platform == "win32":
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_run_async())
        finally:
            loop.close()

    result_container = []
    exc_container = []

    def _thread_target():
        try:
            result_container.append(_run_in_thread())
        except Exception as e:
            exc_container.append(e)

    t = threading.Thread(target=_thread_target)
    t.start()
    t.join()

    if exc_container:
        raise exc_container[0]

    return result_container[0] if result_container else None


def _parse_yamaha_specs_html(html: str) -> dict:
    """
    Parsea el HTML de la página de Yamaha y extrae los pares label/valor
    de la sección .motorcycle-specification → .panel-faq.

    Estructura del HTML:
        <div class="d-flex justify-content-between">
            <p><strong>Label:</strong></p>
            <p class="text-end">Valor</p>
        </div>
    """
    soup = BeautifulSoup(html, "html.parser")

    # Extraer todos los pares label/valor de todos los panel-faq
    raw = {}
    for panel in soup.select(".panel-faq"):
        for row in panel.select(".d-flex.justify-content-between"):
            label_el = row.select_one("p strong")
            value_els = row.select("p")
            if label_el and len(value_els) >= 2:
                label = label_el.get_text(strip=True).rstrip(":").strip().upper()
                value = value_els[-1].get_text(strip=True)
                if label and value:
                    raw[label] = value

    def _get(*keys):
        for k in keys:
            v = raw.get(k.upper())
            if v:
                return v
        return None

    tipo_trans = _get("TRANSMISIÓN", "TRANSMISION")
    numero_cambios = None
    if tipo_trans:
        m = re.search(r"\b(\d+)\s*(velocidades|marchas|gears?|speed)\b", tipo_trans, re.IGNORECASE)
        if m:
            numero_cambios = m.group(0)

    # Manejar confusión combustible / sistema_alimentacion
    combustible_raw = _get("COMBUSTIBLE", "TIPO DE COMBUSTIBLE")
    sistema_raw = _get("SISTEMA DE ALIMENTACIÓN", "SISTEMA DE ALIMENTACION", "ALIMENTACIÓN", "ALIMENTACION")
    sistema_kw = ("carbur", "inye", "efi", "fi", "pgm-fi", "tbi", "mpi", "dfi")
    combustible_kw = ("gasolina", "petrol", "diesel", "diésel", "electr", "flex", "etanol", "hibr")

    if combustible_raw and any(k in combustible_raw.lower() for k in sistema_kw) and not sistema_raw:
        sistema_raw, combustible_raw = combustible_raw, None
    if sistema_raw and any(k in sistema_raw.lower() for k in combustible_kw) and not combustible_raw:
        combustible_raw, sistema_raw = sistema_raw, None

    return {
        "encendido":              _get("SISTEMA DE ENCENDIDO", "ENCENDIDO", "IGNICIÓN", "IGNICION"),
        "posicion_manejo":        _get("POSICIÓN DE MANEJO", "POSICION DE MANEJO"),
        "cilindrada":             _get("CILINDRADA", "CILINDRAJE"),
        "diametro_por_carrera":   _get("DIÁMETRO X CARRERA", "DIAMETRO X CARRERA", "DIÁMETRO POR CARRERA", "DIAMETRO POR CARRERA"),
        "potencia":               _get("POTENCIA", "POTENCIA MÁXIMA", "POTENCIA MAXIMA"),
        "torque_maximo":          _get("TORQUE MÁXIMO", "TORQUE MAXIMO", "TORQUE"),
        "tipo_motor":             _get("MOTOR", "TIPO DE MOTOR"),
        "arranque":               _get("ARRANQUE"),
        "freno_delantero":        _get("FRENO DELANTERO"),
        "freno_trasero":          _get("FRENO TRASERO"),
        "neumatico_delantero":    _get("NEUMÁTICO DELANTERO", "NEUMATICO DELANTERO", "LLANTA DELANTERA"),
        "neumatico_trasero":      _get("NEUMÁTICO TRASERO", "NEUMATICO TRASERO", "LLANTA TRASERA"),
        "suspension_delantera":   _get("SUSPENSIÓN DELANTERA", "SUSPENSION DELANTERA"),
        "suspension_trasera":     _get("SUSPENSIÓN TRASERA", "SUSPENSION TRASERA"),
        "combustible":            combustible_raw,
        "sistema_alimentacion":   sistema_raw,
        "capacidad_combustible":  _get("CAPACIDAD DE COMBUSTIBLE", "CAPACIDAD DEL TANQUE", "TANQUE"),
        "rendimiento":            _get("RENDIMIENTO", "CONSUMO"),
        "tipo_transmision":       tipo_trans,
        "numero_cambios":         numero_cambios,
        "longitud_total":         _get("LONGITUD TOTAL", "LARGO TOTAL"),
        "ancho_total":            _get("ANCHO TOTAL"),
        "altura_total":           _get("ALTURA TOTAL"),
        "altura_asiento":         _get("ALTURA AL SILLÍN", "ALTURA AL SILLIN", "ALTURA DEL ASIENTO"),
        "distancia_entre_ejes":   _get("DISTANCIA ENTRE EJES", "ENTRE EJES"),
        "distancia_minima_suelo": _get("DISTANCIA MÍNIMA AL SUELO", "DISTANCIA MINIMA AL SUELO", "DESPEJE AL SUELO"),
        "peso_total_liquidos":    _get("PESO TOTAL CON LÍQUIDOS", "PESO TOTAL CON LIQUIDOS", "PESO NETO", "PESO EN SECO", "PESO"),
    }


def handle_technical_specs(url: str, content) -> dict | None:
    """
    Extrae la ficha técnica de Yamaha México.

    Los datos están en .motorcycle-specification → .panel-faq sin necesidad de clicks.
    Intenta primero con el HTML de Firecrawl (ya disponible); si no encuentra specs,
    usa Playwright como fallback (stealth mode para evitar detección de bot).
    """
    # Intento 1: HTML de Firecrawl (ya disponible, sin costo adicional)
    html = getattr(content, "html", None)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        if soup.select_one(".motorcycle-specification"):
            parsed = _parse_yamaha_specs_html(html)
            non_null = sum(1 for v in parsed.values() if v is not None)
            if non_null > 0:
                print(f"[yamaha] Specs extraídas del HTML de Firecrawl ({non_null} campos)")
                return parsed

    # Intento 2: Playwright como fallback
    print(f"[yamaha] HTML de Firecrawl insuficiente, usando Playwright: {url}")
    pw_html = _fetch_html_with_playwright(url)
    if pw_html:
        parsed = _parse_yamaha_specs_html(pw_html)
        non_null = sum(1 for v in parsed.values() if v is not None)
        print(f"[yamaha] Specs extraídas con Playwright ({non_null} campos)")
        return parsed if non_null > 0 else None

    print("[yamaha] No se pudo extraer la ficha técnica")
    return None
