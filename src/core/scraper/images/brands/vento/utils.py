def create_urls_from_pattern(base_url: str) -> list:
    image_urls = []
    for i in range(1, 20):
        numero = f"{i:02}" if i < 10 else str(i)
        url_armada = f"{base_url}-{numero}.jpg"
        image_urls.append(url_armada)
    return image_urls