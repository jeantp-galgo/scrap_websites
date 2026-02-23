def extract_main_images(images_list: list[str]):
    print("Extrayendo imágenes principales")
    print(images_list)
    main_images = []
    for image in images_list:
        if "width=800" in image:
            main_images.append(image)
    return main_images

def handle_images(content: list[str]):
    main_images = extract_main_images(content)
    return main_images