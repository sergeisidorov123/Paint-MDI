from tkinter import *
from tkinter import messagebox
from tkinter import ttk

from app.paint_window.PaintWindow import PaintWindow
from app.ButtonDescription import ButtonDescription



class PaintApp:
    """Главный класс приложения"""
    
    def __init__(self, root):
        """Создает главное окно приложения"""
        self.root = root
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")
        self.root.title("Paint Application")
        self.root.geometry("400x300")
        self.root.wm_attributes('-zoomed', True)
        welcome_label = Label(self.root, 
                             text="Paint MDI", 
                             font=("Arial", 16))
        welcome_label.pack(pady=25)
        
        self.__buttons_create()
        
        self.windows = []
        self.tab_to_pw = {}
        
        self.root.protocol("WM_DELETE_WINDOW", self.__exit_app)
        
        self.root.bind_all("<Control-n>", lambda e: self.create_new_tab())
        self.root.bind_all("<Control-q>", lambda e: self.__exit_app())
        self.root.bind_all("<Control-s>", self._dispatch_save)
        self.root.bind_all("<Control-x>", self._dispatch_save_as)
        self.root.bind_all("<Control-w>", self._dispatch_close_active)
        self.root.bind_all("<Control-equal>", self._dispatch_zoom)
        
        self.root.mainloop()
    
    def create_new_tab(self, event=None, image=None):
        new_tab = ttk.Frame(self.notebook)
        self.notebook.add(new_tab, text=f"Paint {self.notebook.index('end') + 1}")

        pw = PaintWindow(new_tab, app=self, preload_image=image)
        self.windows.append(pw)
        self.tab_to_pw[new_tab] = pw

        self.notebook.select(new_tab)

    def create_new_window_from_image(self, image=None):
        top = Toplevel(self.root)
        pw = PaintWindow(top, app=self, preload_image=image)
        self.windows.append(pw)
        return pw

    def detach_tab(self, paintwindow):
        try:
            tab = paintwindow.window
            self.notebook.forget(tab)
            try:
                del self.tab_to_pw[tab]
            except Exception:
                pass
            try:
                paintwindow.window.destroy()
            except Exception:
                pass
            try:
                self.windows.remove(paintwindow)
            except Exception:
                pass
        except Exception:
            pass

    def dock_image_as_tab(self, image):
        self.create_new_tab(image=image)

    def _get_active_paintwindow(self):
        try:
            sel = self.notebook.select()
            if not sel:
                return None
            frame = self.root.nametowidget(sel)
            return self.tab_to_pw.get(frame)
        except Exception:
            return None

    def _dispatch_save(self, event=None):
        pw = self._get_active_paintwindow()
        if pw:
            try:
                pw.save_image()
            except Exception:
                pass

    def _dispatch_save_as(self, event=None):
        pw = self._get_active_paintwindow()
        if pw:
            try:
                pw.save_image_as()
            except Exception:
                pass

    def _dispatch_close_active(self, event=None):
        pw = self._get_active_paintwindow()
        if pw:
            try:
                pw.close_window()
            except Exception:
                pass
    
    def _dispatch_zoom(self, event=None):
        pw = self._get_active_paintwindow()
        if pw:
            try:
                pw.zoom(1.25)
            except Exception:
                pass
    
    def __exit_app(self, event=None):
        """Закрывает приложение"""
        for window in self.windows:
            if not window.is_closed:
                window.close_window()
        self.root.quit()
        self.root.destroy()
        
    def __about_app(self):
        """Показывает информацию о приложении"""
        messagebox.showinfo("About Paint App", 
                            "Paint MDI Application\n\nLaboratory work num 1\n\nCreated by Sidorov Sergei, RIS-24-1")
        
    def __buttons_create(self):
        """Создает кнопки для управления приложением"""
        new_paint_button = Button(self.root, 
                                 text="Create New Paint Window", 
                                 command=self.create_new_tab,
                                 font=("Arial", 12),
                                 padx=20, pady=10)
        new_paint_button.pack(pady=10)
        ButtonDescription(new_paint_button, "Создание нового окна для рисования")
        
        about_button = Button(self.root, 
                              text="About", 
                              command=self.__about_app,
                              font=("Arial", 12),
                              padx=20, pady=10)
        about_button.pack(pady=10)
        ButtonDescription(about_button, "Информация о приложении")
        
        exit_button = Button(self.root, 
                            text="Exit", 
                            command=self.__exit_app,
                            font=("Arial", 12),
                            padx=20, pady=10)
        exit_button.pack(pady=10)
        ButtonDescription(exit_button, "Выход из приложения")