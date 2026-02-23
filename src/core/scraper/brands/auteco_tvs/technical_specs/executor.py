from bs4 import BeautifulSoup


def handle_technical_specs(content: list[str]) -> list:
    html = content.html

    soup = BeautifulSoup(html, "html.parser")
    # El div padre correcto es el que tiene la clase con "spec-productSpecificationGroup pb0"
    specs_div = soup.find("div", class_="vtex-flex-layout-0-x-flexColChild vtex-flex-layout-0-x-flexColChild--spec-productSpecificationGroup pb0")
    specs_html = str(specs_div) if specs_div else None
    return specs_html