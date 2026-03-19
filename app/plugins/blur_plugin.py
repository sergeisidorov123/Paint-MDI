from PIL import Image, ImageFilter, ImageOps

PLUGIN_NAME = "Blur"

def process_image(img: Image.Image) -> Image.Image:
    ImageOps.grayscale(img)
    return img.filter(ImageFilter.BLUR)

