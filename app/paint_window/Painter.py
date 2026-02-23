from tkinter import *
from .ImageBuffer import ImageBuffer
from PIL import Image
import math


class Painter:
    def __init__(self, canvas, image_buffer: ImageBuffer, paper_fill):
        self.canvas = canvas
        self.image_buffer = image_buffer
        self.paper_fill = paper_fill
        
        self.color = "black"
        self.width = 5
        self.tool = "brush"  

        self.last_x = None
        self.last_y = None

    def set_tool(self, new_tool):
        self.tool = new_tool

    def set_color(self, new_color):
        self.color = new_color

    def set_width(self, new_width):
        self.width = int(new_width)

    def reset_coords(self):
        self.last_x = None
        self.last_y = None

    def _clamp_to_paper(self, x, y, paper_w, paper_h):
        x = int(x)
        y = int(y)
        pad = max(1, math.ceil(self.width / 2))
        pad_x = pad if paper_w > 2 * pad else 0
        pad_y = pad if paper_h > 2 * pad else 0
        x = max(pad_x, min(paper_w - pad_x, x))
        y = max(pad_y, min(paper_h - pad_y, y))
        return x, y

    def paint(self, x, y, paper_width, paper_height, is_resizing=False):
        if is_resizing:
            self.reset_coords()
            return

        pad = max(1, math.ceil(self.width / 2))
        if x < pad or y < pad or x > (paper_width - pad) or y > (paper_height - pad):
            self.reset_coords()
            return

        x = int(x)
        y = int(y)

        color = self.paper_fill if self.tool == "eraser" else self.color

        if self.last_x is None or self.last_y is None:
            r = max(1, self.width / 2)
            self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                    fill=color, outline=color, tags=("stroke",))
            try:
                self.image_buffer.draw_ellipse([x - r, y - r, x + r, y + r], fill=color, outline=color)
            except Exception:
                pass
            self.last_x, self.last_y = x, y
            return

        self.canvas.create_line(self.last_x, self.last_y, x, y,
                                fill=color, width=self.width,
                                capstyle=ROUND, joinstyle=ROUND, smooth=True,
                                tags=("stroke",))

        try:
            self.image_buffer.draw_line([self.last_x, self.last_y, x, y], fill=color, width=self.width)
        except Exception:
            try:
                self.image_buffer.draw_line([self.last_x, self.last_y, x, y], fill=color, width=int(self.width))
            except Exception:
                pass

        self.last_x, self.last_y = x, y
