import os
import time
from tkinter import *
import tkinter as tk
from tkinter.ttk import Combobox, Notebook
from tkinter import colorchooser, messagebox, filedialog, simpledialog
from .WindowCounter import WindowCounter
from ..ButtonDescription import ButtonDescription
from .Painter import Painter
from PIL import Image, ImageTk, ImageDraw
from .ImageBuffer import ImageBuffer


class PaintWindow:
    """Main painting window. Can be embedded (Frame) or top-level (Toplevel).

    Constructed as PaintWindow(parent_widget, app=None, preload_image=None).
    """

    def __init__(self, parent, app=None, preload_image=None):
        # parent is either a Frame (embedded tab) or a Toplevel
        self.app = app
        self.window = parent
        self.is_toplevel = isinstance(parent, tk.Toplevel)

        # state
        self.is_closed = False
        self.is_updated = False
        self.is_saved = False
        self.changes = False
        self.file_path = None

        # default paper size and color
        self.base_paper_width = 800
        self.base_paper_height = 600
        self.paper_width = self.base_paper_width
        self.paper_height = self.base_paper_height
        self.paper_fill = "white"

        # image buffer (PIL) backing
        self.image_buffer = ImageBuffer(self.base_paper_width, self.base_paper_height, color=self.paper_fill)
        self.bg_loaded = False
        self.bg_image_id = None
        self.tk_image = None

        # canvas
        self.canvas = Canvas(self.window, width=self.paper_width, height=self.paper_height, bg='gray90')
        self.canvas.pack(expand=True, fill=BOTH)

        # paper rect and outline
        self.paper_bg = self.canvas.create_rectangle(0, 0, self.paper_width, self.paper_height, fill=self.paper_fill, outline='')
        self.paper_outline = self.canvas.create_rectangle(0, 0, self.paper_width, self.paper_height, outline='black', width=1)

        # resizers
        self.resizer_size = 8
        self.right_resizer = self.canvas.create_rectangle(self.paper_width, self.paper_height/2 - self.resizer_size,
                                                          self.paper_width + self.resizer_size, self.paper_height/2 + self.resizer_size,
                                                          fill='black', tags=('resizer',))
        self.bottom_resizer = self.canvas.create_rectangle(self.paper_width/2 - self.resizer_size, self.paper_height,
                                                           self.paper_width/2 + self.resizer_size, self.paper_height + self.resizer_size,
                                                           fill='black', tags=('resizer',))
        self.corner_resizer = self.canvas.create_rectangle(self.paper_width, self.paper_height,
                                                           self.paper_width + self.resizer_size, self.paper_height + self.resizer_size,
                                                           fill='black', tags=('resizer',))

        # painter (freehand)
        self.painter = Painter(self.canvas, self.image_buffer, self.paper_fill)

        # cursor preview
        self.cursor = self.canvas.create_oval(0, 0, 0, 0, outline="black", width=1, tags="cursor")

        # ensure outline and resizers are on top of background
        try:
            self.canvas.tag_raise(self.paper_outline)
            self.canvas.tag_raise('resizer')
            self.canvas.tag_raise('cursor')
        except Exception:
            pass

        # shape state
        self.shape_mode = 'freehand'
        self.fill_shape = False
        self.shape_preview_id = None
        self.shape_start = None
        # active resizer mode while dragging: 'width', 'height', or 'both'
        self.active_resize_mode = None

        # zoom
        self.zoom_level = 1.0

        # UI buttons
        self.__create_toolbar()

        # preload image if provided
        if preload_image is not None:
            try:
                self.image_buffer.paste_image(preload_image.copy().convert('RGB'))
                self.paper_width, self.paper_height = self.image_buffer.get_image().size
                self.bg_loaded = True
                self._refresh_bg_image()
                self.canvas.coords(self.paper_bg, 0, 0, self.paper_width, self.paper_height)
                self.canvas.coords(self.paper_outline, 0, 0, self.paper_width, self.paper_height)
                self.update_resizers()
            except Exception:
                pass

        # bindings
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset)
        self.canvas.bind("<Button-1>", self.on_button_press)
        self.canvas.bind("<Motion>", self.update_oval)
        self.canvas.bind("<Configure>", self.on_canvas_configure)

        if self.is_toplevel:
            try:
                self.window.title("Paint Window")
                self.window.protocol("WM_DELETE_WINDOW", self.close_window)
                self.window.bind("<Control-w>", lambda e: self.close_window())
                self.window.bind("<Control-s>", lambda e: self.save_image())
                self.window.bind("<Control-x>", lambda e: self.save_image_as())
            except Exception:
                pass

    # ----------------- UI creation -----------------
    def __create_toolbar(self):
        # create a small frame above canvas if parent supports pack
        try:
            container = Frame(self.window)
            container.pack(fill=X)
        except Exception:
            container = self.window

        toolbar_notebook = Notebook(container)
        toolbar_notebook.pack(side=LEFT, fill=X, expand=True)

        # Brushes tab
        brushes_tab = Frame(toolbar_notebook)
        toolbar_notebook.add(brushes_tab, text='Brush')
        self.color_button = Button(brushes_tab, text="Choose Color", command=self.choose_color)
        self.color_button.pack(side=LEFT, padx=5)
        self.size_scale = Scale(brushes_tab, from_=1, to=50, orient=HORIZONTAL, command=self.change_size)
        self.size_scale.set(self.painter.width)
        self.size_scale.pack(side=LEFT, padx=5)
        self.brush_combo = Combobox(brushes_tab, values=["brush", "eraser"], state="readonly")
        self.brush_combo.current(0)
        self.brush_combo.pack(side=LEFT, padx=5)
        self.brush_combo.bind("<<ComboboxSelected>>", lambda e: self.painter.set_tool(self.brush_combo.get()))

        # Shapes tab
        shapes_tab = Frame(toolbar_notebook)
        toolbar_notebook.add(shapes_tab, text='Shapes')
        self.shape_combo = Combobox(shapes_tab, values=["freehand", "line", "ellipse", "cylinder", "text", "fill"], state="readonly")
        self.shape_combo.current(0)
        self.shape_combo.pack(side=LEFT, padx=5)
        self.shape_combo.bind("<<ComboboxSelected>>", lambda e: setattr(self, 'shape_mode', self.shape_combo.get()))
        self.fill_var = tk.BooleanVar(value=False)
        self.fill_check = Checkbutton(shapes_tab, text="Fill", variable=self.fill_var, command=lambda: setattr(self, 'fill_shape', self.fill_var.get()))
        self.fill_check.pack(side=LEFT, padx=5)

        # Tools tab
        tools_tab = Frame(toolbar_notebook)
        toolbar_notebook.add(tools_tab, text='Tools')
        self.paper_color_button = Button(tools_tab, text="Paper Color", command=self.change_paper_color)
        self.paper_color_button.pack(side=LEFT, padx=5)
        self.clear_button = Button(tools_tab, text="Clear Canvas", command=self.clear_canvas)
        self.clear_button.pack(side=LEFT, padx=5)
        self.save_button_as = Button(tools_tab, text="Save Image as...", command=self.save_image_as)
        self.save_button_as.pack(side=LEFT, padx=5)
        self.save_button = Button(tools_tab, text="Save Image", command=self.save_image)
        self.save_button.pack(side=LEFT, padx=5)
        self.open_button = Button(tools_tab, text="Open Image", command=self.open_image)
        self.open_button.pack(side=LEFT, padx=5)
        self.dock_button = Button(tools_tab, text=("Dock" if self.is_toplevel else "Undock"), command=self.toggle_dock)
        self.dock_button.pack(side=LEFT, padx=5)
        self.close_button = Button(tools_tab, text="Close Window", command=self.close_window)
        self.close_button.pack(side=LEFT, padx=5)
        self.zoom_in_btn = Button(tools_tab, text="Zoom In", command=lambda: self.zoom(1.25))
        self.zoom_in_btn.pack(side=LEFT, padx=5)
        self.zoom_out_btn = Button(tools_tab, text="Zoom Out", command=lambda: self.zoom(0.8))
        self.zoom_out_btn.pack(side=LEFT, padx=5)
        self.zoom_reset_btn = Button(tools_tab, text="Reset Zoom", command=self.reset_zoom)
        self.zoom_reset_btn.pack(side=LEFT, padx=5)

    # ----------------- Event handlers -----------------
    def paint(self, event):
        if self.is_closed:
            return
        cx = self.canvas.canvasx(event.x)
        cy = self.canvas.canvasy(event.y)

        self.is_updated = True
        if not self.changes:
            self.changes = True
            try:
                self.changes_label = Label(self.window, text="Changes not saved", font=(15))
                self.changes_label.pack(side=LEFT, padx=5)
            except Exception:
                pass

        # resizing handles: if user started dragging a resizer, continue resizing
        try:
            if getattr(self, 'active_resize_mode', None):
                evt = type('E', (), {'x': int(cx), 'y': int(cy)})()
                self.resize_canvas(evt, mode=self.active_resize_mode)
                return
            # fallback: detect resizer under cursor (if drag started without press handler)
            items = self.canvas.find_overlapping(cx, cy, cx, cy)
            for it in items:
                if 'resizer' in self.canvas.gettags(it):
                    mode = 'both'
                    if it == self.right_resizer:
                        mode = 'width'
                    elif it == self.bottom_resizer:
                        mode = 'height'
                    evt = type('E', (), {'x': int(cx), 'y': int(cy)})()
                    self.resize_canvas(evt, mode=mode)
                    return
        except Exception:
            pass

        if getattr(self, 'shape_mode', 'freehand') != 'freehand':
            try:
                self.update_shape_preview(cx, cy)
            except Exception:
                pass
            return

        # freehand painting
        self.painter.paint(cx, cy, self.paper_width, self.paper_height, getattr(self, 'is_resizing', False))
        try:
            self.canvas.tag_raise(self.paper_outline)
            self.canvas.tag_raise('resizer')
            self.canvas.tag_raise('cursor')
        except Exception:
            pass

    def reset(self, event):
        self.is_resizing = False
        if hasattr(self, 'painter'):
            self.painter.reset_coords()
        # clear active resizer when mouse released
        try:
            self.active_resize_mode = None
        except Exception:
            pass
        try:
            if getattr(self, 'shape_mode', 'freehand') != 'freehand':
                self.finish_shape(event)
        except Exception:
            pass

    def on_button_press(self, event):
        mode = getattr(self, 'shape_mode', 'freehand')
        # detect if the click started on a resizer; if so, start resize drag
        try:
            cx = self.canvas.canvasx(event.x)
            cy = self.canvas.canvasy(event.y)
            items = self.canvas.find_overlapping(cx, cy, cx, cy)
            for it in items:
                if 'resizer' in self.canvas.gettags(it):
                    if it == self.right_resizer:
                        self.active_resize_mode = 'width'
                    elif it == self.bottom_resizer:
                        self.active_resize_mode = 'height'
                    else:
                        self.active_resize_mode = 'both'
                    self.is_resizing = True
                    return
        except Exception:
            pass

        if mode == 'freehand':
            return

        x = int(self.canvas.canvasx(event.x))
        y = int(self.canvas.canvasy(event.y))
        x = max(0, min(int(self.paper_width), x))
        y = max(0, min(int(self.paper_height), y))

        if mode == 'text':
            txt = simpledialog.askstring('Text', 'Enter text:', parent=self.window if self.is_toplevel else None)
            if txt:
                try:
                    self.image_buffer.draw_text((x, y), txt, fill=self.painter.color)
                    self.canvas.create_text(x, y, text=txt, fill=self.painter.color, anchor=NW, tags=('stroke',))
                except Exception:
                    pass
            return

        if mode == 'fill':
            try:
                # Rasterize current canvas (paper + strokes) into an image, then flood-fill that image.
                w, h = int(self.paper_width), int(self.paper_height)
                tmp_img = self.build_export_image()
                # perform flood fill on tmp_img using a temporary ImageBuffer
                tmp_buf = ImageBuffer(w, h)
                tmp_buf.image = tmp_img
                tmp_buf.draw = ImageDraw.Draw(tmp_buf.image)
                tmp_buf.flood_fill(x, y, self.painter.color)
                # replace main image_buffer content with the filled image
                try:
                    self.image_buffer.image = tmp_buf.get_image()
                    self.image_buffer.draw = ImageDraw.Draw(self.image_buffer.image)
                except Exception:
                    pass
                # show the updated raster as the paper background (make paper transparent)
                self.bg_loaded = True
                try:
                    self.canvas.itemconfig(self.paper_bg, fill='')
                except Exception:
                    pass
                self._refresh_bg_image()
            except Exception:
                pass
            return

        # start other shapes
        self.shape_start = (x, y)
        self.shape_preview_id = None

    def update_shape_preview(self, cx, cy):
        if not self.shape_start:
            return
        x0, y0 = self.shape_start
        x1 = int(max(0, min(int(self.paper_width), cx)))
        y1 = int(max(0, min(int(self.paper_height), cy)))
        try:
            if self.shape_preview_id:
                if isinstance(self.shape_preview_id, list):
                    for pid in self.shape_preview_id:
                        try:
                            self.canvas.delete(pid)
                        except Exception:
                            pass
                else:
                    try:
                        self.canvas.delete(self.shape_preview_id)
                    except Exception:
                        pass
        except Exception:
            pass

        color = self.painter.color
        width = self.painter.width

        if self.shape_mode == 'line':
            self.shape_preview_id = self.canvas.create_line(x0, y0, x1, y1, fill=color, width=width, dash=(3,5), tags=('preview',))
        elif self.shape_mode == 'ellipse':
            if self.fill_shape:
                self.shape_preview_id = self.canvas.create_oval(x0, y0, x1, y1, fill=color, outline=color, stipple='gray50', tags=('preview',))
            else:
                self.shape_preview_id = self.canvas.create_oval(x0, y0, x1, y1, outline=color, width=width, dash=(3,5), tags=('preview',))
        elif self.shape_mode == 'cylinder':
            h = max(2, abs(y1 - y0))
            ellipse_h = max(4, int(h * 0.15))
            top = (x0, y0, x1, y0 + ellipse_h)
            bottom = (x0, y1 - ellipse_h, x1, y1)
            rect = (x0, y0 + ellipse_h/2, x1, y1 - ellipse_h/2)
            ids = []
            ids.append(self.canvas.create_oval(*top, outline=color, dash=(3,5), tags=('preview',)))
            ids.append(self.canvas.create_rectangle(*rect, outline=color, dash=(3,5), tags=('preview',)))
            ids.append(self.canvas.create_oval(*bottom, outline=color, dash=(3,5), tags=('preview',)))
            self.shape_preview_id = ids

    def finish_shape(self, event=None):
        if not self.shape_start:
            return
        if event is not None:
            ex = int(self.canvas.canvasx(event.x))
            ey = int(self.canvas.canvasy(event.y))
        else:
            coords = None
            if self.shape_preview_id:
                try:
                    if isinstance(self.shape_preview_id, list):
                        coords = self.canvas.coords(self.shape_preview_id[0])
                    else:
                        coords = self.canvas.coords(self.shape_preview_id)
                except Exception:
                    coords = None
            if coords and len(coords) >= 4:
                ex, ey = int(coords[2]), int(coords[3])
            else:
                ex, ey = self.shape_start

        x0, y0 = self.shape_start
        x1 = max(0, min(int(self.paper_width), ex))
        y1 = max(0, min(int(self.paper_height), ey))

        # normalize coordinates to integers for reliable PIL drawing
        try:
            x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        except Exception:
            x0, y0, x1, y1 = map(lambda v: int(round(v)), (x0, y0, x1, y1))

        try:
            if self.shape_preview_id:
                if isinstance(self.shape_preview_id, list):
                    for pid in self.shape_preview_id:
                        try:
                            self.canvas.delete(pid)
                        except Exception:
                            pass
                else:
                    try:
                        self.canvas.delete(self.shape_preview_id)
                    except Exception:
                        pass
        except Exception:
            pass

        color = self.painter.color
        width = self.painter.width

        if self.shape_mode == 'line':
            self.canvas.create_line(x0, y0, x1, y1, fill=color, width=width, capstyle=ROUND, joinstyle=ROUND, tags=('stroke',))
            try:
                self.image_buffer.draw_line([x0, y0, x1, y1], fill=color, width=width)
            except Exception:
                pass
        elif self.shape_mode == 'ellipse':
            if self.fill_shape:
                self.canvas.create_oval(x0, y0, x1, y1, fill=color, outline=color, tags=('stroke',))
                try:
                    self.image_buffer.draw_ellipse([x0, y0, x1, y1], fill=color, outline=color)
                except Exception:
                    pass
            else:
                self.canvas.create_oval(x0, y0, x1, y1, outline=color, width=width, tags=('stroke',))
                try:
                    self.image_buffer.draw_ellipse([x0, y0, x1, y1], outline=color, width=width)
                except Exception:
                    pass
        elif self.shape_mode == 'cylinder':
            h = max(2, abs(y1 - y0))
            ellipse_h = max(4, int(h * 0.15))
            # compute float positions, then convert to ints for PIL
            top_bbox = [x0, y0, x1, int(y0 + ellipse_h)]
            bottom_bbox = [x0, int(y1 - ellipse_h), x1, y1]
            rect_bbox = [x0, int(y0 + ellipse_h/2), x1, int(y1 - ellipse_h/2)]
            if self.fill_shape:
                self.canvas.create_rectangle(*rect_bbox, fill=color, outline=color, tags=('stroke',))
                self.canvas.create_oval(*top_bbox, fill=color, outline=color, tags=('stroke',))
                self.canvas.create_oval(*bottom_bbox, fill=color, outline=color, tags=('stroke',))
                try:
                    self.image_buffer.draw_ellipse(top_bbox, fill=color, outline=color)
                    self.image_buffer.fill_rect(rect_bbox, fill=color)
                    self.image_buffer.draw_ellipse(bottom_bbox, fill=color, outline=color)
                except Exception:
                    pass
            else:
                self.canvas.create_oval(*top_bbox, outline=color, width=width, tags=('stroke',))
                self.canvas.create_rectangle(*rect_bbox, outline=color, width=width, tags=('stroke',))
                self.canvas.create_oval(*bottom_bbox, outline=color, width=width, tags=('stroke',))
                try:
                    self.image_buffer.draw_ellipse(top_bbox, outline=color, width=width)
                    self.image_buffer.draw_ellipse(bottom_bbox, outline=color, width=width)
                    self.image_buffer.draw_line([rect_bbox[0], rect_bbox[1], rect_bbox[0], rect_bbox[3]], fill=color, width=width)
                    self.image_buffer.draw_line([rect_bbox[2], rect_bbox[1], rect_bbox[2], rect_bbox[3]], fill=color, width=width)
                except Exception:
                    pass

        self.shape_start = None
        self.shape_preview_id = None

    # ----------------- Helpers -----------------
    def _refresh_bg_image(self):
        try:
            self.tk_image = ImageTk.PhotoImage(self.image_buffer.get_image())
            if self.bg_image_id:
                self.canvas.itemconfig(self.bg_image_id, image=self.tk_image)
            else:
                self.bg_image_id = self.canvas.create_image(0, 0, anchor=NW, image=self.tk_image, tags='bg_image')
                self.canvas.tag_lower('bg_image')
            # keep resizers and outlines above the background image
            try:
                self.canvas.tag_raise(self.paper_outline)
                self.canvas.tag_raise('resizer')
            except Exception:
                pass
        except Exception:
            pass

    def update_resizers(self):
        w, h = self.paper_width, self.paper_height
        s = self.resizer_size
        try:
            self.canvas.coords(self.right_resizer, w, h/2 - s, w + s, h/2 + s)
            self.canvas.coords(self.bottom_resizer, w/2 - s, h, w/2 + s, h + s)
            self.canvas.coords(self.corner_resizer, w, h, w + s, h + s)
        except Exception:
            pass
        try:
            self.canvas.tag_raise(self.paper_outline)
            self.canvas.tag_raise('resizer')
            self.canvas.tag_raise('cursor')
        except Exception:
            pass

    def resize_canvas(self, event, mode='both'):
        self.is_resizing = True
        old_w, old_h = float(self.paper_width), float(self.paper_height)
        if mode in ('both', 'width'):
            self.paper_width = max(10, event.x)
        if mode in ('both', 'height'):
            self.paper_height = max(10, event.y)
        new_w, new_h = float(self.paper_width), float(self.paper_height)
        try:
            self.canvas.coords(self.paper_bg, 0, 0, self.paper_width, self.paper_height)
            self.canvas.coords(self.paper_outline, 0, 0, self.paper_width, self.paper_height)
        except Exception:
            pass
        try:
            self.image_buffer.resize(int(self.paper_width), int(self.paper_height))
            if self.bg_loaded:
                self._refresh_bg_image()
        except Exception:
            pass
        try:
            sx = new_w / old_w if old_w else 1.0
            sy = new_h / old_h if old_h else 1.0
            for item in self.canvas.find_withtag('stroke'):
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

    def zoom(self, factor: float):
        try:
            new_w = max(10, int(self.paper_width * factor))
            new_h = max(10, int(self.paper_height * factor))
            evt = type('E', (), {'x': int(new_w), 'y': int(new_h)})()
            self.resize_canvas(evt, mode='both')
            self.zoom_level *= factor
        except Exception:
            pass

    def reset_zoom(self):
        try:
            evt = type('E', (), {'x': int(self.base_paper_width), 'y': int(self.base_paper_height)})()
            self.resize_canvas(evt, mode='both')
            self.zoom_level = 1.0
        except Exception:
            pass

    def resize_pillow_image(self):
        w, h = int(self.paper_width), int(self.paper_height)
        if w <= 0 or h <= 0:
            return
        try:
            if (w, h) != self.image_buffer.get_image().size:
                self.image_buffer.resize(w, h)
            if self.bg_loaded:
                self._refresh_bg_image()
            else:
                if self.bg_image_id:
                    try:
                        self.canvas.delete(self.bg_image_id)
                    except Exception:
                        pass
                    self.bg_image_id = None
        except Exception:
            pass

    def update_oval(self, event):
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        r = max(1, int(self.painter.width / 2))
        try:
            self.canvas.coords(self.cursor, x - r, y - r, x + r, y + r)
            self.canvas.tag_raise('cursor')
        except Exception:
            pass

    def choose_color(self):
        color_code = colorchooser.askcolor(parent=self.window if self.is_toplevel else None)
        if color_code and color_code[1]:
            self.painter.set_color(color_code[1])

    def change_paper_color(self):
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
            self.painter = Painter(self.canvas, self.image_buffer, self.paper_fill)
            try:
                self.canvas.itemconfig(self.paper_bg, fill=self.paper_fill)
            except Exception:
                pass

    def clear_canvas(self):
        self.is_updated = True
        try:
            self.canvas.delete('stroke')
        except Exception:
            pass
        try:
            self.image_buffer.fill_rect([0, 0, int(self.paper_width), int(self.paper_height)], fill=self.paper_fill)
        except Exception:
            pass

    def toggle_dock(self):
        try:
            current_img = self.build_export_image()
        except Exception:
            current_img = None
        if not self.is_toplevel and getattr(self, 'app', None):
            try:
                self.app.create_new_window_from_image(current_img)
                try:
                    self.app.detach_tab(self)
                except Exception:
                    pass
            except Exception:
                pass
        elif self.is_toplevel and getattr(self, 'app', None):
            try:
                if current_img is not None:
                    self.app.dock_image_as_tab(current_img)
                self.close_window()
            except Exception:
                pass

    def save_image_as(self, event=None):
        if self.is_closed:
            return
        final_save = self.build_export_image()
        default_name = f"paint_{time.strftime('%Y%m%d_%H%M%S')}"
        file_path = filedialog.asksaveasfilename(defaultextension="", initialfile=default_name,
                                                 filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("BMP files", "*.bmp"), ("All files", "*.*")],
                                                 parent=self.window if self.is_toplevel else None)
        if file_path:
            try:
                self.changes = False
                to_save = final_save
                ext = os.path.splitext(file_path)[1].lower()
                if ext in ['.jpg', '.jpeg']:
                    save_img = to_save.convert('RGB')
                else:
                    save_img = to_save
                save_img.save(file_path)
                self.file_path = file_path
                self.is_saved = True
                if self.is_toplevel:
                    try:
                        self.window.title(f"Paint Window - {os.path.basename(file_path)}")
                    except Exception:
                        pass
                messagebox.showinfo('Success', f'Image saved successfully:\n{file_path}', parent=self.window if self.is_toplevel else None)
            except Exception as e:
                messagebox.showerror('Error', f'Failed to save image:\n{e}', parent=self.window if self.is_toplevel else None)

    def save_image(self, event=None):
        if self.is_closed:
            return
        if self.file_path:
            self.saving()
        else:
            self.save_image_as()

    def saving(self):
        try:
            final_save = self.build_export_image()
            ext = os.path.splitext(self.file_path)[1].lower() if self.file_path else ''
            if ext in ['.jpg', '.jpeg']:
                img_to_write = final_save.convert('RGB')
            else:
                img_to_write = final_save
            img_to_write.save(self.file_path)
        except Exception as e:
            messagebox.showerror('Save Error', f'Could not save file:\n{e}', parent=self.window if self.is_toplevel else None)

    def close_window(self, event=None):
        if self.is_updated and not self.is_saved:
            ans = messagebox.askyesnocancel('Unsaved Changes', 'You have unsaved changes. Do you want to save before exiting?', parent=self.window if self.is_toplevel else None)
            if ans is True:
                self.save_image()
            elif ans is None:
                return
        try:
            WindowCounter().reduce_count()
        except Exception:
            pass
        self.is_closed = True
        try:
            if self.is_toplevel:
                self.window.destroy()
            else:
                # embedded frame: destroy associated widgets
                try:
                    self.canvas.destroy()
                except Exception:
                    pass
        except Exception:
            pass

    def on_canvas_configure(self, event):
        self.visible_width = event.width
        self.visible_height = event.height
        self.visible_x = self.canvas.canvasx(0)
        self.visible_y = self.canvas.canvasy(0)

    def change_size(self, new_size):
        try:
            self.painter.set_width(int(new_size))
        except Exception:
            pass

    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[('Image files', '*.png *.jpg *.jpeg *.bmp *.gif'), ('All files', '*.*')], parent=self.window if self.is_toplevel else None)
        if file_path:
            try:
                opened_image = Image.open(file_path)
                self.image_buffer.paste_image(opened_image.convert('RGB'))
                self.paper_width, self.paper_height = self.image_buffer.get_image().size
                self.bg_loaded = True
                self._refresh_bg_image()
                self.canvas.coords(self.paper_bg, 0, 0, self.paper_width, self.paper_height)
                self.canvas.coords(self.paper_outline, 0, 0, self.paper_width, self.paper_height)
                self.update_resizers()
                self.file_path = file_path
                if self.is_toplevel:
                    try:
                        self.window.title(f'Paint Window - {os.path.basename(file_path)}')
                    except Exception:
                        pass
            except Exception as e:
                messagebox.showerror('Error', f'Could not open image:\n{e}', parent=self.window if self.is_toplevel else None)

    def build_export_image(self):
        w, h = int(self.paper_width), int(self.paper_height)
        if w <= 0 or h <= 0:
            return Image.new('RGB', (1, 1), 'white')
        bg = Image.new('RGB', (w, h), self.paper_fill or 'white')
        try:
            if self.bg_loaded and self.image_buffer:
                try:
                    buf = self.image_buffer.get_image()
                    if buf.size != (w, h):
                        buf = buf.resize((w, h))
                    bg.paste(buf)
                except Exception:
                    pass
        except Exception:
            pass

        draw = ImageDraw.Draw(bg)
        try:
            for item in self.canvas.find_withtag('stroke'):
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
