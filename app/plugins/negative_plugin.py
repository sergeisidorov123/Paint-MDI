from PIL import Image, ImageOps

PLUGIN_NAME = "Negative"

def process_image(pil_image: Image.Image) -> Image.Image:
    try:
        return ImageOps.invert(pil_image.convert('RGB'))
    except Exception:
        return pil_image