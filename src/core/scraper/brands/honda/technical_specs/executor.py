from bs4 import BeautifulSoup

def handle_technical_specs(content: list[str]) -> list:
    html = content.html
    print("Contenido HTML:")
    print(html)

    soup = BeautifulSoup(html, "html.parser")
    specs_div = soup.find("div", id="specsAcordion")
    # Si quieres el HTML completo del div
    specs_html = str(specs_div) if specs_div else None
    # Si quieres el texto limpio
    specs_text = specs_div.get_text(" ", strip=True) if specs_div else None

    return specs_html