from PIL import Image, ImageOps

# Plugin metadata
PLUGIN_NAME = "Negative"

def process_image(pil_image: Image.Image) -> Image.Image:
    """Return a new PIL Image which is the color-inverted version of input."""
    try:
        return ImageOps.invert(pil_image.convert('RGB'))
    except Exception:
        return pil_image