from tkinter import *
from PIL import Image, ImageDraw, ImageTk
from tkinter import colorchooser, messagebox

class PaintApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Paint App")
        self.root.geometry("800x600")

        self.canvas = Canvas(self.root, bg="white", width=800, height=500)
        self.canvas.pack()

        self.color_button = Button(self.root, text="Choose Color", command=self.choose_color)
        self.color_button.pack(side=LEFT)

        self.clear_button = Button(self.root, text="Clear Canvas", command=self.clear_canvas)
        self.clear_button.pack(side=LEFT)

        self.save_button = Button(self.root, text="Save Image", command=self.save_image)
        self.save_button.pack(side=LEFT)

        self.current_color = "black"
        self.last_x, self.last_y = None, None

        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset)

    def choose_color(self):
        color_code = colorchooser.askcolor(title="Choose color")
        if color_code:
            self.current_color = color_code[1]

    def paint(self, event):
        if self.last_x and self.last_y:
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, fill=self.current_color, width=5)
            draw.line([self.last_x, self.last_y, event.x, event.y], fill=self.current_color, width=5)
        self.last_x, self.last_y = event.x, event.y

    def reset(self, event):
        self.last_x, self.last_y = None, None

    def clear_canvas(self):
        self.canvas.delete("all")
        draw.rectangle([0, 0, 800, 500], fill="white")

    def save_image(self):
        file_path = "paint_image.png"
        image.save(file_path)
        messagebox.showinfo("Image Saved", f"Image saved as {file_path}")
        

if __name__ == "__main__":
    root = Tk()
    image = Image.new("RGB", (800, 500), "white")
    draw = ImageDraw.Draw(image)
    app = PaintApp(root)
    root.mainloop()
    