import os
from tkinter import *
import tkinter as tk
from tkinter.ttk import Combobox
from tkinter import colorchooser, messagebox, filedialog, simpledialog
import time
from .WindowCounter import WindowCounter
from ..ButtonDescription import ButtonDescription
from .Painter import Painter
from PIL import Image, ImageDraw, ImageTk, ImageChops

count = WindowCounter()
        
class PaintWindow:
    """Класс отдельного окна для рисования"""
    
    def __init__(self, root=None, app=None, preload_image=None):
        """Создает новое окно для рисования"""
        count.increase_count()
        self.is_toplevel = False
        if root:
            if isinstance(root, (tk.Tk, tk.Toplevel)):
                self.window = root
                self.is_toplevel = True
            else:
                self.window = root
        else:
            self.window = Tk()
            self.is_toplevel = True
            self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.app = app
        self.is_closed = False
        self.is_saved = False
        self.is_updated = False
        self.changes = False
        self.changes_label = None
        self.file_name = ''
        self.file_path = ''
        
        self.paper_width = 400
        self.paper_height = 300
        
        if self.is_toplevel:
            if self.file_name == "":
                self.window.title(f"Paint Window #{count.get_count()}")
            else:
                self.window.title(f"Paint Window - {self.file_name}")
            self.window.geometry("1200x800")
            self.window.minsize(1200,800)
            self.window.resizable(True, True)
        
        self.canvas = Canvas(self.window, bg="gray", highlightthickness=0)
        self.canvas.pack(expand=True, fill=BOTH)
        
        self.paper_fill = "white"
        
        self.paper_bg = self.canvas.create_rectangle(
            0, 0, self.paper_width, self.paper_height, fill=self.paper_fill, outline=""
        )
        self.paper_outline = self.canvas.create_rectangle(
            0, 0, self.paper_width, self.paper_height, fill="", outline="black"
        )

        self.resizer_size = 6
        self.right_resizer = self.canvas.create_rectangle(0,0,0,0, fill="white", outline="black", tags="resizer")
        self.bottom_resizer = self.canvas.create_rectangle(0,0,0,0, fill="white", outline="black", tags="resizer")
        self.corner_resizer = self.canvas.create_rectangle(0,0,0,0, fill="white", outline="black", tags="resizer")

        self.update_resizers()

        self.canvas.tag_bind(self.corner_resizer, "<B1-Motion>", self.resize_canvas)
        self.canvas.tag_bind(self.right_resizer, "<B1-Motion>", lambda e: self.resize_canvas(e, mode="width"))
        self.canvas.tag_bind(self.bottom_resizer, "<B1-Motion>", lambda e: self.resize_canvas(e, mode="height"))
        
        self.canvas_width = 2000
        self.canvas_height = 2000
        self.canvas.configure(scrollregion=(0, 0, self.canvas_width, self.canvas_height))
        
        self.image = Image.new("RGB", (self.canvas_width, self.canvas_height), "white")
        self.draw = ImageDraw.Draw(self.image)
        self.tk_image = None
        self.bg_image_id = None
        self.bg_loaded = False
        
        self.visible_x = 0
        self.visible_y = 0
        self.visible_width = 800
        self.visible_height = 500
        
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.painter = Painter(self.canvas, self.draw, self.paper_fill)

        # shape tool state
        self.shape_mode = 'freehand'  # 'freehand' | 'line' | 'ellipse'
        self.fill_shape = False
        self.shape_preview_id = None
        self.shape_start = None

        if preload_image is not None:
            try:
                self.image = preload_image.copy().convert("RGB")
                self.draw = ImageDraw.Draw(self.image)
                self.paper_width, self.paper_height = self.image.size
                self.bg_loaded = True
                try:
                    self.tk_image = ImageTk.PhotoImage(self.image)
                    if self.bg_image_id:
                        self.canvas.itemconfig(self.bg_image_id, image=self.tk_image)
                    else:
                        self.bg_image_id = self.canvas.create_image(0, 0, anchor=NW, image=self.tk_image, tags="bg_image")
                    self.canvas.tag_lower("bg_image")
                except Exception:
                    pass
                try:
                    self.canvas.itemconfig(self.paper_bg, fill="")
                except Exception:
                    pass
                self.canvas.coords(self.paper_bg, 0, 0, self.paper_width, self.paper_height)
                self.canvas.coords(self.paper_outline, 0, 0, self.paper_width, self.paper_height)
                self.update_resizers()
            except Exception:
                pass
        
        self.__buttons_create()
        
        if self.is_toplevel:
            self.window.bind("<Control-w>", self.close_window)
            self.window.bind("<Control-x>", self.save_image_as)
            self.window.bind("<Control-s>", self.save_image)
        
        
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset)
        self.canvas.bind("<Button-1>", self.on_button_press)
        
        self.canvas.bind("<Motion>", self.update_oval)
        self.cursor = self.canvas.create_oval(0, 0, 0, 0, outline="black", width=1, tags="cursor")
        
        if self.is_toplevel:
            self.window.protocol("WM_DELETE_WINDOW", self.close_window)
    
    def reset(self, event):
        """Сбрасывает флаги и координаты после рисования или изменения размера"""
        self.is_resizing = False 
        if hasattr(self, 'painter'):
            self.painter.reset_coords()
        # finalize shape if we're in shape mode
        try:
            if getattr(self, 'shape_mode', 'freehand') != 'freehand':
                self.finish_shape(event)
        except Exception:
            pass
            
    def update_resizers(self):
        """Перерисовывает маркеры в углах холста"""
        w, h = self.paper_width, self.paper_height
        s = self.resizer_size
        
        self.canvas.coords(self.right_resizer, w, h/2 - s, w + s, h/2 + s)
        self.canvas.coords(self.bottom_resizer, w/2 - s, h, w/2 + s, h + s)
        self.canvas.coords(self.corner_resizer, w, h, w + s, h + s)
        
    def resize_canvas(self, event, mode="both"):
        """Обновляет размеры бумаги при перетаскивании маркеров"""
        self.is_resizing = True

        old_w, old_h = float(self.paper_width), float(self.paper_height)

        if mode == "both" or mode == "width":
            self.paper_width = max(10, event.x)
        if mode == "both" or mode == "height":
            self.paper_height = max(10, event.y)

        new_w, new_h = float(self.paper_width), float(self.paper_height)

        try:
            self.canvas.coords(self.paper_bg, 0, 0, self.paper_width, self.paper_height)
            self.canvas.coords(self.paper_outline, 0, 0, self.paper_width, self.paper_height)
        except Exception:
            pass
        try:
            self.resize_pillow_image()
        except Exception:
            pass

        try:
            sx = new_w / old_w if old_w else 1.0
            sy = new_h / old_h if old_h else 1.0
            for item in self.canvas.find_withtag("stroke"):
                coords = self.canvas.coords(item)
                if not coords:
                    continue
                new_coords = []
                for i, v in enumerate(coords):
                    if i % 2 == 0:
                        new_coords.append(v * sx)
                    else:
                        new_coords.append(v * sy)
                self.canvas.coords(item, *new_coords)
        except Exception:
            pass

        self.update_resizers()

    def resize_pillow_image(self):
        """Синхронизирует / масштабирует Pillow Image и отображение под текущий размер бумаги."""
        w, h = int(self.paper_width), int(self.paper_height)
        if w <= 0 or h <= 0:
            return

        try:
            self.is_updated = True
            if (w, h) != self.image.size:
                try:
                    self.image = self.image.resize((w, h), Image.LANCZOS)
                except Exception:
                    self.image = self.image.resize((w, h))
                self.draw = ImageDraw.Draw(self.image)
                self.painter.draw = self.draw

            if getattr(self, 'bg_loaded', False):
                self.tk_image = ImageTk.PhotoImage(self.image)
                if self.bg_image_id:
                    self.canvas.itemconfig(self.bg_image_id, image=self.tk_image)
                else:
                    self.bg_image_id = self.canvas.create_image(0, 0, anchor=NW, image=self.tk_image, tags="bg_image")
                    self.canvas.tag_lower("bg_image")
            else:
                if self.bg_image_id:
                    try:
                        self.canvas.delete(self.bg_image_id)
                    except Exception:
                        pass
                    self.bg_image_id = None
                self.tk_image = None
        except Exception:
            pass
    
    def update_oval(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        r = self.painter.width / 2
        
        self.canvas.coords(self.cursor, x - r, y - r, x + r, y + r)
        
        self.canvas.tag_raise("cursor")
    
    def choose_color(self):
        color_code = colorchooser.askcolor(parent=self.window if self.is_toplevel else None)
        if color_code[1]:
            self.painter.set_color(color_code[1])
    
    def change_paper_color(self):
        """Изменяет цвет фона холста"""
        self.is_updated = True
        chosen = colorchooser.askcolor(parent=self.window if self.is_toplevel else None)[1]
        if chosen:
            self.paper_fill = chosen
            self.bg_loaded = False
            if self.bg_image_id:
                try:
                    self.canvas.delete(self.bg_image_id)
                except Exception:
                    pass
                self.bg_image_id = None

            self.painter = Painter(self.canvas, self.draw, self.paper_fill)
            self.canvas.itemconfig(self.paper_bg, fill=self.paper_fill)
    
    def paint(self, event):
        """Метод-обработчик событий мыши в окне"""
        if self.is_closed:
            return
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)
        
        self.is_updated = True
        if self.is_updated and not self.changes:
            self.changes_label = Label(self.window, text="Changes not saved", font=(15))
            self.changes_label.pack(side=LEFT, padx=5)
            self.changes = True
            
        try:
            items = self.canvas.find_overlapping(cx, cy, cx, cy)
            for it in items:
                if "resizer" in self.canvas.gettags(it):
                    mode = "both"
                    if it == self.right_resizer:
                        mode = "width"
                    elif it == self.bottom_resizer:
                        mode = "height"

                    self.is_resizing = True
                    evt = type("E", (), {"x": int(cx), "y": int(cy)})()
                    self.resize_canvas(evt, mode=mode)
                    self.update_oval(event)
                    try:
                        self.canvas.tag_raise(self.paper_outline)
                        self.canvas.tag_raise("resizer")
                        self.canvas.tag_raise("cursor")
                    except Exception:
                        pass
                    return
        except Exception:
            pass

        # If a shape tool is selected, update preview instead of freehand drawing
        if getattr(self, 'shape_mode', 'freehand') != 'freehand':
            try:
                self.update_shape_preview(cx, cy)
            except Exception:
                pass
            return

        self.painter.paint(
            cx,
            cy,
            self.paper_width,
            self.paper_height,
            getattr(self, 'is_resizing', False)
        )

        self.update_oval(event)
        try:
            self.canvas.tag_raise(self.paper_outline)
            self.canvas.tag_raise("resizer")
            self.canvas.tag_raise("cursor")
        except Exception:
            pass
    
    
    
    def clear_canvas(self):
        """Очищает холст"""
        self.is_updated = True
        if not self.is_closed:
            try:
                self.canvas.delete("stroke")
            except Exception:
                pass
            self.draw.rectangle([0, 0, int(self.paper_width), int(self.paper_height)], fill="white")

    def toggle_dock(self):
        try:
            current_img = self.build_export_image()
        except Exception:
            current_img = None

        if not getattr(self, 'is_toplevel', False) and getattr(self, 'app', None):
            try:
                self.app.create_new_window_from_image(current_img)
                try:
                    self.app.detach_tab(self)
                except Exception:
                    pass
            except Exception:
                pass
        elif getattr(self, 'is_toplevel', False) and getattr(self, 'app', None):
            try:
                if current_img is not None:
                    self.app.dock_image_as_tab(current_img)
                self.close_window()
            except Exception:
                pass
    

    def save_image_as(self, event=None):
        """Сохранение холста (от 0,0 до границ маркеров)"""
        if self.is_closed:
            return

        final_save = self.build_export_image()

        default_name = f"paint_{time.strftime('%Y%m%d_%H%M%S')}"

        file_path = filedialog.asksaveasfilename(
            defaultextension="",
            initialfile=default_name,
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg"),
                ("BMP files", "*.bmp"),
                ("All files", "*.*")
            ],
            parent=self.window if self.is_toplevel else None
        )
        
        if file_path:
            try:
                self.changes = False
                if getattr(self, 'changes_label', None):
                    try:
                        self.changes_label.destroy()
                    except Exception:
                        pass
                self.changes_label = None

                to_save = final_save

                ext = os.path.splitext(file_path)[1].lower()

                if ext == ".jpg":
                    save_img = to_save.convert("RGB")
                else:
                    save_img = to_save

                save_img.save(file_path)
                
                self.file_path = file_path
                self.is_saved = True
                
                file_name = os.path.basename(file_path)
                if self.is_toplevel:
                    try:
                        self.window.title(f"Paint Window - {file_name}")
                    except Exception:
                        pass

                if self.is_toplevel:
                    messagebox.showinfo("Success", f"Image saved successfully:\n{file_path}", parent=self.window)
                else:
                    messagebox.showinfo("Success", f"Image saved successfully:\n{file_path}")
                
            except Exception as e:
                if self.is_toplevel:
                    messagebox.showerror("Error", f"Failed to save image:\n{e}", parent=self.window)
                else:
                    messagebox.showerror("Error", f"Failed to save image:\n{e}")
    
    def save_image(self, event=None):
        """Быстрое сохранение (Ctrl+S)"""
        if self.is_closed:
            return
        self.changes = False
        if getattr(self, 'changes_label', None):
            try:
                self.changes_label.destroy()
            except Exception:
                pass
        self.changes_label = None
        if self.file_path:
            self.saving()
        else:
            self.save_image_as()

    def saving(self):
        """Технический процесс записи данных в файл по текущему пути"""
        try:
            final_save = self.build_export_image()
            to_save = final_save

            ext = os.path.splitext(self.file_path)[1].lower()

            if ext in ['.jpg', '.jpeg']:
                img_to_write = to_save.convert("RGB")
            else:
                img_to_write = to_save

            img_to_write.save(self.file_path)
            
            file_name = os.path.basename(self.file_path)
            if self.is_toplevel:
                try:
                    self.window.title(f"Paint Window - {file_name}")
                except Exception:
                    pass
            
            
        except Exception as e:
            if self.is_toplevel:
                messagebox.showerror("Save Error", f"Could not save file:\n{e}", parent=self.window)
            else:
                messagebox.showerror("Save Error", f"Could not save file:\n{e}")

    def close_window(self, event=None):
        """Закрывает текущее окно с проверкой сохранения"""
        if self.is_updated and not self.is_saved:
            ans = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before exiting?",
                parent=self.window if self.is_toplevel else None
            )
            
            if ans is True: 
                self.save_image()
            elif ans is None: 
                return 
        
        count.reduce_count()
        self.is_closed = True
        
        if count.get_count() == 0:
            self.window.quit() 
        
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
        
    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"), ("All files", "*.*")],
            parent=self.window if self.is_toplevel else None
        )
        
        if file_path:
            try:
                opened_image = Image.open(file_path)
                self.image = opened_image.convert("RGB")
                self.draw = ImageDraw.Draw(self.image)
                
                self.paper_width, self.paper_height = self.image.size
            
                self.canvas.delete("stroke") 
                self.canvas.delete("bg_image")


                self.bg_loaded = True

                self.tk_image = ImageTk.PhotoImage(self.image)
                if self.bg_image_id:
                    self.canvas.itemconfig(self.bg_image_id, image=self.tk_image)
                else:
                    self.bg_image_id = self.canvas.create_image(0, 0, anchor=NW, image=self.tk_image, tags="bg_image")
                self.canvas.tag_lower("bg_image")

                try:
                    self.canvas.itemconfig(self.paper_bg, fill="")
                except Exception:
                    pass

                self.canvas.coords(self.paper_bg, 0, 0, self.paper_width, self.paper_height)
                self.canvas.coords(self.paper_outline, 0, 0, self.paper_width, self.paper_height)
                self.update_resizers()
                
                self.canvas.tag_raise("resizer")
                self.canvas.tag_raise("cursor")

                self.painter.draw = self.draw
                self.file_path = file_path
                if self.is_toplevel:
                    try:
                        self.window.title(f"Paint Window - {os.path.basename(file_path)}")
                    except Exception:
                        pass
                
            except Exception as e:
                if self.is_toplevel:
                    messagebox.showerror("Error", f"Could not open image:\n{e}", parent=self.window)
                else:
                    messagebox.showerror("Error", f"Could not open image:\n{e}")
                
    def build_export_image(self):
        w, h = int(self.paper_width), int(self.paper_height)
        if w <= 0 or h <= 0:
            return Image.new("RGB", (1, 1), "white")
        bg = Image.new("RGB", (w, h), self.paper_fill or "white")
        try:
            if getattr(self, 'bg_loaded', False) and hasattr(self, 'image') and self.image:
                try:
                    resized = self.image.resize((w, h))
                    bg.paste(resized)
                except Exception:
                    pass
        except Exception:
            pass

        draw = ImageDraw.Draw(bg)

        try:
            for item in self.canvas.find_withtag("stroke"):
                itype = self.canvas.type(item)
                coords = self.canvas.coords(item)
                if not coords:
                    continue
                pts = tuple(int(round(c)) for c in coords)

                fill = self.canvas.itemcget(item, 'fill') or 'black'
                width = int(float(self.canvas.itemcget(item, 'width') or 1))

                if itype == 'line':
                    draw.line(pts, fill=fill, width=width)
                elif itype == 'oval':
                    draw.ellipse(pts, fill=fill, outline=fill)
                else:
                    try:
                        draw.line(pts, fill=fill, width=width)
                    except Exception:
                        pass
        except Exception:
            pass

        return bg

    def on_button_press(self, event):
        """Handle mouse button press to start a shape or begin freehand."""
        if getattr(self, 'shape_mode', 'freehand') == 'freehand':
            return

        x = int(self.canvas.canvasx(event.x))
        y = int(self.canvas.canvasy(event.y))
        x = max(0, min(int(self.paper_width), x))
        y = max(0, min(int(self.paper_height), y))
        self.shape_start = (x, y)
        self.shape_preview_id = None

    def update_shape_preview(self, cx, cy):
        """Update temporary preview of the shape while dragging."""
        if not hasattr(self, 'shape_start') or self.shape_start is None:
            return
        x0, y0 = self.shape_start
        x1 = int(max(0, min(int(self.paper_width), cx)))
        y1 = int(max(0, min(int(self.paper_height), cy)))

        try:
            if getattr(self, 'shape_preview_id', None):
                self.canvas.delete(self.shape_preview_id)
        except Exception:
            pass

        color = self.painter.color
        width = self.painter.width

        if self.shape_mode == 'line':
            self.shape_preview_id = self.canvas.create_line(x0, y0, x1, y1, fill=color, width=width, dash=(3,5), tags=("preview",))
        elif self.shape_mode == 'ellipse':
            if getattr(self, 'fill_shape', False):
                self.shape_preview_id = self.canvas.create_oval(x0, y0, x1, y1, fill=color, outline=color, stipple='gray50', tags=("preview",))
            else:
                self.shape_preview_id = self.canvas.create_oval(x0, y0, x1, y1, outline=color, width=width, dash=(3,5), tags=("preview",))

    def finish_shape(self, event=None):
        """Finalize the shape: draw permanent item and rasterize into PIL image."""
        try:
            if not hasattr(self, 'shape_start') or self.shape_start is None:
                return
            if event is not None:
                ex = int(self.canvas.canvasx(event.x))
                ey = int(self.canvas.canvasy(event.y))
            else:
                coords = None
                if getattr(self, 'shape_preview_id', None):
                    coords = self.canvas.coords(self.shape_preview_id)
                if coords and len(coords) >= 4:
                    ex, ey = int(coords[2]), int(coords[3])
                else:
                    ex, ey = self.shape_start

            x0, y0 = self.shape_start
            x1 = max(0, min(int(self.paper_width), ex))
            y1 = max(0, min(int(self.paper_height), ey))

            try:
                if getattr(self, 'shape_preview_id', None):
                    self.canvas.delete(self.shape_preview_id)
            except Exception:
                pass

            color = self.painter.color
            width = self.painter.width

            if self.shape_mode == 'line':
                self.canvas.create_line(x0, y0, x1, y1, fill=color, width=width, capstyle=ROUND, joinstyle=ROUND, tags=("stroke",))
                try:
                    self.draw.line([x0, y0, x1, y1], fill=color, width=width)
                except Exception:
                    self.draw.line([x0, y0, x1, y1], fill=color, width=int(width))
            elif self.shape_mode == 'ellipse':
                if getattr(self, 'fill_shape', False):
                    self.canvas.create_oval(x0, y0, x1, y1, fill=color, outline=color, tags=("stroke",))
                    try:
                        self.draw.ellipse([x0, y0, x1, y1], fill=color, outline=color)
                    except Exception:
                        self.draw.ellipse([x0, y0, x1, y1], fill=color)
                else:
                    self.canvas.create_oval(x0, y0, x1, y1, outline=color, width=width, tags=("stroke",))
                    try:
                        self.draw.ellipse([x0, y0, x1, y1], outline=color, width=width)
                    except Exception:
                        self.draw.ellipse([x0, y0, x1, y1], outline=color)

        finally:
            self.shape_start = None
            self.shape_preview_id = None
            
    def __buttons_create(self):
        """Создает кнопки для управления окном рисования"""
        button_frame = Frame(self.window)
        button_frame.pack(pady=5)
        
        self.color_button = Button(button_frame, text="Choose Color", 
                                  command=self.choose_color)
        self.color_button.pack(side=LEFT, padx=5)
        ButtonDescription(self.color_button, "Выбор цвета для рисования")
        
        self.paper_color_button = Button(button_frame, text="Choose Paper Color", 
                                  command=self.change_paper_color)
        self.paper_color_button.pack(side=LEFT, padx=5)
        ButtonDescription(self.paper_color_button, "Выбор цвета фона холста")
        
        self.clear_button = Button(button_frame, text="Clear Canvas", 
                                  command=self.clear_canvas)
        self.clear_button.pack(side=LEFT, padx=5)
        ButtonDescription(self.clear_button, "Очистка холста")
        
        self.save_button_as = Button(button_frame, text="Save Image as...", 
                                 command=self.save_image_as)
        self.save_button_as.pack(side=LEFT, padx=5)
        ButtonDescription(self.save_button_as, "Сохранение изображения как...")
        
        self.save_button = Button(button_frame, text="Save Image", 
                                 command=self.save_image)
        self.save_button.pack(side=LEFT, padx=5)
        ButtonDescription(self.save_button, "Сохранение изображения")
        
        self.open_button = Button(button_frame, text="Open Image", 
                                  command=self.open_image)
        self.open_button.pack(side=LEFT, padx=5)

        dock_text = "Dock" if self.is_toplevel else "Undock"
        self.dock_button = Button(button_frame, text=dock_text, command=self.toggle_dock)
        self.dock_button.pack(side=LEFT, padx=5)

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
        
        self.brush_combo = Combobox(button_frame, values=["brush", "eraser"], state="readonly")
        
        self.brush_combo.current(0)
        self.brush_combo.pack(side=LEFT, padx=5)
        self.brush_combo.bind("<<ComboboxSelected>>", lambda e: self.painter.set_tool(self.brush_combo.get()))
        ButtonDescription(self.brush_combo, "Выбор инструмента: кисть или ластик")
        
        self.shape_combo = Combobox(button_frame, values=["hand", "line", "ellipse"], state="readonly")
        self.shape_combo.current(0)
        self.shape_combo.pack(side=LEFT, padx=5)
        self.shape_combo.bind("<<ComboboxSelected>>", lambda e: setattr(self, 'shape_mode', self.shape_combo.get()))
        ButtonDescription(self.shape_combo, "Выбор режима рисования: свободно/линия/эллипс")

        self.fill_var = tk.BooleanVar(value=False)
        self.fill_check = Checkbutton(button_frame, text="Fill", variable=self.fill_var, command=lambda: setattr(self, 'fill_shape', self.fill_var.get()))
        self.fill_check.pack(side=LEFT, padx=5)