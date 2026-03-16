from PIL import Image

PLUGIN_NAME = "Matrix convolution"

def process_image(input_image: Image.Image) -> Image.Image:
    """Apply a small sharpening-like convolution kernel and return a new image."""
    try:
        kernel = [[-1, -1, -1],
                  [-1, 9, -1],
                  [-1, -1, -1]]
        img = input_image.convert('RGB')
        pixels = img.load()
        width, height = img.size
        new_img = Image.new('RGB', (width, height))
        new_pixels = new_img.load()
        k_size = len(kernel)
        offset = k_size // 2
        for x in range(offset, width - offset):
            for y in range(offset, height - offset):
                r_sum = g_sum = b_sum = 0
                for kx in range(k_size):
                    for ky in range(k_size):
                        px = pixels[x + kx - offset, y + ky - offset]
                        w = kernel[kx][ky]
                        r_sum += px[0] * w
                        g_sum += px[1] * w
                        b_sum += px[2] * w
                new_pixels[x, y] = (
                    max(0, min(255, int(r_sum))),
                    max(0, min(255, int(g_sum))),
                    max(0, min(255, int(b_sum)))
                )
        return new_img
    except Exception:
        return input_image