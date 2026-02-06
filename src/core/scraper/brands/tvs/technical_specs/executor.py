from bs4 import BeautifulSoup

def handle_technical_specs(content: list[str]) -> list:
    html = content.html
    soup = BeautifulSoup(html, "html.parser")
    divs = soup.find_all("div", class_="premium-specification-container")
    return divs