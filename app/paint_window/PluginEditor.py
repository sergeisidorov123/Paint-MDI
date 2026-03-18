import os
from tkinter import Toplevel, Frame, Label, Button, Text, Scrollbar, filedialog, messagebox, BOTH, RIGHT, LEFT, END


class PluginEditor:
    
    def __init__(self, parent, plugins_dir, on_saved=None):
        self.parent = parent
        self.plugins_dir = plugins_dir
        self.on_saved = on_saved
        
        # Пример кода плагина
        self.template = '''from PIL import Image

PLUGIN_NAME = "Plugin"

def process_image(img: Image.Image) -> Image.Image:
    """Обработка изображения"""
    return img
'''
        
        # Создание окна
        self.window = Toplevel(parent)
        self.window.title("New Plugin")
        self.window.geometry("600x600")
        
        # Текстовое поле с примером
        text_frame = Frame(self.window)
        text_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        Label(text_frame, text="Plugin Code:", font=("Arial", 10, "bold")).pack(anchor='w')
        
        # Текстовое поле со скроллбаром
        scroll = Scrollbar(text_frame)
        scroll.pack(side=RIGHT, fill='y')
        
        self.code_text = Text(text_frame, font=("Courier", 10), yscrollcommand=scroll.set)
        self.code_text.pack(fill=BOTH, expand=True, side=LEFT)
        scroll.config(command=self.code_text.yview)
        
        # Вставляем пример кода
        self.code_text.insert('1.0', self.template)
        
        # Кнопка сохранить
        btn_frame = Frame(self.window)
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        Button(btn_frame, text="Save Plugin", command=self._save_plugin, font=("Arial", 11)).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Cancel", command=self.window.destroy, font=("Arial", 11)).pack(side=LEFT, padx=5)
    
    def _save_plugin(self):
        code = self.code_text.get('1.0', END)
        
        if not code.strip():
            messagebox.showerror("Error", "Code is empty")
            return
        
        filename = filedialog.asksaveasfilename(
            initialdir=self.plugins_dir,
            defaultextension=".py",
            filetypes=[("Python files", "*.py")],
            parent=self.window
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(code)
            
            messagebox.showinfo("Success", f"Plugin saved: {os.path.basename(filename)}", parent=self.window)
            
            if self.on_saved:
                self.on_saved()
            
            self.window.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save: {str(e)}")
