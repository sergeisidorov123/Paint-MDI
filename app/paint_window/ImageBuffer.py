from PIL import Image, ImageDraw


class ImageBuffer:
    """Wrapper around a PIL Image and ImageDraw to centralize raster ops."""
    def __init__(self, width: int, height: int, color="white"):
        self.image = Image.new("RGB", (max(1, int(width)), max(1, int(height))), color)
        self.draw = ImageDraw.Draw(self.image)

    def resize(self, width: int, height: int, resample=None):
        w, h = max(1, int(width)), max(1, int(height))
        try:
            if resample is None:
                resample = Image.LANCZOS
            self.image = self.image.resize((w, h), resample)
        except Exception:
            self.image = self.image.resize((w, h))
        self.draw = ImageDraw.Draw(self.image)

    def paste_image(self, pil_image):
        try:
            self.image.paste(pil_image.resize(self.image.size))
            self.draw = ImageDraw.Draw(self.image)
        except Exception:
            try:
                self.image = pil_image.convert("RGB").resize(self.image.size)
                self.draw = ImageDraw.Draw(self.image)
            except Exception:
                pass

    def get_image(self):
        return self.image

    def draw_line(self, coords, fill, width=1):
        try:
            self.draw.line(coords, fill=fill, width=width)
        except Exception:
            self.draw.line(coords, fill=fill, width=int(width))

    def draw_ellipse(self, bbox, fill=None, outline=None, width=1):
        try:
            if fill is not None and outline is not None:
                # Pillow supports both
                self.draw.ellipse(bbox, fill=fill, outline=outline)
            elif fill is not None:
                self.draw.ellipse(bbox, fill=fill)
            elif outline is not None:
                # width parameter may not be supported; emulate if needed
                try:
                    self.draw.ellipse(bbox, outline=outline, width=width)
                except Exception:
                    self.draw.ellipse(bbox, outline=outline)
            else:
                self.draw.ellipse(bbox)
        except Exception:
            try:
                # fallback
                self.draw.ellipse(bbox)
            except Exception:
                pass
