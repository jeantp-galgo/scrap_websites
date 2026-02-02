
def extract_main_images(images_list: list[str]):
    main_images = []
    for images in images_list:
        if "width" in images:
            main_images.append(images)
    return main_images

def handle_images(extracted_images_list: list[str]):
    main_images = extract_main_images(extracted_images_list)
    return main_images