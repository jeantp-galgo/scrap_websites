

def handle_technical_specs(content: list[str]) -> list:
    content = content.links
    for link in content:
        if "https://www.vento.com/wp-content/uploads/FT-" in link:
            print(link)
            return link
    return content