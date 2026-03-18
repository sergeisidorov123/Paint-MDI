from PIL import Image, ImageFilter, ImageOps

PLUGIN_NAME = "Example"

def process_image(img: Image.Image) -> Image.Image:
    ImageOps.grayscale(img)
    return img.filter(ImageFilter.BLUR)
