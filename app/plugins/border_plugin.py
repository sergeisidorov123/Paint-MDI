from PIL import Image, ImageDraw

PLUGIN_NAME = "Add Border"

def process_image(input_image: Image.Image, cancel_context=None) -> Image.Image:
    try:
        if cancel_context and callable(cancel_context.get('cancelled')):
            if cancel_context['cancelled']():
                return input_image
        
        border_width = 15
        border_color = (255, 0, 0)  
        
        img = input_image.convert('RGB')
        width, height = img.size
        
        draw = ImageDraw.Draw(img)
        for i in range(border_width):
            if cancel_context and callable(cancel_context.get('cancelled')) and cancel_context['cancelled']():
                return input_image
            draw.rectangle(
                [(i, i), (width - 1 - i, height - 1 - i)],
                outline=border_color,
                fill=None
            )
        
        return img
    except Exception:
        return input_image
