def detect_url_pattern(content: list[str]):
    for image in content:
        # Con esta se arma la url base
        if "interna-de-producto" in image:
            url_base_to_process = image # 'https://media.autecomobility.com/recursos/marcas/tvs/raider-125/interna-de-producto/Imagen_Fondo_Texto_detalle_2_TVS.webp'
            break # Solo con la primera coincidencia sirve

    # Se separa por barras (/) y se elimina el último elemento para crear así la url base
    text_to_eliminate = url_base_to_process.split("/")[-1] # /interna-de-producto/'
    url_base = url_base_to_process.replace(text_to_eliminate, "") # 'https://media.autecomobility.com/recursos/marcas/tvs/raider-125/interna-de-producto/'
    return url_base

def create_urls_from_pattern(url_base: str):
    urls_list = []
    for url in range(0,7):
        urls_list.append(f"{url_base}Galeria-imagen-{url+1}")
    return urls_list

def get_images_from_url_pattern(urls_list: list[str]):
    import requests
    default_extension = "webp"
    alt_extension = "png"
    url_list_checked = []
    # Itera entre cada url sin extensión y agrega la extensión por defecto
    for url in urls_list:
        url_to_check = f"{url}.{default_extension}"
        response = requests.get(url_to_check) # Se hace un reuquest para comprobar el status_code que retorne
        if response.status_code == 404: # Si el status_code es 404, se agrega la extensión alternativa
            print("No se encontró la imagen con la extensión por defecto, se intenta con la extensión alternativa")
            url_alt_to_check = f"{url}.{alt_extension}"
            print("Probando con extensión alternativa: ", url_alt_to_check)
            response = requests.get(url_alt_to_check) # Se vuelve a hacer el request con la extensión alternativa
            if response.status_code == 200: # Si el status_code es 200, se agrega la url con la extensión alternativa
                url_list_checked.append(url_alt_to_check)
            if response.status_code == 404:
                print("No se encontró la imagen con ninguna extensión")
        # Finalmente, si es 200, se agrega.
        if response.status_code == 200:
            url_list_checked.append(url_to_check)
    return url_list_checked

def handle_images(content: list[str]):
    # Detecta el patrón de URL: https://media.autecomobility.com/recursos/marcas/tvs/ntorq-125/interna-de-producto/Galeria-imagen-1.webp
    # Detecta: https://media.autecomobility.com/recursos/marcas/tvs/ntorq-125/interna-de-producto/
    url_base = detect_url_pattern(content.images)
    # Se crea las URLs apartir de la URL base
    # Crea: {url}/tvs/ntorq-125/interna-de-producto/Galeria-imagen-{N}.webp
    urls_list = create_urls_from_pattern(url_base)
    # Se verifica las URLs y se agregan las que existen
    urls_list_checked = get_images_from_url_pattern(urls_list)
    return urls_list_checked
