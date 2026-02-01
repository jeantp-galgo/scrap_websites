from typing import Any
import re

def get_urls_from_firecrawl_map(url_list: Any):
    """ Obtiene las URLs de un sitio web desde la respuesta de Firecrawl """
    links = getattr(url_list, "links", []) or []
    tuplas_urls = [(link.url, link.title, link.description) for link in links]
    return [tupla[0] for tupla in tuplas_urls]


def extract_image_urls_from_html(html: str) -> list:
    """ Extrae URLs de imágenes desde HTML sin depender de clases específicas """
    if not html:
        return []

    urls = []
    seen = set()

    def add_url(url: str):
        if not url:
            return
        cleaned = url.strip().strip("\"'")
        if not cleaned or cleaned.startswith("data:"):
            return
        if cleaned in seen:
            return
        seen.add(cleaned)
        urls.append(cleaned)

    # comentario en español: src / data-src / data-lazy-src / data-original
    img_src_pattern = re.compile(
        r"<img[^>]+(?:src|data-src|data-lazy-src|data-original)\s*=\s*['\"]([^'\"]+)['\"]",
        re.IGNORECASE,
    )
    for match in img_src_pattern.findall(html):
        add_url(match)

    # comentario en español: srcset con multiples URLs
    srcset_pattern = re.compile(
        r"srcset\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE
    )
    for srcset in srcset_pattern.findall(html):
        for part in srcset.split(","):
            candidate = part.strip().split(" ")[0]
            add_url(candidate)

    # comentario en español: background-image en estilos inline o bloques
    url_pattern = re.compile(r"url\(([^)]+)\)", re.IGNORECASE)
    for match in url_pattern.findall(html):
        candidate = match.strip().strip("\"'")
        # comentario en español: evitar recursos no imagen
        if re.search(r"\.(js|css|woff2?|ttf|eot|map)(\?|#|$)", candidate, re.IGNORECASE):
            continue
        add_url(candidate)

    return urls