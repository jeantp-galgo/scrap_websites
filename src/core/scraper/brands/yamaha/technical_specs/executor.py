from bs4 import BeautifulSoup
def detect_url_pattern(url: str):
    """
    Detecta el patrón de las imágenes de la marca y devuelve la URL base.
    """
    return url.split("/")[-1]

def handle_technical_specs(url: str, content: list[str]) -> list:
    url_base = detect_url_pattern(url)
    html = content.html

    soup = BeautifulSoup(html, "html.parser")
    ficha = soup.select_one(f'a[href*="/sheet/{url_base}"]')
    content = ficha["href"] if ficha else None

    print(f"La ficha técnica encontrada: {content}")
    return content