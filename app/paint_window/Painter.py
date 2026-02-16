from tkinter import *
from tkinter.ttk import Combobox
from PIL import Image, ImageDraw
from tkinter import colorchooser, messagebox, filedialog


class Painter:
    def __init__(self, canvas, draw):
        self.canvas = canvas        
        self.draw = draw     
        
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
        self.width = new_width

    def reset_coords(self):
        """Сброс координат (вызывается при отпускании кнопки мыши)"""
        self.last_x = None
        self.last_y = None

    def paint(self, x, y):
        """Основной метод рисования"""
        if self.last_x is not None and self.last_y is not None:
            current_fill = self.color if self.tool == "brush" else self.canvas["background"]
            
            self.canvas.create_line(
                self.last_x, self.last_y, x, y,
                fill=current_fill, width=self.width, 
                capstyle="round", smooth=True
            )
            
            self.draw.line(
                [self.last_x, self.last_y, x, y], 
                fill=current_fill, width=self.width
            )
            
        self.last_x, self.last_y = x, y
        
        
        
  