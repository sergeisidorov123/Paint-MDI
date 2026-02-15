from tkinter import *
from PIL import Image, ImageDraw
from tkinter import colorchooser, messagebox, filedialog
import time
from .WindowCounter import WindowCounter
from ..ButtonDescription import ButtonDescription
from .Painter import Painter

count = WindowCounter()
        
class PaintWindow:
    """Класс отдельного окна для рисования"""
    
    def __init__(self, root=None):
        """Создает новое окно для рисования"""
        count.increase_count()
        if root:
            self.window = Toplevel(root)
        else:
            self.window = Tk()
            self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.window.title(f"Paint Window #{count.get_count()}")
        self.window.geometry("800x600")
        
        self.is_closed = False
        
        self.window.resizable(True, True)
        
        self.canvas = Canvas(self.window, bg="white")
        self.canvas.pack(expand=True, fill=BOTH)
         
        self.canvas_width = 2000
        self.canvas_height = 2000
        self.canvas.configure(scrollregion=(0, 0, self.canvas_width, self.canvas_height))
        
        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
        self.draw = ImageDraw.Draw(self.image)
        
        self.visible_x = 0
        self.visible_y = 0
        self.visible_width = 800
        self.visible_height = 500
        
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        self.__buttons_create()
        
        #binds
        self.window.bind("<Control-w>", self.close_window)
        self.window.bind("<Control-x>", self.save_image_as)
        
        
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset)
        
        self.painter = Painter(self.canvas, self.draw)
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
    
    def choose_color(self):
        color_code = colorchooser.askcolor(parent=self.window)
        if color_code[1]:
            self.painter.set_color(color_code[1])
    
    def paint(self, event):
        if not self.is_closed:
            self.painter.paint(event.x, event.y)
    
    def reset(self, event):
        self.painter.reset_coords()
    
    def clear_canvas(self):
        """Очищает холст"""
        if not self.is_closed:
            self.canvas.delete("all")
            self.draw.rectangle([0, 0, self.canvas_width, self.canvas_height], fill=self.canvas["background"])
    
    def save_image_as(self, event=None):
        """Сохраняет ТО, ЧТО ВИДИТ ПОЛЬЗОВАТЕЛЬ"""
        if not self.is_closed:
            self.visible_x = self.canvas.canvasx(0)
            self.visible_y = self.canvas.canvasy(0)
            
            visible_region = self.image.crop((
                int(self.visible_x),
                int(self.visible_y),
                int(self.visible_x + self.visible_width),
                int(self.visible_y + self.visible_height)
            ))
            
            filename = f"paint_{time.strftime('%Y%m%d_%H%M%S')}.png"
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                initialfile=filename,
                parent=self.window
            )
            
            if file_path:
                visible_region.save(file_path)
                messagebox.showinfo("Success", 
                                   f"Image saved in \n{file_path}", 
                                   parent=self.window)
    
    
    def close_window(self, event=None):
        """Закрывает текущее окно"""
        count.reduce_count()
        self.is_closed = True
        self.window.destroy()
    
    def on_closing(self):
        """Обработчик закрытия главного окна"""
        self.is_closed = True
        self.window.quit()
        self.window.destroy()
        
    def on_canvas_configure(self, event):
        """Обновляет информацию о видимой области"""
        self.visible_width = event.width
        self.visible_height = event.height
        self.visible_x = self.canvas.canvasx(0)
        self.visible_y = self.canvas.canvasy(0)
        
        self.canvas.configure(scrollregion=(0, 0, self.canvas_width, self.canvas_height))
        
    def change_size(self, new_size):
        self.painter.set_width(int(new_size))
        
    def __buttons_create(self):
        """Создает кнопки для управления окном рисования"""
        button_frame = Frame(self.window)
        button_frame.pack(pady=5)
        
        self.color_button = Button(button_frame, text="Choose Color", 
                                  command=self.choose_color)
        self.color_button.pack(side=LEFT, padx=5)
        ButtonDescription(self.color_button, "Выбор цвета для рисования")
        
        self.clear_button = Button(button_frame, text="Clear Canvas", 
                                  command=self.clear_canvas)
        self.clear_button.pack(side=LEFT, padx=5)
        ButtonDescription(self.clear_button, "Очистка холста")
        
        self.save_button = Button(button_frame, text="Save Image", 
                                 command=self.save_image_as)
        self.save_button.pack(side=LEFT, padx=5)
        ButtonDescription(self.save_button, "Сохранение изображения")
        
        self.close_button = Button(button_frame, text="Close Window", 
                                  command=self.close_window)
        self.close_button.pack(side=LEFT, padx=5)
        ButtonDescription(self.close_button, "Закрытие окна рисования")
        
        self.size_label = Label(button_frame, text="Size:", font=(15))
        self.size_label.pack(side=LEFT, padx=5)

        self.size_scale = Scale(button_frame, 
                                from_=1, to=20, 
                                orient=HORIZONTAL,
                                command=self.change_size)
        self.size_scale.set(5) 
        self.size_scale.pack(side=LEFT, padx=10, pady=(0,17))

        ButtonDescription(self.size_scale, "Изменение толщины кисти")
        
