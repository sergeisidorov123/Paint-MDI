from tkinter import *
from tkinter import messagebox
from tkinter import ttk
import os, json, importlib, importlib.util

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
        
        self.selected_plugins_for_new_windows = None
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
    
    def create_new_tab(self, event=None, image=None, file_path=None, is_saved=False, is_updated=False, changes=False):
        new_tab = ttk.Frame(self.notebook)
        self.notebook.add(new_tab, text=f"Paint {self.notebook.index('end') + 1}")

        pw = PaintWindow(new_tab, app=self, preload_image=image, file_path=file_path, is_saved=is_saved, is_updated=is_updated, changes=changes, allowed_plugins=self.selected_plugins_for_new_windows)
        self.windows.append(pw)
        self.tab_to_pw[new_tab] = pw

        self.notebook.select(new_tab)

    def create_new_window_from_image(self, image=None, file_path=None, is_saved=False, is_updated=False, changes=False):
        top = Toplevel(self.root)
        pw = PaintWindow(top, app=self, preload_image=image, file_path=file_path, is_saved=is_saved, is_updated=is_updated, changes=changes, allowed_plugins=self.selected_plugins_for_new_windows)
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

    def dock_image_as_tab(self, image, file_path=None, is_saved=False, is_updated=False, changes=False):
        self.create_new_tab(image=image, file_path=file_path, is_saved=is_saved, is_updated=is_updated, changes=changes)

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
        
    def __plugins_info(self):
        """Открыть селектор для выбора плагинов для новых окон Paint"""
        try:
            plugins_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'plugins'))
            if not os.path.isdir(plugins_dir):
                os.makedirs(plugins_dir, exist_ok=True)
            cfg_path = os.path.join(plugins_dir, 'plugins_config.json')
            
            # Прочитать текущую конфигурацию
            cfg = None
            try:
                if os.path.isfile(cfg_path):
                    with open(cfg_path, 'r', encoding='utf-8') as fh:
                        cfg = json.load(fh)
            except Exception:
                cfg = None

            # Получить список всех файлов плагинов
            files = sorted([f for f in os.listdir(plugins_dir) if f.endswith('.py') and not f.startswith('__')])

            # Helper для получения PLUGIN_NAME
            def get_plugin_display_name(fname):
                try:
                    fpath = os.path.join(plugins_dir, fname)
                    spec = importlib.util.spec_from_file_location(f'temp_{fname[:-3]}', fpath)
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        return getattr(module, 'PLUGIN_NAME', None) or os.path.splitext(fname)[0]
                except Exception:
                    pass
                return os.path.splitext(fname)[0]

            # Создать окно селектора
            win = Toplevel(self.root)
            win.title('Select Plugins for New Paint Windows')
            win.geometry('360x400')
            vars_map = {}  # filename -> var
            display_map = {}  # filename -> display_name

            # Создать список с прокруткой
            frm = Frame(win)
            frm.pack(fill=BOTH, expand=True, padx=8, pady=8)
            canvas = Canvas(frm)
            scrollbar = ttk.Scrollbar(frm, orient='vertical', command=canvas.yview)
            list_frame = Frame(canvas)
            list_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
            canvas.create_window((0, 0), window=list_frame, anchor='nw')
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side=LEFT, fill=BOTH, expand=True)
            scrollbar.pack(side=RIGHT, fill=Y)

            # Получить сохраненные значения
            cfg_plugins = {}
            if cfg and isinstance(cfg.get('plugins'), dict):
                cfg_plugins = cfg.get('plugins')

            # Создать чекбоксы для каждого плагина
            for f in files:
                val = bool(cfg_plugins.get(f, True))
                v = BooleanVar(value=val)
                # Показывать дружественное имя вместо имени файла
                disp = get_plugin_display_name(f)
                display_map[f] = disp
                cb = Checkbutton(list_frame, text=disp, variable=v)
                cb.pack(anchor='w')
                vars_map[f] = v

            def apply_selection():
                selected = [fname for fname, var in vars_map.items() if var.get()]
                # Сохранить выбор в переменную приложения
                self.selected_plugins_for_new_windows = selected if selected else None
                # Сохранить в файл конфигурации
                try:
                    plugins_map = {}
                    for f in files:
                        plugins_map[f] = True if f in selected else False
                    cfg_out = {'mode': 'manual', 'plugins': plugins_map}
                    with open(cfg_path, 'w', encoding='utf-8') as fh:
                        json.dump(cfg_out, fh, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                try:
                    win.destroy()
                except Exception:
                    pass

            # Кнопки
            btns = Frame(win)
            btns.pack(fill=X, padx=8, pady=6)
            ok = Button(btns, text='OK', command=apply_selection)
            ok.pack(side=LEFT, padx=4)
            cancel = Button(btns, text='Cancel', command=lambda: win.destroy())
            cancel.pack(side=LEFT, padx=4)
        except Exception as e:
            messagebox.showerror('Plugins', f'Could not open plugins selector:\n{e}')
        
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
        
        plugin_button = Button(self.root, 
                              text="Plugins", 
                              command=self.__plugins_info,
                              font=("Arial", 12),
                              padx=20, pady=10)
        plugin_button.pack(pady=10)
        ButtonDescription(plugin_button, "Плагины для приложения")
        
        exit_button = Button(self.root, 
                            text="Exit", 
                            command=self.__exit_app,
                            font=("Arial", 12),
                            padx=20, pady=10)
        exit_button.pack(pady=10)
        ButtonDescription(exit_button, "Выход из приложения")
        
        