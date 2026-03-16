from bs4 import BeautifulSoup
import asyncio, threading, re

# Selector del botón que abre la ficha técnica (primer trigger de disclosure en la página)
_DISCLOSURE_BTN_SELECTOR = "button.vtex-disclosure-layout-1-x-trigger--trigger-d-pdp-tvs"
# Selector del contenedor de specs tras abrir el accordion
_SPECS_CONTAINER_SELECTOR = "div.vtex-flex-layout-0-x-flexColChild--spec-productSpecificationGroup"


def _fetch_specs_with_playwright(url: str) -> str | None:
    """Abre la página con Playwright, espera JS, clica el botón de specs y retorna el HTML del bloque."""

    async def _run_async():
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            # Stealth mode: user-agent real + deshabilitar señales de automatización
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
            # Ocultar webdriver flag
            await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            await page.goto(url, wait_until="domcontentloaded")

            # Esperar a que VTEX monte todos los componentes
            await page.wait_for_timeout(8000)

            # Scroll progresivo lento para activar lazy-load de componentes
            for _ in range(10):
                await page.evaluate("window.scrollBy(0, 400)")
                await page.wait_for_timeout(1200)

            # Espera adicional tras scroll completo
            await page.wait_for_timeout(3000)

            # Volver arriba y esperar
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(2000)

            specs_html = None
            btn_count = await page.locator(_DISCLOSURE_BTN_SELECTOR).count()

            if btn_count > 0:
                btn = page.locator(_DISCLOSURE_BTN_SELECTOR).first
                await btn.scroll_into_view_if_needed()
                await page.wait_for_timeout(1000)
                await btn.click(force=True)
                await page.wait_for_timeout(3000)

                specs_count = await page.locator(_SPECS_CONTAINER_SELECTOR).count()
                if specs_count > 0:
                    specs_html = await page.locator(_SPECS_CONTAINER_SELECTOR).first.inner_html()
            else:
                print("[auteco_tvs] Botón de ficha técnica no encontrado en el DOM")

            await context.close()
            await browser.close()
            return specs_html

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


def _parse_vtex_specs_html(html: str) -> dict:
    """
    Parsea el HTML de VTEX (pares data-specification-name / data-specification-value)
    y retorna un dict estandarizado con los campos de TechnicalSpecsData.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Extraer todos los pares nombre → valor del HTML de VTEX
    raw = {}
    for span in soup.select("span[data-specification-name][data-specification-value]"):
        name = span.get("data-specification-name", "").strip().upper()
        value = span.get("data-specification-value", "").strip()
        if name and value:
            raw[name] = value

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
    combustible_raw = _get("COMBUSTIBLE")
    sistema_raw = _get("SISTEMA DE ALIMENTACIÓN", "SISTEMA DE ALIMENTACION")
    sistema_kw = ("carbur", "inye", "efi", "fi", "pgm-fi", "tbi", "mpi", "dfi")
    combustible_kw = ("gasolina", "petrol", "diesel", "diésel", "electr", "flex", "etanol", "hibr")

    if combustible_raw and any(k in combustible_raw.lower() for k in sistema_kw) and not sistema_raw:
        sistema_raw, combustible_raw = combustible_raw, None
    if sistema_raw and any(k in sistema_raw.lower() for k in combustible_kw) and not combustible_raw:
        combustible_raw, sistema_raw = sistema_raw, None

    return {
        "encendido":              _get("SISTEMA DE ENCENDIDO", "ENCENDIDO", "IGNICIÓN", "IGNICION"),
        "posicion_manejo":        _get("POSICIÓN DE MANEJO", "POSICION DE MANEJO"),
        "cilindrada":             _get("CILINDRAJE", "CILINDRADA"),
        "diametro_por_carrera":   _get("DIÁMETRO POR CARRERA", "DIAMETRO POR CARRERA", "DIÁMETRO X CARRERA"),
        "potencia":               _get("POTENCIA MÁXIMA", "POTENCIA MAXIMA", "POTENCIA"),
        "torque_maximo":          _get("TORQUE MÁXIMO", "TORQUE MAXIMO", "TORQUE"),
        "tipo_motor":             _get("MOTOR", "TIPO DE MOTOR"),
        "arranque":               _get("ARRANQUE"),
        "freno_delantero":        _get("FRENO DELANTERO"),
        "freno_trasero":          _get("FRENO TRASERO"),
        "neumatico_delantero":    _get("LLANTA DELANTERA", "NEUMÁTICO DELANTERO", "NEUMATICO DELANTERO"),
        "neumatico_trasero":      _get("LLANTA TRASERA", "NEUMÁTICO TRASERO", "NEUMATICO TRASERO"),
        "suspension_delantera":   _get("SUSPENSIÓN DELANTERA", "SUSPENSION DELANTERA"),
        "suspension_trasera":     _get("SUSPENSIÓN TRASERA", "SUSPENSION TRASERA"),
        "combustible":            combustible_raw,
        "sistema_alimentacion":   sistema_raw,
        "capacidad_combustible":  _get("CAPACIDAD DEL TANQUE (INCLUYENDO LA RESERVA)", "CAPACIDAD DEL TANQUE", "CAPACIDAD DE COMBUSTIBLE"),
        "rendimiento":            _get("RENDIMIENTO", "CONSUMO"),
        "tipo_transmision":       tipo_trans,
        "numero_cambios":         numero_cambios,
        "longitud_total":         _get("LARGO TOTAL", "LONGITUD TOTAL"),
        "ancho_total":            _get("ANCHO TOTAL"),
        "altura_total":           _get("ALTURA TOTAL"),
        "altura_asiento":         _get("ALTURA AL SILLÍN", "ALTURA AL SILLIN", "ALTURA DEL ASIENTO"),
        "distancia_entre_ejes":   _get("DISTANCIA ENTRE EJES"),
        "distancia_minima_suelo": _get("DISTANCIA MÍNIMA AL SUELO", "DISTANCIA MINIMA AL SUELO", "DESPEJE AL SUELO"),
        "peso_total_liquidos":    _get("PESO TOTAL CON LÍQUIDOS", "PESO TOTAL CON LIQUIDOS", "PESO NETO", "PESO EN SECO"),
    }


def handle_technical_specs(content) -> dict | None:
    """
    Extrae la ficha técnica de Auteco TVS usando Playwright.
    Retorna un dict estandarizado con los campos de TechnicalSpecsData.
    """
    page_url = None
    try:
        page_url = content.metadata.url
    except Exception:
        pass

    if page_url:
        print(f"[auteco_tvs] Extrayendo specs con Playwright: {page_url}")
        specs_html = _fetch_specs_with_playwright(page_url)
        if specs_html:
            return _parse_vtex_specs_html(specs_html)

    # Fallback: intentar con el HTML de Firecrawl (puede estar incompleto)
    html = getattr(content, "html", None)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    specs_div = soup.select_one(_SPECS_CONTAINER_SELECTOR)
    if specs_div:
        return _parse_vtex_specs_html(str(specs_div))
    return None
