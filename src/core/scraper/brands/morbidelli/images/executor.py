from bs4 import BeautifulSoup

def extract_main_images(content):
    for image in content:
        if "width=800" in image:
            main_images.append(image)
    return main_images

def handle_images(content):
    main_images = extract_main_images(content)
    return main_images