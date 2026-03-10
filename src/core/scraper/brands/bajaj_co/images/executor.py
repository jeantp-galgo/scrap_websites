from bs4 import BeautifulSoup


def detect_url_patterns_from_html(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    rotators = soup.find_all("image-rotator")
    patterns = []

    for specs_div in rotators:
        src = specs_div.get("src")
        total_images = specs_div.get("total-images")

        if not src or not total_images:
            continue

        clean_src = src.replace("-${var}", "")
        if "." not in clean_src:
            continue

        image_src, extension = clean_src.rsplit(".", 1)
        patterns.append((image_src, extension, total_images))

    return patterns

def create_urls_from_pattern(image_src: str, extension: str, total_images: int) -> list:
    """
    Crea las URLs de las imágenes de la marca Bajaj_co
    """
    urls = []
    url_base = "https://grupouma.com/"
    total = int(total_images)
    if total <= 1:
        # Para consistencia, cuando hay 1 imagen se normaliza con consecutivo -01.
        urls.append(f"{url_base}{image_src}-01.{extension}")
        return urls

    for i in range(1, total + 1):
        if total <= 10:
            index = f"0{i}"
        else:
            index = f"{i}"
        urls.append(f"{url_base}{image_src}-{index}.{extension}")
    return urls


def handle_images(content) -> list:
    """
    Maneja el caso específico de la marca Bajaj_co.
    """
    all_urls = []

    # Compatibilidad con el flujo anterior (objeto con .html)
    if hasattr(content, "html"):
        patterns = detect_url_patterns_from_html(content.html)
        for image_src, extension, total_images in patterns:
            return create_urls_from_pattern(image_src, extension, total_images)
        return []

    # Nuevo flujo: diccionario {"dsm_shapes_0": "<html...>", ...}
    if isinstance(content, dict):
        print(f"[bajaj_co] HTMLs recibidos: {len(content)}")
        for shape_key, html in content.items():
            patterns = detect_url_patterns_from_html(html)
            print(f"[bajaj_co] {shape_key} -> rotators detectados: {len(patterns)}")

            shape_urls = []
            # Evita duplicar patrones iguales dentro del mismo HTML
            for image_src, extension, total_images in set(patterns):
                urls = create_urls_from_pattern(image_src, extension, total_images)
                shape_urls.extend(urls)

            print(f"[bajaj_co] {shape_key} -> urls generadas: {len(shape_urls)}")
            all_urls.extend(shape_urls)

        # Deduplicar manteniendo orden
        return list(dict.fromkeys(all_urls))

    return []