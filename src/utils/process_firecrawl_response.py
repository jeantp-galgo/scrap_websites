def get_urls_from_firecrawl_map(url_list:tuple):
    """ Obtiene las URLs de un sitio web desde la respuesta de Firecrawl """
    links = url_list.links
    tuplas_urls = [(link.url, link.title, link.description) for link in links]
    return [tupla[0] for tupla in tuplas_urls]