from tkinter import *
from PIL import Image, ImageDraw
from tkinter import colorchooser, messagebox, filedialog
import time

class WindowCounter:
    """Класс для отслеживания количества открытых окон рисования """
    __count_of_window = 0
    
    def increase_count(self):
        self.__count_of_window += 1

    def get_count(self): 
        return self.__count_of_window
    
    def reduce_count(self): 
        self.__count_of_window -= 1

class PaintWindow:
    """Класс отдельного окна для рисования"""
    
    global count
    count = WindowCounter()
        
    def __init__(self, root=None):
        """Создает новое окно для рисования"""
        if root:
            self.window = Toplevel(root)
            count.increase_count()
        else:
            count.increase_count()
            self.window = Tk()
            self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.window.title(f"Paint Window #{count.get_count()}")
        self.window.geometry("800x600")
        
        self.is_closed = False
        
        # Создание холста для рисования
        self.window.resizable(True, True)
        
        self.canvas = Canvas(self.window, bg="white")
        self.canvas.pack(expand=True, fill=BOTH)
         
        self.canvas_width = 2000
        self.canvas_height = 2000
        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.canvas.configure(scrollregion=(0, 0, self.canvas_width, self.canvas_height))
        
        self.visible_x = 0
        self.visible_y = 0
        self.visible_width = 800
        self.visible_height = 500
        
        button_frame = Frame(self.window)
        button_frame.pack(pady=5)
        
        self.color_button = Button(button_frame, text="Choose Color", 
                                  command=self.choose_color)
        self.color_button.pack(side=LEFT, padx=5)
        
        self.clear_button = Button(button_frame, text="Clear Canvas", 
                                  command=self.clear_canvas)
        self.clear_button.pack(side=LEFT, padx=5)
        
        self.save_button = Button(button_frame, text="Save Image", 
                                 command=self.save_image)
        self.save_button.pack(side=LEFT, padx=5)
        
        self.new_window_button = Button(button_frame, text="New Window", 
                                       command=self.create_new_window)
        self.new_window_button.pack(side=LEFT, padx=5)
        
        self.close_button = Button(button_frame, text="Close Window", 
                                  command=self.close_window)
        self.close_button.pack(side=LEFT, padx=5)
        
        self.current_color = "black"
        self.last_x, self.last_y = None, None
        
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset)
        
        self.window.protocol("WM_DELETE_WINDOW", self.close_window)
    
    def choose_color(self):
        """Открывает диалог выбора цвета"""
        color_code = colorchooser.askcolor(title="Choose color", parent=self.window)
        if color_code:
            self.current_color = color_code[1]
    
    def paint(self, event):
        """Рисует линию на холсте"""
        if self.last_x and self.last_y and not self.is_closed:
            self.canvas.create_line(self.last_x, self.last_y, event.x, event.y, 
                                  fill=self.current_color, width=5)
            self.draw.line([self.last_x, self.last_y, event.x, event.y], 
                          fill=self.current_color, width=5)
        self.last_x, self.last_y = event.x, event.y
    
    def reset(self, event):
        """Сбрасывает координаты"""
        self.last_x, self.last_y = None, None
    
    def clear_canvas(self):
        """Очищает холст"""
        if not self.is_closed:
            self.canvas.delete("all")
            self.draw.rectangle([0, 0, self.canvas_width, self.canvas_height], fill="white")
    
    def save_image(self):
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
                messagebox.showinfo("Image Saved", 
                                   f"Visible area saved!\n{file_path}")
    
    def create_new_window(self):
        """Создает новое окно для рисования"""
        if not self.is_closed:
            root = self.window.master if self.window.master else self.window
            PaintWindow(root)
    
    def close_window(self):
        """Закрывает текущее окно"""
        count.reduce_count()
        self.is_closed = True
        self.window.destroy()
    
    def on_closing(self):
        """Обработчик закрытия главного окна"""
        self.is_closed = True
        self.window.quit()
        self.window.destroy()
    
    def on_canvas_resize(self, event):
        """Обновляет размеры холста при изменении размера окна"""
        self.canvas_width = event.width
        self.canvas_height = event.height
        self.image = self.image.resize((self.canvas_width, self.canvas_height), Image.ANTIALIAS)
        self.draw = ImageDraw.Draw(self.image)
        
    def on_canvas_configure(self, event):
        """Обновляет информацию о видимой области"""
        self.visible_width = event.width
        self.visible_height = event.height
        self.visible_x = self.canvas.canvasx(0)
        self.visible_y = self.canvas.canvasy(0)
        

        self.canvas.configure(scrollregion=(0, 0, self.canvas_width, self.canvas_height))
