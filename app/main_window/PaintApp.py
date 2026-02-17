from tkinter import *
from tkinter import messagebox

from app.paint_window.PaintWindow import PaintWindow
from app.ButtonDescription import ButtonDescription



class PaintApp:
    """Главный класс приложения"""
    
    def __init__(self):
        """Создает главное окно приложения"""
        self.root = Tk()
        #self.notebook = ttk.Notebook(self.root)
        #self.notebook.pack(expand=True, fill="both")
        self.root.title("Paint Application")
        self.root.geometry("400x300")
        
        welcome_label = Label(self.root, 
                             text="Paint MDI", 
                             font=("Arial", 16))
        welcome_label.pack(pady=25)
        
        self.__buttons_create()
        
        self.windows = []
        
        self.root.protocol("WM_DELETE_WINDOW", self.__exit_app)
        
        self.root.bind_all("<Control-n>", self.__create_paint_window)
        self.root.bind_all("<Control-q>", self.__exit_app)
        
        self.root.mainloop()
    
    def __create_paint_window(self, event=None):
        """Создает новое окно для рисования"""
        paint_window = PaintWindow(self.root)
        self.windows.append(paint_window)
    
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
                                 command=self.__create_paint_window,
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